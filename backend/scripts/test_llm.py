# 验证 DeepSeek LLM: 直连 chat/completions
import asyncio
import json

import httpx

from app.config import settings

CHAT_URL = f"{settings.llm_base_url}/chat/completions"


async def chat(messages: list[dict]) -> str:
    """调用 LLM, 返回回复文本"""
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.llm_model_id,
        "messages": messages,
        "temperature": 0.7,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:   # LLM 慢, 超时给足
        resp = await client.post(CHAT_URL, headers=headers, json=payload)
    if resp.status_code != 200:
        print(f"请求失败: {resp.status_code}")
        print(resp.text)
        return ""
    data = resp.json()
    print("本次 token 用量:", data.get("usage"))   # 看看花了多少钱(很便宜, 但养成观察习惯)
    return data["choices"][0]["message"]["content"]  # 注意这层"洋葱"的剥法


async def main():
    messages = [
        {"role": "system", "content": "你是旅游助手, 始终用 JSON 格式回答, 不要输出 JSON 以外的任何内容"},
        {"role": "user", "content": '列出北京的3个著名景点, 严格按格式: {"spots": ["景点1", "景点2", "景点3"]}'},
    ]
    content = await chat(messages)
    print("原始回复:", content)
    try:
        parsed = json.loads(content)
        print("JSON 解析成功:", parsed["spots"])
    except json.JSONDecodeError:
        print("警告: 回复不是合法 JSON —— 阶段3 依赖 JSON 输出, 需要调整提示词策略")


if __name__ == "__main__":
    asyncio.run(main())
