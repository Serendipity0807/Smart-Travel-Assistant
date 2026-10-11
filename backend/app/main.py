#应用入口,CORS
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="Smart Travel Assistant", version="0.1.0")

# CORS: 开发阶段全放开(前端5173调后端8000属于跨域), 部署到服务器时收紧(阶段9)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 后续阶段在这里注册路由:
# app.include_router(trip.router)
# app.include_router(place.router)


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
