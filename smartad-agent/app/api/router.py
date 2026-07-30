"""
FastAPI 路由模块
- GET  /ai/health              健康检查
- GET  /ai/metrics             运行指标（JSON 格式）
- GET  /ai/prometheus          Prometheus 指标导出
- POST /ai/trigger/evaluate    手动触发策略评估
- POST /ai/trigger/alert       手动触发告警检测
- GET  /ai/ping/server         测试与 Java 后端连通性
- POST /ai/stream/command      SSE 流式指令处理（Agent 模式）
- GET  /ai/agent/status        Agent 状态查询
"""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response
from loguru import logger

from app.service.evaluate_service import evaluate_active_strategies, check_alerts_for_strategies
from app.util.http_client import get
from app.monitoring import metrics, get_prometheus_metrics

router = APIRouter(prefix="/ai")


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "SmartAD AI Agent",
        "version": "3.0.0",
        "rag_enabled": True,
        "agent_enabled": True,
    }


@router.get("/metrics")
async def get_metrics():
    """返回运行指标（JSON 格式）"""
    return {"status": "ok", "metrics": metrics.to_dict()}


@router.get("/prometheus")
async def prometheus_metrics():
    """Prometheus 指标导出端点"""
    return Response(
        content=get_prometheus_metrics(),
        media_type="text/plain; charset=utf-8",
    )


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


@router.post("/stream/command")
async def stream_command(command_text: str):
    """
    SSE 流式指令处理
    实时推送 Agent 执行过程中的每个步骤
    """
    return StreamingResponse(
        _stream_agent_execution(command_text),
        media_type="text/event-stream",
    )


async def _stream_agent_execution(command_text: str):
    """流式推送 Agent 执行事件"""
    try:
        from agent.smartad_agent import get_agent
        agent = get_agent()

        yield _sse_event("status", {"phase": "init", "message": "Agent 初始化中..."})

        if not agent._initialized:
            agent.initialize()

        yield _sse_event("status", {"phase": "thinking", "message": "Agent 开始分析指令..."})

        result = await agent.ainvoke(command_text=command_text)

        # 推送最终结果
        yield _sse_event("result", result)

        strategies = result.get("strategies", [])
        if strategies:
            yield _sse_event(
                "complete",
                {
                    "message": f"成功生成 {len(strategies)} 条策略",
                    "hasQuestion": False,
                },
            )
        elif result.get("hasQuestion"):
            yield _sse_event(
                "complete",
                {
                    "message": "Agent 需要更多信息",
                    "hasQuestion": True,
                    "question": result.get("question", ""),
                },
            )
        else:
            yield _sse_event("complete", {"message": "Agent 未能生成策略", "hasQuestion": False})

    except Exception as e:
        logger.error(f"SSE 流式执行异常: {e}")
        yield _sse_event(
            "error",
            {"message": f"执行异常: {str(e)[:100]}"},
        )


def _sse_event(event_type: str, data: dict) -> str:
    """构建 SSE 事件"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/agent/status")
async def agent_status():
    """查询 Agent 状态"""
    try:
        from agent.smartad_agent import get_agent
        agent = get_agent()
        return {
            "status": "ok",
            "initialized": agent._initialized,
            "tools": agent.get_tools_info(),
            "max_iterations": 5,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
