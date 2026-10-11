# 验证高德 MCP server: 连接 + 列出工具
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client   # ← 改: 带下划线

from app.config import settings


async def main():
    url = f"https://mcp.amap.com/mcp?key={settings.amap_maps_api_key}"
    # 新版只返回 (read, write) 两个流, 不是三个
    async with streamable_http_client(url) as (read, write):     # ← 改: 2 个值
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            weather = await session.call_tool("maps_weather", {"city": "北京"})
            print(f"- {weather}")

            address = await session.call_tool("maps_text_search", {"keywords":"故宫"})
            print(f"- {address}")


if __name__ == "__main__":
    asyncio.run(main())
