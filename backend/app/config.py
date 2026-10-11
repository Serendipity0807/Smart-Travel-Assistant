# 读取 .env 配置
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 基于本文件所在位置定位 .env: config.py 在 backend/app/ 下, 上一级就是 backend/
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """全局配置: 从 backend/.env 读取"""

    # LLM (DeepSeek)
    llm_model_id: str = "deepseek-flash"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"

    # 高德地图 (Web服务 key, 同时用于高德 MCP server)
    amap_maps_api_key: str = ""

    # Unsplash
    unsplash_access_key: str = ""

    # 预算核算(阶段6): 城市内交通按每人每天估算, 精确路线计算在阶段10自写MCP时做
    transport_daily_budget_per_person: float = 50

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",   # ← 改成绝对路径
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()