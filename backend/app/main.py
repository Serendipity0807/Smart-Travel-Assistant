#应用入口,CORS
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.exceptions import AppError, app_error_handler
from app.core.logging import logger
from app.routers import trip

app = FastAPI(title="Smart Travel Assistant", version="0.1.0")

# CORS: 只放行白名单来源(阶段9收紧, 不再使用 *), 白名单在 config.py / .env 配置
_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(trip.router)

# 异常处理: 业务异常走统一 {code, message} 格式
app.add_exception_handler(AppError, app_error_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底: 未预期的异常记录完整日志, 响应统一格式(不泄露内部细节)"""
    logger.exception("未处理异常: {}", exc)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误, 请查看日志"},
    )


@app.get("/")
async def root(name: str):
    return {"message": f"Hello {name}"}


@app.get("/api/health")
def health() -> dict:
    """健康检查: 后端是否存活 + 三个密钥是否已配置(不返回密钥本身)"""
    return {
        "status": "ok",
        "llm_configured": bool(settings.llm_api_key),
        "amap_configured": bool(settings.amap_maps_api_key),
        "unsplash_configured": bool(settings.unsplash_access_key),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True, port=8000)
