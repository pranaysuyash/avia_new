"""
Embedding generation and management for semantic search
"""

import logging
from typing import List, Dict, Any, Optional, Protocol
from abc import abstractmethod
import numpy as np
from pathlib import Path
import json
import hashlib

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers"""
    
    @abstractmethod
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the embedding model"""
        pass


class EmbeddingManager:
    """Manages embedding generation with caching"""
    
    def __init__(self, 
                 provider: EmbeddingProvider,
                 cache_dir: str = "cache/embeddings"):
        self.provider = provider
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._embedding_cache = {}
        
    def get_embeddings(self, texts: List[str], use_cache: bool = True) -> np.ndarray:
        """
        Get embeddings for texts with optional caching
        
        Args:
            texts: List of text strings
            use_cache: Whether to use cached embeddings
            
        Returns:
            numpy array of embeddings
        """
        if not texts:
            return np.array([])
            
        # Check cache first
        embeddings = []
        texts_to_generate = []
        text_indices = []
        
        for i, text in enumerate(texts):
            if use_cache:
                cache_key = self._get_cache_key(text)
                
                # Check in-memory cache
                if cache_key in self._embedding_cache:
                    embeddings.append(self._embedding_cache[cache_key])
                    continue
                    
                # Check disk cache
                cached = self._load_cached_embedding(cache_key)
                if cached is not None:
                    self._embedding_cache[cache_key] = cached
                    embeddings.append(cached)
                    continue
            
            texts_to_generate.append(text)
            text_indices.append(i)
        
        # Generate new embeddings
        if texts_to_generate:
            logger.info(f"Generating embeddings for {len(texts_to_generate)} texts")
            new_embeddings = self.provider.generate_embeddings(texts_to_generate)
            
            # Cache the new embeddings
            for j, (text, embedding) in enumerate(zip(texts_to_generate, new_embeddings)):
                cache_key = self._get_cache_key(text)
                self._embedding_cache[cache_key] = embedding
                
                if use_cache:
                    self._save_cached_embedding(cache_key, embedding)
        
        # Reconstruct full embedding array in correct order
        result = np.zeros((len(texts), self.provider.get_embedding_dimension()))
        
        embedding_idx = 0
        new_embedding_idx = 0
        
        for i in range(len(texts)):
            if i in text_indices:
                result[i] = new_embeddings[new_embedding_idx]
                new_embedding_idx += 1
            else:
                result[i] = embeddings[embedding_idx]
                embedding_idx += 1
                
        return result
    
    def get_embedding(self, text: str, use_cache: bool = True) -> np.ndarray:
        """Get embedding for a single text"""
        embeddings = self.get_embeddings([text], use_cache)
        return embeddings[0] if len(embeddings) > 0 else None
    
    def precompute_embeddings(self, texts: List[str], batch_size: int = 100):
        """
        Precompute and cache embeddings for a list of texts
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
        """
        logger.info(f"Precomputing embeddings for {len(texts)} texts")
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            self.get_embeddings(batch, use_cache=True)
            logger.info(f"Processed {min(i + batch_size, len(texts))}/{len(texts)} texts")
    
    def clear_cache(self):
        """Clear the embedding cache"""
        self._embedding_cache.clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.npy"):
            cache_file.unlink()
            
        logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        disk_files = list(self.cache_dir.glob("*.npy"))
        
        return {
            "memory_cache_size": len(self._embedding_cache),
            "disk_cache_size": len(disk_files),
            "cache_directory": str(self.cache_dir),
            "embedding_dimension": self.provider.get_embedding_dimension(),
            "model_name": self.provider.get_model_name()
        }
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        # Include model name in cache key
        model_name = self.provider.get_model_name()
        key_string = f"{model_name}:{text}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _load_cached_embedding(self, cache_key: str) -> Optional[np.ndarray]:
        """Load embedding from disk cache"""
        cache_file = self.cache_dir / f"{cache_key}.npy"
        
        if cache_file.exists():
            try:
                return np.load(cache_file)
            except Exception as e:
                logger.warning(f"Failed to load cached embedding: {e}")
                return None
                
        return None
    
    def _save_cached_embedding(self, cache_key: str, embedding: np.ndarray):
        """Save embedding to disk cache"""
        cache_file = self.cache_dir / f"{cache_key}.npy"
        
        try:
            np.save(cache_file, embedding)
        except Exception as e:
            logger.warning(f"Failed to save embedding to cache: {e}")
    
    def compute_similarity(self, 
                          embedding1: np.ndarray, 
                          embedding2: np.ndarray,
                          metric: str = "cosine") -> float:
        """
        Compute similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            metric: Similarity metric (cosine, euclidean, dot)
            
        Returns:
            Similarity score
        """
        if metric == "cosine":
            # Cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            return float(dot_product / (norm1 * norm2))
            
        elif metric == "euclidean":
            # Negative euclidean distance (higher is more similar)
            return float(-np.linalg.norm(embedding1 - embedding2))
            
        elif metric == "dot":
            # Dot product
            return float(np.dot(embedding1, embedding2))
            
        else:
            raise ValueError(f"Unknown similarity metric: {metric}")
    
    def find_similar(self,
                    query_embedding: np.ndarray,
                    embeddings: np.ndarray,
                    top_k: int = 10,
                    metric: str = "cosine") -> List[tuple]:
        """
        Find most similar embeddings to query
        
        Args:
            query_embedding: Query embedding
            embeddings: Array of embeddings to search
            top_k: Number of results to return
            metric: Similarity metric
            
        Returns:
            List of (index, similarity_score) tuples
        """
        if len(embeddings) == 0:
            return []
            
        similarities = []
        
        for i, embedding in enumerate(embeddings):
            similarity = self.compute_similarity(query_embedding, embedding, metric)
            similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]