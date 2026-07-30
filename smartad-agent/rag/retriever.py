"""
知识检索器（Retriever）
- 优先使用向量语义检索
- 向量库不可用时降级为关键词匹配
- 支持分类型检索（人群画像/渠道特征/策略规则）
- 支持结构化上下文组装（供 Prompt 注入）
"""
import re
from loguru import logger
from rag.vector_store import get_vector_store
from rag.knowledge import (
    CROWD_KNOWLEDGE, CHANNEL_KNOWLEDGE, STRATEGY_RULES,
    CROWD_DATABASE, CHANNEL_DATABASE,
)


class KnowledgeRetriever:
    """知识检索器"""

    def __init__(self):
        self._vs = get_vector_store()
        self._use_vector = False

    def initialize(self) -> bool:
        """初始化向量库并加载知识"""
        self._use_vector = self._vs.initialize()
        if self._use_vector:
            self._seed_knowledge()
        return self._use_vector

    def _seed_knowledge(self) -> None:
        """将知识数据种子导入向量库"""
        existing_count = self._vs.count()
        if existing_count > 0:
            logger.info(f"[Retriever] 向量库已有 {existing_count} 条知识，跳过种子导入")
            return

        documents = []
        metadatas = []
        ids = []

        # 人群画像
        for i, item in enumerate(CROWD_DATABASE):
            documents.append(
                f"人群标签: {item['tag']}\n描述: {item['description']}"
            )
            metadatas.append({"type": "crowd", "tag": item["tag"]})
            ids.append(f"crowd_{i}")

        # 渠道特征
        for i, item in enumerate(CHANNEL_DATABASE):
            documents.append(
                f"渠道: {item['channel']}\n特征: {item['feature']}"
            )
            metadatas.append({"type": "channel", "channel": item["channel"]})
            ids.append(f"channel_{i}")

        # 策略规则
        for i, rule in enumerate(STRATEGY_RULES.split("\n")):
            if rule.strip():
                documents.append(rule.strip())
                metadatas.append({"type": "rule"})
                ids.append(f"rule_{i}")

        # 人群画像知识库文本
        documents.append(CROWD_KNOWLEDGE)
        metadatas.append({"type": "knowledge_text", "category": "crowd"})
        ids.append("knowledge_crowd")

        # 渠道知识库文本
        documents.append(CHANNEL_KNOWLEDGE)
        metadatas.append({"type": "knowledge_text", "category": "channel"})
        ids.append("knowledge_channel")

        # 策略规则知识库文本
        documents.append(STRATEGY_RULES)
        metadatas.append({"type": "knowledge_text", "category": "rules"})
        ids.append("knowledge_rules")

        self._vs.add_documents(documents=documents, metadatas=metadatas, ids=ids)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
    ) -> list[dict]:
        """
        检索知识
        :param query: 查询文本
        :param top_k: 返回数量
        :param category: 过滤类型 (crowd/channel/rule/None)
        :return: [{"document": str, "metadata": dict, "score": float}, ...]
        """
        if self._use_vector:
            return self._vector_retrieve(query, top_k, category)
        else:
            return self._keyword_retrieve(query, top_k, category)

    def _vector_retrieve(
        self, query: str, top_k: int, category: str | None
    ) -> list[dict]:
        """向量语义检索"""
        filter_conditions = {"type": category} if category else None
        results = self._vs.query(
            query_text=query,
            n_results=top_k,
            filter_conditions=filter_conditions,
        )
        for r in results:
            r["score"] = 1.0 - r.pop("distance", 0)
        return results

    def _keyword_retrieve(
        self, query: str, top_k: int, category: str | None
    ) -> list[dict]:
        """关键词匹配降级方案"""
        results = []
        query_lower = query.lower()

        knowledge_sources = {
            "crowd": CROWD_DATABASE,
            "channel": CHANNEL_DATABASE,
        }

        if category in knowledge_sources:
            sources = knowledge_sources[category]
        elif category is None:
            sources = CROWD_DATABASE + CHANNEL_DATABASE
        else:
            sources = []

        query_terms = set(re.findall(r"\w+", query_lower))

        for item in sources:
            text = str(item).lower()
            score = sum(1 for term in query_terms if term in text)
            if score > 0:
                results.append({
                    "document": str(item),
                    "metadata": item if isinstance(item, dict) else {"value": item},
                    "score": score / max(len(query_terms), 1),
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def get_crowd_context(self, crowd_list: list[dict] | None = None) -> str:
        """
        获取人群画像上下文（供 Prompt 注入）
        优先使用向量检索增强，降级使用原始知识文本
        """
        if self._use_vector and crowd_list:
            tags = [c.get("crowdTag", "") for c in crowd_list]
            retrieved_docs = []
            for tag in tags:
                results = self._vector_retrieve(
                    query=tag, top_k=2, category="crowd"
                )
                retrieved_docs.extend([r["document"] for r in results])

            if retrieved_docs:
                return "\n".join(retrieved_docs)

        return CROWD_KNOWLEDGE

    def get_channel_context(self, channel: str | None = None) -> str:
        """获取渠道特征上下文"""
        if self._use_vector and channel:
            results = self._vector_retrieve(
                query=channel, top_k=2, category="channel"
            )
            if results:
                return "\n".join(r["document"] for r in results)

        return CHANNEL_KNOWLEDGE

    def get_rules_context(self) -> str:
        """获取策略规则上下文"""
        return STRATEGY_RULES

    def get_full_context(
        self,
        command_text: str = "",
        crowd_list: list[dict] | None = None,
    ) -> dict[str, str]:
        """
        获取完整上下文（用于 Prompt 注入）
        返回: {"crowd_knowledge": str, "channel_knowledge": str, "strategy_rules": str}
        """
        crowd_ctx = self.get_crowd_context(crowd_list)
        channel_ctx = self.get_channel_context()
        rules_ctx = self.get_rules_context()

        if self._use_vector and command_text:
            relevant = self._vector_retrieve(query=command_text, top_k=3)
            if relevant:
                extra = "\n".join(r["document"] for r in relevant)
                channel_ctx = channel_ctx + "\n\n## 相关知识\n" + extra

        return {
            "crowd_knowledge": crowd_ctx,
            "channel_knowledge": channel_ctx,
            "strategy_rules": rules_ctx,
        }


# ──────────────────────────────────────────────────────────────────────────────
# 全局单例
# ──────────────────────────────────────────────────────────────────────────────

_retriever = KnowledgeRetriever()


def get_retriever() -> KnowledgeRetriever:
    """获取检索器单例"""
    return _retriever
