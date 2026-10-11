# 行程规划业务层: 路由层与智能体层之间的桥梁
from agents.planner_agent import run_planner
from app.config import settings
from app.core.logging import logger
from app.schemas.itinerary import Itinerary
from app.schemas.request import TripRequest
from app.services.budget_service import calculate_budget, check_budget


async def plan_trip(request: TripRequest) -> Itinerary:
    """把行程请求交给编排器(天气→景点→酒店→整合), 核算预算后返回完整行程"""
    logger.info(
        "收到行程规划请求: 目的地={}, {}~{}, 偏好={}, 预算={}, {}人",
        request.destination,
        request.start_date,
        request.end_date,
        request.preferences,
        request.budget,
        request.travelers,
    )
    itinerary = await run_planner(request)

    # 阶段6: 用确定性代码重算预算, 覆盖 LLM 整合时的估值
    itinerary.budget = calculate_budget(
        itinerary,
        travelers=request.travelers,
        transport_per_person_per_day=settings.transport_daily_budget_per_person,
    )
    itinerary.travelers = request.travelers
    itinerary.budget_limit = request.budget
    check_budget(itinerary, request.budget)
    return itinerary
