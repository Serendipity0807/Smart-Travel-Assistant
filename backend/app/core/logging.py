# 统一日志: 全项目用 loguru, 级别/格式/文件滚动集中在此配置
import sys
from pathlib import Path

from loguru import logger

# 日志文件放 backend/logs/ 下
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"

# 移除默认配置, 换成统一格式
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
)
logger.add(
    LOG_DIR / "app.log",
    level="DEBUG",
    rotation="10 MB",   # 单文件 10MB 自动滚动
    retention="7 days",  # 保留 7 天
    encoding="utf-8",
)
