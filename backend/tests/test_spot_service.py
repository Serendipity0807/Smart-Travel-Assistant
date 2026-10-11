# 景点搜索解析单元测试: 高德 POI → 候选景点(纯函数, 不调外部服务)
from app.schemas.spot import CandidateSpot
from app.services.spot_service import _poi_to_candidate


def test_normal_poi():
    """正常 POI: 解析出完整候选景点"""
    poi = {
        "name": "故宫博物院",
        "location": "116.397,39.917",
        "address": ["北京市", "东城区", "景山前街4号"],
        "type": "风景名胜;博物馆;国家级景点",
    }
    spot = _poi_to_candidate(poi)
    assert spot is not None
    assert spot.name == "故宫博物院"
    assert spot.lng == 116.397
    assert spot.lat == 39.917
    assert spot.address == "北京市东城区景山前街4号"


def test_missing_location_skipped():
    """缺 location 的 POI 跳过(返回 None)"""
    assert _poi_to_candidate({"name": "无名景点"}) is None


def test_bad_location_skipped():
    """location 格式非法的 POI 跳过"""
    assert _poi_to_candidate({"name": "x", "location": "abc"}) is None
    assert _poi_to_candidate({"name": "x", "location": "116.397"}) is None  # 缺纬度


def test_string_address_passthrough():
    """address 是字符串时原样保留(兼容不同返回格式)"""
    spot = _poi_to_candidate(
        {"name": "西湖", "location": "120.14,30.24", "address": "杭州市西湖区"}
    )
    assert spot is not None
    assert spot.address == "杭州市西湖区"


def test_type_is_valid_schema():
    """返回类型是合法的 CandidateSpot 模型"""
    poi = {"name": "灵隐寺", "location": "120.102,30.239", "type": "风景名胜;寺庙"}
    spot = _poi_to_candidate(poi)
    assert isinstance(spot, CandidateSpot)
