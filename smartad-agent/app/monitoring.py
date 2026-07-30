"""
监控模块（Monitoring Layer）
- 统计每次 LLM 调用的耗时、成功/失败次数
- 统计指令解析成功率、评估执行次数
- 暴露 /ai/metrics 接口供运维查看
- 支持 Prometheus 指标导出
- 支持 LangSmith/Langfuse 链路追踪（可选）
"""
import time
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger

# Prometheus 可选依赖
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


# ──────────────────────────────────────────────────────────────────────────────
# Prometheus 指标
# ──────────────────────────────────────────────────────────────────────────────

if PROMETHEUS_AVAILABLE:
    llm_calls_total = Counter(
        "smartad_llm_calls_total",
        "Total LLM calls",
        ["model", "status"],
    )
    llm_latency_seconds = Histogram(
        "smartad_llm_latency_seconds",
        "LLM call latency",
        ["model"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 60.0],
    )
    command_parse_total = Counter(
        "smartad_command_parse_total",
        "Total command parse requests",
        ["status"],
    )
    agent_steps_total = Counter(
        "smartad_agent_steps_total",
        "Total agent tool calls",
        ["tool_name"],
    )
    evaluate_total = Counter(
        "smartad_evaluate_total",
        "Total strategy evaluations",
    )
    alert_total = Counter(
        "smartad_alert_total",
        "Total alert checks",
        ["status"],
    )
    cache_hit_ratio = Gauge(
        "smartad_cache_hit_ratio",
        "Cache hit ratio",
    )
    active_strategies_gauge = Gauge(
        "smartad_active_strategies",
        "Number of active strategies",
    )


# ──────────────────────────────────────────────────────────────────────────────
# 内存指标（兼容模式）
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Metrics:
    """全局指标计数器（单例）"""
    llm_call_total: int = 0
    llm_call_success: int = 0
    llm_call_fail: int = 0
    llm_total_latency_ms: float = 0.0

    command_parse_total: int = 0
    command_parse_success: int = 0
    command_parse_fail: int = 0
    command_need_question: int = 0

    evaluate_total: int = 0
    evaluate_adjust: int = 0
    alert_total: int = 0
    alert_triggered: int = 0

    guardrail_rejected: int = 0
    guardrail_high_risk: int = 0

    cache_hit: int = 0
    cache_miss: int = 0

    agent_total_steps: int = 0
    agent_tool_calls: dict = field(default_factory=lambda: defaultdict(int))

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
            "agent": {
                "total_steps": self.agent_total_steps,
                "tool_calls": dict(self.agent_tool_calls),
            },
        }


metrics = Metrics()


# ──────────────────────────────────────────────────────────────────────────────
# 上下文管理器：记录 LLM 调用耗时
# ──────────────────────────────────────────────────────────────────────────────

class LLMCallContext:
    def __init__(self, label: str = "", model: str = "unknown"):
        self.label = label
        self.model = model
        self._start = 0.0

    def __enter__(self):
        self._start = time.time()
        metrics.llm_call_total += 1
        if PROMETHEUS_AVAILABLE:
            llm_calls_total.labels(model=self.model, status="started").inc()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_s = time.time() - self._start
        elapsed_ms = elapsed_s * 1000
        metrics.llm_total_latency_ms += elapsed_ms

        if PROMETHEUS_AVAILABLE:
            llm_latency_seconds.labels(model=self.model).observe(elapsed_s)

        if exc_type is None:
            metrics.llm_call_success += 1
            if PROMETHEUS_AVAILABLE:
                llm_calls_total.labels(model=self.model, status="success").inc()
            logger.debug(f"[Metrics] LLM调用成功 [{self.label}], 耗时 {elapsed_ms:.0f}ms")
        else:
            metrics.llm_call_fail += 1
            if PROMETHEUS_AVAILABLE:
                llm_calls_total.labels(model=self.model, status="fail").inc()
            logger.warning(f"[Metrics] LLM调用失败 [{self.label}], 耗时 {elapsed_ms:.0f}ms")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────────────────────────────────────

def record_command_parse(status: str) -> None:
    """记录指令解析结果"""
    metrics.command_parse_total += 1
    if status == "success":
        metrics.command_parse_success += 1
        if PROMETHEUS_AVAILABLE:
            command_parse_total.labels(status="success").inc()
    elif status == "fail":
        metrics.command_parse_fail += 1
        if PROMETHEUS_AVAILABLE:
            command_parse_total.labels(status="fail").inc()
    elif status == "need_question":
        metrics.command_need_question += 1
        if PROMETHEUS_AVAILABLE:
            command_parse_total.labels(status="need_question").inc()


def record_agent_step(tool_name: str) -> None:
    """记录 Agent 工具调用"""
    metrics.agent_total_steps += 1
    metrics.agent_tool_calls[tool_name] += 1
    if PROMETHEUS_AVAILABLE:
        agent_steps_total.labels(tool_name=tool_name).inc()


def record_alert(triggered: bool) -> None:
    """记录告警"""
    metrics.alert_total += 1
    if triggered:
        metrics.alert_triggered += 1
        if PROMETHEUS_AVAILABLE:
            alert_total.labels(status="triggered").inc()
    else:
        if PROMETHEUS_AVAILABLE:
            alert_total.labels(status="checked").inc()


def get_prometheus_metrics() -> bytes:
    """获取 Prometheus 格式的指标"""
    if PROMETHEUS_AVAILABLE:
        return generate_latest(REGISTRY)
    return b"# Prometheus not available\n"
