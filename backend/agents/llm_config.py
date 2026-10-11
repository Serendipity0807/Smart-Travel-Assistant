# LLM 统一配置: 所有 Agent 共用同一个 DeepSeek 模型(OpenAI 兼容协议)
from langchain_openai import ChatOpenAI

from app.config import settings


def get_llm() -> ChatOpenAI:
    """返回连到 DeepSeek 的 ChatOpenAI 实例

    注意 use_responses_api=False: DeepSeek 只支持 /chat/completions,
    不能走 OpenAI 新出的 Responses API。
    """
    return ChatOpenAI(
        model_name=settings.llm_model_id,
        openai_api_key=settings.llm_api_key,
        openai_api_base=settings.llm_base_url,
        temperature=0.7,
        max_retries=2,        # SDK 内置重试, 网络抖动自动重发
        request_timeout=60,
        use_responses_api=False,
    )
