# 冒烟测试: 验证 LangChain/LangGraph 智能体层全链路
# 运行方式(必须在 backend 目录下, -m 让脚本能 import app 和 agents):
#   venv/Scripts/python.exe -m scripts.test_langchain_agents
import asyncio
import json
import sys
from datetime import date

from agents.llm_config import get_llm
from agents.planner_agent import build_planner
from agents.tools.amap_tools import load_amap_tools
from agents.weather_agent import build_weather_agent
from app.schemas.request import TripRequest

# Windows 控制台默认 GBK, 强制 UTF-8 输出避免中文乱码(stdout 和 stderr 都要)
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


async def test_llm():
    """1. LLM 直连 DeepSeek"""
    print("=" * 60)
    print("1. LLM 直连 DeepSeek")
    resp = await get_llm().ainvoke("用一句话介绍北京")
    print("回答:", resp.content)


async def test_amap_tools():
    """2. 高德 MCP 工具加载"""
    print("=" * 60)
    print("2. 高德 MCP 工具加载")
    tools = await load_amap_tools()
    print(f"加载到 {len(tools)} 个工具:")
    for t in tools:
        print(f"  - {t.name}")


async def test_weather_agent():
    """3. 天气 Agent(LLM + 高德天气工具)"""
    print("=" * 60)
    print("3. 天气 Agent")
    agent = await build_weather_agent()
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "查询北京 2026-10-15 到 2026-10-16 的天气"}]}
    )
    print("结果:", result["messages"][-1].content)


async def test_planner():
    """4. 完整规划(天气 → 景点 → 酒店 → 整合)"""
    print("=" * 60)
    print("4. 完整行程规划")
    request = TripRequest(
        destination="北京",
        start_date=date(2026, 10, 15),
        end_date=date(2026, 10, 16),
        preferences=["历史文化"],
        budget=3000,
        travelers=2,
    )
    planner = build_planner()
    state = await planner.ainvoke({"request": request.model_dump(mode="json")})
    print("最终行程:")
    print(json.dumps(json.loads(state["itinerary_json"]), ensure_ascii=False, indent=2))


async def main():
    await test_llm()
    await test_amap_tools()
    await test_weather_agent()
    await test_planner()


if __name__ == "__main__":
    asyncio.run(main())
