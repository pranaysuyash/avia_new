"""
Visual Search and Content Discovery Module
Implements Task 38: Build visual search and content discovery
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
import time
from collections import defaultdict
import streamlit as st
from sentence_transformers import SentenceTransformer
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import faiss
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import umap

logger = logging.getLogger(__name__)


@dataclass
class ContentItem:
    """Represents a piece of content for visual search"""
    id: str
    title: str
    transcript: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    timestamp: float
    duration: float
    file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None


@dataclass
class SearchResult:
    """Search result with similarity score"""
    content_item: ContentItem
    similarity_score: float
    relevance_explanation: str


@dataclass
class ContentCluster:
    """Cluster of similar content"""
    id: str
    name: str
    items: List[ContentItem]
    centroid: np.ndarray
    topics: List[str]
    summary: str


class EmbeddingGenerator:
    """Generates embeddings for text content"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            # Fallback to a smaller model
            try:
                self.model = SentenceTransformer("all-MiniLM-L12-v2")
                logger.info("Loaded fallback embedding model")
            except Exception as e2:
                logger.error(f"Failed to load fallback model: {e2}")
                raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        try:
            # Clean and prepare text
            cleaned_text = self._clean_text(text)
            
            # Generate embedding
            embedding = self.model.encode(cleaned_text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(384)  # Default dimension for MiniLM
    
    def generate_batch_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        try:
            cleaned_texts = [self._clean_text(text) for text in texts]
            embeddings = self.model.encode(cleaned_texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            # Return zero vectors as fallback
            return np.zeros((len(texts), 384))
    
    def _clean_text(self, text: str) -> str:
        """Clean text for embedding generation"""
        if not text:
            return ""
        
        # Basic cleaning
        text = text.strip()
        text = ' '.join(text.split())  # Normalize whitespace
        
        # Truncate if too long (models have token limits)
        max_length = 500  # Approximate token limit
        if len(text) > max_length:
            text = text[:max_length]
        
        return text


class VisualSearchEngine:
    """Main visual search engine"""
    
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.content_items: List[ContentItem] = []
        self.index = None
        self.clusters: List[ContentCluster] = []
        self._build_index()
    
    def add_content(self, content_item: ContentItem):
        """Add content item to search index"""
        self.content_items.append(content_item)
        self._rebuild_index()
    
    def add_transcript(self, transcript_id: str, title: str, transcript: str, 
                      metadata: Dict[str, Any] = None) -> ContentItem:
        """Add transcript to search index"""
        if metadata is None:
            metadata = {}
        
        # Generate embedding
        embedding = self.embedding_generator.generate_embedding(transcript)
        
        # Create content item
        content_item = ContentItem(
            id=transcript_id,
            title=title,
            transcript=transcript,
            embedding=embedding,
            metadata=metadata,
            timestamp=time.time(),
            duration=metadata.get('duration', 0),
            file_path=metadata.get('file_path'),
            thumbnail_path=metadata.get('thumbnail_path')
        )
        
        self.add_content(content_item)
        return content_item
    
    def search_by_text(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search for similar content by text query"""
        if not self.content_items:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        # Search using FAISS index
        if self.index is None:
            self._build_index()
        
        # Perform search
        similarities, indices = self.index.search(
            query_embedding.reshape(1, -1).astype('float32'), 
            min(top_k, len(self.content_items))
        )
        
        # Create search results
        results = []
        for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            if idx < len(self.content_items):
                content_item = self.content_items[idx]
                
                # Generate relevance explanation
                explanation = self._generate_relevance_explanation(query, content_item)
                
                results.append(SearchResult(
                    content_item=content_item,
                    similarity_score=float(similarity),
                    relevance_explanation=explanation
                ))
        
        return results
    
    def search_by_content(self, content_item: ContentItem, top_k: int = 10) -> List[SearchResult]:
        """Search for similar content by existing content item"""
        if not self.content_items or self.index is None:
            return []
        
        # Search using the content item's embedding
        similarities, indices = self.index.search(
            content_item.embedding.reshape(1, -1).astype('float32'),
            min(top_k + 1, len(self.content_items))  # +1 to exclude self
        )
        
        # Create search results (excluding the input item itself)
        results = []
        for similarity, idx in zip(similarities[0], indices[0]):
            if idx < len(self.content_items):
                similar_item = self.content_items[idx]
                
                # Skip if it's the same item
                if similar_item.id == content_item.id:
                    continue
                
                explanation = f"Similar content based on semantic similarity"
                
                results.append(SearchResult(
                    content_item=similar_item,
                    similarity_score=float(similarity),
                    relevance_explanation=explanation
                ))
                
                if len(results) >= top_k:
                    break
        
        return results
    
    def get_content_clusters(self, n_clusters: int = 5) -> List[ContentCluster]:
        """Generate content clusters using K-means"""
        if len(self.content_items) < n_clusters:
            n_clusters = max(1, len(self.content_items))
        
        # Get embeddings
        embeddings = np.array([item.embedding for item in self.content_items])
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Create clusters
        clusters = []
        for cluster_id in range(n_clusters):
            # Get items in this cluster
            cluster_items = [
                item for i, item in enumerate(self.content_items)
                if cluster_labels[i] == cluster_id
            ]
            
            if not cluster_items:
                continue
            
            # Generate cluster summary
            cluster_topics = self._extract_cluster_topics(cluster_items)
            cluster_summary = self._generate_cluster_summary(cluster_items)
            
            cluster = ContentCluster(
                id=f"cluster_{cluster_id}",
                name=f"Topic Cluster {cluster_id + 1}",
                items=cluster_items,
                centroid=kmeans.cluster_centers_[cluster_id],
                topics=cluster_topics,
                summary=cluster_summary
            )
            
            clusters.append(cluster)
        
        self.clusters = clusters
        return clusters
    
    def get_content_map_data(self, method: str = "tsne") -> Dict[str, Any]:
        """Generate data for content visualization map"""
        if not self.content_items:
            return {}
        
        # Get embeddings
        embeddings = np.array([item.embedding for item in self.content_items])
        
        # Reduce dimensionality
        if method == "tsne":
            reducer = TSNE(n_components=2, random_state=42, perplexity=min(30, len(self.content_items) - 1))
        elif method == "pca":
            reducer = PCA(n_components=2, random_state=42)
        elif method == "umap":
            reducer = umap.UMAP(n_components=2, random_state=42)
        else:
            raise ValueError(f"Unknown dimensionality reduction method: {method}")
        
        # Fit and transform
        coords_2d = reducer.fit_transform(embeddings)
        
        # Prepare data
        map_data = {
            'x': coords_2d[:, 0].tolist(),
            'y': coords_2d[:, 1].tolist(),
            'titles': [item.title for item in self.content_items],
            'ids': [item.id for item in self.content_items],
            'transcripts': [item.transcript[:200] + "..." if len(item.transcript) > 200 else item.transcript for item in self.content_items],
            'durations': [item.duration for item in self.content_items],
            'timestamps': [item.timestamp for item in self.content_items]
        }
        
        # Add cluster information if available
        if self.clusters:
            cluster_labels = []
            cluster_colors = []
            
            for item in self.content_items:
                # Find which cluster this item belongs to
                item_cluster = None
                for cluster in self.clusters:
                    if any(cluster_item.id == item.id for cluster_item in cluster.items):
                        item_cluster = cluster
                        break
                
                if item_cluster:
                    cluster_labels.append(item_cluster.name)
                    cluster_colors.append(hash(item_cluster.id) % 10)  # Simple color mapping
                else:
                    cluster_labels.append("Unclustered")
                    cluster_colors.append(0)
            
            map_data['cluster_labels'] = cluster_labels
            map_data['cluster_colors'] = cluster_colors
        
        return map_data
    
    def _build_index(self):
        """Build FAISS index for fast similarity search"""
        if not self.content_items:
            return
        
        # Get embeddings
        embeddings = np.array([item.embedding for item in self.content_items])
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings.astype('float32'))
        
        # Add to index
        self.index.add(embeddings.astype('float32'))
        
        logger.info(f"Built FAISS index with {len(self.content_items)} items")
    
    def _rebuild_index(self):
        """Rebuild the search index"""
        self._build_index()
    
    def _generate_relevance_explanation(self, query: str, content_item: ContentItem) -> str:
        """Generate explanation for why content is relevant"""
        # Simple keyword-based explanation
        query_words = set(query.lower().split())
        content_words = set(content_item.transcript.lower().split())
        
        common_words = query_words.intersection(content_words)
        
        if common_words:
            return f"Contains keywords: {', '.join(list(common_words)[:3])}"
        else:
            return "Semantically similar content"
    
    def _extract_cluster_topics(self, cluster_items: List[ContentItem]) -> List[str]:
        """Extract main topics from cluster items"""
        # Simple frequency-based topic extraction
        word_freq = defaultdict(int)
        
        for item in cluster_items:
            words = item.transcript.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_freq[word] += 1
        
        # Get top words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return [word for word, freq in top_words]
    
    def _generate_cluster_summary(self, cluster_items: List[ContentItem]) -> str:
        """Generate summary for cluster"""
        if not cluster_items:
            return "Empty cluster"
        
        # Simple summary based on titles and topics
        titles = [item.title for item in cluster_items]
        return f"Cluster of {len(cluster_items)} items including: {', '.join(titles[:3])}"


class ContentTimelineGenerator:
    """Generates visual timeline of content"""
    
    def __init__(self, search_engine: VisualSearchEngine):
        self.search_engine = search_engine
    
    def generate_timeline_data(self, time_granularity: str = "day") -> Dict[str, Any]:
        """Generate timeline data for visualization"""
        if not self.search_engine.content_items:
            return {}
        
        # Group content by time
        timeline_data = defaultdict(list)
        
        for item in self.search_engine.content_items:
            # Convert timestamp to appropriate granularity
            if time_granularity == "hour":
                time_key = pd.Timestamp(item.timestamp, unit='s').floor('H')
            elif time_granularity == "day":
                time_key = pd.Timestamp(item.timestamp, unit='s').floor('D')
            elif time_granularity == "week":
                time_key = pd.Timestamp(item.timestamp, unit='s').floor('W')
            elif time_granularity == "month":
                time_key = pd.Timestamp(item.timestamp, unit='s').floor('M')
            else:
                time_key = pd.Timestamp(item.timestamp, unit='s').floor('D')
            
            timeline_data[time_key].append(item)
        
        # Prepare visualization data
        dates = []
        content_counts = []
        total_durations = []
        sample_titles = []
        
        for date, items in sorted(timeline_data.items()):
            dates.append(date)
            content_counts.append(len(items))
            total_durations.append(sum(item.duration for item in items))
            sample_titles.append(", ".join([item.title for item in items[:3]]))
        
        return {
            'dates': dates,
            'content_counts': content_counts,
            'total_durations': total_durations,
            'sample_titles': sample_titles
        }
    
    def generate_content_density_map(self) -> Dict[str, Any]:
        """Generate content density visualization data"""
        if not self.search_engine.content_items:
            return {}
        
        # Create density map based on content similarity
        embeddings = np.array([item.embedding for item in self.search_engine.content_items])
        
        # Use t-SNE for 2D projection
        tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(embeddings) - 1))
        coords_2d = tsne.fit_transform(embeddings)
        
        # Calculate density using KDE-like approach
        from scipy.spatial.distance import pdist, squareform
        
        # Calculate pairwise distances
        distances = squareform(pdist(coords_2d))
        
        # Calculate density for each point
        densities = []
        for i in range(len(coords_2d)):
            # Count neighbors within a certain radius
            radius = np.percentile(distances[i], 20)  # 20th percentile as radius
            neighbors = np.sum(distances[i] < radius)
            densities.append(neighbors)
        
        return {
            'x': coords_2d[:, 0].tolist(),
            'y': coords_2d[:, 1].tolist(),
            'densities': densities,
            'titles': [item.title for item in self.search_engine.content_items],
            'ids': [item.id for item in self.search_engine.content_items]
        }


# Global instance
visual_search_engine = VisualSearchEngine()
timeline_generator = ContentTimelineGenerator(visual_search_engine)