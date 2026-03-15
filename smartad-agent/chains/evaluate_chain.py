"""
评估与告警链（Evaluate & Alert Chains）
- 评估链：EVALUATE_PROMPT | 标准LLM | JSON解析器
- 告警链：ALERT_PROMPT | 标准LLM | JSON解析器
- 并行评估入口：asyncio.gather 并发处理多条策略
"""
import asyncio
from langchain_core.runnables import RunnableSequence
from loguru import logger

from ai_config.llm_client import get_llm_standard
from rag.prompt_builder import EVALUATE_PROMPT, ALERT_PROMPT, build_evaluate_vars, build_alert_vars
from chains.parsers import JsonOutputParser


def build_evaluate_chain() -> RunnableSequence:
    """
    策略评估链：EVALUATE_PROMPT | 标准LLM | JSON解析器
    输入变量: strategy_id, crowd_tag, channel, budget_day, bid_price, report_desc
    """
    return EVALUATE_PROMPT | get_llm_standard() | JsonOutputParser()


def build_alert_chain() -> RunnableSequence:
    """
    告警检测链：ALERT_PROMPT | 标准LLM | JSON解析器
    输入变量: strategy_id, crowd_tag, channel, budget_day, report_desc
    """
    return ALERT_PROMPT | get_llm_standard() | JsonOutputParser()


async def run_evaluate_single(
    strategy: dict,
    report_data: list[dict],
    evaluate_chain: RunnableSequence,
) -> tuple[dict, dict]:
    """
    对单条策略执行评估，返回 (strategy, result)
    """
    try:
        vars_ = build_evaluate_vars(strategy, report_data)
        result = await evaluate_chain.ainvoke(vars_)
        return strategy, result
    except Exception as e:
        strategy_id = strategy.get("strategyId", "unknown")
        logger.error(f"[EvaluateChain] 策略 {strategy_id} 评估异常: {e}")
        return strategy, {}


async def run_alert_single(
    strategy: dict,
    report_data: list[dict],
    alert_chain: RunnableSequence,
) -> tuple[dict, dict]:
    """
    对单条策略执行告警检测，返回 (strategy, result)
    """
    try:
        vars_ = build_alert_vars(strategy, report_data)
        result = await alert_chain.ainvoke(vars_)
        return strategy, result
    except Exception as e:
        strategy_id = strategy.get("strategyId", "unknown")
        logger.error(f"[AlertChain] 策略 {strategy_id} 告警检测异常: {e}")
        return strategy, {}


async def run_evaluate_parallel(
    strategies_with_reports: list[tuple[dict, list[dict]]],
) -> list[tuple[dict, dict]]:
    """
    并行评估多条策略（asyncio.gather）
    输入: [(strategy, report_data), ...]
    输出: [(strategy, evaluate_result), ...]
    """
    evaluate_chain = build_evaluate_chain()
    tasks = [
        run_evaluate_single(strategy, report_data, evaluate_chain)
        for strategy, report_data in strategies_with_reports
    ]
    return list(await asyncio.gather(*tasks))


async def run_alert_parallel(
    strategies_with_reports: list[tuple[dict, list[dict]]],
) -> list[tuple[dict, dict]]:
    """
    并行告警检测多条策略（asyncio.gather）
    """
    alert_chain = build_alert_chain()
    tasks = [
        run_alert_single(strategy, report_data, alert_chain)
        for strategy, report_data in strategies_with_reports
    ]
    return list(await asyncio.gather(*tasks))
