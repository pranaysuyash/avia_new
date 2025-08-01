"""
Embedding providers for different AI services
"""

import logging
import openai
import numpy as np
from typing import List, Optional
import time
from sentence_transformers import SentenceTransformer
import os

from .embeddings import EmbeddingProvider

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider using text-embedding-ada-002"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "text-embedding-ada-002",
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.dimension = 1536  # Ada-002 embedding dimension
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
            
        # Set up OpenAI client
        openai.api_key = self.api_key
        
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        if not texts:
            return np.array([])
            
        # Clean and prepare texts
        cleaned_texts = [self._clean_text(text) for text in texts]
        
        # Process in batches to avoid rate limits
        batch_size = 100  # OpenAI recommended batch size
        all_embeddings = []
        
        for i in range(0, len(cleaned_texts), batch_size):
            batch = cleaned_texts[i:i + batch_size]
            batch_embeddings = self._generate_batch_embeddings(batch)
            all_embeddings.extend(batch_embeddings)
            
            # Add small delay between batches
            if i + batch_size < len(cleaned_texts):
                time.sleep(0.1)
        
        return np.array(all_embeddings)
    
    def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = openai.Embedding.create(
                    input=texts,
                    model=self.model
                )
                
                # Extract embeddings from response
                embeddings = [item['embedding'] for item in response['data']]
                
                logger.info(f"Generated {len(embeddings)} embeddings using {self.model}")
                return embeddings
                
            except openai.error.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise e
                    
            except openai.error.APIError as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"API error, retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    raise e
                    
            except Exception as e:
                logger.error(f"Unexpected error generating embeddings: {e}")
                raise e
    
    def _clean_text(self, text: str) -> str:
        """Clean text for embedding generation"""
        if not text:
            return ""
            
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Truncate if too long (OpenAI has token limits)
        max_tokens = 8000  # Conservative limit
        if len(text.split()) > max_tokens:
            text = ' '.join(text.split()[:max_tokens])
            
        return text
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.dimension
    
    def get_model_name(self) -> str:
        """Get the name of the embedding model"""
        return self.model


class SentenceTransformerProvider(EmbeddingProvider):
    """Local sentence transformer provider for offline embeddings"""
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        
        try:
            self.model = SentenceTransformer(model_name, device=device)
            self.dimension = self.model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model {model_name}: {e}")
            raise e
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using sentence transformers"""
        if not texts:
            return np.array([])
            
        try:
            # Clean texts
            cleaned_texts = [self._clean_text(text) for text in texts]
            
            # Generate embeddings
            embeddings = self.model.encode(
                cleaned_texts,
                convert_to_numpy=True,
                show_progress_bar=len(cleaned_texts) > 10
            )
            
            logger.info(f"Generated {len(embeddings)} embeddings using {self.model_name}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings with SentenceTransformer: {e}")
            raise e
    
    def _clean_text(self, text: str) -> str:
        """Clean text for embedding generation"""
        if not text:
            return ""
            
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Truncate if too long
        max_length = 512  # Most sentence transformers have this limit
        if len(text) > max_length:
            text = text[:max_length]
            
        return text
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.dimension
    
    def get_model_name(self) -> str:
        """Get the name of the embedding model"""
        return self.model_name


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock provider for testing"""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.model_name = "mock-embeddings"
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate random embeddings for testing"""
        if not texts:
            return np.array([])
            
        # Generate random normalized embeddings
        embeddings = np.random.randn(len(texts), self.dimension)
        
        # Normalize to unit vectors
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.dimension
    
    def get_model_name(self) -> str:
        """Get the name of the embedding model"""
        return self.model_name