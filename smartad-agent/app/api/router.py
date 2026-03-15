"""
FastAPI 路由模块
- GET  /ai/health           健康检查
- GET  /ai/metrics          运行指标（LLM调用/解析成功率/缓存命中等）
- POST /ai/trigger/evaluate 手动触发策略评估（调试用）
- POST /ai/trigger/alert    手动触发告警检测（调试用）
- GET  /ai/ping/server      测试与 Java 后端连通性
"""
from fastapi import APIRouter
from loguru import logger

from app.service.evaluate_service import evaluate_active_strategies, check_alerts_for_strategies
from app.util.http_client import get
from app.monitoring import metrics

router = APIRouter(prefix="/ai")


@router.get("/health")
async def health():
    return {"status": "ok", "service": "SmartAD AI Agent"}


@router.get("/metrics")
async def get_metrics():
    """返回运行指标，供运维监控"""
    return {"status": "ok", "metrics": metrics.to_dict()}


@router.post("/trigger/evaluate")
async def trigger_evaluate():
    """手动触发策略评估（调试接口）"""
    logger.info("手动触发策略评估")
    await evaluate_active_strategies()
    return {"status": "ok", "message": "评估任务已触发"}


@router.post("/trigger/alert")
async def trigger_alert():
    """手动触发告警检测（调试接口）"""
    logger.info("手动触发告警检测")
    await check_alerts_for_strategies()
    return {"status": "ok", "message": "告警检测已触发"}


@router.get("/ping/server")
async def ping_server():
    """测试与 Java 后端的连通性"""
    try:
        resp = await get("/api/ai/health")
        return {"status": "ok", "server_response": resp}
    except Exception as e:
        return {"status": "error", "message": str(e)}
