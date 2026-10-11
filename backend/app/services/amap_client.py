# 高德 REST API 封装(POI 搜索等)
# 这里直连 REST 而不是走 MCP: 响应格式可控、无 LLM 开销, 适合"搜索候选景点"这种高频轻量场景
import httpx

from app.config import settings
from app.core.logging import logger

AMAP_REST_BASE = "https://restapi.amap.com"


async def search_pois(keywords: str, city: str = "", offset: int = 10) -> list[dict]:
    """文本搜索 POI, 返回原始 pois 列表(每个含 name/location/address 等字段)

    文档: https://lbs.amap.com/api/webservice/guide/api/search
    """
    params: dict = {
        "key": settings.amap_maps_api_key,
        "keywords": keywords,
        "offset": offset,
    }
    if city:
        params["city"] = city
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{AMAP_REST_BASE}/v3/place/text", params=params)
        resp.raise_for_status()
        data = resp.json()
    if data.get("status") != "1":
        logger.warning("高德 POI 搜索失败: {}", data.get("info"))
        return []
    return data.get("pois", [])
