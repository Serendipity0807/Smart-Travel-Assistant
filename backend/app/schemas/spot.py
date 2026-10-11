# CandidateSpot(候选景点): 阶段7"添加景点"功能, 前端搜索时的候选列表项
from pydantic import BaseModel, Field


class CandidateSpot(BaseModel):
    """高德 POI 转成的候选景点(门票/停留时长由用户在前端补充)"""

    name: str = Field(description="景点名称")
    lng: float = Field(ge=-180, le=180, description="经度(GCJ-02坐标系)")
    lat: float = Field(ge=-90, le=90, description="纬度(GCJ-02坐标系)")
    address: str = Field(default="", description="地址")
    description: str = Field(default="", description="POI类型/简介")
