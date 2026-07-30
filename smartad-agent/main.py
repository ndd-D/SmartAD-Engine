"""
SmartAD AI Agent 主入口（LangChain + RAG + Agent 重构版）
分层架构说明：
  核心层：LangChain LCEL 链 + ReAct Agent（路由/解析/评估/反思）
  RAG层：Chroma 向量库 + 语义检索 + 动态知识注入
  扩展层：RESTful 接口对接 Java 后端 + Redis Stream 事件驱动
  保障层：护栏(guardrails) + 缓存(cache) + 监控(monitoring) + 异常处理
  优化层：分级模型（轻量/标准/旗舰） + 并行评估 + 缓存复用 + Prometheus
"""
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from ai_config.settings import settings
from app.api.router import router
from app.service.scheduler import start_scheduler

# ── 日志配置 ────────────────────────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
)
logger.add(
    "logs/smartad-agent.log",
    rotation="10 MB",
    retention="7 days",
    level=settings.log_level,
)

# ── FastAPI 应用 ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="SmartAD AI Agent",
    description=(
        "智能广告投放 AI 服务 - 基于 LangChain LCEL + RAG + Agent 架构\n\n"
        "核心能力：\n"
        "- RAG 增强的指令解析 → 结构化投放策略草案（含路由/解析/反思链）\n"
        "- ReAct Agent 自主决策 → 工具调用（查人群/查报表/调参数）\n"
        "- 策略效果并行评估 + 自动调参建议\n"
        "- 风险告警并行检测\n"
        "- 输入/输出护栏 + 参数合规校验\n"
        "- 多级缓存（人群/历史/报表）降低后端压力\n"
        "- Prometheus 监控 + 可观测性"
    ),
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
async def on_startup():
    logger.info("SmartAD AI Agent 启动中...")
    logger.info(
        f"配置摘要: model={settings.deepseek_model}, "
        f"model_light={settings.deepseek_model_light}, "
        f"model_heavy={settings.deepseek_model_heavy}, "
        f"poll={settings.poll_interval}s, port={settings.port}, "
        f"rag_enabled={settings.rag_enabled}, "
        f"agent_enabled={settings.agent_enabled}, "
        f"event_driven={settings.event_driven_enabled}"
    )

    # ── 初始化 RAG 向量库 ────────────────────────────────────────────────
    if settings.rag_enabled:
        try:
            from rag.retriever import get_retriever
            retriever = get_retriever()
            success = retriever.initialize()
            if success:
                logger.info("[RAG] 向量库初始化成功，知识检索已启用")
            else:
                logger.warning("[RAG] 向量库初始化失败，降级为关键词匹配模式")
        except Exception as e:
            logger.warning(f"[RAG] 向量库初始化异常: {e}")

    # ── 启动调度器 ──────────────────────────────────────────────────────
    start_scheduler()
    logger.info(f"SmartAD AI Agent 启动完成，监听端口: {settings.port}")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("SmartAD AI Agent 正在关闭...")
    from app.service.scheduler import scheduler
    if scheduler.running:
        scheduler.shutdown()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=False)
