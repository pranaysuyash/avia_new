"""
Vector store implementations for efficient similarity search
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Protocol
from abc import abstractmethod
import json
import pickle
from pathlib import Path
import sqlite3
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """Result from vector similarity search"""
    id: str
    score: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VectorStore(Protocol):
    """Protocol for vector store implementations"""
    
    @abstractmethod
    def add_vectors(self, 
                   ids: List[str], 
                   vectors: np.ndarray, 
                   metadata: List[Dict[str, Any]] = None) -> bool:
        """Add vectors to the store"""
        pass
    
    @abstractmethod
    def search(self, 
              query_vector: np.ndarray, 
              k: int = 10,
              filter_dict: Dict[str, Any] = None) -> List[VectorSearchResult]:
        """Search for similar vectors"""
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """Delete vectors by IDs"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics"""
        pass


class FAISSVectorStore:
    """FAISS-based vector store for efficient similarity search"""
    
    def __init__(self, 
                 dimension: int,
                 index_path: str = "cache/vector_index",
                 metadata_db_path: str = "cache/vector_metadata.db"):
        self.dimension = dimension
        self.index_path = Path(index_path)
        self.metadata_db_path = metadata_db_path
        
        # Create cache directory
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize FAISS index
        self.index = None
        self.id_to_index = {}  # Map document IDs to FAISS indices
        self.index_to_id = {}  # Map FAISS indices to document IDs
        
        # Initialize metadata database
        self._init_metadata_db()
        
        # Load existing index if available
        self._load_index()
    
    def _init_metadata_db(self):
        """Initialize SQLite database for metadata"""
        with sqlite3.connect(self.metadata_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vector_metadata (
                    id TEXT PRIMARY KEY,
                    faiss_index INTEGER,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_faiss_index ON vector_metadata(faiss_index)")
            conn.commit()
    
    def _load_index(self):
        """Load existing FAISS index"""
        try:
            import faiss
            
            index_file = self.index_path.with_suffix('.faiss')
            mapping_file = self.index_path.with_suffix('.pkl')
            
            if index_file.exists() and mapping_file.exists():
                # Load FAISS index
                self.index = faiss.read_index(str(index_file))
                
                # Load ID mappings
                with open(mapping_file, 'rb') as f:
                    mappings = pickle.load(f)
                    self.id_to_index = mappings['id_to_index']
                    self.index_to_id = mappings['index_to_id']
                
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            else:
                # Create new index
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
                logger.info(f"Created new FAISS index with dimension {self.dimension}")
                
        except ImportError:
            logger.error("FAISS not installed. Install with: pip install faiss-cpu")
            raise
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            # Create new index as fallback
            import faiss
            self.index = faiss.IndexFlatIP(self.dimension)
    
    def _save_index(self):
        """Save FAISS index and mappings"""
        try:
            import faiss
            
            index_file = self.index_path.with_suffix('.faiss')
            mapping_file = self.index_path.with_suffix('.pkl')
            
            # Save FAISS index
            faiss.write_index(self.index, str(index_file))
            
            # Save ID mappings
            mappings = {
                'id_to_index': self.id_to_index,
                'index_to_id': self.index_to_id
            }
            
            with open(mapping_file, 'wb') as f:
                pickle.dump(mappings, f)
            
            logger.info(f"Saved FAISS index with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
    
    def add_vectors(self, 
                   ids: List[str], 
                   vectors: np.ndarray, 
                   metadata: List[Dict[str, Any]] = None) -> bool:
        """Add vectors to the FAISS index"""
        try:
            if len(ids) != len(vectors):
                raise ValueError("Number of IDs must match number of vectors")
            
            if vectors.shape[1] != self.dimension:
                raise ValueError(f"Vector dimension {vectors.shape[1]} doesn't match index dimension {self.dimension}")
            
            # Normalize vectors for cosine similarity
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            normalized_vectors = vectors / norms
            
            # Add to FAISS index
            start_index = self.index.ntotal
            self.index.add(normalized_vectors.astype(np.float32))
            
            # Update ID mappings
            for i, doc_id in enumerate(ids):
                faiss_index = start_index + i
                self.id_to_index[doc_id] = faiss_index
                self.index_to_id[faiss_index] = doc_id
            
            # Store metadata in database
            if metadata is None:
                metadata = [{}] * len(ids)
            
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                
                for i, doc_id in enumerate(ids):
                    faiss_index = start_index + i
                    cursor.execute("""
                        INSERT OR REPLACE INTO vector_metadata (id, faiss_index, metadata)
                        VALUES (?, ?, ?)
                    """, (doc_id, faiss_index, json.dumps(metadata[i])))
                
                conn.commit()
            
            # Save index
            self._save_index()
            
            logger.info(f"Added {len(ids)} vectors to FAISS index")
            return True
            
        except Exception as e:
            logger.error(f"Error adding vectors to FAISS: {e}")
            return False
    
    def search(self, 
              query_vector: np.ndarray, 
              k: int = 10,
              filter_dict: Dict[str, Any] = None) -> List[VectorSearchResult]:
        """Search for similar vectors"""
        try:
            if self.index.ntotal == 0:
                return []
            
            # Normalize query vector
            query_norm = np.linalg.norm(query_vector)
            if query_norm > 0:
                normalized_query = (query_vector / query_norm).astype(np.float32).reshape(1, -1)
            else:
                return []
            
            # Search in FAISS
            scores, indices = self.index.search(normalized_query, min(k * 2, self.index.ntotal))
            
            # Convert results
            results = []
            
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                
                for score, faiss_idx in zip(scores[0], indices[0]):
                    if faiss_idx == -1:  # FAISS returns -1 for invalid indices
                        continue
                    
                    # Get document ID
                    doc_id = self.index_to_id.get(faiss_idx)
                    if not doc_id:
                        continue
                    
                    # Get metadata
                    cursor.execute("SELECT metadata FROM vector_metadata WHERE id = ?", (doc_id,))
                    metadata_row = cursor.fetchone()
                    metadata = json.loads(metadata_row[0]) if metadata_row and metadata_row[0] else {}
                    
                    # Apply filters if specified
                    if filter_dict and not self._matches_filter(metadata, filter_dict):
                        continue
                    
                    results.append(VectorSearchResult(
                        id=doc_id,
                        score=float(score),
                        metadata=metadata
                    ))
                    
                    if len(results) >= k:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            return []
    
    def delete(self, ids: List[str]) -> bool:
        """Delete vectors by IDs (FAISS doesn't support deletion, so we rebuild)"""
        try:
            if not ids:
                return True
            
            # Get all current vectors except the ones to delete
            remaining_ids = []
            remaining_vectors = []
            remaining_metadata = []
            
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, faiss_index, metadata FROM vector_metadata")
                
                for doc_id, faiss_idx, metadata_json in cursor.fetchall():
                    if doc_id not in ids:
                        # Get vector from FAISS
                        vector = self.index.reconstruct(faiss_idx)
                        remaining_ids.append(doc_id)
                        remaining_vectors.append(vector)
                        remaining_metadata.append(json.loads(metadata_json) if metadata_json else {})
                
                # Delete from metadata database
                cursor.executemany("DELETE FROM vector_metadata WHERE id = ?", [(id,) for id in ids])
                conn.commit()
            
            # Rebuild FAISS index
            import faiss
            self.index = faiss.IndexFlatIP(self.dimension)
            self.id_to_index = {}
            self.index_to_id = {}
            
            if remaining_vectors:
                remaining_vectors = np.array(remaining_vectors)
                self.add_vectors(remaining_ids, remaining_vectors, remaining_metadata)
            
            logger.info(f"Deleted {len(ids)} vectors from FAISS index")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vectors from FAISS: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM vector_metadata")
                metadata_count = cursor.fetchone()[0]
            
            return {
                'total_vectors': self.index.ntotal if self.index else 0,
                'metadata_entries': metadata_count,
                'dimension': self.dimension,
                'index_type': 'FAISS IndexFlatIP',
                'index_path': str(self.index_path)
            }
            
        except Exception as e:
            logger.error(f"Error getting FAISS stats: {e}")
            return {}
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria"""
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
            
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        
        return True


class QdrantVectorStore:
    """Qdrant-based vector store (requires qdrant-client)"""
    
    def __init__(self, 
                 dimension: int,
                 collection_name: str = "transcripts",
                 host: str = "localhost",
                 port: int = 6333):
        self.dimension = dimension
        self.collection_name = collection_name
        self.host = host
        self.port = port
        
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            self.client = QdrantClient(host=host, port=port)
            
            # Create collection if it doesn't exist
            try:
                self.client.get_collection(collection_name)
                logger.info(f"Connected to existing Qdrant collection: {collection_name}")
            except:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
                )
                logger.info(f"Created new Qdrant collection: {collection_name}")
                
        except ImportError:
            raise ImportError("Qdrant client not installed. Install with: pip install qdrant-client")
        except Exception as e:
            logger.error(f"Error connecting to Qdrant: {e}")
            raise
    
    def add_vectors(self, 
                   ids: List[str], 
                   vectors: np.ndarray, 
                   metadata: List[Dict[str, Any]] = None) -> bool:
        """Add vectors to Qdrant"""
        try:
            from qdrant_client.models import PointStruct
            
            if metadata is None:
                metadata = [{}] * len(ids)
            
            points = []
            for i, (doc_id, vector) in enumerate(zip(ids, vectors)):
                points.append(PointStruct(
                    id=doc_id,
                    vector=vector.tolist(),
                    payload=metadata[i]
                ))
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(ids)} vectors to Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Error adding vectors to Qdrant: {e}")
            return False
    
    def search(self, 
              query_vector: np.ndarray, 
              k: int = 10,
              filter_dict: Dict[str, Any] = None) -> List[VectorSearchResult]:
        """Search for similar vectors in Qdrant"""
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Build filter
            query_filter = None
            if filter_dict:
                conditions = []
                for key, value in filter_dict.items():
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
                
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                limit=k,
                query_filter=query_filter
            )
            
            # Convert results
            results = []
            for result in search_results:
                results.append(VectorSearchResult(
                    id=str(result.id),
                    score=result.score,
                    metadata=result.payload or {}
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []
    
    def delete(self, ids: List[str]) -> bool:
        """Delete vectors from Qdrant"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=ids
            )
            
            logger.info(f"Deleted {len(ids)} vectors from Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vectors from Qdrant: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Qdrant collection statistics"""
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                'total_vectors': info.points_count,
                'dimension': self.dimension,
                'index_type': 'Qdrant',
                'collection_name': self.collection_name,
                'host': self.host,
                'port': self.port
            }
            
        except Exception as e:
            logger.error(f"Error getting Qdrant stats: {e}")
            return {}


class ChromaVectorStore:
    """ChromaDB-based vector store"""
    
    def __init__(self, 
                 dimension: int,
                 collection_name: str = "transcripts",
                 persist_directory: str = "cache/chroma"):
        self.dimension = dimension
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        try:
            import chromadb
            
            self.client = chromadb.PersistentClient(path=persist_directory)
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(collection_name)
                logger.info(f"Connected to existing Chroma collection: {collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"dimension": dimension}
                )
                logger.info(f"Created new Chroma collection: {collection_name}")
                
        except ImportError:
            raise ImportError("ChromaDB not installed. Install with: pip install chromadb")
        except Exception as e:
            logger.error(f"Error connecting to ChromaDB: {e}")
            raise
    
    def add_vectors(self, 
                   ids: List[str], 
                   vectors: np.ndarray, 
                   metadata: List[Dict[str, Any]] = None) -> bool:
        """Add vectors to ChromaDB"""
        try:
            if metadata is None:
                metadata = [{}] * len(ids)
            
            self.collection.upsert(
                ids=ids,
                embeddings=vectors.tolist(),
                metadatas=metadata
            )
            
            logger.info(f"Added {len(ids)} vectors to ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Error adding vectors to ChromaDB: {e}")
            return False
    
    def search(self, 
              query_vector: np.ndarray, 
              k: int = 10,
              filter_dict: Dict[str, Any] = None) -> List[VectorSearchResult]:
        """Search for similar vectors in ChromaDB"""
        try:
            # ChromaDB query
            results = self.collection.query(
                query_embeddings=[query_vector.tolist()],
                n_results=k,
                where=filter_dict
            )
            
            # Convert results
            search_results = []
            
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    score = 1.0 - results['distances'][0][i]  # Convert distance to similarity
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    
                    search_results.append(VectorSearchResult(
                        id=doc_id,
                        score=score,
                        metadata=metadata
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}")
            return []
    
    def delete(self, ids: List[str]) -> bool:
        """Delete vectors from ChromaDB"""
        try:
            self.collection.delete(ids=ids)
            
            logger.info(f"Deleted {len(ids)} vectors from ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vectors from ChromaDB: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ChromaDB collection statistics"""
        try:
            count = self.collection.count()
            
            return {
                'total_vectors': count,
                'dimension': self.dimension,
                'index_type': 'ChromaDB',
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Error getting ChromaDB stats: {e}")
            return {}


def create_vector_store(store_type: str = "faiss", 
                       dimension: int = 384,
                       **kwargs) -> VectorStore:
    """Factory function to create vector store instances"""
    
    if store_type.lower() == "faiss":
        return FAISSVectorStore(dimension=dimension, **kwargs)
    elif store_type.lower() == "qdrant":
        return QdrantVectorStore(dimension=dimension, **kwargs)
    elif store_type.lower() == "chroma":
        return ChromaVectorStore(dimension=dimension, **kwargs)
    else:
        raise ValueError(f"Unknown vector store type: {store_type}")