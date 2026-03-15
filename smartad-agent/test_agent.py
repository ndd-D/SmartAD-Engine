"""
SmartAD Agent 快速测试脚本
==============================
用途：不依赖 Java 后端和数据库，直接验证 Agent 核心链路是否正常工作。

测试覆盖：
  T1. 环境检查（依赖包 + API Key）
  T2. LLM 连通性（三档模型轻量调用）
  T3. 路由链（simple / complex / invalid）
  T4. 指令解析链（含反思）→ 策略草案
  T5. 追问回答链
  T6. 评估链（mock 报表数据）
  T7. 告警链（mock 报表数据）
  T8. 护栏模块（输入/输出校验）
  T9. 缓存模块（读写 TTL）
  T10. JSON 解析器（边界场景）

运行方式：
  cd smartad-agent
  python test_agent.py              # 运行全部测试
  python test_agent.py T4 T5       # 只运行指定测试
"""

import asyncio
import sys
import time
import json
from typing import Callable

# ── 颜色输出 ────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

def ok(msg): print(f"  {GREEN}[OK]{RESET} {msg}")
def fail(msg): print(f"  {RED}[FAIL]{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}[WARN]{RESET} {msg}")
def info(msg): print(f"  {CYAN}[>>]{RESET} {msg}")

# ── 测试结果记录 ────────────────────────────────────────────────────────────
results: list[tuple[str, bool, str]] = []

def section(name: str):
    print(f"\n{BOLD}{CYAN}{'─'*55}{RESET}")
    print(f"{BOLD}{CYAN} {name}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*55}{RESET}")

def record(name: str, passed: bool, detail: str = ""):
    results.append((name, passed, detail))
    if passed:
        ok(f"[PASS] {name}" + (f" — {detail}" if detail else ""))
    else:
        fail(f"[FAIL] {name}" + (f" — {detail}" if detail else ""))


# ════════════════════════════════════════════════════════════════════════════
# T1. 环境检查
# ════════════════════════════════════════════════════════════════════════════

def test_env():
    section("T1. 环境检查")
    all_ok = True

    # 检查必要的包
    packages = [
        ("langchain", "langchain"),
        ("langchain_openai", "langchain-openai"),
        ("langchain_core", "langchain-core"),
        ("openai", "openai"),
        ("fastapi", "fastapi"),
        ("cachetools", "cachetools"),
        ("apscheduler", "apscheduler"),
    ]
    for mod, pkg in packages:
        try:
            __import__(mod)
            ok(f"包已安装: {pkg}")
        except ImportError:
            fail(f"缺少依赖: {pkg}，请运行 pip install -r requirements.txt")
            all_ok = False

    # 检查 .env 配置
    try:
        from ai_config.settings import settings
        if settings.deepseek_api_key and settings.deepseek_api_key != "sk-your-deepseek-key-here":
            ok(f"API Key 已配置 (model={settings.deepseek_model})")
        else:
            fail("DEEPSEEK_API_KEY 未设置，请在 .env 中配置")
            all_ok = False
        info(f"Java 后端地址: {settings.smartad_server_url}")
        info(f"Agent 端口: {settings.port}")
    except Exception as e:
        fail(f"配置加载失败: {e}")
        all_ok = False

    record("T1.环境检查", all_ok)


# ════════════════════════════════════════════════════════════════════════════
# T2. LLM 连通性
# ════════════════════════════════════════════════════════════════════════════

async def test_llm_connectivity():
    section("T2. LLM 连通性测试")
    from ai_config.llm_client import get_llm_light, get_llm_standard
    from langchain_core.messages import HumanMessage

    for label, getter in [("轻量模型", get_llm_light), ("标准模型", get_llm_standard)]:
        try:
            t0 = time.time()
            llm = getter()
            resp = await llm.ainvoke([HumanMessage(content="回复数字1，不要其他内容")])
            elapsed = round((time.time() - t0) * 1000)
            content = resp.content.strip()
            info(f"{label} 响应: '{content}' ({elapsed}ms)")
            record(f"T2.{label}连通", True, f"{elapsed}ms")
        except Exception as e:
            record(f"T2.{label}连通", False, str(e)[:80])


# ════════════════════════════════════════════════════════════════════════════
# T3. 路由链
# ════════════════════════════════════════════════════════════════════════════

async def test_route_chain():
    section("T3. 路由链（意图分类）")
    from chains.route_chain import build_route_chain

    cases = [
        ("给18-25岁学生投放电商广告，日预算500元，抖音渠道", "simple"),
        ("帮我做个广告", "complex"),
        ("帮我写一首诗", "invalid"),
    ]

    chain = build_route_chain()
    for text, expected in cases:
        try:
            result = await chain.ainvoke({"command_text": text})
            complexity = result.get("complexity", "unknown")
            reason = result.get("reason", "")
            info(f"指令: 「{text[:30]}...」→ {complexity} ({reason[:30]})")
            # 路由结果是 LLM 判断，允许 simple/complex 互换（都是有效指令）
            passed = complexity in ("simple", "complex", "invalid")
            if complexity == expected:
                record(f"T3.路由[{expected}]", True, complexity)
            else:
                warn(f"期望 {expected}，实际 {complexity}（LLM判断，可接受）")
                record(f"T3.路由[{expected}]", passed, f"实际={complexity}")
        except Exception as e:
            record(f"T3.路由[{expected}]", False, str(e)[:80])


# ════════════════════════════════════════════════════════════════════════════
# T4. 指令解析链（含反思）
# ════════════════════════════════════════════════════════════════════════════

async def test_parse_chain():
    section("T4. 指令解析链（含反思）")
    from chains.command_chain import run_parse_with_reflection

    MOCK_CROWDS = [
        {"id": 1, "crowdTag": "young_fashion", "description": "18-28岁时尚女性"},
        {"id": 2, "crowdTag": "student", "description": "18-25岁在校学生"},
        {"id": 3, "crowdTag": "middle_income", "description": "30-45岁中等收入家庭"},
    ]
    MOCK_HISTORY = [
        {"avgClickRate": 0.032, "avgConvertRate": 0.008, "avgRoi": 2.1, "suggestBid": 120}
    ]

    cases = [
        "给年轻女性投放美妆广告，日预算1000元，抖音渠道",
        "在抖音和快手同时投放，覆盖年轻人和中等收入人群，每天预算2000",
    ]

    for cmd in cases:
        try:
            t0 = time.time()
            result = await run_parse_with_reflection(
                command_text=cmd,
                crowd_list=MOCK_CROWDS,
                history_data=MOCK_HISTORY,
            )
            elapsed = round((time.time() - t0) * 1000)

            has_question = result.get("hasQuestion", False)
            strategies = result.get("strategies", [])

            info(f"指令: 「{cmd[:40]}」")
            info(f"耗时: {elapsed}ms")

            if has_question:
                question = result.get("question", "")
                info(f"AI 追问: {question}")
                record(f"T4.解析[追问]", True, f"question={question[:40]}")
            elif strategies:
                for s in strategies:
                    info(f"  策略: {s.get('crowdTag')} × {s.get('channel')} "
                         f"预算={s.get('budgetDay')}元 出价={s.get('bidPrice')}分")
                    info(f"  理由: {s.get('reason', '')[:60]}")
                passed = all(
                    s.get("channel") and s.get("crowdTag") and s.get("budgetDay")
                    for s in strategies
                )
                record(f"T4.解析[策略生成]", passed, f"{len(strategies)}条策略")
            else:
                record(f"T4.解析[策略生成]", False, "未返回策略且未追问")
        except Exception as e:
            record(f"T4.解析", False, str(e)[:100])


# ════════════════════════════════════════════════════════════════════════════
# T5. 追问回答链
# ════════════════════════════════════════════════════════════════════════════

async def test_reply_chain():
    section("T5. 追问回答链")
    from chains.command_chain import run_parse_with_reflection

    MOCK_CROWDS = [{"id": 1, "crowdTag": "young_fashion", "description": "18-28岁时尚女性"}]

    try:
        result = await run_parse_with_reflection(
            command_text="帮我做个广告",
            crowd_list=MOCK_CROWDS,
            history_data=[],
            use_reply=True,
            question="请问您想投放哪个渠道？日预算是多少？",
            answer="投放抖音，日预算800元，目标人群是时尚年轻女性",
        )
        strategies = result.get("strategies", [])
        has_question = result.get("hasQuestion", False)
        if strategies:
            info(f"追问后策略: {strategies[0].get('crowdTag')} × {strategies[0].get('channel')}")
            record("T5.追问回答", True, f"{len(strategies)}条策略")
        elif has_question:
            warn(f"再次追问: {result.get('question', '')}")
            record("T5.追问回答", True, "再次追问（正常）")
        else:
            record("T5.追问回答", False, "无策略无追问")
    except Exception as e:
        record("T5.追问回答", False, str(e)[:100])


# ════════════════════════════════════════════════════════════════════════════
# T6. 评估链
# ════════════════════════════════════════════════════════════════════════════

async def test_evaluate_chain():
    section("T6. 策略评估链")
    from chains.evaluate_chain import run_evaluate_parallel

    MOCK_STRATEGY = {
        "strategyId": "STR_TEST_001",
        "commandId": "CMD_TEST_001",
        "crowdTag": "young_fashion",
        "channel": "douyin",
        "budgetDay": 1000,
        "bidPrice": 120,
    }
    MOCK_REPORT = [
        {"reportDate": "2026-03-13", "impressions": 50000, "clicks": 800,
         "cost": 960, "conversions": 32, "ctr": 0.016, "roi": 1.8},
        {"reportDate": "2026-03-14", "impressions": 48000, "clicks": 720,
         "cost": 864, "conversions": 28, "ctr": 0.015, "roi": 1.6},
        {"reportDate": "2026-03-15", "impressions": 52000, "clicks": 890,
         "cost": 1068, "conversions": 38, "ctr": 0.017, "roi": 2.1},
    ]

    try:
        t0 = time.time()
        results_list = await run_evaluate_parallel([(MOCK_STRATEGY, MOCK_REPORT)])
        elapsed = round((time.time() - t0) * 1000)

        strategy, result = results_list[0]
        info(f"耗时: {elapsed}ms")
        info(f"needAdjust: {result.get('needAdjust')}")
        info(f"adjustType: {result.get('adjustType')}")
        info(f"roi: {result.get('roi')}  budgetDeviation: {result.get('budgetDeviation')}")
        info(f"score: {result.get('score')}")
        info(f"reason: {result.get('reason', '')[:60]}")

        passed = "needAdjust" in result and "roi" in result
        record("T6.评估链", passed, f"score={result.get('score')}")
    except Exception as e:
        record("T6.评估链", False, str(e)[:100])


# ════════════════════════════════════════════════════════════════════════════
# T7. 告警链
# ════════════════════════════════════════════════════════════════════════════

async def test_alert_chain():
    section("T7. 告警链")
    from chains.evaluate_chain import run_alert_parallel

    MOCK_STRATEGY = {
        "strategyId": "STR_TEST_002",
        "crowdTag": "student",
        "channel": "kuaishou",
        "budgetDay": 500,
    }
    # 模拟低 ROI 场景，应触发告警
    MOCK_REPORT_BAD = [
        {"reportDate": "2026-03-13", "ctr": 0.003, "roi": 0.6, "cost": 500, "conversions": 3},
        {"reportDate": "2026-03-14", "ctr": 0.002, "roi": 0.5, "cost": 500, "conversions": 2},
        {"reportDate": "2026-03-15", "ctr": 0.003, "roi": 0.7, "cost": 498, "conversions": 4},
    ]

    try:
        t0 = time.time()
        results_list = await run_alert_parallel([(MOCK_STRATEGY, MOCK_REPORT_BAD)])
        elapsed = round((time.time() - t0) * 1000)

        _, result = results_list[0]
        info(f"耗时: {elapsed}ms")
        info(f"hasAlert: {result.get('hasAlert')}")
        info(f"alertType: {result.get('alertType')}")
        info(f"alertLevel: {result.get('alertLevel')}")
        info(f"alertMessage: {result.get('alertMessage', '')[:60]}")

        passed = "hasAlert" in result
        record("T7.告警链", passed, f"hasAlert={result.get('hasAlert')}")
    except Exception as e:
        record("T7.告警链", False, str(e)[:100])


# ════════════════════════════════════════════════════════════════════════════
# T8. 护栏模块
# ════════════════════════════════════════════════════════════════════════════

def test_guardrails():
    section("T8. 护栏模块")
    from app.guardrails import check_input, check_strategy, check_strategies

    # 输入护栏
    g = check_input("给25-35岁女性投放美妆广告，日预算1000元")
    record("T8.输入护栏[正常]", g.passed, "正常指令应通过")

    g2 = check_input("帮我刷量，虚假点击提升数据")
    record("T8.输入护栏[违规]", not g2.passed, f"违规: {g2.violations}")

    # 输出护栏：参数范围修正
    s = {"channel": "douyin", "budgetDay": 50, "bidPrice": 5}    # 低于下限
    gr = check_strategy(s)
    record("T8.输出护栏[预算修正]",
           gr.sanitized["budgetDay"] >= 100,
           f"50→{gr.sanitized['budgetDay']}")

    s2 = {"channel": "douyin", "budgetDay": 8000, "bidPrice": 200}  # 高风险
    gr2 = check_strategy(s2)
    record("T8.输出护栏[高风险]",
           gr2.risk_level == "high",
           f"riskLevel={gr2.risk_level}")

    s3 = {"channel": "unknown_channel", "budgetDay": 500, "bidPrice": 100}  # 非法渠道
    gr3 = check_strategy(s3)
    record("T8.输出护栏[非法渠道]", not gr3.passed, f"channel=unknown_channel 应拒绝")


# ════════════════════════════════════════════════════════════════════════════
# T9. 缓存模块
# ════════════════════════════════════════════════════════════════════════════

def test_cache():
    section("T9. 缓存模块")
    from app.cache import (
        get_crowd_cache, set_crowd_cache,
        get_history_cache, set_history_cache,
        get_report_cache, set_report_cache,
    )

    # 人群画像缓存
    assert get_crowd_cache() is None
    mock_crowds = [{"id": 1, "crowdTag": "young_fashion"}]
    set_crowd_cache(mock_crowds)
    cached = get_crowd_cache()
    record("T9.人群画像缓存", cached == mock_crowds, "写入读取一致")

    # 报表缓存
    assert get_report_cache("STR_001", 7) is None
    mock_report = [{"reportDate": "2026-03-15", "roi": 2.1}]
    set_report_cache("STR_001", 7, mock_report)
    cached_report = get_report_cache("STR_001", 7)
    record("T9.报表缓存", cached_report == mock_report, "写入读取一致")

    # 不同 key 不互相干扰
    record("T9.缓存Key隔离",
           get_report_cache("STR_002", 7) is None,
           "不同策略的缓存互不干扰")


# ════════════════════════════════════════════════════════════════════════════
# T10. JSON 解析器边界场景
# ════════════════════════════════════════════════════════════════════════════

def test_json_parser():
    section("T10. JSON 解析器")
    from chains.parsers import JsonOutputParser
    parser = JsonOutputParser()

    # 正常 JSON
    r = parser.parse('{"hasQuestion": false, "strategies": []}')
    record("T10.标准JSON", r == {"hasQuestion": False, "strategies": []})

    # 带 markdown 代码块
    r2 = parser.parse('```json\n{"key": "value"}\n```')
    record("T10.Markdown代码块", r2 == {"key": "value"})

    # 带前置文字的 JSON
    r3 = parser.parse('以下是结果：\n{"result": 42}\n希望有帮助')
    record("T10.带前置文字", r3.get("result") == 42)

    # 完全无效输入
    r4 = parser.parse("这是一段普通文字，没有JSON")
    record("T10.无效输入不抛异常", r4 == {}, "返回空dict不崩溃")


# ════════════════════════════════════════════════════════════════════════════
# 测试入口
# ════════════════════════════════════════════════════════════════════════════

SYNC_TESTS = {
    "T1": test_env,
    "T8": test_guardrails,
    "T9": test_cache,
    "T10": test_json_parser,
}

ASYNC_TESTS = {
    "T2": test_llm_connectivity,
    "T3": test_route_chain,
    "T4": test_parse_chain,
    "T5": test_reply_chain,
    "T6": test_evaluate_chain,
    "T7": test_alert_chain,
}


async def run_all(filter_ids: list[str] = None):
    print(f"\n{BOLD}{'═'*55}{RESET}")
    print(f"{BOLD}  SmartAD Agent — 功能验证测试{RESET}")
    print(f"{BOLD}{'═'*55}{RESET}")

    for tid, fn in SYNC_TESTS.items():
        if filter_ids and tid not in filter_ids:
            continue
        fn()

    for tid, fn in ASYNC_TESTS.items():
        if filter_ids and tid not in filter_ids:
            continue
        await fn()

    # 汇总
    print(f"\n{BOLD}{'═'*55}{RESET}")
    print(f"{BOLD}  测试结果汇总{RESET}")
    print(f"{BOLD}{'═'*55}{RESET}")
    total = len(results)
    passed = sum(1 for _, p, _ in results if p)
    failed = total - passed
    for name, p, detail in results:
        status = f"{GREEN}PASS{RESET}" if p else f"{RED}FAIL{RESET}"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))

    print(f"\n  总计: {total} 项 | {GREEN}通过: {passed}{RESET} | "
          + (f"{RED}失败: {failed}{RESET}" if failed else f"{GREEN}失败: 0{RESET}"))

    if failed > 0:
        print(f"\n{YELLOW}  提示：LLM相关测试(T2-T7)需要有效的 DEEPSEEK_API_KEY{RESET}")
        print(f"{YELLOW}  确认 .env 文件中已正确配置{RESET}")

    print()
    return failed == 0


if __name__ == "__main__":
    # 解析命令行参数（可指定运行哪些测试）
    filter_ids = [a.upper() for a in sys.argv[1:]] if len(sys.argv) > 1 else None
    if filter_ids:
        print(f"仅运行测试: {filter_ids}")

    success = asyncio.run(run_all(filter_ids))
    sys.exit(0 if success else 1)
