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
    smartad_server_url: str = Field(default="http://localhost:8080", alias="SMARTAD_SERVER_URL")
    ai_token: str = Field(default="smartad-ai-internal-token-2024", alias="AI_TOKEN")

    # ===== 调度 =====
    poll_interval: int = Field(default=5, alias="POLL_INTERVAL")

    # ===== 服务端口 =====
    port: int = Field(default=8001, alias="PORT")

    # ===== 日志级别 =====
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ===== 缓存 TTL（秒）=====
    cache_ttl_crowd: int = Field(default=300, alias="CACHE_TTL_CROWD")       # 人群画像缓存 5 分钟
    cache_ttl_history: int = Field(default=600, alias="CACHE_TTL_HISTORY")   # 历史数据缓存 10 分钟
    cache_ttl_report: int = Field(default=180, alias="CACHE_TTL_REPORT")     # 报表缓存 3 分钟

    # ===== 护栏阈值 =====
    guardrail_max_budget: int = Field(default=100000, alias="GUARDRAIL_MAX_BUDGET")   # 单条策略最大日预算（元）
    guardrail_min_budget: int = Field(default=100, alias="GUARDRAIL_MIN_BUDGET")
    guardrail_max_bid: int = Field(default=10000, alias="GUARDRAIL_MAX_BID")          # 最大出价（分）
    guardrail_min_bid: int = Field(default=10, alias="GUARDRAIL_MIN_BID")
    guardrail_high_risk_budget: int = Field(default=5000, alias="GUARDRAIL_HIGH_RISK_BUDGET")
    guardrail_high_risk_bid: int = Field(default=5000, alias="GUARDRAIL_HIGH_RISK_BID")  # 50元=5000分

    # ===== 反思最大迭代次数 =====
    reflect_max_iterations: int = Field(default=2, alias="REFLECT_MAX_ITERATIONS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


settings = Settings()
