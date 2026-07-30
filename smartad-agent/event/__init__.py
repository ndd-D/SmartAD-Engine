"""
SmartAD 事件驱动模块
- redis_stream: Redis Stream 事件总线
- handlers: 事件处理器（桥接事件到业务服务）
"""
from event.redis_stream import EventBus, event_bus, init_event_bus

__all__ = ["EventBus", "event_bus", "init_event_bus"]
