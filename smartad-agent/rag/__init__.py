"""
SmartAD RAG 模块
- embedding: Embedding 模型
- vector_store: Chroma 向量存储
- retriever: 知识检索器
- knowledge: 结构化知识数据
- prompt_builder: Prompt 构建（RAG 增强）
"""
from rag.embedding import EmbeddingProvider, get_embedding_provider
from rag.vector_store import VectorStore, get_vector_store
from rag.retriever import KnowledgeRetriever, get_retriever
from rag.knowledge import (
    CROWD_DATABASE, CHANNEL_DATABASE,
    CROWD_KNOWLEDGE, CHANNEL_KNOWLEDGE, STRATEGY_RULES,
)

__all__ = [
    "EmbeddingProvider", "get_embedding_provider",
    "VectorStore", "get_vector_store",
    "KnowledgeRetriever", "get_retriever",
    "CROWD_DATABASE", "CHANNEL_DATABASE",
    "CROWD_KNOWLEDGE", "CHANNEL_KNOWLEDGE", "STRATEGY_RULES",
]
