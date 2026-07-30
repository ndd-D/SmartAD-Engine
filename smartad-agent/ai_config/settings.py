from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ===== DeepSeek LLM =====
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com/v1", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")

    # 旗舰模型（用于高精度复杂任务：规划/反思）
    deepseek_model_heavy: str = Field(default="deepseek-reasoner", alias="DEEPSEEK_MODEL_HEAVY")
    # 轻量模型（用于简单分类/路由判断）
    deepseek_model_light: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL_LIGHT")

    # ===== Java 后端 =====
    smartad_server_url: str = Field(default="http://localhost:8090", alias="SMARTAD_SERVER_URL")
    ai_token: str = Field(default="smartad-ai-internal-token-2024", alias="AI_TOKEN")

    # ===== 调度 =====
    poll_interval: int = Field(default=5, alias="POLL_INTERVAL")

    # ===== 服务端口 =====
    port: int = Field(default=8001, alias="PORT")

    # ===== 日志级别 =====
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ===== 缓存 TTL（秒）=====
    cache_ttl_crowd: int = Field(default=300, alias="CACHE_TTL_CROWD")
    cache_ttl_history: int = Field(default=600, alias="CACHE_TTL_HISTORY")
    cache_ttl_report: int = Field(default=180, alias="CACHE_TTL_REPORT")

    # ===== 护栏阈值 =====
    guardrail_max_budget: int = Field(default=100000, alias="GUARDRAIL_MAX_BUDGET")
    guardrail_min_budget: int = Field(default=100, alias="GUARDRAIL_MIN_BUDGET")
    guardrail_max_bid: int = Field(default=10000, alias="GUARDRAIL_MAX_BID")
    guardrail_min_bid: int = Field(default=10, alias="GUARDRAIL_MIN_BID")
    guardrail_high_risk_budget: int = Field(default=5000, alias="GUARDRAIL_HIGH_RISK_BUDGET")
    guardrail_high_risk_bid: int = Field(default=5000, alias="GUARDRAIL_HIGH_RISK_BID")

    # ===== 反思最大迭代次数 =====
    reflect_max_iterations: int = Field(default=2, alias="REFLECT_MAX_ITERATIONS")

    # ===== RAG 配置 =====
    embedding_model: str = Field(default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    chroma_collection: str = Field(default="smartad_knowledge", alias="CHROMA_COLLECTION")
    rag_enabled: bool = Field(default=True, alias="RAG_ENABLED")

    # ===== Agent 配置 =====
    agent_enabled: bool = Field(default=True, alias="AGENT_ENABLED")
    agent_max_iterations: int = Field(default=5, alias="AGENT_MAX_ITERATIONS")

    # ===== Redis Stream 配置（事件驱动）=====
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_stream_commands: str = Field(default="smartad_commands", alias="REDIS_STREAM_COMMANDS")
    redis_stream_evaluate: str = Field(default="smartad_evaluate", alias="REDIS_STREAM_EVALUATE")
    redis_consumer_group: str = Field(default="smartad_agent", alias="REDIS_CONSUMER_GROUP")
    event_driven_enabled: bool = Field(default=False, alias="EVENT_DRIVEN_ENABLED")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


settings = Settings()
