# TripRequest(目的地/日期/偏好/预算)前端返回给后端
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

# 旅行偏好: 前端多选时只能传这些值
Preference = Literal["历史文化", "自然风光", "美食", "亲子", "购物", "文艺"]


class TripRequest(BaseModel):
    """行程规划请求: 前端表单提交的数据"""

    destination: str = Field(min_length=1, max_length=50, description="目的地城市, 如: 北京")
    start_date: date = Field(description="出发日期")
    end_date: date = Field(description="返程日期")
    preferences: list[Preference] = Field(default_factory=list, description="旅行偏好")
    budget: float = Field(gt=0, description="总预算(元)")
    travelers: int = Field(default=1, ge=1, le=20, description="出行人数")

    @model_validator(mode="after")
    def check_dates(self) -> "TripRequest":
        """业务规则校验: 日期合法性 + 行程天数上限"""
        if self.end_date < self.start_date:
            raise ValueError("返程日期不能早于出发日期")
        if self.days > 15:
            raise ValueError("单次行程最多规划15天")
        return self

    @property
    def days(self) -> int:
        """旅行天数(含出发日和返程日)"""
        return (self.end_date - self.start_date).days + 1
