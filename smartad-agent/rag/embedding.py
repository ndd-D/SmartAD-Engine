"""
Embedding 模型模块
支持两种嵌入方式：
1. 本地 sentence-transformers（默认，离线可用）
2. API-based Embedding（通过 LLM 接口的 embedding endpoint）
"""
from functools import lru_cache
from loguru import logger
from ai_config.settings import settings


class EmbeddingProvider:
    """Embedding 提供者基类"""

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_query(self, query: str) -> list[float]:
        raise NotImplementedError


class LocalSentenceTransformerEmbedding(EmbeddingProvider):
    """
    本地 sentence-transformers 嵌入
    轻量级模型，首次加载需下载约 90MB
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name)
            logger.info(f"[Embedding] 本地模型加载完成: {model_name}")
        except ImportError:
            logger.warning("[Embedding] sentence-transformers 未安装，降级为 Mock 嵌入")
            self._model = None

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        if self._model is None:
            return [self._mock_embed(d) for d in documents]
        return self._model.encode(documents).tolist()

    def embed_query(self, query: str) -> list[float]:
        if self._model is None:
            return self._mock_embed(query)
        return self._model.encode([query])[0].tolist()

    @staticmethod
    def _mock_embed(text: str) -> list[float]:
        import hashlib
        hash_bytes = hashlib.md5(text.encode()).digest()
        return [float(b) / 255.0 for b in hash_bytes] + [0.0] * (384 - 16)


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    """获取 Embedding 提供者（单例）"""
    return LocalSentenceTransformerEmbedding(
        model_name=settings.embedding_model
    )
