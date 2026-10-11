# Unsplash 工具: 搜索景点配图(阶段2 scripts/test_unsplash.py 的 search_photo 封装成 LangChain 工具)
import httpx
from langchain.tools import tool

from app.config import settings


@tool
async def search_unsplash_photo(keyword: str) -> str:
    """搜索与关键词相关的景点照片, 返回图片 URL。

    Args:
        keyword: 搜索关键词, 如 "故宫 北京" 或 "The Forbidden City"
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.unsplash.com/search/photos",
            params={"query": keyword, "per_page": 1},
            headers={"Authorization": f"Client-ID {settings.unsplash_access_key}"},
        )
        resp.raise_for_status()
        data = resp.json()
    results = data.get("results", [])
    if not results:
        return ""
    return results[0]["urls"]["regular"]
