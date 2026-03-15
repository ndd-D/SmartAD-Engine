"""
保障层：护栏模块（Guardrails）
- 输入验证：投放指令安全性检查
- 输出审核：策略参数合规检查（预算/出价范围、高风险标注）
- 最小权限：仅允许操作白名单渠道与人群标签
"""
from dataclasses import dataclass, field
from ai_config.settings import settings
from loguru import logger


# ──────────────────────────────────────────────────────────────────────────────
# 护栏检查结果
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class GuardrailResult:
    passed: bool
    risk_level: str = "normal"        # normal / high / rejected
    violations: list[str] = field(default_factory=list)
    sanitized: dict | None = None     # 修正后的策略（如有）


# ──────────────────────────────────────────────────────────────────────────────
# 输入护栏：校验自然语言指令
# ──────────────────────────────────────────────────────────────────────────────

_BLOCKED_KEYWORDS = ["刷量", "刷数据", "虚假点击", "作弊", "bypass", "ignore rules"]

def check_input(command_text: str) -> GuardrailResult:
    """
    输入护栏：检查用户指令是否包含违规内容
    """
    violations = []
    for kw in _BLOCKED_KEYWORDS:
        if kw.lower() in command_text.lower():
            violations.append(f"指令包含违规关键词: {kw}")

    if violations:
        logger.warning(f"[Guardrail] 输入违规: {violations}")
        return GuardrailResult(passed=False, risk_level="rejected", violations=violations)

    return GuardrailResult(passed=True)


# ──────────────────────────────────────────────────────────────────────────────
# 输出护栏：校验策略参数合规性
# ──────────────────────────────────────────────────────────────────────────────

_ALLOWED_CHANNELS = {"douyin", "kuaishou", "weibo", "toutiao", "baidu"}

def check_strategy(strategy: dict) -> GuardrailResult:
    """
    输出护栏：对单条策略进行参数合规检查
    - 预算范围 [100, 100000] 元
    - 出价范围 [10, 10000] 分
    - 渠道白名单
    - 高风险标记（日预算 > 5000 或出价 > 5000分）
    """
    violations = []
    risk_level = "normal"
    sanitized = dict(strategy)

    # 1. 渠道白名单
    channel = strategy.get("channel", "")
    if channel not in _ALLOWED_CHANNELS:
        violations.append(f"不支持的渠道: {channel}")

    # 2. 预算范围检查
    budget = strategy.get("budgetDay", 0)
    try:
        budget = int(budget)
    except (TypeError, ValueError):
        violations.append("budgetDay 类型异常")
        budget = settings.guardrail_min_budget

    if budget < settings.guardrail_min_budget:
        violations.append(f"日预算 {budget} 低于最低限 {settings.guardrail_min_budget} 元，已自动修正")
        sanitized["budgetDay"] = settings.guardrail_min_budget
        budget = settings.guardrail_min_budget
    elif budget > settings.guardrail_max_budget:
        violations.append(f"日预算 {budget} 超过上限 {settings.guardrail_max_budget} 元，已自动修正")
        sanitized["budgetDay"] = settings.guardrail_max_budget
        budget = settings.guardrail_max_budget

    # 3. 出价范围检查
    bid = strategy.get("bidPrice", 0)
    try:
        bid = int(bid)
    except (TypeError, ValueError):
        violations.append("bidPrice 类型异常")
        bid = settings.guardrail_min_bid

    if bid < settings.guardrail_min_bid:
        violations.append(f"出价 {bid} 低于最低限 {settings.guardrail_min_bid} 分，已自动修正")
        sanitized["bidPrice"] = settings.guardrail_min_bid
        bid = settings.guardrail_min_bid
    elif bid > settings.guardrail_max_bid:
        violations.append(f"出价 {bid} 超过上限 {settings.guardrail_max_bid} 分，已自动修正")
        sanitized["bidPrice"] = settings.guardrail_max_bid
        bid = settings.guardrail_max_bid

    # 4. 高风险检测
    if budget > settings.guardrail_high_risk_budget or bid > settings.guardrail_high_risk_bid:
        risk_level = "high"
        sanitized["riskLevel"] = "高风险"
        logger.warning(
            f"[Guardrail] 高风险策略: channel={channel}, budget={budget}, bid={bid}"
        )
    else:
        sanitized["riskLevel"] = "普通"

    passed = channel in _ALLOWED_CHANNELS  # 渠道不合法则不通过
    if violations:
        logger.info(f"[Guardrail] 策略检查: passed={passed}, violations={violations}")

    return GuardrailResult(
        passed=passed,
        risk_level=risk_level,
        violations=violations,
        sanitized=sanitized,
    )


def check_strategies(strategies: list[dict]) -> list[dict]:
    """
    批量检查策略列表，返回通过护栏的策略（已修正参数）
    """
    result = []
    for s in strategies:
        gr = check_strategy(s)
        if gr.passed:
            result.append(gr.sanitized or s)
        else:
            logger.warning(f"[Guardrail] 策略被拒绝: {gr.violations}")
    return result
