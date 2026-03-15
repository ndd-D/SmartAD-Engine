"""
指令解析服务（LangChain 重构版）
架构分层：
  核心层：LangChain 解析链 + 反思链
  扩展层：路由链（意图分类）
  保障层：护栏（参数合规）+ 缓存 + 异常处理
  优化层：缓存复用（人群/历史数据）

主要流程：
  parse_command()           → 路由 → 解析 → 反思 → 护栏 → 上报
  parse_command_with_reply()→ 追问回答 → 反思 → 护栏 → 上报
"""
from loguru import logger

from app.util.http_client import get, post
from app.cache import (
    get_crowd_cache, set_crowd_cache,
    get_history_cache, set_history_cache,
)
from app.guardrails import check_input, check_strategies
from app.monitoring import metrics

from chains.route_chain import build_route_chain
from chains.command_chain import run_parse_with_reflection


# ──────────────────────────────────────────────────────────────────────────────
# 上下文拉取（带缓存）
# ──────────────────────────────────────────────────────────────────────────────

async def _fetch_context() -> tuple[list[dict], list[dict]]:
    """获取人群画像列表 + 历史投放效果数据（带本地缓存）"""
    # 人群画像
    crowd_list = get_crowd_cache()
    if crowd_list is None:
        metrics.cache_miss += 1
        try:
            crowd_resp = await get("/api/ai/crowd/list")
            crowd_list = crowd_resp.get("data") or []
            set_crowd_cache(crowd_list)
        except Exception as e:
            logger.warning(f"获取人群画像失败: {e}")
            crowd_list = []
    else:
        metrics.cache_hit += 1

    # 历史数据
    history_data = get_history_cache()
    if history_data is None:
        metrics.cache_miss += 1
        try:
            history_resp = await get("/api/ai/report/history")
            raw_history = history_resp.get("data")
            if isinstance(raw_history, dict):
                history_data = [raw_history] if any(raw_history.values()) else []
            elif isinstance(raw_history, list):
                history_data = raw_history
            else:
                history_data = []
            set_history_cache(history_data)
        except Exception as e:
            logger.warning(f"获取历史投放效果失败: {e}")
            history_data = []
    else:
        metrics.cache_hit += 1

    return crowd_list, history_data


# ──────────────────────────────────────────────────────────────────────────────
# 策略上报
# ──────────────────────────────────────────────────────────────────────────────

async def _sync_strategies(command_id: str, strategies: list[dict]) -> None:
    """逐条上报策略草案到 Java 后端"""
    for s in strategies:
        channel = s.get("channel", "")
        crowd_tag = s.get("crowdTag", "")
        budget_day = s.get("budgetDay", 500)
        bid_price = s.get("bidPrice", 100)
        risk_level = s.get("riskLevel", "普通")
        reason = s.get("reason", "AI智能推荐")
        try:
            await post("/api/ai/strategy/sync", {
                "commandId": command_id,
                "strategyName": f"{crowd_tag}-{channel}-智能投放",
                "channels": [channel],
                "budgetDay": int(budget_day),
                "crowdTag": crowd_tag,
                "bidPrice": int(bid_price),
                "runTime": "00:00-23:59",
                "riskLevel": risk_level,
            })
            logger.info(f"策略上报成功: commandId={command_id}, channel={channel}")
        except Exception as e:
            logger.error(f"策略上报失败: commandId={command_id}, channel={channel}, error={e}")


# ──────────────────────────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────────────────────────

async def parse_command(command_id: str, command_text: str) -> None:
    """
    主流程：
    1. 输入护栏校验
    2. 路由判断（轻量模型）：simple / complex / invalid
    3. 拉取上下文（带缓存）
    4. 调用 LangChain 解析链 + 反思链生成策略草案
    5. 输出护栏校验（参数合规修正）
    6. 上报策略草案给 Java 后端
    """
    logger.info(f"开始解析指令: commandId={command_id}, text={command_text}")
    metrics.command_parse_total += 1

    # ── 1. 输入护栏 ────────────────────────────────────────────────────────────
    input_guard = check_input(command_text)
    if not input_guard.passed:
        logger.warning(f"[Guardrail] 输入违规，拒绝处理: {input_guard.violations}")
        metrics.guardrail_rejected += 1
        await _mark_command_failed(command_id, f"输入违规: {'; '.join(input_guard.violations)}")
        return

    # ── 2. 路由判断（轻量模型，低成本）────────────────────────────────────────
    try:
        route_chain = build_route_chain()
        route_result = await route_chain.ainvoke({"command_text": command_text})
        complexity = route_result.get("complexity", "simple")
        logger.info(f"路由判断: complexity={complexity}, reason={route_result.get('reason', '')}")
    except Exception as e:
        logger.warning(f"路由判断失败，降级为 simple: {e}")
        complexity = "simple"

    if complexity == "invalid":
        await _mark_command_failed(command_id, "非广告投放相关指令，无法处理")
        metrics.command_parse_fail += 1
        return

    # ── 3. 拉取上下文（带缓存）────────────────────────────────────────────────
    crowd_list, history_data = await _fetch_context()

    # ── 4. 调用 LangChain 解析链（含反思）─────────────────────────────────────
    try:
        result = await run_parse_with_reflection(
            command_text=command_text,
            crowd_list=crowd_list,
            history_data=history_data,
        )
    except Exception as e:
        logger.error(f"[ParseChain] 指令解析异常: commandId={command_id}, error={e}")
        await _mark_command_failed(command_id, f"AI解析异常: {e}")
        metrics.command_parse_fail += 1
        return

    logger.debug(f"LLM 解析结果: {result}")

    # ── 5. 处理追问 ────────────────────────────────────────────────────────────
    has_question = result.get("hasQuestion", False)
    if has_question:
        question = result.get("question", "")
        logger.info(f"指令需要追问: commandId={command_id}, question={question}")
        metrics.command_need_question += 1
        await post("/api/ai/command/update", {
            "commandId": command_id,
            "status": "AI提问中",
            "aiQuestion": question,
        })
        return

    # ── 6. 输出护栏 + 上报 ────────────────────────────────────────────────────
    strategies = result.get("strategies", [])
    if not strategies:
        logger.warning(f"LLM 未生成任何策略草案，commandId={command_id}")
        await _mark_command_failed(command_id, "AI未能生成策略草案")
        metrics.command_parse_fail += 1
        return

    safe_strategies = check_strategies(strategies)
    if not safe_strategies:
        logger.error(f"[Guardrail] 所有策略被护栏拒绝，commandId={command_id}")
        await _mark_command_failed(command_id, "策略未通过合规校验")
        metrics.guardrail_rejected += 1
        metrics.command_parse_fail += 1
        return

    metrics.guardrail_high_risk += sum(
        1 for s in safe_strategies if s.get("riskLevel") == "高风险"
    )

    logger.info(f"生成策略草案 {len(safe_strategies)} 条，开始上报")
    await _sync_strategies(command_id, safe_strategies)
    metrics.command_parse_success += 1


async def parse_command_with_reply(
    command_id: str,
    command_text: str,
    question: str,
    answer: str,
) -> None:
    """
    追问回答后重新解析，生成策略草案
    """
    logger.info(f"追问回答后重新解析: commandId={command_id}")
    metrics.command_parse_total += 1

    crowd_list, history_data = await _fetch_context()

    try:
        result = await run_parse_with_reflection(
            command_text=command_text,
            crowd_list=crowd_list,
            history_data=history_data,
            use_reply=True,
            question=question,
            answer=answer,
        )
    except Exception as e:
        logger.error(f"[ParseChain] 追问后解析异常: commandId={command_id}, error={e}")
        await _mark_command_failed(command_id, f"追问后AI解析异常: {e}")
        metrics.command_parse_fail += 1
        return

    logger.debug(f"追问后 LLM 解析结果: {result}")

    has_question = result.get("hasQuestion", False)
    if has_question:
        question2 = result.get("question", "")
        metrics.command_need_question += 1
        await post("/api/ai/command/update", {
            "commandId": command_id,
            "status": "AI提问中",
            "aiQuestion": question2,
        })
        return

    strategies = result.get("strategies", [])
    if not strategies:
        await _mark_command_failed(command_id, "追问后AI仍未生成策略")
        metrics.command_parse_fail += 1
        return

    safe_strategies = check_strategies(strategies)
    if not safe_strategies:
        await _mark_command_failed(command_id, "追问后策略未通过合规校验")
        metrics.guardrail_rejected += 1
        metrics.command_parse_fail += 1
        return

    logger.info(f"追问后生成策略草案 {len(safe_strategies)} 条，开始上报")
    await _sync_strategies(command_id, safe_strategies)
    metrics.command_parse_success += 1


async def _mark_command_failed(command_id: str, reason: str) -> None:
    try:
        await post("/api/ai/command/update", {
            "commandId": command_id,
            "status": "处理失败",
            "failReason": reason,
        })
    except Exception as e:
        logger.error(f"标记指令失败时出错: {e}")
