"""API 层测试: 路由/参数校验/容错降级(阶段9)

原则: 外部依赖(高德/LLM)全部 mock, 测试不访问真实网络。
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    # 三个密钥状态只能是 bool, 响应不泄露密钥本身
    assert isinstance(body["llm_configured"], bool)
    assert isinstance(body["amap_configured"], bool)
    assert isinstance(body["unsplash_configured"], bool)


def test_plan_requires_body():
    """缺请求体 → FastAPI 校验直接 422, 不会进入耗时规划流程"""
    resp = client.post("/api/trip/plan")
    assert resp.status_code == 422


def test_search_spots_requires_keyword():
    """keyword 是必填参数 → 缺省直接 422"""
    resp = client.get("/api/trip/spots/search")
    assert resp.status_code == 422


def test_search_spots_ok(monkeypatch):
    """mock 掉高德客户端: 验证响应包装格式与 POI 转换正确

    spot_service 里是 from app.services.amap_client import search_pois,
    函数名已绑定到 spot_service 命名空间, 因此 patch spot_service.search_pois。
    """
    from app.services import spot_service

    async def fake_search(keyword, city="", offset=10):
        return [
            {
                "name": "测试景点",
                "location": "120.100000,30.200000",
                "address": ["西湖区", "测试路1号"],
                "type": "风景名胜;国家级景点",
            }
        ]

    monkeypatch.setattr(spot_service, "search_pois", fake_search)

    resp = client.get("/api/trip/spots/search", params={"keyword": "测试", "city": "杭州"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["message"] == "success"
    spots = body["data"]
    assert len(spots) == 1
    assert spots[0]["name"] == "测试景点"
    assert spots[0]["lng"] == 120.1
    assert spots[0]["lat"] == 30.2
    assert spots[0]["address"] == "西湖区测试路1号"
    assert spots[0]["description"] == "风景名胜;国家级景点"


def test_search_spots_empty_result_ok(monkeypatch):
    """搜索无结果 → 200 + 空列表(不是错误)"""
    from app.services import spot_service

    async def fake_search(keyword, city="", offset=10):
        return []

    monkeypatch.setattr(spot_service, "search_pois", fake_search)
    resp = client.get("/api/trip/spots/search", params={"keyword": "不存在的地方"})
    assert resp.status_code == 200
    assert resp.json() == {"code": 0, "message": "success", "data": []}


def test_search_spots_amap_failure_degrades(monkeypatch):
    """高德故障时降级返回空列表: 企业容错原则, 外部依赖失败不级联成 500

    amap_client 内部已把网络/接口异常降级为 [], 这里模拟其降级结果,
    验证业务层与路由层在降级数据上依然正常响应。
    """
    from app.services import spot_service

    async def fake_search(keyword, city="", offset=10):
        return []

    monkeypatch.setattr(spot_service, "search_pois", fake_search)
    resp = client.get("/api/trip/spots/search", params={"keyword": "测试"})
    assert resp.status_code == 200
    assert resp.json()["code"] == 0
    assert resp.json()["data"] == []
