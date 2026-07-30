"""
向量存储模块（ChromaDB 嵌入式模式）
- 知识数据持久化到本地目录
- 支持语义检索（similarity search）
- 支持 MMR（最大边际相关性）多样化检索
- 支持动态增删知识条目
"""
import os
from loguru import logger
from ai_config.settings import settings
from rag.embedding import get_embedding_provider

# ChromaDB 可选依赖
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("[VectorStore] chromadb 未安装，RAG 将使用关键词匹配降级方案")


class VectorStore:
    """向量存储管理器"""

    def __init__(self):
        self._client = None
        self._collection = None
        self._embedding_fn = None
        self._initialized = False

    def initialize(self) -> bool:
        """初始化 ChromaDB 客户端和集合"""
        if not CHROMA_AVAILABLE:
            logger.warning("[VectorStore] ChromaDB 不可用，使用降级模式")
            return False

        try:
            persist_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data",
                "chroma"
            )
            os.makedirs(persist_dir, exist_ok=True)

            self._client = chromadb.Client(
                ChromaSettings(
                    persist_directory=persist_dir,
                    anonymized_telemetry=False,
                )
            )

            self._embedding_fn = get_embedding_provider()

            self._collection = self._client.get_or_create_collection(
                name=settings.chroma_collection,
                metadata={"hnsw:space": "cosine"},
            )

            self._initialized = True
            count = self._collection.count()
            logger.info(
                f"[VectorStore] 初始化完成: collection={settings.chroma_collection}, "
                f"已有 {count} 条知识"
            )
            return True

        except Exception as e:
            logger.error(f"[VectorStore] 初始化失败: {e}")
            self._initialized = False
            return False

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        """添加文档到向量库"""
        if not self._initialized:
            logger.warning("[VectorStore] 未初始化，跳过 add_documents")
            return

        try:
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]

            embeddings = self._embedding_fn.embed_documents(documents)

            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas or [{}] * len(documents),
            )
            logger.info(f"[VectorStore] 添加 {len(documents)} 条文档")
        except Exception as e:
            logger.error(f"[VectorStore] 添加文档失败: {e}")

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter_conditions: dict | None = None,
    ) -> list[dict]:
        """
        语义检索（余弦相似度）
        返回: [{"document": str, "metadata": dict, "distance": float}, ...]
        """
        if not self._initialized:
            return []

        try:
            query_embedding = self._embedding_fn.embed_query(query_text)

            kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": min(n_results, self._collection.count()),
                "include": ["documents", "metadatas", "distances"],
            }
            if filter_conditions:
                kwargs["where"] = filter_conditions

            results = self._collection.query(**kwargs)

            documents = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0] if results["distances"] else []

            return [
                {
                    "document": doc,
                    "metadata": meta,
                    "distance": dist,
                }
                for doc, meta, dist in zip(documents, metadatas, distances)
            ]
        except Exception as e:
            logger.error(f"[VectorStore] 检索失败: {e}")
            return []

    def query_mmr(
        self,
        query_text: str,
        n_results: int = 5,
        lambda_param: float = 0.5,
    ) -> list[dict]:
        """
        MMR 多样化检索（避免返回过于相似的结果）
        lambda_param: 0=纯相关性, 1=最大多样性
        """
        if not self._initialized:
            return []

        try:
            query_embedding = self._embedding_fn.embed_query(query_text)

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results * 2, self._collection.count()),
                include=["documents", "metadatas", "distances", "embeddings"],
            )

            if not results["documents"] or not results["documents"][0]:
                return []

            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]
            embeddings = results["embeddings"][0]

            selected_indices = []
            remaining = list(range(len(docs)))

            if not remaining:
                return []

            selected_indices.append(remaining.pop(0))

            for _ in range(min(n_results - 1, len(remaining))):
                best_score = -1.0
                best_idx = -1

                for ri in remaining:
                    relevance = 1.0 - distances[ri]
                    max_similarity = 0.0
                    for si in selected_indices:
                        sim = _cosine_similarity(embeddings[ri], embeddings[si])
                        max_similarity = max(max_similarity, sim)
                    score = lambda_param * relevance - (1 - lambda_param) * max_similarity
                    if score > best_score:
                        best_score = score
                        best_idx = ri

                if best_idx >= 0:
                    selected_indices.append(best_idx)
                    remaining.remove(best_idx)

            return [
                {
                    "document": docs[i],
                    "metadata": metas[i],
                    "distance": distances[i],
                }
                for i in selected_indices
            ]
        except Exception as e:
            logger.error(f"[VectorStore] MMR 检索失败: {e}")
            return []

    def delete(self, ids: list[str]) -> None:
        """删除指定 ID 的文档"""
        if not self._initialized:
            return
        try:
            self._collection.delete(ids=ids)
            logger.info(f"[VectorStore] 删除 {len(ids)} 条文档")
        except Exception as e:
            logger.error(f"[VectorStore] 删除失败: {e}")

    def count(self) -> int:
        """获取集合中的文档数量"""
        if not self._initialized:
            return 0
        return self._collection.count()


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算余弦相似度"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ──────────────────────────────────────────────────────────────────────────────
# 全局单例
# ──────────────────────────────────────────────────────────────────────────────

_vector_store = VectorStore()


def get_vector_store() -> VectorStore:
    """获取向量存储单例"""
    return _vector_store
