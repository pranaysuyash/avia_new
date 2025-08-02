"""
Semantic search functionality for AI-powered content discovery
"""

from .embeddings import EmbeddingManager, EmbeddingProvider
from .vector_store import create_vector_store, VectorStore, FAISSVectorStore, QdrantVectorStore, ChromaVectorStore
from .semantic_engine import SemanticSearchEngine
from .providers import (
    OpenAIEmbeddingProvider,
    SentenceTransformerProvider,
    MockEmbeddingProvider
)

__all__ = [
    'SemanticSearchEngine',
    'EmbeddingManager',
    'EmbeddingProvider',
    'VectorStore',
    'ChromaStore',
    'FaissStore',
    'OpenAIEmbeddingProvider',
    'SentenceTransformerProvider',
    'MockEmbeddingProvider'
]