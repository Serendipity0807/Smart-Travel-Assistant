# 预算核算服务: 用确定性代码核算行程预算(覆盖 LLM 整合时的估值)
# 原则: LLM 负责"选什么", 代码负责"算多少"——LLM 做算术不可靠
import math

from app.core.logging import logger
from app.schemas.itinerary import Budget, Itinerary


def calculate_budget(
    itinerary: Itinerary,
    travelers: int,
    transport_per_person_per_day: float,
) -> Budget:
    """按真实数据核算四项预算:

    - 门票 = 所有景点门票价之和 × 人数
    - 酒店 = 每晚房价 × 房间数(一间双人房住 2 人, 人数向上取整)
    - 餐饮 = 每餐人均 × 餐数 × 人数
    - 交通 = 每人每天基准(城市内通勤, 精确路线计算留到阶段10自写MCP时做)
    """
    tickets = sum(s.ticket_price for d in itinerary.days for s in d.spots) * travelers

    rooms = math.ceil(travelers / 2)
    hotels = sum(d.hotel.price_per_night for d in itinerary.days if d.hotel) * rooms

    dining = sum(m.price_estimate for d in itinerary.days for m in d.meals) * travelers

    transport = transport_per_person_per_day * travelers * len(itinerary.days)

    return Budget(
        tickets=round(tickets, 2),
        hotels=round(hotels, 2),
        dining=round(dining, 2),
        transport=round(transport, 2),
    )


def check_budget(itinerary: Itinerary, budget_limit: float) -> bool:
    """是否超支: 核算总额与用户预算对比, 超支记警告日志(不强制, 前端负责提示)"""
    total = itinerary.budget.total
    if total > budget_limit:
        logger.warning(
            "行程预算超支: 核算总额 {} 元 > 用户预算 {} 元",
            total,
            budget_limit,
        )
        return False
    return True
