"""
策略评估服务（LangChain 重构版）
架构分层：
  核心层：LangChain 评估链 + 告警链
  优化层：并行化处理（asyncio.gather）+ 报表缓存
  保障层：异常处理 + 监控指标

评估规则：
  成功：ROI >= 2 且 预算消耗偏差 <= 10%
  失败：ROI < 1  且 预算消耗偏差 > 20%
"""
import asyncio
from loguru import logger

from app.util.http_client import get, post
from app.cache import get_report_cache, set_report_cache
from app.monitoring import metrics
from ai_evaluate.archiver import save_evaluate_result

from chains.evaluate_chain import run_evaluate_parallel, run_alert_parallel


# ──────────────────────────────────────────────────────────────────────────────
# 数据拉取
# ──────────────────────────────────────────────────────────────────────────────

async def _get_active_strategies() -> list[dict]:
    """拉取所有投放中策略（status=running）"""
    try:
        resp = await get("/api/ai/strategy/active")
        return resp.get("data") or []
    except Exception as e:
        logger.warning(f"获取投放中策略失败: {e}")
        return []


async def _fetch_report(strategy_id: str, days: int) -> list[dict]:
    """拉取策略报表数据（带本地缓存）"""
    cached = get_report_cache(strategy_id, days)
    if cached is not None:
        metrics.cache_hit += 1
        return cached

    metrics.cache_miss += 1
    try:
        report_resp = await get("/api/ai/report/strategy", params={"strategyId": strategy_id, "days": days})
        data = report_resp.get("data") or []
        if data:
            set_report_cache(strategy_id, days, data)
        return data
    except Exception as e:
        logger.warning(f"获取策略 {strategy_id} 报表失败: {e}")
        return []


async def _fetch_all_reports(
    strategies: list[dict], days: int
) -> list[tuple[dict, list[dict]]]:
    """并发拉取所有策略的报表数据"""
    tasks = [_fetch_report(s.get("strategyId"), days) for s in strategies]
    reports = await asyncio.gather(*tasks)
    return [
        (strategy, report)
        for strategy, report in zip(strategies, reports)
        if report  # 跳过无报表数据的策略
    ]


# ──────────────────────────────────────────────────────────────────────────────
# 评估结果判定
# ──────────────────────────────────────────────────────────────────────────────

def _judge_evaluate_result(roi: float, budget_deviation: float) -> str | None:
    """
    按文档规则判定评估结果：
    成功：ROI >= 2 且 预算消耗偏差 <= 0.10
    失败：ROI < 1  且 预算消耗偏差 > 0.20
    其余：不标记，返回 None
    """
    try:
        roi_f = float(roi)
        dev_f = float(budget_deviation)
    except (TypeError, ValueError):
        return None

    if roi_f >= 2 and dev_f <= 0.10:
        return "成功"
    if roi_f < 1 and dev_f > 0.20:
        return "失败"
    return None


# ──────────────────────────────────────────────────────────────────────────────
# 评估服务
# ──────────────────────────────────────────────────────────────────────────────

async def evaluate_active_strategies() -> None:
    """
    并行拉取所有投放中策略报表 → LangChain 评估链（并发）→ 上报调参/评估结果
    """
    strategies = await _get_active_strategies()
    if not strategies:
        logger.debug("当前没有投放中策略，跳过评估")
        return

    logger.info(f"开始评估 {len(strategies)} 条投放中策略（并行模式）")
    metrics.evaluate_total += len(strategies)

    # 并发拉取报表
    strategies_with_reports = await _fetch_all_reports(strategies, days=7)
    if not strategies_with_reports:
        logger.debug("所有策略暂无报表数据，跳过评估")
        return

    # 并行 LLM 评估
    results = await run_evaluate_parallel(strategies_with_reports)

    # 逐条上报
    for strategy, result in results:
        if not result:
            continue

        strategy_id = strategy.get("strategyId")
        command_id = strategy.get("commandId", "")

        need_adjust = result.get("needAdjust", False)
        roi = result.get("roi", 0)
        budget_deviation = result.get("budgetDeviation", 0)
        reason = result.get("reason", "")
        logger.info(
            f"策略 {strategy_id} 评估: needAdjust={need_adjust}, "
            f"roi={roi}, deviation={budget_deviation}"
        )

        # 存档评估结果
        save_evaluate_result(strategy_id, result)

        # 参数调优
        if need_adjust:
            metrics.evaluate_adjust += 1
            await _post_adjustment(strategy, result)

        # 判定并上报评估结论
        evaluate_result = _judge_evaluate_result(roi, budget_deviation)
        if evaluate_result and command_id:
            try:
                await post("/api/ai/strategy/evaluate", {
                    "strategyId": strategy_id,
                    "commandId": command_id,
                    "evaluateResult": evaluate_result,
                    "roi": roi,
                    "budgetDeviation": budget_deviation,
                    "evaluateReason": reason,
                })
                logger.info(f"策略 {strategy_id} 评估结果已上报: {evaluate_result}")
            except Exception as e:
                logger.error(f"策略 {strategy_id} 评估结果上报失败: {e}")


async def _post_adjustment(strategy: dict, result: dict) -> None:
    """上报调参建议"""
    strategy_id = strategy.get("strategyId")
    llm_adjust_type = result.get("adjustType", "no_action")
    reason = result.get("reason", "")
    adjust_map = {
        "bid_up":     ("bidPrice",  result.get("newBidPrice")),
        "bid_down":   ("bidPrice",  result.get("newBidPrice")),
        "budget_up":  ("budgetDay", result.get("newBudgetDay")),
        "budget_down":("budgetDay", result.get("newBudgetDay")),
    }
    if llm_adjust_type in adjust_map:
        backend_type, new_value = adjust_map[llm_adjust_type]
        if new_value is not None:
            old_value = (
                strategy.get("bidPrice") if backend_type == "bidPrice"
                else strategy.get("budgetDay")
            )
            try:
                await post("/api/ai/strategy/adjust", {
                    "strategyId": strategy_id,
                    "adjustType": backend_type,
                    "oldValue": old_value,
                    "newValue": new_value,
                    "reason": reason,
                })
                logger.info(f"策略 {strategy_id} 调参: type={backend_type}, {old_value} -> {new_value}")
            except Exception as e:
                logger.error(f"策略 {strategy_id} 调参上报失败: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# 告警服务
# ──────────────────────────────────────────────────────────────────────────────

async def check_alerts_for_strategies() -> None:
    """
    并行检测投放中策略告警
    """
    strategies = await _get_active_strategies()
    if not strategies:
        return

    metrics.alert_total += len(strategies)

    # 并发拉取近 3 天报表
    strategies_with_reports = await _fetch_all_reports(strategies, days=3)
    if not strategies_with_reports:
        return

    # 并行 LLM 告警检测
    results = await run_alert_parallel(strategies_with_reports)

    for strategy, result in results:
        if not result:
            continue

        has_alert = result.get("hasAlert", False)
        if has_alert:
            strategy_id = strategy.get("strategyId")
            alert_type = result.get("alertType", "策略执行失败")
            alert_message = result.get("alertMessage", "")
            logger.warning(f"策略 {strategy_id} 触发告警: {alert_type} - {alert_message}")
            metrics.alert_triggered += 1
            try:
                await post("/api/ai/notice/alert/push", {
                    "alertContent": alert_message,
                    "alertType": alert_type,
                    "relatedId": strategy.get("strategyId"),
                })
            except Exception as e:
                logger.error(f"告警推送失败: strategy={strategy.get('strategyId')}, error={e}")
