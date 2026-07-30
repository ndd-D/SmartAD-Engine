"""
Redis Stream 事件驱动模块
- 生产者：Java 后端投递指令到 Redis Stream
- 消费者：Agent 监听 Stream，实时处理指令
- 支持消费者组：多实例部署不重复消费
- 支持降级：Redis 不可用时自动回退到轮询模式

事件类型：
- command:new       → 新指令待 AI 处理
- command:reply     → 用户追问回答
- strategy:evaluate → 定时评估策略
- alert:check       → 定时告警检测
"""
from __future__ import annotations

import json
import asyncio
from typing import Callable, Optional
from loguru import logger

from ai_config.settings import settings

# Redis 可选依赖
try:
    import redis.asyncio as redis_async
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("[EventBus] redis 未安装，事件驱动不可用")


class EventBus:
    """Redis Stream 事件总线"""

    def __init__(self):
        self._redis = None
        self._connected = False
        self._consumers: list[asyncio.Task] = []
        self._handlers: dict[str, Callable] = {}

    async def connect(self) -> bool:
        """连接 Redis"""
        if not REDIS_AVAILABLE:
            return False

        try:
            self._redis = redis_async.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            self._connected = True
            logger.info(f"[EventBus] Redis 连接成功: {settings.redis_url}")
            return True
        except Exception as e:
            logger.warning(f"[EventBus] Redis 连接失败: {e}")
            self._connected = False
            return False

    async def close(self) -> None:
        """关闭 Redis 连接"""
        self._connected = False
        for task in self._consumers:
            task.cancel()
        self._consumers.clear()
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass
        logger.info("[EventBus] Redis 已断开")

    def register_handler(self, event_type: str, handler: Callable) -> None:
        """注册事件处理器"""
        self._handlers[event_type] = handler
        logger.info(f"[EventBus] 注册处理器: {event_type}")

    async def publish(self, stream: str, data: dict) -> str | None:
        """发布事件到 Stream"""
        if not self._connected:
            return None

        try:
            message = json.dumps(data, ensure_ascii=False)
            msg_id = await self._redis.xadd(
                stream,
                {"data": message},
                maxlen=10000,
                approximate=True,
            )
            logger.debug(f"[EventBus] 发布事件: stream={stream}, id={msg_id}")
            return msg_id
        except Exception as e:
            logger.error(f"[EventBus] 发布事件失败: {e}")
            return None

    async def consume(
        self,
        stream: str,
        handler: Callable,
        consumer_name: str = "agent",
        block_ms: int = 5000,
    ) -> None:
        """
        消费 Stream 事件（异步循环）
        使用消费者组确保多实例不重复消费
        """
        if not self._connected:
            return

        # 确保消费者组存在
        try:
            await self._redis.xgroup_create(stream, settings.redis_consumer_group, mkstream=True)
        except Exception:
            pass  # 组已存在

        logger.info(f"[EventBus] 开始消费: stream={stream}, consumer={consumer_name}")

        while self._connected:
            try:
                # 读取新消息
                results = await self._redis.xreadgroup(
                    settings.redis_consumer_group,
                    consumer_name,
                    {stream: ">"},
                    count=1,
                    block=block_ms,
                )

                if results:
                    for stream_name, messages in results:
                        for msg_id, msg_data in messages:
                            try:
                                data = json.loads(msg_data.get("data", "{}"))
                                await handler(data, msg_id)
                                await self._redis.xack(
                                    stream, settings.redis_consumer_group, msg_id
                                )
                            except Exception as e:
                                logger.error(f"[EventBus] 处理消息 {msg_id} 失败: {e}")
                                # 不 ack，消息会重投
                                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[EventBus] 消费异常: {e}")
                await asyncio.sleep(2)

    def start_consumer(
        self,
        stream: str,
        handler: Callable,
        consumer_name: str = "agent",
    ) -> asyncio.Task:
        """启动消费者协程"""
        task = asyncio.create_task(
            self.consume(stream=stream, handler=handler, consumer_name=consumer_name)
        )
        self._consumers.append(task)
        return task

    @property
    def is_connected(self) -> bool:
        return self._connected


# ──────────────────────────────────────────────────────────────────────────────
# 全局单例
# ──────────────────────────────────────────────────────────────────────────────

event_bus = EventBus()


async def init_event_bus() -> bool:
    """初始化事件总线"""
    if not settings.event_driven_enabled:
        logger.info("[EventBus] 事件驱动未启用 (EVENT_DRIVEN_ENABLED=false)")
        return False

    return await event_bus.connect()
