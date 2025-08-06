#!/usr/bin/env python3
"""
Conversational Query Bot for Media Libraries
Advanced RAG (Retrieval Augmented Generation) system for natural language querying
of transcripts, documents, and media content with timestamp citations.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import openai
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MediaContent:
    """Represents a piece of media content with metadata"""
    id: str
    title: str
    content_type: str  # 'transcript', 'document', 'image_text', 'video'
    text_content: str
    timestamp: Optional[float] = None
    speaker: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class QueryResult:
    """Represents a query result with relevance and citations"""
    content: MediaContent
    relevance_score: float
    snippet: str
    timestamp_citation: Optional[str] = None
    context_window: Optional[str] = None

@dataclass
class ConversationContext:
    """Maintains conversation context for follow-up queries"""
    conversation_id: str
    query_history: List[str]
    result_history: List[List[QueryResult]]
    context_embeddings: Optional[np.ndarray] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class EmbeddingManager:
    """Manages text embeddings for semantic search"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding model"""
        try:
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded embedding model: {model_name} (dim: {self.dimension})")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            # Fallback to mock embeddings for testing
            self.model = None
            self.dimension = 384
    
    def encode_text(self, text: str) -> np.ndarray:
        """Generate embeddings for text"""
        if self.model is None:
            # Mock embedding for testing
            return np.random.random(self.dimension).astype(np.float32)
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            return np.random.random(self.dimension).astype(np.float32)
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        if self.model is None:
            # Mock embeddings for testing
            return np.random.random((len(texts), self.dimension)).astype(np.float32)
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.error(f"Failed to encode batch: {e}")
            return np.random.random((len(texts), self.dimension)).astype(np.float32)

class VectorDatabase:
    """FAISS-based vector database for similarity search"""
    
    def __init__(self, dimension: int = 384):
        """Initialize vector database"""
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        self.content_map: Dict[int, MediaContent] = {}
        self.next_id = 0
        
    def add_content(self, content: MediaContent, embedding: np.ndarray) -> int:
        """Add content with its embedding to the database"""
        # Normalize embedding for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        embedding = embedding.reshape(1, -1)
        
        content_id = self.next_id
        self.index.add(embedding)
        self.content_map[content_id] = content
        self.next_id += 1
        
        return content_id
    
    def search(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[MediaContent, float]]:
        """Search for similar content"""
        # Normalize query embedding
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        query_embedding = query_embedding.reshape(1, -1)
        
        scores, indices = self.index.search(query_embedding, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx in self.content_map:
                results.append((self.content_map[idx], float(score)))
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return {
            "total_documents": self.index.ntotal,
            "dimension": self.dimension,
            "content_types": list(set(content.content_type for content in self.content_map.values()))
        }

class ConversationalQueryBot:
    """Main conversational query bot for media libraries"""
    
    def __init__(self, db_path: str = "media_query_bot.db"):
        """Initialize the conversational query bot"""
        self.db_path = db_path
        self.embedding_manager = EmbeddingManager()
        self.vector_db = VectorDatabase(self.embedding_manager.dimension)
        self.conversations: Dict[str, ConversationContext] = {}
        
        # Initialize database
        self._init_database()
        
        # Load existing content
        self._load_existing_content()
        
        logger.info("Conversational Query Bot initialized successfully")
    
    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_content (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    text_content TEXT NOT NULL,
                    timestamp REAL,
                    speaker TEXT,
                    file_path TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    query_history TEXT NOT NULL,
                    result_history TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS query_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    query TEXT NOT NULL,
                    results_count INTEGER,
                    processing_time REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def _load_existing_content(self):
        """Load existing content from database into vector database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM media_content')
            rows = cursor.fetchall()
            
            for row in rows:
                content = MediaContent(
                    id=row[0],
                    title=row[1],
                    content_type=row[2],
                    text_content=row[3],
                    timestamp=row[4],
                    speaker=row[5],
                    file_path=row[6],
                    metadata=json.loads(row[7]) if row[7] else None,
                    created_at=datetime.fromisoformat(row[8])
                )
                
                # Generate embedding and add to vector database
                embedding = self.embedding_manager.encode_text(content.text_content)
                self.vector_db.add_content(content, embedding)
            
            conn.close()
            logger.info(f"Loaded {len(rows)} existing content items")
            
        except Exception as e:
            logger.error(f"Failed to load existing content: {e}")
    
    def add_content(self, content: MediaContent) -> bool:
        """Add new content to the media library"""
        try:
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO media_content 
                (id, title, content_type, text_content, timestamp, speaker, file_path, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                content.id,
                content.title,
                content.content_type,
                content.text_content,
                content.timestamp,
                content.speaker,
                content.file_path,
                json.dumps(content.metadata) if content.metadata else None,
                content.created_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            # Add to vector database
            embedding = self.embedding_manager.encode_text(content.text_content)
            self.vector_db.add_content(content, embedding)
            
            logger.info(f"Added content: {content.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add content: {e}")
            return False
    
    def query(self, 
              query_text: str, 
              conversation_id: Optional[str] = None,
              max_results: int = 5,
              content_types: Optional[List[str]] = None) -> List[QueryResult]:
        """Query the media library with natural language"""
        start_time = datetime.now()
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_manager.encode_text(query_text)
            
            # Search vector database
            search_results = self.vector_db.search(query_embedding, k=max_results * 2)
            
            # Filter by content types if specified
            if content_types:
                search_results = [
                    (content, score) for content, score in search_results
                    if content.content_type in content_types
                ]
            
            # Convert to QueryResult objects
            query_results = []
            for content, score in search_results[:max_results]:
                # Generate snippet (first 200 characters)
                snippet = content.text_content[:200] + "..." if len(content.text_content) > 200 else content.text_content
                
                # Generate timestamp citation if available
                timestamp_citation = None
                if content.timestamp is not None:
                    minutes = int(content.timestamp // 60)
                    seconds = int(content.timestamp % 60)
                    timestamp_citation = f"{minutes:02d}:{seconds:02d}"
                
                # Generate context window (surrounding text)
                context_window = self._generate_context_window(content, query_text)
                
                result = QueryResult(
                    content=content,
                    relevance_score=score,
                    snippet=snippet,
                    timestamp_citation=timestamp_citation,
                    context_window=context_window
                )
                query_results.append(result)
            
            # Update conversation context
            if conversation_id:
                self._update_conversation_context(conversation_id, query_text, query_results)
            
            # Log query
            processing_time = (datetime.now() - start_time).total_seconds()
            self._log_query(conversation_id, query_text, len(query_results), processing_time)
            
            return query_results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def _generate_context_window(self, content: MediaContent, query: str) -> str:
        """Generate context window around relevant text"""
        try:
            text = content.text_content.lower()
            query_words = query.lower().split()
            
            # Find the best matching position
            best_pos = 0
            best_score = 0
            
            for i in range(len(text) - 100):
                window = text[i:i+200]
                score = sum(1 for word in query_words if word in window)
                if score > best_score:
                    best_score = score
                    best_pos = i
            
            # Extract context window
            start = max(0, best_pos - 50)
            end = min(len(content.text_content), best_pos + 250)
            context = content.text_content[start:end]
            
            if start > 0:
                context = "..." + context
            if end < len(content.text_content):
                context = context + "..."
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to generate context window: {e}")
            return content.text_content[:200] + "..."
    
    def _update_conversation_context(self, conversation_id: str, query: str, results: List[QueryResult]):
        """Update conversation context for follow-up queries"""
        try:
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = ConversationContext(
                    conversation_id=conversation_id,
                    query_history=[],
                    result_history=[]
                )
            
            context = self.conversations[conversation_id]
            context.query_history.append(query)
            context.result_history.append(results)
            
            # Keep only last 10 queries for memory efficiency
            if len(context.query_history) > 10:
                context.query_history = context.query_history[-10:]
                context.result_history = context.result_history[-10:]
            
        except Exception as e:
            logger.error(f"Failed to update conversation context: {e}")
    
    def _log_query(self, conversation_id: Optional[str], query: str, results_count: int, processing_time: float):
        """Log query for analytics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO query_logs (conversation_id, query, results_count, processing_time)
                VALUES (?, ?, ?, ?)
            ''', (conversation_id, query, results_count, processing_time))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log query: {e}")
    
    def get_conversation_history(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation history"""
        return self.conversations.get(conversation_id)
    
    def generate_answer(self, query: str, results: List[QueryResult]) -> str:
        """Generate a natural language answer using the query results"""
        try:
            if not results:
                return "I couldn't find any relevant information in your media library for that query."
            
            # Prepare context from results
            context_parts = []
            for i, result in enumerate(results[:3]):  # Use top 3 results
                citation = f"[{i+1}]"
                if result.timestamp_citation:
                    citation += f" at {result.timestamp_citation}"
                if result.content.speaker:
                    citation += f" ({result.content.speaker})"
                
                context_parts.append(f"{citation}: {result.context_window}")
            
            context = "\n\n".join(context_parts)
            
            # Simple answer generation (in production, use OpenAI or similar)
            answer = f"Based on your media library, here's what I found:\n\n{context}\n\n"
            answer += f"Found {len(results)} relevant results. "
            
            if results[0].timestamp_citation:
                answer += f"The most relevant content is at timestamp {results[0].timestamp_citation}."
            
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return "I encountered an error while generating the answer."
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get content statistics
            cursor.execute('SELECT content_type, COUNT(*) FROM media_content GROUP BY content_type')
            content_stats = dict(cursor.fetchall())
            
            # Get query statistics
            cursor.execute('SELECT COUNT(*) FROM query_logs')
            total_queries = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(processing_time) FROM query_logs')
            avg_processing_time = cursor.fetchone()[0] or 0
            
            conn.close()
            
            vector_stats = self.vector_db.get_stats()
            
            return {
                "content_statistics": content_stats,
                "total_queries": total_queries,
                "average_processing_time": avg_processing_time,
                "active_conversations": len(self.conversations),
                "vector_database": vector_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history"""
        try:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to clear conversation: {e}")
            return False

# Demo function for testing
def demo_conversational_query_bot():
    """Demonstrate the conversational query bot functionality"""
    print("🤖 Conversational Query Bot Demo")
    print("=" * 50)
    
    # Initialize bot
    bot = ConversationalQueryBot()
    
    # Add sample content
    sample_contents = [
        MediaContent(
            id="transcript_001",
            title="Team Meeting - Q4 Planning",
            content_type="transcript",
            text_content="We discussed the Q4 budget allocation and decided to increase marketing spend by 20%. John mentioned that we need to focus on customer acquisition in the next quarter. The sales team reported a 15% increase in leads.",
            timestamp=120.5,
            speaker="Sarah"
        ),
        MediaContent(
            id="transcript_002",
            title="Product Demo",
            content_type="transcript",
            text_content="The new AI features include automated transcription, entity extraction, and sentiment analysis. These features will help users process audio content more efficiently. The beta testing showed 95% accuracy.",
            timestamp=45.2,
            speaker="Mike"
        ),
        MediaContent(
            id="document_001",
            title="Project Requirements",
            content_type="document",
            text_content="The project requires implementation of natural language processing capabilities, including semantic search and conversational interfaces. The system should support multiple languages and provide real-time responses."
        )
    ]
    
    # Add content to bot
    for content in sample_contents:
        bot.add_content(content)
    
    print(f"✅ Added {len(sample_contents)} sample content items")
    
    # Demo queries
    queries = [
        "What did we discuss about budget?",
        "Tell me about AI features",
        "What are the project requirements?",
        "Who talked about customer acquisition?"
    ]
    
    conversation_id = "demo_conversation"
    
    for query in queries:
        print(f"\n🔍 Query: {query}")
        results = bot.query(query, conversation_id=conversation_id, max_results=3)
        
        if results:
            print(f"📊 Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.content.title}")
                print(f"     Relevance: {result.relevance_score:.3f}")
                if result.timestamp_citation:
                    print(f"     Timestamp: {result.timestamp_citation}")
                if result.content.speaker:
                    print(f"     Speaker: {result.content.speaker}")
                print(f"     Snippet: {result.snippet}")
                print()
            
            # Generate answer
            answer = bot.generate_answer(query, results)
            print(f"🤖 Answer: {answer}")
        else:
            print("❌ No results found")
        
        print("-" * 50)
    
    # Show statistics
    stats = bot.get_statistics()
    print(f"\n📈 System Statistics:")
    print(f"Content Types: {stats.get('content_statistics', {})}")
    print(f"Total Queries: {stats.get('total_queries', 0)}")
    print(f"Avg Processing Time: {stats.get('average_processing_time', 0):.3f}s")
    print(f"Active Conversations: {stats.get('active_conversations', 0)}")
    
    print("\n🎉 Demo completed successfully!")

if __name__ == "__main__":
    demo_conversational_query_bot()