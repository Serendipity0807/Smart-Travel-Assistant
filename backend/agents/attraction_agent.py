# 景点 Agent: 搜索目的地景点并配图(高德搜索工具 + Unsplash 工具)
from langchain.agents import create_agent
from langchain_core.tools import BaseTool

from agents.llm_config import get_llm
from agents.tools.amap_tools import SEARCH_TOOLS, load_amap_tools
from agents.tools.unsplash_tool import search_unsplash_photo

ATTRACTION_SYSTEM_PROMPT = """你是景点推荐助手。根据用户的目的地、旅行偏好和预算, 推荐合适的景点。
要求:
1. 用搜索工具查找景点信息
2. 为每个推荐的景点用图片工具搜索一张配图
3. 最后用中文输出景点列表, 每个景点一行, 包含这些字段:
   名称 | 经度lng | 纬度lat | 地址 | 门票价(元) | 建议停留分钟数 | 简介 | 图片URL
   字段之间用 | 分隔, 坐标必须是数字
4. 景点数量按行程天数安排(每天2-3个), 不要推荐超出行程容量的景点"""


async def build_attraction_agent():
    """构建景点 Agent: LLM + 高德搜索工具 + Unsplash 配图工具"""
    all_tools: list[BaseTool] = await load_amap_tools()
    tools = [t for t in all_tools if t.name in SEARCH_TOOLS]
    tools.append(search_unsplash_photo)
    return create_agent(model=get_llm(), tools=tools, system_prompt=ATTRACTION_SYSTEM_PROMPT)
