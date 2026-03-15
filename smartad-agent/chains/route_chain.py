"""
路由链（Router Chain）：轻量模型判断指令复杂度
- simple  → 直接走标准解析链
- complex → 走追问 + 反思链
- invalid → 直接拒绝，不消耗重型 LLM
"""
from langchain_core.runnables import RunnableSequence
from ai_config.llm_client import get_llm_light
from rag.prompt_builder import ROUTE_PROMPT
from chains.parsers import JsonOutputParser


def build_route_chain() -> RunnableSequence:
    """
    构建路由链：ROUTE_PROMPT | 轻量LLM | JSON解析器
    返回: {"complexity": "simple"|"complex"|"invalid", "reason": str}
    """
    return ROUTE_PROMPT | get_llm_light() | JsonOutputParser()
