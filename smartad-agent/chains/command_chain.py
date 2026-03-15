"""
指令解析链（Command Parse Chain）
核心 LCEL 管道：
  Prompt → 标准LLM → JSON解析器 → [可选] 反思链

包含：
1. 基础解析链（parse_chain）：处理常规指令
2. 追问回答链（reply_chain）：处理追问后的重新解析
3. 反思链（reflect_chain）：对草案进行自我审查（旗舰模型）
"""
import json
from langchain_core.runnables import RunnableSequence, RunnableLambda
from loguru import logger

from ai_config.llm_client import get_llm_standard, get_llm_heavy
from ai_config.settings import settings
from rag.prompt_builder import (
    CMD_PARSE_PROMPT, CMD_REPLY_PROMPT, REFLECT_PROMPT,
    build_command_parse_vars, build_command_reply_vars,
)
from chains.parsers import JsonOutputParser


# ──────────────────────────────────────────────────────────────────────────────
# 基础解析链
# ──────────────────────────────────────────────────────────────────────────────

def build_parse_chain() -> RunnableSequence:
    """
    指令解析链：CMD_PARSE_PROMPT | 标准LLM | JSON解析器
    输入变量: command_text, crowd_desc, history_desc
    """
    return CMD_PARSE_PROMPT | get_llm_standard() | JsonOutputParser()


# ──────────────────────────────────────────────────────────────────────────────
# 追问回答链
# ──────────────────────────────────────────────────────────────────────────────

def build_reply_chain() -> RunnableSequence:
    """
    追问回答链：CMD_REPLY_PROMPT | 标准LLM | JSON解析器
    输入变量: command_text, question, answer, crowd_desc, history_desc
    """
    return CMD_REPLY_PROMPT | get_llm_standard() | JsonOutputParser()


# ──────────────────────────────────────────────────────────────────────────────
# 反思链：对策略草案进行合规审查
# ──────────────────────────────────────────────────────────────────────────────

def build_reflect_chain() -> RunnableSequence:
    """
    反思链：REFLECT_PROMPT | 旗舰LLM | JSON解析器
    输入变量: command_text, draft_json
    对生成的策略草案进行自我审查与修正
    """
    return REFLECT_PROMPT | get_llm_heavy() | JsonOutputParser()


# ──────────────────────────────────────────────────────────────────────────────
# 带反思的完整解析管道
# ──────────────────────────────────────────────────────────────────────────────

async def run_parse_with_reflection(
    command_text: str,
    crowd_list: list[dict],
    history_data: list[dict],
    use_reply: bool = False,
    question: str = "",
    answer: str = "",
) -> dict:
    """
    完整解析流程（含反思迭代）：
    1. 调用解析链生成策略草案
    2. 若草案不为空，调用反思链审查
    3. 最多重试 settings.reflect_max_iterations 次

    返回最终 result dict，格式同原 parse_chain 输出
    """
    parse_chain = build_parse_chain()
    reply_chain = build_reply_chain()
    reflect_chain = build_reflect_chain()

    # Step 1: 生成初始草案
    if use_reply:
        vars_ = build_command_reply_vars(command_text, question, answer, crowd_list, history_data)
        result = await reply_chain.ainvoke(vars_)
    else:
        vars_ = build_command_parse_vars(command_text, crowd_list, history_data)
        result = await parse_chain.ainvoke(vars_)

    logger.debug(f"[ParseChain] 初始草案: {result}")

    # 若需要追问，无需反思
    if result.get("hasQuestion"):
        return result

    strategies = result.get("strategies", [])
    if not strategies:
        return result

    # Step 2: 反思迭代
    for i in range(settings.reflect_max_iterations):
        try:
            reflected = await reflect_chain.ainvoke({
                "command_text": command_text,
                "draft_json": json.dumps(result, ensure_ascii=False),
            })
            if reflected and reflected.get("strategies"):
                logger.debug(f"[ReflectChain] 第{i+1}次反思完成")
                result = reflected
                break
        except Exception as e:
            logger.warning(f"[ReflectChain] 第{i+1}次反思失败，使用原始草案: {e}")
            break

    return result
