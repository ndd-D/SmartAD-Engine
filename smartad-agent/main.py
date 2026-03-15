"""
SmartAD AI Agent 主入口（LangChain 重构版）
分层架构说明：
  核心层：LangChain LCEL 链（路由/解析/评估/反思）
  扩展层：RESTful 接口对接 Java 后端
  保障层：护栏(guardrails) + 缓存(cache) + 监控(monitoring) + 异常处理
  优化层：分级模型（轻量/标准/旗舰） + 并行评估 + 缓存复用
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
        "智能广告投放 AI 服务 - 基于 LangChain LCEL 分层架构\n\n"
        "核心能力：\n"
        "- 自然语言指令解析 → 结构化投放策略草案（含路由/解析/反思链）\n"
        "- 策略效果并行评估 + 自动调参建议\n"
        "- 风险告警并行检测\n"
        "- 输入/输出护栏 + 参数合规校验\n"
        "- 多级缓存（人群/历史/报表）降低后端压力"
    ),
    version="2.0.0",
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
        f"poll={settings.poll_interval}s, port={settings.port}"
    )
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
