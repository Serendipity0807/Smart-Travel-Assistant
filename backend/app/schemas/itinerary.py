# Itinerary/DayPlan/Spot/Hotel/Budget 后端返回给前端
import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class Budget(BaseModel):
    """预算明细(单位: 元)"""

    tickets: float = Field(default=0, description="门票")
    hotels: float = Field(default=0, description="酒店")
    dining: float = Field(default=0, description="餐饮")
    transport: float = Field(default=0, description="交通")

    @computed_field(description="总花费(随四项自动计算, 序列化时输出)")
    @property
    def total(self) -> float:
        """总花费"""
        return self.tickets + self.hotels + self.dining + self.transport


class Spot(BaseModel):
    """景点"""

    name: str = Field(description="景点名称")
    lng: float = Field(ge=-180, le=180, description="经度(GCJ-02坐标系)")
    lat: float = Field(ge=-90, le=90, description="纬度(GCJ-02坐标系)")
    period: str = Field(default="morning", description="游览时段: morning/afternoon/evening")
    address: str = Field(default="", description="地址")
    ticket_price: float = Field(default=0, ge=0, description="门票价(元)")
    stay_minutes: int = Field(default=120, ge=0, description="建议停留时长(分钟)")
    description: str = Field(default="", description="简介")
    image_url: str = Field(default="", description="Unsplash 配图地址")


class Meal(BaseModel):
    """一餐"""

    period: str = Field(description="早餐/午餐/晚餐")
    name: str = Field(description="餐厅名")
    price_estimate: float = Field(default=0, ge=0, description="预估人均(元)")


class Hotel(BaseModel):
    """酒店"""

    name: str = Field(description="酒店名")
    lng: float = Field(ge=-180, le=180, description="经度(GCJ-02坐标系)")
    lat: float = Field(ge=-90, le=90, description="纬度(GCJ-02坐标系)")
    price_per_night: float = Field(default=0, ge=0, description="每晚价格(元)")
    rating: float = Field(default=0, ge=0, le=5, description="评分(0-5)")
    address: str = Field(default="", description="地址")


class DayPlan(BaseModel):
    """单日行程"""

    day: int = Field(ge=1, description="第几天(从1开始)")
    date: datetime.date = Field(description="日期")
    weather: str = Field(default="", description="当天天气(天气Agent填入)")
    spots: list[Spot] = Field(default_factory=list, description="当日景点(按游览顺序)")
    meals: list[Meal] = Field(default_factory=list, description="当日三餐")
    hotel: Optional[Hotel] = Field(default=None, description="当晚入住酒店")


class Itinerary(BaseModel):
    """完整行程: 后端返回给前端的最终结果"""

    destination: str = Field(description="目的地")
    start_date: datetime.date = Field(description="开始日期")
    end_date: datetime.date = Field(description="结束日期")
    preferences: list[str] = Field(default_factory=list, description="旅行偏好")
    days: list[DayPlan] = Field(default_factory=list, description="每日行程")
    budget: Budget = Field(default_factory=Budget, description="预算汇总")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, description="生成时间")
    # 阶段6新增: 由业务层核算时回填(LLM 不输出这两个字段, 用默认值)
    travelers: int = Field(default=1, ge=1, description="出行人数")
    budget_limit: float = Field(default=0, description="用户设定的总预算(前端超支提示用)")
