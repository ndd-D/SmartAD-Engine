"""
监控模块（Monitoring Layer）
- 统计每次 LLM 调用的耗时、成功/失败次数
- 统计指令解析成功率、评估执行次数
- 暴露 /ai/metrics 接口供运维查看
"""
import time
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger


@dataclass
class Metrics:
    """全局指标计数器（单例）"""
    # LLM 调用统计
    llm_call_total: int = 0
    llm_call_success: int = 0
    llm_call_fail: int = 0
    llm_total_latency_ms: float = 0.0

    # 指令解析统计
    command_parse_total: int = 0
    command_parse_success: int = 0
    command_parse_fail: int = 0
    command_need_question: int = 0

    # 评估统计
    evaluate_total: int = 0
    evaluate_adjust: int = 0
    alert_total: int = 0
    alert_triggered: int = 0

    # 护栏统计
    guardrail_rejected: int = 0
    guardrail_high_risk: int = 0

    # 缓存命中率
    cache_hit: int = 0
    cache_miss: int = 0

    def to_dict(self) -> dict:
        avg_latency = (
            round(self.llm_total_latency_ms / self.llm_call_total, 1)
            if self.llm_call_total > 0 else 0
        )
        cache_total = self.cache_hit + self.cache_miss
        cache_rate = round(self.cache_hit / cache_total * 100, 1) if cache_total > 0 else 0

        return {
            "llm": {
                "total": self.llm_call_total,
                "success": self.llm_call_success,
                "fail": self.llm_call_fail,
                "avg_latency_ms": avg_latency,
            },
            "command": {
                "total": self.command_parse_total,
                "success": self.command_parse_success,
                "fail": self.command_parse_fail,
                "need_question": self.command_need_question,
            },
            "evaluate": {
                "total": self.evaluate_total,
                "adjust": self.evaluate_adjust,
            },
            "alert": {
                "total": self.alert_total,
                "triggered": self.alert_triggered,
            },
            "guardrail": {
                "rejected": self.guardrail_rejected,
                "high_risk": self.guardrail_high_risk,
            },
            "cache": {
                "hit": self.cache_hit,
                "miss": self.cache_miss,
                "hit_rate_pct": cache_rate,
            },
        }


# 全局单例
metrics = Metrics()


# ──────────────────────────────────────────────────────────────────────────────
# 上下文管理器：记录 LLM 调用耗时
# ──────────────────────────────────────────────────────────────────────────────

class LLMCallContext:
    def __init__(self, label: str = ""):
        self.label = label
        self._start = 0.0

    def __enter__(self):
        self._start = time.time()
        metrics.llm_call_total += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.time() - self._start) * 1000
        metrics.llm_total_latency_ms += elapsed_ms
        if exc_type is None:
            metrics.llm_call_success += 1
            logger.debug(f"[Metrics] LLM调用成功 [{self.label}], 耗时 {elapsed_ms:.0f}ms")
        else:
            metrics.llm_call_fail += 1
            logger.warning(f"[Metrics] LLM调用失败 [{self.label}], 耗时 {elapsed_ms:.0f}ms")
        return False  # 不抑制异常
