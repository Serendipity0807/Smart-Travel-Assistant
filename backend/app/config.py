# 读取 .env 配置
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()