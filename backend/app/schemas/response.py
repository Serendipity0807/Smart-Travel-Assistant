# ApiResponse(统一响应格式)前端拿到的是 {code, message, data}
from pydantic import BaseModel


class ApiResponse[T](BaseModel):
    """所有业务接口的统一响应包装: code=0 成功, 非 0 失败(与异常处理器一致)

    用 PEP 695 新语法 class ApiResponse[T](BaseModel) 代替旧式 Generic[T]。
    """

    code: int = 0
    message: str = "success"
    data: T | None = None
