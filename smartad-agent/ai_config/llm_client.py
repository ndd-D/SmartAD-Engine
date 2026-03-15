"""
LLM 客户端工厂：基于 LangChain ChatOpenAI，支持分级模型（轻量/标准/旗舰）
- 轻量模型：路由判断、简单分类（低延迟、低成本）
- 标准模型：指令解析、策略生成（常规任务）
- 旗舰模型：反思、复杂规划（高精度任务）
"""
from functools import lru_cache
from langchain_openai import ChatOpenAI
from ai_config.settings import settings


@lru_cache(maxsize=1)
def get_llm_light() -> ChatOpenAI:
    """
    轻量 LLM：用于路由判断、意图分类等低复杂度任务
    低温度保证输出稳定，max_tokens 限制控制成本
    """
    return ChatOpenAI(
        model=settings.deepseek_model_light,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.1,
        max_tokens=256,
    )


@lru_cache(maxsize=1)
def get_llm_standard() -> ChatOpenAI:
    """
    标准 LLM：用于指令解析、策略生成等常规任务
    """
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.3,
        max_tokens=2048,
    )


@lru_cache(maxsize=1)
def get_llm_heavy() -> ChatOpenAI:
    """
    旗舰 LLM：用于复杂反思、规划任务
    高 max_tokens 保障推理质量
    """
    return ChatOpenAI(
        model=settings.deepseek_model_heavy,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.2,
        max_tokens=4096,
    )
