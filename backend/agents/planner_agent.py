# 行程规划编排器: LangGraph 按固定流程编排专业 Agent
# 流程: 天气 → 景点 → 酒店 → LLM 整合成行程 JSON
# 用确定性图编排而不是让 LLM 自由发挥: 可控、可测、省钱
import datetime
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from agents.attraction_agent import build_attraction_agent
from agents.hotel_agent import build_hotel_agent
from agents.llm_config import get_llm
from agents.weather_agent import build_weather_agent
from app.core.exceptions import AgentError
from app.core.logging import logger
from app.schemas.itinerary import Itinerary
from app.schemas.request import TripRequest


class PlannerState(TypedDict):
    """编排状态: 各节点读写的字段"""

    request: dict        # 前端行程请求(TripRequest 转 dict)
    weather: str         # 天气 Agent 结果
    attractions: str     # 景点 Agent 结果
    hotels: str          # 酒店 Agent 结果
    itinerary_json: str  # 最终行程 JSON(符合 Itinerary schema)


def build_planner():
    """构建行程规划编排图: 天气 → 景点 → 酒店 → 整合"""
    graph = StateGraph(PlannerState)
    graph.add_node("weather", plan_weather)
    graph.add_node("attractions", plan_attractions)
    graph.add_node("hotels", plan_hotels)
    graph.add_node("integrate", integrate_itinerary)
    graph.add_edge(START, "weather")
    graph.add_edge("weather", "attractions")
    graph.add_edge("attractions", "hotels")
    graph.add_edge("hotels", "integrate")
    graph.add_edge("integrate", END)
    return graph.compile()


async def run_planner(request: TripRequest) -> Itinerary:
    """入口: 传入行程请求, 返回完整行程(阶段4的路由层直接调这个)"""
    planner = build_planner()
    state = await planner.ainvoke({"request": request.model_dump(mode="json")})
    return Itinerary.model_validate_json(state["itinerary_json"])


async def plan_weather(state: PlannerState) -> dict:
    """节点1: 调用天气 Agent 查询目的地每天天气"""
    req = state["request"]
    logger.info("规划天气: {} {}~{}", req["destination"], req["start_date"], req["end_date"])
    agent = await build_weather_agent()
    prompt = (
        f"请查询{req['destination']}在 {req['start_date']} 至 {req['end_date']} "
        "期间每天的天气。"
    )
    result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    return {"weather": result["messages"][-1].content}


async def plan_attractions(state: PlannerState) -> dict:
    """节点2: 调用景点 Agent 推荐景点(带偏好/预算约束)"""
    req = state["request"]
    logger.info("规划景点: {} 偏好={}", req["destination"], req["preferences"])
    agent = await build_attraction_agent()
    days = _days_between(req["start_date"], req["end_date"])
    prompt = (
        f"请为{req['destination']}推荐景点。行程 {req['start_date']} 至 {req['end_date']} "
        f"共{days}天, {req['travelers']}人, 旅行偏好: {req['preferences'] or '无特别偏好'}, "
        f"总预算{req['budget']}元。请按景点 Agent 的输出格式给出推荐列表。"
    )
    result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    return {"attractions": result["messages"][-1].content}


async def plan_hotels(state: PlannerState) -> dict:
    """节点3: 调用酒店 Agent 推荐酒店(带人数/预算约束)"""
    req = state["request"]
    logger.info("规划酒店: {} {}人", req["destination"], req["travelers"])
    agent = await build_hotel_agent()
    days = _days_between(req["start_date"], req["end_date"])
    prompt = (
        f"请为{req['destination']}推荐酒店。行程共{days}天需住{days - 1}晚, "
        f"{req['travelers']}人, 总预算{req['budget']}元。请按酒店 Agent 的输出格式给出推荐列表。"
    )
    result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    return {"hotels": result["messages"][-1].content}


async def integrate_itinerary(state: PlannerState) -> dict:
    """节点4: 把天气/景点/酒店结果交给 LLM, 整合成符合 Itinerary schema 的 JSON

    修复循环: LLM 输出 JSON 校验失败时, 把报错喂回去重试一次。
    """
    logger.info("整合行程 JSON")
    llm = get_llm()
    prompt = _build_integrate_prompt(state)
    for attempt in range(1, 3):
        resp = await llm.ainvoke(prompt)
        content = _strip_code_fence(resp.content)
        try:
            itinerary = Itinerary.model_validate_json(content)
            logger.info("行程 JSON 校验通过, 共 {} 天", len(itinerary.days))
            return {"itinerary_json": itinerary.model_dump_json()}
        except ValidationError as exc:
            logger.warning("整合 JSON 校验失败(第 {} 次): {}", attempt, exc)
            # 修复循环: 把校验报错附加到提示词, 让 LLM 自己改正
            prompt = (
                f"{prompt}\n\n注意: 你上次的输出没有通过校验, 报错如下:\n{exc}\n"
                "请修正字段后重新输出完整 JSON。"
            )
    raise AgentError("LLM 两次输出均未通过行程 schema 校验")


def _build_integrate_prompt(state: PlannerState) -> str:
    """构造整合提示词: 把 Itinerary schema 结构写清楚, 要求只输出 JSON"""
    req = state["request"]
    days = _days_between(req["start_date"], req["end_date"])
    return f"""你是行程规划师。请把下面的天气、景点、酒店信息整合成一份完整的旅行行程 JSON。

目的地: {req['destination']}
日期: {req['start_date']} 至 {req['end_date']}(共 {days} 天)
偏好: {req['preferences'] or '无特别偏好'}
人数: {req['travelers']} 人
总预算: {req['budget']} 元

【天气】
{state['weather']}

【景点】
{state['attractions']}

【酒店】
{state['hotels']}

输出要求: 只输出 JSON, 不要任何其他文字, 结构如下:
{{
  "destination": "{req['destination']}",
  "start_date": "{req['start_date']}",
  "end_date": "{req['end_date']}",
  "preferences": {req['preferences']},
  "days": [
    {{
      "day": 1,
      "date": "{req['start_date']}",
      "weather": "晴天, 25度",
      "spots": [
        {{"name": "景点名", "lng": 116.39, "lat": 39.90, "period": "morning",
          "address": "地址", "ticket_price": 60, "stay_minutes": 150,
          "description": "简介", "image_url": "https://..."}}
      ],
      "meals": [
        {{"period": "午餐", "name": "餐厅名", "price_estimate": 50}}
      ],
      "hotel": {{"name": "酒店名", "lng": 116.39, "lat": 39.90, "address": "地址",
                "price_per_night": 400, "rating": 4.5}}
    }}
  ],
  "budget": {{"tickets": 0, "hotels": 0, "dining": 0, "transport": 0}}
}}

规则:
1. days 数组长度必须是 {days}, day 从 1 到 {days}, date 依次对应每天
2. 每天 2-3 个景点, 按游览顺序排列, period 取值 morning/afternoon/evening
3. 每天安排午餐和晚餐两个 meal, 结合目的地特色
4. 每晚一个 hotel(最后一晚可没有), 价格在预算范围内
5. budget 四项按天数累加填写, 四项之和不超过 {req['budget']} 元
6. 所有字段都要填, 数值字段是数字不是字符串"""


def _days_between(start: str, end: str) -> int:
    """字符串日期 → 天数(含首尾)"""
    start_date = datetime.date.fromisoformat(start)
    end_date = datetime.date.fromisoformat(end)
    return (end_date - start_date).days + 1


def _strip_code_fence(content: str) -> str:
    """去掉 LLM 输出常见的 ```json 围栏"""
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
    return content.strip()
