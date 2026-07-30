"""
Prompt 版本管理模块
- Prompt 模板版本化（支持多版本共存）
- A/B 测试（对比不同版本 Prompt 效果）
- 离线评估数据集（标准化测试用例）
- 自动评分（合规性、完整性、合理性）
"""
from __future__ import annotations

import json
import time
from typing import Callable, Optional
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class PromptVersion:
    """Prompt 版本信息"""
    version: str
    template: str
    description: str
    created_at: float = field(default_factory=time.time)
    is_active: bool = True


@dataclass
class EvaluationCase:
    """评估测试用例"""
    case_id: str
    input_command: str
    expected_keywords: list[str] = field(default_factory=list)
    expected_structure: list[str] = field(default_factory=list)
    min_strategies: int = 0
    should_have_question: bool = False
    category: str = "general"


@dataclass
class EvaluationResult:
    """评估结果"""
    case_id: str
    passed: bool
    score: float  # 0-100
    details: dict
    execution_time_ms: float


# ──────────────────────────────────────────────────────────────────────────────
# Prompt 版本注册表
# ──────────────────────────────────────────────────────────────────────────────

class PromptRegistry:
    """Prompt 版本注册表"""

    def __init__(self):
        self._versions: dict[str, PromptVersion] = {}
        self._active_version: str = "v1"

    def register(self, version: str, template: str, description: str = "") -> None:
        self._versions[version] = PromptVersion(
            version=version,
            template=template,
            description=description,
        )
        logger.info(f"[PromptRegistry] 注册版本: {version}")

    def get(self, version: Optional[str] = None) -> PromptVersion:
        v = version or self._active_version
        if v not in self._versions:
            raise ValueError(f"Prompt 版本不存在: {v}")
        return self._versions[v]

    def set_active(self, version: str) -> None:
        if version not in self._versions:
            raise ValueError(f"Prompt 版本不存在: {version}")
        self._active_version = version
        logger.info(f"[PromptRegistry] 激活版本: {version}")

    def list_versions(self) -> list[dict]:
        return [
            {
                "version": v.version,
                "description": v.description,
                "is_active": v.version == self._active_version,
                "created_at": v.created_at,
            }
            for v in self._versions.values()
        ]


# ──────────────────────────────────────────────────────────────────────────────
# 评估数据集
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_EVALUATION_CASES = [
    EvaluationCase(
        case_id="E001",
        input_command="给18-25岁女学生投放美妆广告，日预算500元，抖音渠道",
        expected_keywords=["crowdTag", "channel", "budgetDay", "bidPrice"],
        expected_structure=["strategies"],
        min_strategies=1,
        category="clear_instruction",
    ),
    EvaluationCase(
        case_id="E002",
        input_command="在抖音和快手同时投放年轻时尚人群，总预算2000元",
        expected_keywords=["crowdTag", "channel", "budgetDay"],
        expected_structure=["strategies"],
        min_strategies=2,
        category="multi_channel",
    ),
    EvaluationCase(
        case_id="E003",
        input_command="帮我做个广告投放",
        expected_keywords=["hasQuestion", "question"],
        expected_structure=["hasQuestion"],
        should_have_question=True,
        category="ambiguous",
    ),
    EvaluationCase(
        case_id="E004",
        input_command="给企业客户投放B端产品，百度渠道，日预算10000元",
        expected_keywords=["crowdTag", "channel", "budgetDay", "bidPrice"],
        min_strategies=1,
        category="high_value",
    ),
    EvaluationCase(
        case_id="E005",
        input_command="给中老年科技爱好者推荐高ROI的投放策略",
        expected_keywords=["crowdTag", "bidPrice"],
        min_strategies=1,
        category="specific_crowd",
    ),
]


# ──────────────────────────────────────────────────────────────────────────────
# 评估引擎
# ──────────────────────────────────────────────────────────────────────────────

class EvaluationEngine:
    """Prompt/Agent 评估引擎"""

    def __init__(self, cases: list[EvaluationCase] | None = None):
        self._cases = cases or DEFAULT_EVALUATION_CASES
        self._results: list[EvaluationResult] = []

    def add_case(self, case: EvaluationCase) -> None:
        self._cases.append(case)

    async def evaluate(
        self,
        executor: Callable,
        case_ids: list[str] | None = None,
    ) -> list[EvaluationResult]:
        """
        执行评估
        :param executor: async callable(command_text) -> dict
        :param case_ids: 指定测试用例 ID（None=全部）
        :return: 评估结果列表
        """
        self._results = []
        target_cases = [c for c in self._cases if not case_ids or c.case_id in case_ids]

        logger.info(f"[EvalEngine] 开始评估: {len(target_cases)} 个用例")

        for case in target_cases:
            try:
                t0 = time.time()
                result = await executor(case.input_command)
                elapsed_ms = (time.time() - t0) * 1000

                eval_result = self._score_case(case, result, elapsed_ms)
                self._results.append(eval_result)

                status = "PASS" if eval_result.passed else "FAIL"
                logger.info(
                    f"[EvalEngine] [{status}] {case.case_id}: "
                    f"score={eval_result.score}, time={elapsed_ms:.0f}ms"
                )
            except Exception as e:
                logger.error(f"[EvalEngine] {case.case_id} 执行异常: {e}")
                self._results.append(EvaluationResult(
                    case_id=case.case_id,
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    execution_time_ms=0,
                ))

        return self._results

    def _score_case(
        self, case: EvaluationCase, result: dict, elapsed_ms: float
    ) -> EvaluationResult:
        """评分单个用例"""
        score = 0.0
        details = {}

        # 1. 结构检查
        strategies = result.get("strategies", [])
        has_question = result.get("hasQuestion", False)

        if case.should_have_question:
            if has_question:
                score += 30
                details["question_correct"] = True
            else:
                details["question_correct"] = False
        else:
            if not has_question and strategies:
                score += 20
                details["structure_correct"] = True
            else:
                details["structure_correct"] = False

        # 2. 策略数量检查
        if not case.should_have_question:
            if len(strategies) >= case.min_strategies:
                score += 20
                details["strategy_count_ok"] = True
            else:
                details["strategy_count_ok"] = False

        # 3. 关键字段检查
        all_text = json.dumps(result, ensure_ascii=False)
        keyword_score = 0
        for kw in case.expected_keywords:
            if kw in all_text:
                keyword_score += 10
        score += min(keyword_score, 30)
        details["keyword_score"] = keyword_score

        # 4. 字段完整性
        if strategies:
            strategy = strategies[0]
            completeness = sum(
                1 for k in ["crowdTag", "channel", "budgetDay", "bidPrice", "reason"]
                if k in strategy and strategy[k]
            )
            score += completeness * 4  # 最高 20 分
            details["completeness"] = completeness

        # 5. 耗时惩罚
        if elapsed_ms > 30000:
            score -= 10
        elif elapsed_ms > 15000:
            score -= 5

        score = max(0, min(100, score))
        passed = score >= 60

        return EvaluationResult(
            case_id=case.case_id,
            passed=passed,
            score=score,
            details=details,
            execution_time_ms=elapsed_ms,
        )

    def summary(self) -> dict:
        """生成评估报告摘要"""
        if not self._results:
            return {"total": 0}

        total = len(self._results)
        passed = sum(1 for r in self._results if r.passed)
        avg_score = sum(r.score for r in self._results) / total if total > 0 else 0
        avg_time = sum(r.execution_time_ms for r in self._results) / total if total > 0 else 0

        return {
            "total_cases": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "avg_score": round(avg_score, 1),
            "avg_time_ms": round(avg_time, 0),
            "details": [
                {
                    "case_id": r.case_id,
                    "passed": r.passed,
                    "score": r.score,
                    "time_ms": round(r.execution_time_ms, 0),
                }
                for r in self._results
            ],
        }


# ──────────────────────────────────────────────────────────────────────────────
# 全局单例
# ──────────────────────────────────────────────────────────────────────────────

prompt_registry = PromptRegistry()
evaluation_engine = EvaluationEngine()


def get_prompt_registry() -> PromptRegistry:
    return prompt_registry


def get_evaluation_engine() -> EvaluationEngine:
    return evaluation_engine
