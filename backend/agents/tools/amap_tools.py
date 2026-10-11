# 高德 MCP 工具: 通过 MCPAdapter 把高德官方 MCP server 的工具转成 LangChain 工具
# 对比 scripts/test_amap_mcp.py(阶段2): 那时是手写 MCP 客户端, 现在 langchain 内置适配器替我们做
from langchain.mcp import MCPAdapter
from langchain_core.tools import BaseTool

from app.config import settings
from app.core.logging import logger

# 高德官方 MCP server 地址(Streamable HTTP, key 放 URL query)
AMAP_MCP_URL = f"https://mcp.amap.com/mcp?key={settings.amap_maps_api_key}"

# 各专业 Agent 关心的工具名: 只给相关的工具, 省 token 也防止误用
WEATHER_TOOLS = {"maps_weather"}
SEARCH_TOOLS = {"maps_text_search", "maps_search_detail", "maps_geo", "maps_around_search"}

# 模块级缓存: MCP 连接 + 12 个工具的 schema 拉取有开销, 进程内只做一次
_cached_tools: list[BaseTool] | None = None


async def load_amap_tools(use_cache: bool = True) -> list[BaseTool]:
    """连接高德 MCP server, 加载全部工具(天气/搜索/路线/地理编码等)"""
    global _cached_tools
    if use_cache and _cached_tools is not None:
        return _cached_tools
    async with MCPAdapter(AMAP_MCP_URL) as adapter:
        tools = await adapter.list_tools()
    logger.info("从高德 MCP 加载了 {} 个工具: {}", len(tools), [t.name for t in tools])
    _cached_tools = tools
    return tools
