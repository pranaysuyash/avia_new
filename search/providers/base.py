"""
Base search provider interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

@dataclass
class SearchDocument:
    """Standard document representation for search providers"""
    doc_id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'doc_id': self.doc_id,
            'title': self.title,
            'content': self.content,
            'metadata': self.metadata
        }

class BaseSearchProvider(ABC):
    """Abstract base class for search providers"""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]):
        """Initialize the search provider with configuration"""
        pass
    
    @abstractmethod
    def index_document(self, document: SearchDocument):
        """Index a single document"""
        pass
    
    @abstractmethod
    def index_batch(self, documents: List[SearchDocument]):
        """Index multiple documents efficiently"""
        pass
    
    @abstractmethod
    def search(self, 
               query: str,
               filters: Dict[str, Any] = None,
               limit: int = 50,
               offset: int = 0,
               highlight: bool = True) -> Tuple[List[Dict], int]:
        """
        Search documents
        
        Returns: (results, total_count)
        """
        pass
    
    @abstractmethod
    def delete_document(self, doc_id: str):
        """Delete a document from the index"""
        pass
    
    @abstractmethod
    def clear_index(self):
        """Clear all documents from the index"""
        pass
    
    @abstractmethod
    def close(self):
        """Close the search provider and cleanup resources"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics (optional)"""
        return {}
    
    def optimize_index(self):
        """Optimize the search index (optional)"""
        pass