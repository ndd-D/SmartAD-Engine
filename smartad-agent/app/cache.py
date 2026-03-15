"""
缓存模块（Cache Layer）
- 使用 TTLCache 对高频查询结果进行缓存
- 减少对 Java 后端的重复 HTTP 请求
- 缓存 key: 接口路径 + 参数哈希
"""
import time
import hashlib
import json
from cachetools import TTLCache
from loguru import logger
from ai_config.settings import settings


# ──────────────────────────────────────────────────────────────────────────────
# 缓存实例（按类型独立设置 TTL）
# ──────────────────────────────────────────────────────────────────────────────

_crowd_cache: TTLCache = TTLCache(maxsize=32, ttl=settings.cache_ttl_crowd)
_history_cache: TTLCache = TTLCache(maxsize=32, ttl=settings.cache_ttl_history)
_report_cache: TTLCache = TTLCache(maxsize=128, ttl=settings.cache_ttl_report)


def _make_key(path: str, params: dict | None = None) -> str:
    raw = path + json.dumps(params or {}, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# 人群画像缓存
# ──────────────────────────────────────────────────────────────────────────────

def get_crowd_cache() -> list[dict] | None:
    key = _make_key("/api/ai/crowd/list")
    val = _crowd_cache.get(key)
    if val is not None:
        logger.debug("[Cache] 命中人群画像缓存")
    return val


def set_crowd_cache(data: list[dict]) -> None:
    key = _make_key("/api/ai/crowd/list")
    _crowd_cache[key] = data


# ──────────────────────────────────────────────────────────────────────────────
# 历史数据缓存
# ──────────────────────────────────────────────────────────────────────────────

def get_history_cache() -> list[dict] | None:
    key = _make_key("/api/ai/report/history")
    val = _history_cache.get(key)
    if val is not None:
        logger.debug("[Cache] 命中历史投放效果缓存")
    return val


def set_history_cache(data: list[dict]) -> None:
    key = _make_key("/api/ai/report/history")
    _history_cache[key] = data


# ──────────────────────────────────────────────────────────────────────────────
# 报表数据缓存
# ──────────────────────────────────────────────────────────────────────────────

def get_report_cache(strategy_id: str, days: int) -> list[dict] | None:
    key = _make_key("/api/ai/report/strategy", {"strategyId": strategy_id, "days": days})
    val = _report_cache.get(key)
    if val is not None:
        logger.debug(f"[Cache] 命中报表缓存: strategy={strategy_id}, days={days}")
    return val


def set_report_cache(strategy_id: str, days: int, data: list[dict]) -> None:
    key = _make_key("/api/ai/report/strategy", {"strategyId": strategy_id, "days": days})
    _report_cache[key] = data
