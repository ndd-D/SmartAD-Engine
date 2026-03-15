import httpx
from loguru import logger
from ai_config.settings import settings

_BASE = settings.smartad_server_url
_HEADERS = {
    "Content-Type": "application/json",
    "ai-token": settings.ai_token,
}


async def get(path: str, params: dict = None) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{_BASE}{path}", params=params, headers=_HEADERS)
        resp.raise_for_status()
        return resp.json()


async def post(path: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{_BASE}{path}", json=body, headers=_HEADERS)
        resp.raise_for_status()
        return resp.json()
