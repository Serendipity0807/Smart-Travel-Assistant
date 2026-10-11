# 景点搜索业务层: 高德 POI → 候选景点(前端"添加景点"功能用)
from app.core.logging import logger
from app.schemas.spot import CandidateSpot
from app.services.amap_client import search_pois


async def search_candidate_spots(keyword: str, city: str = "") -> list[CandidateSpot]:
    """关键词搜索候选景点列表"""
    pois = await search_pois(keyword, city)
    spots = []
    for poi in pois:
        spot = _poi_to_candidate(poi)
        if spot is not None:
            spots.append(spot)
    logger.info("景点搜索 {} 命中 {} 个候选", keyword, len(spots))
    return spots


def _poi_to_candidate(poi: dict) -> CandidateSpot | None:
    """高德 POI 原始字典 → 候选景点(纯函数, 便于单元测试)

    location 格式为逗号分隔的 "lng,lat" 字符串, 缺省或解析失败时跳过该条。
    """
    location = poi.get("location", "")
    if not location:
        return None
    try:
        lng_str, lat_str = location.split(",")
        lng, lat = float(lng_str), float(lat_str)
    except ValueError:
        return None
    # address 在高德里是列表(省/市/区/街道...), 拼接成完整地址
    raw_address = poi.get("address", "")
    if isinstance(raw_address, list):
        raw_address = "".join(raw_address)
    return CandidateSpot(
        name=poi.get("name", ""),
        lng=lng,
        lat=lat,
        address=raw_address,
        description=poi.get("type", ""),
    )
