# 统一异常体系: 业务异常 + 全局处理器
# 全局处理器注册在阶段4做路由时接入 main.py(需要 main.py 加两行)
from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """业务异常基类: code 为 HTTP 状态码, message 给前端展示"""

    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)


class ExternalServiceError(AppError):
    """外部服务(高德/Unsplash/LLM)调用失败"""

    def __init__(self, message: str):
        super().__init__(message=f"外部服务调用失败: {message}", code=502)


class AgentError(AppError):
    """智能体执行失败"""

    def __init__(self, message: str):
        super().__init__(message=f"智能体执行失败: {message}", code=500)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """全局异常处理器: 统一错误响应格式 {code, message}"""
    return JSONResponse(status_code=exc.code, content={"code": exc.code, "message": exc.message})
