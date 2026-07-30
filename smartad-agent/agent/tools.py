"""
SmartAD Agent 工具定义
每个工具都是 LangChain StructuredTool，供 Agent 自主调用
设计原则：
- 单一职责：每个工具只做一件事
- 返回结构化数据：便于 Agent 链式推理
- 容错降级：外部依赖不可用时返回 Mock 数据
"""
from __future__ import annotations

from typing import Optional, Type
from loguru import logger
from pydantic import BaseModel, Field

from app.util.http_client import get
from app.cache import (
    get_crowd_cache, set_crowd_cache,
    get_history_cache, set_history_cache,
    get_report_cache, set_report_cache,
)
from ai_config.settings import settings


# ──────────────────────────────────────────────────────────────────────────────
# 工具参数 Schema
# ──────────────────────────────────────────────────────────────────────────────

class GetCrowdInfoInput(BaseModel):
    """查询人群画像信息"""
    crowd_tag: str = Field(description="人群标签，如 young_fashion, student")


class GetHistoryReportInput(BaseModel):
    """查询历史投放效果"""
    crowd_tag: Optional[str] = Field(default=None, description="人群标签（可选）")
    channel: Optional[str] = Field(default=None, description="渠道（可选）")


class GetRealtimeReportInput(BaseModel):
    """查询策略实时报表"""
    strategy_id: str = Field(description="策略 ID")
    days: int = Field(default=7, description="查询天数")


class SearchKnowledgeInput(BaseModel):
    """检索知识库"""
    query: str = Field(description="检索查询文本")
    category: Optional[str] = Field(default=None, description="知识类型: crowd/channel/rule")
    top_k: int = Field(default=3, description="返回条数")


class ValidateStrategyInput(BaseModel):
    """校验策略合规性"""
    channel: str = Field(description="投放渠道")
    crowd_tag: str = Field(description="人群标签")
    budget_day: float = Field(description="日预算（元）")
    bid_price: int = Field(description="出价（分）")


class CalculateBidInput(BaseModel):
    """根据历史数据建议出价"""
    crowd_tag: str = Field(description="人群标签")
    channel: str = Field(description="投放渠道")
    budget_day: Optional[float] = Field(default=None, description="日预算（可选）")


# ──────────────────────────────────────────────────────────────────────────────
# 工具实现（同步包装器）
# ──────────────────────────────────────────────────────────────────────────────

def get_crowd_info(crowd_tag: str) -> dict:
    """查询指定人群标签的详细信息，包含画像描述、转化率、出价策略。"""
    cache = get_crowd_cache()
    if cache:
        for c in cache:
            if c.get("crowdTag") == crowd_tag:
                return {"status": "ok", "source": "cache", "data": c}

    try:
        resp = get("/api/ai/crowd/info", params={"crowdTag": crowd_tag})
        return {"status": "ok", "source": "api", "data": resp.get("data", {})}
    except Exception as e:
        logger.warning(f"[Tool] get_crowd_info 降级: {e}")
        from rag.knowledge import CROWD_DATABASE
        for item in CROWD_DATABASE:
            if item["tag"] == crowd_tag:
                return {"status": "ok", "source": "knowledge", "data": item}
        return {"status": "error", "message": f"未找到人群: {crowd_tag}"}


def get_history_report(crowd_tag: Optional[str] = None, channel: Optional[str] = None) -> dict:
    """查询指定人群和渠道的历史投放效果数据，包含 CTR、转化率、ROI、建议出价。"""
    cache = get_history_cache()
    if cache:
        return {"status": "ok", "source": "cache", "data": cache}

    try:
        params = {}
        if crowd_tag:
            params["crowdTag"] = crowd_tag
        if channel:
            params["channel"] = channel
        resp = get("/api/ai/report/history", params=params)
        data = resp.get("data") or []
        set_history_cache(data if isinstance(data, list) else [data])
        return {"status": "ok", "source": "api", "data": data}
    except Exception as e:
        logger.warning(f"[Tool] get_history_report 降级: {e}")
        return {
            "status": "ok",
            "source": "mock",
            "data": [{"avgClickRate": 0.03, "avgConvertRate": 0.008, "avgRoi": 2.0, "suggestBid": 120}],
        }


def get_realtime_report(strategy_id: str, days: int = 7) -> dict:
    """查询指定策略近 N 天的实时投放报表，包含曝光、点击、CTR、消耗、转化、ROI。"""
    cached = get_report_cache(strategy_id, days)
    if cached:
        return {"status": "ok", "source": "cache", "data": cached}

    try:
        resp = get("/api/ai/report/strategy", params={"strategyId": strategy_id, "days": days})
        data = resp.get("data") or []
        if data:
            set_report_cache(strategy_id, days, data)
        return {"status": "ok", "source": "api", "data": data}
    except Exception as e:
        logger.warning(f"[Tool] get_realtime_report 降级: {e}")
        return {
            "status": "ok",
            "source": "mock",
            "data": [
                {"reportDate": "2026-03-15", "impressions": 50000, "clicks": 800,
                 "cost": 960, "conversions": 32, "ctr": 0.016, "roi": 1.8}
            ],
        }


def search_knowledge(query: str, category: Optional[str] = None, top_k: int = 3) -> dict:
    """从 RAG 知识库中检索与查询最相关的知识条目，支持按类型过滤。"""
    try:
        from rag.retriever import get_retriever
        retriever = get_retriever()
        results = retriever.retrieve(query=query, top_k=top_k, category=category)
        return {"status": "ok", "source": "rag", "data": results}
    except Exception as e:
        logger.warning(f"[Tool] search_knowledge 降级: {e}")
        from rag.knowledge import CROWD_DATABASE, CHANNEL_DATABASE
        all_data = CROWD_DATABASE + CHANNEL_DATABASE
        results = []
        query_lower = query.lower()
        for item in all_data:
            text = str(item).lower()
            if any(term in text for term in query_lower.split()):
                results.append(item)
            if len(results) >= top_k:
                break
        return {"status": "ok", "source": "keyword", "data": results}


def validate_strategy(channel: str, crowd_tag: str, budget_day: float, bid_price: int) -> dict:
    """校验投放策略的合规性：渠道合法性、预算范围、出价范围、高风险标记。"""
    from app.guardrails import check_strategy

    strategy = {
        "channel": channel,
        "crowdTag": crowd_tag,
        "budgetDay": budget_day,
        "bidPrice": bid_price,
    }
    result = check_strategy(strategy)

    return {
        "status": "ok" if result.passed else "rejected",
        "passed": result.passed,
        "risk_level": result.risk_level,
        "violations": result.violations,
        "sanitized": result.sanitized,
        "message": "策略合规" if result.passed else f"策略不合规: {'; '.join(result.violations)}",
    }


def calculate_bid(crowd_tag: str, channel: str, budget_day: Optional[float] = None) -> dict:
    """根据人群画像、渠道特征和历史数据，智能建议出价和预算分配方案。"""
    suggestions = []

    crowd_info = get_crowd_info(crowd_tag)
    if crowd_info.get("status") == "ok":
        data = crowd_info.get("data", {})
        bid_strategy = data.get("bid_strategy", "中等出价")
        conversion_rate = data.get("conversion_rate", "中等")
        suggestions.append(f"人群 {crowd_tag}: {bid_strategy}, 转化率{conversion_rate}")

    history = get_history_report(crowd_tag=crowd_tag, channel=channel)
    if history.get("status") == "ok" and history.get("data"):
        avg_roi = history["data"][0].get("avgRoi", "N/A")
        suggest_bid = history["data"][0].get("suggestBid", 120)
        suggestions.append(f"历史ROI: {avg_roi}, 建议出价: {suggest_bid}分")

    if budget_day:
        per_day = budget_day
        suggestions.append(f"日预算: {per_day}元")

    from rag.knowledge import CHANNEL_DATABASE
    for ch in CHANNEL_DATABASE:
        if ch["channel"] == channel:
            suggestions.append(f"渠道 {channel}: {ch['feature']}")
            break

    suggested_bid = 120
    if history.get("data"):
        suggested_bid = history["data"][0].get("suggestBid", 120)

    return {
        "status": "ok",
        "crowd_tag": crowd_tag,
        "channel": channel,
        "suggested_bid_price": suggested_bid,
        "suggested_budget_day": budget_day or 500,
        "analysis": suggestions,
    }


# ──────────────────────────────────────────────────────────────────────────────
# LangChain Tool 导出（延迟导入避免循环依赖）
# ──────────────────────────────────────────────────────────────────────────────

def _build_tools():
    """构建 LangChain 工具列表"""
    try:
        from langchain_core.tools import StructuredTool

        return [
            StructuredTool.from_function(
                func=get_crowd_info,
                name="get_crowd_info",
                description="查询指定人群标签的详细信息，包含画像描述、转化率、出价策略。当需要了解某个人群的特征时使用此工具。",
                args_schema=GetCrowdInfoInput,
            ),
            StructuredTool.from_function(
                func=get_history_report,
                name="get_history_report",
                description="查询指定人群和渠道的历史投放效果数据，包含 CTR、转化率、ROI、建议出价。用于参考历史表现做决策。",
                args_schema=GetHistoryReportInput,
            ),
            StructuredTool.from_function(
                func=get_realtime_report,
                name="get_realtime_report",
                description="查询指定策略近 N 天的实时投放报表，包含曝光、点击、CTR、消耗、转化、ROI。用于监控策略效果。",
                args_schema=GetRealtimeReportInput,
            ),
            StructuredTool.from_function(
                func=search_knowledge,
                name="search_knowledge",
                description="从 RAG 知识库中检索与查询最相关的知识条目，支持按类型过滤。用于获取广告投放相关的背景知识。",
                args_schema=SearchKnowledgeInput,
            ),
            StructuredTool.from_function(
                func=validate_strategy,
                name="validate_strategy",
                description="校验投放策略的合规性：渠道合法性、预算范围、出价范围、高风险标记。在生成策略后必须调用此工具。",
                args_schema=ValidateStrategyInput,
            ),
            StructuredTool.from_function(
                func=calculate_bid,
                name="calculate_bid",
                description="根据人群画像、渠道特征和历史数据，智能建议出价和预算分配方案。在需要制定具体出价时使用。",
                args_schema=CalculateBidInput,
            ),
        ]
    except ImportError:
        logger.warning("[Tools] langchain_core 未安装，工具不可用")
        return []


def get_all_tools():
    """获取所有 Agent 工具"""
    return _build_tools()
