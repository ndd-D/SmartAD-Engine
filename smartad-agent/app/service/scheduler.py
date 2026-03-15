"""
定时调度器（APScheduler）
- 每 N 秒：轮询待处理指令（parse_command）
- 每 N 秒：轮询追问回答指令（parse_command_with_reply）
- 每 5 分钟：并行评估投放中策略
- 每 10 分钟：并行告警检测

调度器设计原则：
- 每个任务均为独立协程，异常不影响其他任务
- 日志记录任务开始/结束，便于可观测性
"""
import asyncio
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ai_config.settings import settings
from app.util.http_client import get
from app.service.command_service import parse_command, parse_command_with_reply
from app.service.evaluate_service import evaluate_active_strategies, check_alerts_for_strategies

scheduler = AsyncIOScheduler()


# ──────────────────────────────────────────────────────────────────────────────
# 轮询任务：待处理指令
# ──────────────────────────────────────────────────────────────────────────────

async def poll_pending_commands():
    """
    轮询 Java 后端「待AI处理」的指令，调用解析链处理
    """
    try:
        resp = await get("/api/ai/command/list", params={"status": "待AI处理"})
        commands = resp.get("data") or []
        if not commands:
            return
        logger.info(f"[Scheduler] 获取到 {len(commands)} 条待处理指令")
        for cmd in commands:
            command_id = str(cmd.get("commandId", ""))
            command_text = cmd.get("commandText", "")
            if command_id and command_text:
                asyncio.create_task(
                    _safe_run(
                        parse_command(command_id, command_text),
                        label=f"parse_command:{command_id}",
                    )
                )
    except Exception as e:
        logger.error(f"[Scheduler] 轮询待处理指令异常: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# 轮询任务：追问回答指令
# ──────────────────────────────────────────────────────────────────────────────

async def poll_waiting_reply_commands():
    """
    轮询 Java 后端「处理中」（用户已回答追问）的指令
    """
    try:
        resp = await get("/api/ai/command/list", params={"status": "处理中"})
        commands = resp.get("data") or []
        if not commands:
            return
        logger.info(f"[Scheduler] 获取到 {len(commands)} 条追问回答指令")
        for cmd in commands:
            command_id = str(cmd.get("commandId", ""))
            command_text = cmd.get("commandText", "")
            question = cmd.get("aiQuestion", "")
            answer = cmd.get("userAnswer", "")
            if command_id and command_text:
                asyncio.create_task(
                    _safe_run(
                        parse_command_with_reply(command_id, command_text, question, answer),
                        label=f"parse_reply:{command_id}",
                    )
                )
    except Exception as e:
        logger.error(f"[Scheduler] 轮询追问回答指令异常: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# 定时任务：策略评估 & 告警
# ──────────────────────────────────────────────────────────────────────────────

async def run_evaluate():
    await _safe_run(evaluate_active_strategies(), label="evaluate_active_strategies")


async def run_alert():
    await _safe_run(check_alerts_for_strategies(), label="check_alerts_for_strategies")


# ──────────────────────────────────────────────────────────────────────────────
# 安全包装：任务异常不影响调度器
# ──────────────────────────────────────────────────────────────────────────────

async def _safe_run(coro, label: str = ""):
    try:
        await coro
    except Exception as e:
        logger.error(f"[Scheduler] 任务 [{label}] 异常: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# 启动调度器
# ──────────────────────────────────────────────────────────────────────────────

def start_scheduler():
    interval = settings.poll_interval

    scheduler.add_job(
        poll_pending_commands,
        trigger=IntervalTrigger(seconds=interval),
        id="poll_pending",
        replace_existing=True,
    )
    scheduler.add_job(
        poll_waiting_reply_commands,
        trigger=IntervalTrigger(seconds=interval),
        id="poll_waiting_reply",
        replace_existing=True,
    )
    scheduler.add_job(
        run_evaluate,
        trigger=IntervalTrigger(minutes=5),
        id="evaluate_strategies",
        replace_existing=True,
    )
    scheduler.add_job(
        run_alert,
        trigger=IntervalTrigger(minutes=10),
        id="check_alerts",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"[Scheduler] 启动完成: 轮询间隔={interval}s, "
        f"评估间隔=5min, 告警间隔=10min"
    )
