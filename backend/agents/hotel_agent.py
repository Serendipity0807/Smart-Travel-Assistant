# 酒店 Agent: 搜索目的地酒店(高德搜索工具)
from langchain.agents import create_agent
from langchain_core.tools import BaseTool

from agents.llm_config import get_llm
from agents.tools.amap_tools import SEARCH_TOOLS, load_amap_tools

HOTEL_SYSTEM_PROMPT = """你是酒店推荐助手。根据用户的目的地、人数和预算, 推荐合适的酒店。
要求:
1. 用搜索工具查找酒店信息
2. 每晚一间双人房按两人入住考虑, 人数超过2人时按房间数折算价格
3. 最后用中文输出酒店列表, 每个酒店一行, 包含这些字段:
   名称 | 经度lng | 纬度lat | 地址 | 每晚价格(元) | 评分(0-5)
   字段之间用 | 分隔, 坐标和数字必须是数字
4. 推荐2-3家备选, 按性价比排序, 说明每晚住哪家(可以全程一家或中途换)"""


async def build_hotel_agent():
    """构建酒店 Agent: LLM + 高德搜索工具"""
    all_tools: list[BaseTool] = await load_amap_tools()
    tools = [t for t in all_tools if t.name in SEARCH_TOOLS]
    return create_agent(model=get_llm(), tools=tools, system_prompt=HOTEL_SYSTEM_PROMPT)
