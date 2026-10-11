# Unsplash 工具: 搜索景点配图(阶段2 scripts/test_unsplash.py 的 search_photo 封装成 LangChain 工具)
import httpx
from langchain.tools import tool

from app.config import settings
from app.core.logging import logger


@tool
async def search_unsplash_photo(keyword: str) -> str:
    """搜索与关键词相关的景点照片, 返回图片 URL。

    Args:
        keyword: 搜索关键词, 如 "故宫 北京" 或 "The Forbidden City"
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": keyword, "per_page": 1},
                headers={"Authorization": f"Client-ID {settings.unsplash_access_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        # 降级: 配图是辅助数据, 网络抖动时返回空串(无图), 不影响行程主体
        logger.warning("Unsplash 搜索失败({}), 该景点将无配图: {}", keyword, exc)
        return ""
    results = data.get("results", [])
    if not results:
        return ""
    return results[0]["urls"]["regular"]
