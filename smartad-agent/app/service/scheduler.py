"""
SmartAD 调度器（Polling + Event-Driven 双模式）
- 轮询模式（默认）：APScheduler 定时轮询 Java 后端
- 事件驱动模式：Redis Stream 实时消费

根据 EVENT_DRIVEN_ENABLED 配置自动选择模式
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
_event_consumers_started = False


# ──────────────────────────────────────────────────────────────────────────────
# 事件驱动模式：消息处理器
# ──────────────────────────────────────────────────────────────────────────────

async def _handle_new_command(data: dict, msg_id: str) -> None:
    """处理新指令事件"""
    command_id = data.get("commandId", "")
    command_text = data.get("commandText", "")
    if command_id and command_text:
        logger.info(f"[Event] 处理新指令: commandId={command_id}")
        asyncio.create_task(
            _safe_run(
                parse_command(command_id, command_text),
                label=f"parse_command:{command_id}",
            )
        )


async def _handle_command_reply(data: dict, msg_id: str) -> None:
    """处理追问回答事件"""
    command_id = data.get("commandId", "")
    command_text = data.get("commandText", "")
    question = data.get("aiQuestion", "")
    answer = data.get("userReply", "")
    if command_id and command_text:
        logger.info(f"[Event] 处理追问回答: commandId={command_id}")
        asyncio.create_task(
            _safe_run(
                parse_command_with_reply(command_id, command_text, question, answer),
                label=f"parse_reply:{command_id}",
            )
        )


async def _handle_evaluate_event(data: dict, msg_id: str) -> None:
    """处理策略评估事件"""
    logger.info("[Event] 触发策略评估")
    asyncio.create_task(
        _safe_run(evaluate_active_strategies(), label="evaluate_active_strategies")
    )


async def _handle_alert_event(data: dict, msg_id: str) -> None:
    """处理告警检测事件"""
    logger.info("[Event] 触发告警检测")
    asyncio.create_task(
        _safe_run(check_alerts_for_strategies(), label="check_alerts")
    )


# ──────────────────────────────────────────────────────────────────────────────
# 轮询模式：定时任务
# ──────────────────────────────────────────────────────────────────────────────

async def poll_pending_commands():
    """轮询 Java 后端「待AI处理」的指令"""
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


async def poll_waiting_reply_commands():
    """轮询 Java 后端「处理中」的追问回答指令"""
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


async def run_evaluate():
    await _safe_run(evaluate_active_strategies(), label="evaluate_active_strategies")


async def run_alert():
    await _safe_run(check_alerts_for_strategies(), label="check_alerts")


# ──────────────────────────────────────────────────────────────────────────────
# 安全包装
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
    """启动调度器（根据配置选择模式）"""

    # ── 事件驱动模式 ──────────────────────────────────────────────────────
    if settings.event_driven_enabled:
        try:
            from event.redis_stream import event_bus, init_event_bus

            loop = asyncio.get_event_loop()
            loop.create_task(_start_event_consumers())
            logger.info("[Scheduler] 事件驱动模式已启用，等待 Redis 连接...")
        except Exception as e:
            logger.warning(f"[Scheduler] 事件驱动启动失败: {e}，降级为轮询模式")
            _start_polling_mode()
        return

    # ── 轮询模式（默认）────────────────────────────────────────────────────
    _start_polling_mode()


def _start_polling_mode():
    """启动轮询模式"""
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
        f"[Scheduler] 轮询模式启动: 轮询间隔={interval}s, "
        f"评估间隔=5min, 告警间隔=10min"
    )


async def _start_event_consumers():
    """启动事件驱动消费者"""
    global _event_consumers_started

    success = await init_event_bus()
    if not success:
        logger.warning("[Scheduler] 事件驱动初始化失败，降级为轮询模式")
        _start_polling_mode()
        return

    from event.redis_stream import event_bus

    # 注册并启动消费者
    event_bus.register_handler("command:new", _handle_new_command)
    event_bus.register_handler("command:reply", _handle_command_reply)
    event_bus.register_handler("strategy:evaluate", _handle_evaluate_event)
    event_bus.register_handler("alert:check", _handle_alert_event)

    event_bus.start_consumer(
        settings.redis_stream_commands,
        _handle_new_command,
        consumer_name="agent_cmd",
    )
    event_bus.start_consumer(
        settings.redis_stream_commands,
        _handle_command_reply,
        consumer_name="agent_reply",
    )
    event_bus.start_consumer(
        settings.redis_stream_evaluate,
        _handle_evaluate_event,
        consumer_name="agent_eval",
    )

    # 事件驱动模式下仍保留定时评估和告警（可通过事件触发）
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

    _event_consumers_started = True
    logger.info(
        f"[Scheduler] 事件驱动模式启动: "
        f"streams=[{settings.redis_stream_commands}, {settings.redis_stream_evaluate}]"
    )
