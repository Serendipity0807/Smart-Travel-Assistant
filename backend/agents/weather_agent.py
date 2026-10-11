# 天气 Agent: 查询目的地各天天气(用高德 MCP 的天气工具)
from langchain.agents import create_agent
from langchain_core.tools import BaseTool

from agents.llm_config import get_llm
from agents.tools.amap_tools import WEATHER_TOOLS, load_amap_tools

WEATHER_SYSTEM_PROMPT = """你是天气查询助手。根据用户提供的城市和日期范围, 查询每天的天气。
要求:
1. 只使用提供的天气工具查询
2. 最后用中文总结: 每一天一行, 格式为 "YYYY-MM-DD: 天气状况, 温度, 风力"
3. 不要编造工具返回之外的信息"""


async def build_weather_agent():
    """构建天气 Agent: LLM + 高德天气工具"""
    all_tools: list[BaseTool] = await load_amap_tools()
    tools = [t for t in all_tools if t.name in WEATHER_TOOLS]
    return create_agent(model=get_llm(), tools=tools, system_prompt=WEATHER_SYSTEM_PROMPT)
