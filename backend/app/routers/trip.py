# POST /api/trip/plan 行程规划 + GET /api/trip/spots/search 候选景点搜索
from fastapi import APIRouter

from app.schemas.itinerary import Itinerary
from app.schemas.request import TripRequest
from app.schemas.response import ApiResponse
from app.schemas.spot import CandidateSpot
from app.services.spot_service import search_candidate_spots
from app.services.trip_service import plan_trip

router = APIRouter(prefix="/api/trip", tags=["trip"])


@router.post("/plan", response_model=ApiResponse[Itinerary], summary="生成行程")
async def plan(request: TripRequest) -> ApiResponse[Itinerary]:
    """接收目的地/日期/偏好/预算, 返回完整行程(景点/餐饮/酒店/预算明细)

    全流程由后端智能体编排: 天气 → 景点 → 酒店 → LLM 整合, 约需 1-2 分钟。
    """
    itinerary = await plan_trip(request)
    return ApiResponse(data=itinerary)


@router.get(
    "/spots/search",
    response_model=ApiResponse[list[CandidateSpot]],
    summary="搜索候选景点",
)
async def search_spots(keyword: str, city: str = "") -> ApiResponse[list[CandidateSpot]]:
    """关键词搜索景点(高德 POI), 供前端"添加景点"功能使用(阶段7)"""
    spots = await search_candidate_spots(keyword, city)
    return ApiResponse(data=spots)
