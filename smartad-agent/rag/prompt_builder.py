"""
Prompt 构建模块（LangChain LCEL 版）
使用 ChatPromptTemplate 替换裸字符串拼接，支持变量注入和复用
"""
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from rag.knowledge import CROWD_KNOWLEDGE, CHANNEL_KNOWLEDGE, STRATEGY_RULES


# ──────────────────────────────────────────────────────────────────────────────
# 工具函数：将列表数据格式化为文本
# ──────────────────────────────────────────────────────────────────────────────

def _format_crowd_list(crowd_list: list[dict]) -> str:
    if not crowd_list:
        return "暂无人群画像数据"
    return "\n".join(
        f"- id={c.get('id')}, tag={c.get('crowdTag')}, desc={c.get('description', '')}"
        for c in crowd_list
    )


def _format_history(history_data: list[dict]) -> str:
    if not history_data:
        return "暂无历史数据"
    return "\n".join(
        f"- avgClickRate={h.get('avgClickRate', 'N/A')}, "
        f"avgConvertRate={h.get('avgConvertRate', 'N/A')}, "
        f"avgRoi={h.get('avgRoi', 'N/A')}, "
        f"suggestBid={h.get('suggestBid', 'N/A')}"
        for h in history_data
    )


def _format_report(report_data: list[dict], fields: list[str] | None = None) -> str:
    if not report_data:
        return "暂无报表数据"
    lines = []
    for r in report_data:
        if fields:
            parts = [f"{f}={r.get(f, 'N/A')}" for f in fields]
        else:
            parts = [
                f"日期={r.get('reportDate')}", f"曝光={r.get('impressions', 0)}",
                f"点击={r.get('clicks', 0)}", f"消耗={r.get('cost', 0)}",
                f"转化={r.get('conversions', 0)}", f"CTR={r.get('ctr', 'N/A')}",
                f"ROI={r.get('roi', 'N/A')}",
            ]
        lines.append("- " + ", ".join(parts))
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# 路由 Prompt：判断指令复杂度（轻量模型使用）
# ──────────────────────────────────────────────────────────────────────────────

_ROUTE_SYSTEM = """\
你是一个广告投放指令分类器。
判断用户输入的广告投放指令属于哪种复杂度：
- simple：指令明确，包含人群/渠道/预算等关键信息，可直接生成策略
- complex：指令模糊或包含复杂条件，需要追问或多步骤规划
- invalid：非广告投放相关的无效请求

只输出以下 JSON，不要输出任何其他内容：
{{"complexity": "simple"|"complex"|"invalid", "reason": "简要原因"}}"""

_ROUTE_HUMAN = "用户指令：{command_text}"

ROUTE_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(_ROUTE_SYSTEM),
    HumanMessagePromptTemplate.from_template(_ROUTE_HUMAN),
])


# ──────────────────────────────────────────────────────────────────────────────
# 指令解析 Prompt：自然语言 → 策略草案（标准模型使用）
# ──────────────────────────────────────────────────────────────────────────────

_CMD_PARSE_SYSTEM = f"""\
你是一个专业的智能广告投放 AI，名字叫 SmartAD Engine。

{CROWD_KNOWLEDGE}

{CHANNEL_KNOWLEDGE}

{STRATEGY_RULES}

## 当前可用人群画像
{{crowd_desc}}

## 历史投放效果数据（聚合均值）
{{history_desc}}

## 你的任务
根据用户下发的广告投放指令，生成一份或多份结构化投放策略草案。
每份草案包含：crowdId、crowdTag、channel、budgetDay（元）、bidPrice（分）、reason（简要理由）。

**输出格式要求（严格 JSON）**：
{{{{
  "strategies": [
    {{{{
      "crowdId": 1,
      "crowdTag": "young_fashion",
      "channel": "douyin",
      "budgetDay": 500,
      "bidPrice": 120,
      "reason": "历史CTR较高，出价适中"
    }}}}
  ],
  "hasQuestion": false,
  "question": ""
}}}}

若指令不清晰需要追问，则设 hasQuestion=true 并在 question 中给出问题，strategies 返回空数组。
不要输出任何 JSON 以外的内容。"""

_CMD_PARSE_HUMAN = "用户指令：{command_text}"

CMD_PARSE_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(_CMD_PARSE_SYSTEM),
    HumanMessagePromptTemplate.from_template(_CMD_PARSE_HUMAN),
])


# ──────────────────────────────────────────────────────────────────────────────
# 追问回答 Prompt：带对话历史的多轮推理
# ──────────────────────────────────────────────────────────────────────────────

_CMD_REPLY_HUMAN_ANSWER = "回答：{answer}"

CMD_REPLY_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(_CMD_PARSE_SYSTEM),
    HumanMessagePromptTemplate.from_template(_CMD_PARSE_HUMAN),
    # assistant 追问轮（动态插入，见 build_command_reply_messages）
    ("assistant", '{{"hasQuestion": true, "question": "{question}", "strategies": []}}'),
    HumanMessagePromptTemplate.from_template(_CMD_REPLY_HUMAN_ANSWER),
])


# ──────────────────────────────────────────────────────────────────────────────
# 反思 Prompt：对策略草案进行自我审查（旗舰模型使用）
# ──────────────────────────────────────────────────────────────────────────────

_REFLECT_SYSTEM = f"""\
你是一个广告投放策略审核专家。
你的任务是审查 AI 生成的投放策略草案，检查是否符合以下规则：

{STRATEGY_RULES}

如果策略存在问题，返回修正后的策略；若策略合理，原样返回。
输出与输入相同的 JSON 格式，不要输出任何 JSON 以外的内容。"""

_REFLECT_HUMAN = """\
原始指令：{command_text}
待审查策略草案：
{draft_json}

请审查并输出最终策略 JSON。"""

REFLECT_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(_REFLECT_SYSTEM),
    HumanMessagePromptTemplate.from_template(_REFLECT_HUMAN),
])


# ──────────────────────────────────────────────────────────────────────────────
# 策略评估 Prompt（标准模型）
# ──────────────────────────────────────────────────────────────────────────────

_EVAL_SYSTEM = f"""\
你是一个广告投放效果分析 AI。

{STRATEGY_RULES}

## 当前策略信息
- 策略ID: {{strategy_id}}
- 人群标签: {{crowd_tag}}
- 渠道: {{channel}}
- 日预算: {{budget_day}} 元
- 当前出价: {{bid_price}} 分

## 近期投放报表
{{report_desc}}

## 你的任务
评估当前策略的投放效果，判断是否需要调整。

**输出格式（严格 JSON）**：
{{{{
  "needAdjust": true,
  "adjustType": "bid_up",
  "newBidPrice": 150,
  "newBudgetDay": 600,
  "roi": 1.5,
  "budgetDeviation": 0.08,
  "reason": "CTR偏低，建议提升出价以争抢更多流量",
  "score": 72
}}}}

adjustType 可选值：bid_up / bid_down / budget_up / budget_down / pause / no_action
score 为 0-100 策略健康评分。
不要输出任何 JSON 以外的内容。"""

_EVAL_HUMAN = "请评估以上策略并给出调整建议。"

EVALUATE_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(_EVAL_SYSTEM),
    HumanMessagePromptTemplate.from_template(_EVAL_HUMAN),
])


# ──────────────────────────────────────────────────────────────────────────────
# 告警检测 Prompt（标准模型）
# ──────────────────────────────────────────────────────────────────────────────

_ALERT_SYSTEM = f"""\
你是一个广告投放风险监控 AI。

{STRATEGY_RULES}

## 当前策略
- 策略ID: {{strategy_id}}
- 人群标签: {{crowd_tag}}
- 渠道: {{channel}}
- 日预算: {{budget_day}} 元

## 近期报表
{{report_desc}}

## 你的任务
判断该策略当前是否存在风险需要告警。

**输出格式（严格 JSON）**：
{{{{
  "hasAlert": true,
  "alertType": "low_roi",
  "alertLevel": "warning",
  "alertMessage": "过去3天ROI持续低于1.0，建议暂停或降低出价"
}}}}

alertType: low_ctr / low_roi / budget_overrun / no_conversion / abnormal_cost / normal
alertLevel: info / warning / critical
hasAlert=false 时其他字段可省略。
不要输出任何 JSON 以外的内容。"""

_ALERT_HUMAN = "请检查以上策略是否存在风险告警。"

ALERT_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(_ALERT_SYSTEM),
    HumanMessagePromptTemplate.from_template(_ALERT_HUMAN),
])


# ──────────────────────────────────────────────────────────────────────────────
# 便捷构建函数（供 chains 层调用）
# ──────────────────────────────────────────────────────────────────────────────

def build_command_parse_vars(
    command_text: str,
    crowd_list: list[dict],
    history_data: list[dict],
) -> dict:
    return {
        "command_text": command_text,
        "crowd_desc": _format_crowd_list(crowd_list),
        "history_desc": _format_history(history_data),
    }


def build_command_reply_vars(
    command_text: str,
    question: str,
    answer: str,
    crowd_list: list[dict],
    history_data: list[dict],
) -> dict:
    return {
        "command_text": command_text,
        "question": question,
        "answer": answer,
        "crowd_desc": _format_crowd_list(crowd_list),
        "history_desc": _format_history(history_data),
    }


def build_evaluate_vars(strategy: dict, report_data: list[dict]) -> dict:
    return {
        "strategy_id": strategy.get("strategyId"),
        "crowd_tag": strategy.get("crowdTag"),
        "channel": strategy.get("channel"),
        "budget_day": strategy.get("budgetDay"),
        "bid_price": strategy.get("bidPrice"),
        "report_desc": _format_report(report_data),
    }


def build_alert_vars(strategy: dict, report_data: list[dict]) -> dict:
    return {
        "strategy_id": strategy.get("strategyId"),
        "crowd_tag": strategy.get("crowdTag"),
        "channel": strategy.get("channel"),
        "budget_day": strategy.get("budgetDay"),
        "report_desc": _format_report(
            report_data,
            fields=["reportDate", "ctr", "roi", "cost", "conversions"],
        ),
    }


# ──────────────────────────────────────────────────────────────────────────────
# 向后兼容函数（供旧代码调用，内部已切换到 ChatPromptTemplate）
# ──────────────────────────────────────────────────────────────────────────────

def build_command_parse_prompt(command_text: str, crowd_list: list[dict], history_data: list[dict]) -> list[dict]:
    """向后兼容：返回 OpenAI messages 格式"""
    vars_ = build_command_parse_vars(command_text, crowd_list, history_data)
    msgs = CMD_PARSE_PROMPT.format_messages(**vars_)
    return [{"role": m.type if m.type != "human" else "user", "content": m.content} for m in msgs]


def build_command_reply_prompt(
    command_text: str, question: str, answer: str,
    crowd_list: list[dict], history_data: list[dict],
) -> list[dict]:
    """向后兼容：返回 OpenAI messages 格式"""
    vars_ = build_command_reply_vars(command_text, question, answer, crowd_list, history_data)
    msgs = CMD_REPLY_PROMPT.format_messages(**vars_)
    return [{"role": m.type if m.type != "human" else "user", "content": m.content} for m in msgs]


def build_evaluate_prompt(strategy: dict, report_data: list[dict]) -> list[dict]:
    """向后兼容"""
    vars_ = build_evaluate_vars(strategy, report_data)
    msgs = EVALUATE_PROMPT.format_messages(**vars_)
    return [{"role": m.type if m.type != "human" else "user", "content": m.content} for m in msgs]


def build_alert_prompt(strategy: dict, report_data: list[dict]) -> list[dict]:
    """向后兼容"""
    vars_ = build_alert_vars(strategy, report_data)
    msgs = ALERT_PROMPT.format_messages(**vars_)
    return [{"role": m.type if m.type != "human" else "user", "content": m.content} for m in msgs]
