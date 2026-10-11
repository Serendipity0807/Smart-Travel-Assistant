# 验证 Unsplash API: 关键词搜图
import asyncio

import httpx

from app.config import settings

SEARCH_URL = "https://api.unsplash.com/search/photos"


async def search_photo(keyword: str) -> dict | None:
    """按关键词搜索一张图, 返回图片信息"""
    headers = {"Authorization": f"Client-ID {settings.unsplash_access_key}"}
    params = {"query": keyword, "per_page": 1}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(SEARCH_URL, headers=headers, params=params)
    if resp.status_code != 200:
        print(f"请求失败: {resp.status_code}")
        print(resp.text)          # 失败时把响应体打出来, 里面通常写着原因
        return None
    data = resp.json()
    if not data["results"]:
        print(f"「{keyword}」没有搜到结果")
        return None
    return data["results"][0]


async def main():
    for keyword in ["故宫", "beijing"]:
        photo = await search_photo(keyword)
        if photo:
            print(f"[{keyword}] 描述: {photo.get('alt_description')}")
            print(f"[{keyword}] 图片URL: {photo['urls']['small']}")


if __name__ == "__main__":
    asyncio.run(main())
