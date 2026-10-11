# 预算核算单元测试: 验证确定性核算公式
# 运行: 在 backend 目录执行 venv/Scripts/python.exe -m pytest tests/
import datetime

from app.schemas.itinerary import Budget, DayPlan, Hotel, Itinerary, Meal, Spot
from app.services.budget_service import calculate_budget, check_budget


def _make_spot(name: str = "景点", price: float = 60.0) -> Spot:
    return Spot(name=name, lng=116.0, lat=39.0, ticket_price=price)


def _make_meal(period: str = "午餐", price: float = 50.0) -> Meal:
    return Meal(period=period, name="餐厅", price_estimate=price)


def _make_hotel(price: float = 400.0) -> Hotel:
    return Hotel(name="酒店", lng=116.0, lat=39.0, price_per_night=price)


def _make_itinerary(
    days: int = 2,
    spots_per_day: int = 2,
    meals_per_day: int = 2,
    hotel_every_night: bool = True,
) -> Itinerary:
    """构造一个规整的测试行程: 每天 N 个景点(60元)、N 餐(50元)、每晚酒店(400元)"""
    day_plans = []
    for i in range(days):
        day_plans.append(
            DayPlan(
                day=i + 1,
                date=datetime.date(2026, 10, 15 + i),
                spots=[_make_spot(f"景点{i}-{j}") for j in range(spots_per_day)],
                meals=[_make_meal() for _ in range(meals_per_day)],
                hotel=_make_hotel() if hotel_every_night else None,
            )
        )
    return Itinerary(
        destination="测试市",
        start_date=datetime.date(2026, 10, 15),
        end_date=datetime.date(2026, 10, 15 + days - 1),
        days=day_plans,
        budget=Budget(),
    )


def test_tickets_multiply_by_travelers():
    """门票 = 景点门票总和 × 人数"""
    it = _make_itinerary(days=2, spots_per_day=2)  # 4 个景点 × 60 元
    budget = calculate_budget(it, travelers=3, transport_per_person_per_day=50)
    assert budget.tickets == 4 * 60 * 3  # 720


def test_hotels_rooms_round_up():
    """酒店房间数按 2 人一间向上取整: 3 人 → 2 间"""
    it = _make_itinerary(days=2)  # 2 晚 × 400 元
    budget_two = calculate_budget(it, travelers=2, transport_per_person_per_day=50)
    budget_three = calculate_budget(it, travelers=3, transport_per_person_per_day=50)
    assert budget_two.hotels == 2 * 400 * 1   # 2 人 → 1 间
    assert budget_three.hotels == 2 * 400 * 2  # 3 人 → 2 间


def test_hotels_skip_none_hotel_day():
    """最后一天没有酒店的行程, 酒店费用只算有酒店的晚数"""
    it = _make_itinerary(days=3, hotel_every_night=True)
    it.days[2].hotel = None  # 最后一晚不入住
    budget = calculate_budget(it, travelers=2, transport_per_person_per_day=50)
    assert budget.hotels == 2 * 400  # 只住 2 晚


def test_dining_multiply_by_travelers():
    """餐饮 = 每餐人均 × 餐数 × 人数"""
    it = _make_itinerary(days=2, meals_per_day=2)  # 4 餐 × 50 元
    budget = calculate_budget(it, travelers=2, transport_per_person_per_day=50)
    assert budget.dining == 4 * 50 * 2  # 400


def test_transport_formula():
    """交通 = 每人每天基准 × 人数 × 天数"""
    it = _make_itinerary(days=3)
    budget = calculate_budget(it, travelers=2, transport_per_person_per_day=40)
    assert budget.transport == 40 * 2 * 3  # 240


def test_total_is_sum_of_four_items():
    """总额 = 四项之和"""
    it = _make_itinerary(days=2)
    budget = calculate_budget(it, travelers=2, transport_per_person_per_day=50)
    assert budget.total == budget.tickets + budget.hotels + budget.dining + budget.transport


def test_check_budget_over_limit():
    """超支检查: 不抛错, 返回 False(前端负责提示)"""
    it = _make_itinerary(days=2)
    it.budget = calculate_budget(it, travelers=2, transport_per_person_per_day=50)
    assert check_budget(it, budget_limit=100) is False  # 明显超支
    assert check_budget(it, budget_limit=999999) is True


def test_total_is_serialized_in_json():
    """防回归: total 是 @computed_field, 必须出现在 model_dump 输出里(前端要读)"""
    budget = Budget(tickets=100, hotels=200, dining=50, transport=50)
    assert budget.total == 400
    dumped = budget.model_dump()
    assert "total" in dumped
    assert dumped["total"] == 400
