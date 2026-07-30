"""
SmartAD ReAct Agent
基于 LangChain 的 ReAct（Reasoning + Acting）模式
- Agent 自主决定调用哪些工具、以什么顺序调用
- 支持多步推理：先查人群 → 再查历史 → 再计算出价 → 最后校验合规
- 支持追问：信息不足时主动向用户提问
- 与现有 Fixed Chain 无缝切换（agent_enabled 配置）
"""
from __future__ import annotations

import json
from typing import Any
from loguru import logger

from ai_config.llm_client import get_llm_standard, get_llm_heavy
from ai_config.settings import settings


AGENT_SYSTEM_PROMPT = """\
你是 SmartAD Engine，一个专业的智能广告投放 AI 助手。

## 你的能力
你可以使用以下工具来帮助用户制定广告投放策略：
1. get_crowd_info - 查询人群画像（特征、转化率、出价策略）
2. get_history_report - 查询历史投放效果（CTR、ROI、建议出价）
3. get_realtime_report - 查询策略实时报表（用于效果评估）
4. search_knowledge - 检索广告投放知识库（规则、最佳实践）
5. calculate_bid - 根据历史数据计算建议出价和预算
6. validate_strategy - 校验策略合规性（必须调用）

## 你的工作流程
1. 分析用户指令，理解投放目标
2. 自主决定调用哪些工具获取必要信息
3. 综合工具返回的数据，制定投放策略
4. 调用 validate_strategy 校验合规性
5. 输出最终策略方案或向用户提问

## 输出格式
当信息充足时，输出 JSON 格式的策略：
{{{{
  "strategies": [
    {{{{
      "crowdTag": "young_fashion",
      "channel": "douyin",
      "budgetDay": 500,
      "bidPrice": 120,
      "reason": "策略制定理由"
    }}}}
  ],
  "hasQuestion": false,
  "question": ""
}}}}

当信息不足需要追问时：
{{{{
  "strategies": [],
  "hasQuestion": true,
  "question": "你想在哪个渠道投放？日预算是多少？"
}}}}

注意：在输出最终策略前，必须调用 validate_strategy 进行合规校验。"""


def _build_react_agent(llm, tools: list):
    """构建 ReAct Agent"""
    try:
        from langchain.agents import create_react_agent, AgentExecutor
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        prompt = ChatPromptTemplate.from_messages([
            ("system", AGENT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            max_iterations=settings.agent_max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )
        return executor
    except ImportError as e:
        logger.error(f"[Agent] LangChain Agent 导入失败: {e}")
        return None


class SmartADAgent:
    """SmartAD ReAct Agent 封装"""

    def __init__(self):
        self._executor = None
        self._tools = None
        self._initialized = False

    def initialize(self) -> bool:
        """初始化 Agent（延迟到首次使用）"""
        if self._initialized:
            return True

        try:
            from agent.tools import get_all_tools
            self._tools = get_all_tools()
            if not self._tools:
                logger.warning("[Agent] 工具列表为空")
                return False

            llm = get_llm_standard()
            self._executor = _build_react_agent(llm, self._tools)
            if self._executor:
                self._initialized = True
                logger.info(f"[Agent] 初始化完成: {len(self._tools)} 个工具, max_iter={settings.agent_max_iterations}")
                return True
            else:
                logger.warning("[Agent] 执行器创建失败")
                return False
        except Exception as e:
            logger.error(f"[Agent] 初始化异常: {e}")
            return False

    async def ainvoke(
        self,
        command_text: str,
        chat_history: list[tuple[str, str]] | None = None,
    ) -> dict[str, Any]:
        """
        异步执行 Agent 推理
        :param command_text: 用户投放指令
        :param chat_history: 对话历史 [(role, content), ...]
        :return: {"strategies": [...], "hasQuestion": bool, "question": str}
        """
        if not self._initialized:
            success = self.initialize()
            if not success:
                return {
                    "strategies": [],
                    "hasQuestion": True,
                    "question": "Agent 初始化失败，请稍后重试",
                }

        try:
            input_data = {"input": command_text}
            if chat_history:
                input_data["chat_history"] = chat_history
            else:
                input_data["chat_history"] = []

            result = await self._executor.ainvoke(input_data)

            output_text = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])

            logger.info(
                f"[Agent] 执行完成: input='{command_text[:30]}', "
                f"steps={len(intermediate_steps)}, output='{output_text[:100]}'"
            )

            parsed = self._parse_output(output_text)
            parsed["_agent_steps"] = len(intermediate_steps)
            return parsed

        except Exception as e:
            logger.error(f"[Agent] 执行异常: {e}")
            return {
                "strategies": [],
                "hasQuestion": True,
                "question": f"Agent 执行出错: {str(e)[:100]}，请尝试更明确的指令",
            }

    def _parse_output(self, output_text: str) -> dict[str, Any]:
        """解析 Agent 输出为结构化结果"""
        try:
            parsed = json.loads(output_text)
            if "strategies" in parsed or "hasQuestion" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass

        import re
        json_match = re.search(r"\{.*\}", output_text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                if "strategies" in parsed or "hasQuestion" in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass

        return {
            "strategies": [],
            "hasQuestion": True,
            "question": f"AI 生成了非标准回复：{output_text[:100]}",
        }

    def get_tools_info(self) -> list[dict]:
        """获取所有可用工具的描述"""
        if not self._tools:
            return []
        return [
            {"name": t.name, "description": t.description[:100]}
            for t in self._tools
        ]


# ──────────────────────────────────────────────────────────────────────────────
# 全局单例
# ──────────────────────────────────────────────────────────────────────────────

_agent_instance = SmartADAgent()


def get_agent() -> SmartADAgent:
    """获取 SmartAD Agent 单例"""
    return _agent_instance
