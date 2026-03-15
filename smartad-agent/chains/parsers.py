"""
解析输出解析器：LLM 输出 → Python dict
支持自动提取 JSON 代码块，带详细错误日志
"""
import json
import re
from langchain_core.output_parsers import BaseOutputParser
from loguru import logger


class JsonOutputParser(BaseOutputParser[dict]):
    """
    通用 JSON 解析器
    - 优先直接解析
    - 失败则用正则提取 {...} 或 ```json ... ``` 块
    - 仍失败则返回空 dict，不抛异常（由调用方护栏处理）
    """

    def parse(self, text: str) -> dict:
        text = text.strip()
        # 1. 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. 提取 ```json ... ``` 块
        md_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if md_match:
            try:
                return json.loads(md_match.group(1))
            except json.JSONDecodeError:
                pass

        # 3. 提取最外层 {...} 块
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group())
            except json.JSONDecodeError:
                pass

        logger.warning(f"[JsonOutputParser] 无法解析 LLM 输出为 JSON: {text[:200]}")
        return {}

    @property
    def _type(self) -> str:
        return "json_output_parser"
