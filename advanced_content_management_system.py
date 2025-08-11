"""
Task 203: Advanced Content Management and Organization System
Comprehensive system for organizing, categorizing, and managing transcribed content
with smart tagging, search capabilities, and content lifecycle management
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, JSON, String, Text,
    create_engine, ForeignKey, Index, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import re
from collections import Counter
import hashlib

Base = declarative_base()

# Enums
class ContentType(Enum):
    """Content types for transcriptions"""
    AUDIO_TRANSCRIPTION = "audio_transcription"
    VIDEO_TRANSCRIPTION = "video_transcription" 
    INTERVIEW = "interview"
    MEETING = "meeting"
    LECTURE = "lecture"
    PODCAST = "podcast"
    WEBINAR = "webinar"
    CALL_RECORDING = "call_recording"
    PRESENTATION = "presentation"
    OTHER = "other"

class ContentStatus(Enum):
    """Content lifecycle status"""
    PROCESSING = "processing"
    READY = "ready"
    ARCHIVED = "archived"
    DELETED = "deleted"
    FLAGGED = "flagged"
    PRIVATE = "private"
    PUBLIC = "public"

class ContentQuality(Enum):
    """Content quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    NEEDS_REVIEW = "needs_review"

class AccessLevel(Enum):
    """Content access levels"""
    PRIVATE = "private"
    TEAM = "team"
    ORGANIZATION = "organization"
    PUBLIC = "public"

# Database Models
class ContentItem(Base):
    """Core content item model"""
    __tablename__ = "content_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    content_type = Column(String(50), nullable=False)
    status = Column(String(50), default=ContentStatus.PROCESSING.value)
    quality = Column(String(50), default=ContentQuality.NEEDS_REVIEW.value)
    access_level = Column(String(50), default=AccessLevel.PRIVATE.value)
    
    # File information
    original_filename = Column(String(500))
    file_size = Column(Integer)
    duration = Column(Float)  # in seconds
    file_hash = Column(String(64))  # SHA-256 hash
    
    # Content data
    transcription_text = Column(Text)
    summary = Column(Text)
    key_points = Column(JSON)  # List of key points
    topics = Column(JSON)  # List of identified topics
    entities = Column(JSON)  # Named entities (people, places, organizations)
    sentiment_score = Column(Float)  # -1 to 1
    language = Column(String(10), default="en")
    
    # Metadata
    content_metadata = Column(JSON)  # Additional metadata
    processing_info = Column(JSON)  # Processing details
    ai_analysis = Column(JSON)  # AI-generated insights
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    last_accessed = Column(DateTime)
    
    # Relationships
    tags = relationship("ContentTag", back_populates="content_item", cascade="all, delete-orphan")
    categories = relationship("ContentCategory", back_populates="content_item", cascade="all, delete-orphan")
    collections = relationship("CollectionItem", back_populates="content_item")
    versions = relationship("ContentVersion", back_populates="content_item", cascade="all, delete-orphan")
    sharing = relationship("ContentSharing", back_populates="content_item", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_content_type', 'user_id', 'content_type'),
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_content_search', 'title', 'description'),
    )

class Tag(Base):
    """Tags for content organization"""
    __tablename__ = "tags"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), default="#007bff")  # Hex color
    description = Column(Text)
    created_by = Column(String(255))
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content_tags = relationship("ContentTag", back_populates="tag")

class ContentTag(Base):
    """Many-to-many relationship between content and tags"""
    __tablename__ = "content_tags"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(String(36), ForeignKey("content_items.id"), nullable=False)
    tag_id = Column(String(36), ForeignKey("tags.id"), nullable=False)
    auto_generated = Column(Boolean, default=False)
    confidence_score = Column(Float)  # For AI-generated tags
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content_item = relationship("ContentItem", back_populates="tags")
    tag = relationship("Tag", back_populates="content_tags")

class Category(Base):
    """Hierarchical categories for content organization"""
    __tablename__ = "categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    parent_id = Column(String(36), ForeignKey("categories.id"))
    path = Column(String(1000))  # Full hierarchy path
    level = Column(Integer, default=0)
    icon = Column(String(50))
    color = Column(String(7), default="#28a745")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship("Category", remote_side="Category.id")
    children = relationship("Category", remote_side="Category.parent_id")
    content_categories = relationship("ContentCategory", back_populates="category")

class ContentCategory(Base):
    """Many-to-many relationship between content and categories"""
    __tablename__ = "content_categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(String(36), ForeignKey("content_items.id"), nullable=False)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False)
    primary = Column(Boolean, default=False)  # Primary category
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content_item = relationship("ContentItem", back_populates="categories")
    category = relationship("Category", back_populates="content_categories")

class Collection(Base):
    """Collections of content items"""
    __tablename__ = "collections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    user_id = Column(String(255), nullable=False)
    access_level = Column(String(50), default=AccessLevel.PRIVATE.value)
    cover_image = Column(String(500))
    collection_metadata = Column(JSON)
    items_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("CollectionItem", back_populates="collection", cascade="all, delete-orphan")

class CollectionItem(Base):
    """Items within collections"""
    __tablename__ = "collection_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id = Column(String(36), ForeignKey("collections.id"), nullable=False)
    content_id = Column(String(36), ForeignKey("content_items.id"), nullable=False)
    order_index = Column(Integer, default=0)
    notes = Column(Text)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    collection = relationship("Collection", back_populates="items")
    content_item = relationship("ContentItem", back_populates="collections")

class ContentVersion(Base):
    """Version history for content items"""
    __tablename__ = "content_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(String(36), ForeignKey("content_items.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String(500))
    transcription_text = Column(Text)
    summary = Column(Text)
    key_points = Column(JSON)
    change_description = Column(Text)
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content_item = relationship("ContentItem", back_populates="versions")

class ContentSharing(Base):
    """Content sharing and collaboration"""
    __tablename__ = "content_sharing"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(String(36), ForeignKey("content_items.id"), nullable=False)
    shared_with = Column(String(255), nullable=False)  # User ID or email
    permissions = Column(JSON)  # read, edit, comment, etc.
    share_token = Column(String(64))  # For public sharing
    expires_at = Column(DateTime)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime)
    
    # Relationships
    content_item = relationship("ContentItem", back_populates="sharing")

class ContentSearch(Base):
    """Search index and analytics"""
    __tablename__ = "content_search"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(String(36), ForeignKey("content_items.id"), nullable=False)
    search_vector = Column(Text)  # Full-text search vector
    keywords = Column(JSON)  # Extracted keywords
    phrases = Column(JSON)  # Key phrases
    search_score = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@dataclass
class ContentAnalysis:
    """Content analysis results"""
    content_id: str
    topics: List[str] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    keywords: List[Tuple[str, float]] = field(default_factory=list)
    sentiment: float = 0.0
    quality_score: float = 0.0
    readability_score: float = 0.0
    language: str = "en"
    key_points: List[str] = field(default_factory=list)
    summary: str = ""

class ContentManagementSystem:
    """Advanced Content Management and Organization System"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    async def create_content_item(
        self, 
        user_id: str,
        title: str,
        content_type: str,
        transcription_text: str,
        original_filename: Optional[str] = None,
        file_size: Optional[int] = None,
        duration: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new content item with automatic analysis"""
        db = self.SessionLocal()
        try:
            # Generate file hash
            file_hash = self._generate_content_hash(transcription_text)
            
            # Create content item
            content_item = ContentItem(
                user_id=user_id,
                title=title,
                content_type=content_type,
                transcription_text=transcription_text,
                original_filename=original_filename,
                file_size=file_size,
                duration=duration,
                file_hash=file_hash,
                content_metadata=metadata or {},
                status=ContentStatus.PROCESSING.value
            )
            
            db.add(content_item)
            db.commit()
            db.refresh(content_item)
            
            # Perform automatic analysis
            await self._analyze_content(content_item.id, transcription_text, db)
            
            return {
                "content_id": content_item.id,
                "status": "created",
                "analysis_queued": True,
                "created_at": content_item.created_at.isoformat()
            }
        finally:
            db.close()
    
    async def get_content_item(self, content_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get content item with full details"""
        db = self.SessionLocal()
        try:
            content = db.query(ContentItem).filter(
                ContentItem.id == content_id,
                ContentItem.user_id == user_id
            ).first()
            
            if not content:
                return None
            
            # Update last accessed
            content.last_accessed = datetime.utcnow()
            db.commit()
            
            # Load relationships
            tags = [{"id": ct.tag.id, "name": ct.tag.name, "color": ct.tag.color} 
                   for ct in content.tags]
            categories = [{"id": cc.category.id, "name": cc.category.name, "path": cc.category.path}
                         for cc in content.categories]
            
            return {
                "id": content.id,
                "title": content.title,
                "description": content.description,
                "content_type": content.content_type,
                "status": content.status,
                "quality": content.quality,
                "access_level": content.access_level,
                "original_filename": content.original_filename,
                "file_size": content.file_size,
                "duration": content.duration,
                "transcription_text": content.transcription_text,
                "summary": content.summary,
                "key_points": content.key_points or [],
                "topics": content.topics or [],
                "entities": content.entities or {},
                "sentiment_score": content.sentiment_score,
                "language": content.language,
                "tags": tags,
                "categories": categories,
                "metadata": content.content_metadata or {},
                "ai_analysis": content.ai_analysis or {},
                "created_at": content.created_at.isoformat(),
                "updated_at": content.updated_at.isoformat(),
                "last_accessed": content.last_accessed.isoformat() if content.last_accessed else None
            }
        finally:
            db.close()
    
    async def search_content(
        self,
        user_id: str,
        query: Optional[str] = None,
        content_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        quality_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Advanced content search with multiple filters"""
        db = self.SessionLocal()
        try:
            query_builder = db.query(ContentItem).filter(ContentItem.user_id == user_id)
            
            # Text search
            if query:
                search_terms = query.split()
                for term in search_terms:
                    query_builder = query_builder.filter(
                        func.lower(ContentItem.title).contains(term.lower()) |
                        func.lower(ContentItem.description).contains(term.lower()) |
                        func.lower(ContentItem.transcription_text).contains(term.lower())
                    )
            
            # Content type filter
            if content_types:
                query_builder = query_builder.filter(ContentItem.content_type.in_(content_types))
            
            # Tag filter
            if tags:
                query_builder = query_builder.join(ContentTag).join(Tag).filter(
                    Tag.name.in_(tags)
                )
            
            # Category filter
            if categories:
                query_builder = query_builder.join(ContentCategory).join(Category).filter(
                    Category.name.in_(categories)
                )
            
            # Date range filter
            if date_range:
                start_date, end_date = date_range
                query_builder = query_builder.filter(
                    ContentItem.created_at.between(start_date, end_date)
                )
            
            # Quality filter
            if quality_filter:
                query_builder = query_builder.filter(ContentItem.quality == quality_filter)
            
            # Status filter
            if status_filter:
                query_builder = query_builder.filter(ContentItem.status == status_filter)
            
            # Get total count
            total_count = query_builder.count()
            
            # Apply pagination and ordering
            results = query_builder.order_by(ContentItem.created_at.desc()).offset(offset).limit(limit).all()
            
            # Format results
            content_items = []
            for content in results:
                tags = [{"name": ct.tag.name, "color": ct.tag.color} for ct in content.tags]
                categories = [{"name": cc.category.name} for cc in content.categories]
                
                content_items.append({
                    "id": content.id,
                    "title": content.title,
                    "description": content.description,
                    "content_type": content.content_type,
                    "status": content.status,
                    "quality": content.quality,
                    "duration": content.duration,
                    "summary": content.summary[:200] + "..." if content.summary and len(content.summary) > 200 else content.summary,
                    "tags": tags,
                    "categories": categories,
                    "sentiment_score": content.sentiment_score,
                    "created_at": content.created_at.isoformat(),
                    "updated_at": content.updated_at.isoformat()
                })
            
            return {
                "results": content_items,
                "total_count": total_count,
                "page": offset // limit + 1,
                "page_size": limit,
                "total_pages": (total_count + limit - 1) // limit,
                "has_more": offset + limit < total_count
            }
        finally:
            db.close()
    
    async def create_tag(self, name: str, color: str = "#007bff", description: str = "", created_by: str = "") -> Dict[str, Any]:
        """Create a new tag"""
        db = self.SessionLocal()
        try:
            # Check if tag exists
            existing_tag = db.query(Tag).filter(Tag.name == name).first()
            if existing_tag:
                return {"error": "Tag already exists", "tag_id": existing_tag.id}
            
            tag = Tag(
                name=name,
                color=color,
                description=description,
                created_by=created_by
            )
            
            db.add(tag)
            db.commit()
            db.refresh(tag)
            
            return {
                "tag_id": tag.id,
                "name": tag.name,
                "color": tag.color,
                "created_at": tag.created_at.isoformat()
            }
        finally:
            db.close()
    
    async def add_tags_to_content(self, content_id: str, tag_names: List[str], user_id: str) -> Dict[str, Any]:
        """Add tags to content item"""
        db = self.SessionLocal()
        try:
            # Verify content ownership
            content = db.query(ContentItem).filter(
                ContentItem.id == content_id,
                ContentItem.user_id == user_id
            ).first()
            
            if not content:
                return {"error": "Content not found"}
            
            added_tags = []
            for tag_name in tag_names:
                # Get or create tag
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name, created_by=user_id)
                    db.add(tag)
                    db.commit()
                    db.refresh(tag)
                
                # Check if relationship already exists
                existing = db.query(ContentTag).filter(
                    ContentTag.content_id == content_id,
                    ContentTag.tag_id == tag.id
                ).first()
                
                if not existing:
                    content_tag = ContentTag(
                        content_id=content_id,
                        tag_id=tag.id,
                        auto_generated=False
                    )
                    db.add(content_tag)
                    
                    # Update tag usage count
                    tag.usage_count += 1
                    added_tags.append({"id": tag.id, "name": tag.name, "color": tag.color})
            
            db.commit()
            return {"added_tags": added_tags, "status": "success"}
        finally:
            db.close()
    
    async def create_collection(
        self, 
        name: str, 
        user_id: str,
        description: str = "",
        access_level: str = AccessLevel.PRIVATE.value
    ) -> Dict[str, Any]:
        """Create a new content collection"""
        db = self.SessionLocal()
        try:
            collection = Collection(
                name=name,
                description=description,
                user_id=user_id,
                access_level=access_level
            )
            
            db.add(collection)
            db.commit()
            db.refresh(collection)
            
            return {
                "collection_id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "access_level": collection.access_level,
                "created_at": collection.created_at.isoformat()
            }
        finally:
            db.close()
    
    async def add_content_to_collection(self, collection_id: str, content_id: str, user_id: str, notes: str = "") -> Dict[str, Any]:
        """Add content to a collection"""
        db = self.SessionLocal()
        try:
            # Verify collection ownership
            collection = db.query(Collection).filter(
                Collection.id == collection_id,
                Collection.user_id == user_id
            ).first()
            
            if not collection:
                return {"error": "Collection not found"}
            
            # Verify content ownership
            content = db.query(ContentItem).filter(
                ContentItem.id == content_id,
                ContentItem.user_id == user_id
            ).first()
            
            if not content:
                return {"error": "Content not found"}
            
            # Check if already in collection
            existing = db.query(CollectionItem).filter(
                CollectionItem.collection_id == collection_id,
                CollectionItem.content_id == content_id
            ).first()
            
            if existing:
                return {"error": "Content already in collection"}
            
            # Get next order index
            max_order = db.query(func.max(CollectionItem.order_index)).filter(
                CollectionItem.collection_id == collection_id
            ).scalar() or 0
            
            collection_item = CollectionItem(
                collection_id=collection_id,
                content_id=content_id,
                order_index=max_order + 1,
                notes=notes
            )
            
            db.add(collection_item)
            
            # Update collection items count
            collection.items_count += 1
            collection.updated_at = datetime.utcnow()
            
            db.commit()
            
            return {"status": "added", "order_index": collection_item.order_index}
        finally:
            db.close()
    
    async def get_user_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user's content management analytics"""
        db = self.SessionLocal()
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Basic stats
            total_content = db.query(ContentItem).filter(ContentItem.user_id == user_id).count()
            recent_content = db.query(ContentItem).filter(
                ContentItem.user_id == user_id,
                ContentItem.created_at >= since_date
            ).count()
            
            # Content by type
            content_by_type = db.query(
                ContentItem.content_type,
                func.count(ContentItem.id).label('count')
            ).filter(ContentItem.user_id == user_id).group_by(ContentItem.content_type).all()
            
            # Quality distribution
            quality_distribution = db.query(
                ContentItem.quality,
                func.count(ContentItem.id).label('count')
            ).filter(ContentItem.user_id == user_id).group_by(ContentItem.quality).all()
            
            # Storage usage
            total_size = db.query(func.sum(ContentItem.file_size)).filter(
                ContentItem.user_id == user_id
            ).scalar() or 0
            
            # Duration statistics
            total_duration = db.query(func.sum(ContentItem.duration)).filter(
                ContentItem.user_id == user_id
            ).scalar() or 0
            
            # Tags usage
            top_tags = db.query(
                Tag.name,
                func.count(ContentTag.id).label('usage_count')
            ).join(ContentTag).join(ContentItem).filter(
                ContentItem.user_id == user_id
            ).group_by(Tag.name).order_by(func.count(ContentTag.id).desc()).limit(10).all()
            
            return {
                "user_id": user_id,
                "period_days": days,
                "overview": {
                    "total_content": total_content,
                    "recent_content": recent_content,
                    "total_file_size": total_size,
                    "total_duration_hours": round(total_duration / 3600, 2) if total_duration else 0
                },
                "content_by_type": [{"type": ct, "count": count} for ct, count in content_by_type],
                "quality_distribution": [{"quality": q, "count": count} for q, count in quality_distribution],
                "top_tags": [{"tag": name, "usage_count": count} for name, count in top_tags],
                "generated_at": datetime.utcnow().isoformat()
            }
        finally:
            db.close()
    
    async def _analyze_content(self, content_id: str, text: str, db) -> ContentAnalysis:
        """Perform comprehensive content analysis"""
        try:
            analysis = ContentAnalysis(content_id=content_id)
            
            # Extract topics using keyword analysis
            analysis.topics = self._extract_topics(text)
            
            # Extract entities (simplified)
            analysis.entities = self._extract_entities(text)
            
            # Extract keywords with scores
            analysis.keywords = self._extract_keywords(text)
            
            # Calculate sentiment (simplified)
            analysis.sentiment = self._calculate_sentiment(text)
            
            # Calculate quality score
            analysis.quality_score = self._calculate_quality_score(text)
            
            # Generate summary
            analysis.summary = self._generate_summary(text)
            
            # Extract key points
            analysis.key_points = self._extract_key_points(text)
            
            # Update content item with analysis
            content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
            if content:
                content.summary = analysis.summary
                content.key_points = analysis.key_points
                content.topics = analysis.topics
                content.entities = analysis.entities
                content.sentiment_score = analysis.sentiment
                content.quality = self._determine_quality_level(analysis.quality_score)
                content.status = ContentStatus.READY.value
                content.processed_at = datetime.utcnow()
                content.ai_analysis = {
                    "quality_score": analysis.quality_score,
                    "readability_score": analysis.readability_score,
                    "keywords": analysis.keywords,
                    "processed_at": datetime.utcnow().isoformat()
                }
                
                # Auto-generate tags based on topics
                await self._auto_generate_tags(content_id, analysis.topics, db)
                
                db.commit()
            
            return analysis
            
        except Exception as e:
            # Mark content as needing review on analysis failure
            content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
            if content:
                content.status = ContentStatus.READY.value
                content.quality = ContentQuality.NEEDS_REVIEW.value
                content.processed_at = datetime.utcnow()
                db.commit()
            
            return ContentAnalysis(content_id=content_id)
    
    def _generate_content_hash(self, text: str) -> str:
        """Generate SHA-256 hash of content"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _extract_topics(self, text: str, max_topics: int = 10) -> List[str]:
        """Extract topics from text (simplified implementation)"""
        # Simple keyword-based topic extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_counts = Counter(words)
        
        # Filter out common words
        common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'way', 'she', 'may', 'say', 'use', 'her', 'each', 'which', 'their', 'said', 'will', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were'}
        
        topics = [word for word, count in word_counts.most_common(max_topics * 2) 
                 if word not in common_words and len(word) > 3]
        
        return topics[:max_topics]
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities (simplified implementation)"""
        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "dates": []
        }
        
        # Simple pattern-based entity extraction
        # This would be replaced with proper NER in production
        person_patterns = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)
        entities["persons"] = list(set(person_patterns))[:10]
        
        # Extract potential organization names (capitalized words followed by Inc, Corp, LLC, etc.)
        org_patterns = re.findall(r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)*(?: (?:Inc|Corp|LLC|Ltd|Company)\.?)\b', text)
        entities["organizations"] = list(set(org_patterns))[:10]
        
        # Extract dates
        date_patterns = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2},? \d{4}\b', text)
        entities["dates"] = list(set(date_patterns))[:10]
        
        return entities
    
    def _extract_keywords(self, text: str, max_keywords: int = 20) -> List[Tuple[str, float]]:
        """Extract keywords with relevance scores"""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_counts = Counter(words)
        total_words = len(words)
        
        # Calculate TF scores (simplified)
        keywords = []
        for word, count in word_counts.most_common(max_keywords * 2):
            if len(word) > 3 and word not in {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'way', 'she'}:
                score = count / total_words
                keywords.append((word, round(score, 4)))
        
        return keywords[:max_keywords]
    
    def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score (simplified implementation)"""
        # Simple sentiment analysis using word lists
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'positive', 'happy', 'love', 'best', 'perfect', 'outstanding', 'brilliant', 'superb', 'awesome', 'incredible', 'magnificent', 'marvelous', 'terrific', 'fabulous']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing', 'poor', 'worst', 'hate', 'disgusting', 'pathetic', 'useless', 'dreadful', 'appalling', 'atrocious', 'abysmal', 'deplorable', 'disastrous', 'horrendous', 'lousy', 'miserable']
        
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        # Return score between -1 and 1
        sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        return round(sentiment, 3)
    
    def _calculate_quality_score(self, text: str) -> float:
        """Calculate content quality score"""
        if not text or len(text.strip()) < 10:
            return 0.0
        
        score = 0.0
        
        # Length factor (optimal around 1000-5000 characters)
        length = len(text)
        if 500 <= length <= 10000:
            score += 0.3
        elif length > 100:
            score += 0.1
        
        # Sentence structure (presence of punctuation)
        sentences = len(re.findall(r'[.!?]+', text))
        if sentences > 0:
            score += 0.2
            avg_sentence_length = length / sentences
            if 50 <= avg_sentence_length <= 200:
                score += 0.2
        
        # Vocabulary diversity
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        if words:
            unique_words = len(set(words))
            diversity = unique_words / len(words)
            score += min(diversity * 0.3, 0.3)
        
        return min(score, 1.0)
    
    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate content summary (simplified implementation)"""
        if not text or len(text.strip()) < 50:
            return ""
        
        # Simple extractive summarization
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if not sentences:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Take first and most important sentences
        summary_sentences = []
        current_length = 0
        
        # Add first sentence
        if sentences:
            summary_sentences.append(sentences[0])
            current_length += len(sentences[0])
        
        # Add more sentences if space allows
        for sentence in sentences[1:]:
            if current_length + len(sentence) + 2 <= max_length:
                summary_sentences.append(sentence)
                current_length += len(sentence) + 2
            else:
                break
        
        return '. '.join(summary_sentences) + '.'
    
    def _extract_key_points(self, text: str, max_points: int = 5) -> List[str]:
        """Extract key points from text"""
        if not text:
            return []
        
        # Look for bullet points or numbered lists
        bullet_points = re.findall(r'(?:^|\n)\s*[•\-*]\s*(.+)', text, re.MULTILINE)
        numbered_points = re.findall(r'(?:^|\n)\s*\d+\.\s*(.+)', text, re.MULTILINE)
        
        key_points = bullet_points + numbered_points
        
        if not key_points:
            # Extract sentences that might be key points (longer, declarative sentences)
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if 20 <= len(s.strip()) <= 150]
            key_points = sentences[:max_points]
        
        return key_points[:max_points]
    
    def _determine_quality_level(self, quality_score: float) -> str:
        """Determine quality level from score"""
        if quality_score >= 0.8:
            return ContentQuality.EXCELLENT.value
        elif quality_score >= 0.6:
            return ContentQuality.GOOD.value
        elif quality_score >= 0.4:
            return ContentQuality.FAIR.value
        elif quality_score >= 0.2:
            return ContentQuality.POOR.value
        else:
            return ContentQuality.NEEDS_REVIEW.value
    
    async def _auto_generate_tags(self, content_id: str, topics: List[str], db) -> None:
        """Auto-generate tags based on content analysis"""
        for topic in topics[:5]:  # Limit to top 5 topics
            # Get or create tag
            tag = db.query(Tag).filter(Tag.name == topic).first()
            if not tag:
                tag = Tag(name=topic, created_by="system")
                db.add(tag)
                db.commit()
                db.refresh(tag)
            
            # Check if tag already assigned
            existing = db.query(ContentTag).filter(
                ContentTag.content_id == content_id,
                ContentTag.tag_id == tag.id
            ).first()
            
            if not existing:
                content_tag = ContentTag(
                    content_id=content_id,
                    tag_id=tag.id,
                    auto_generated=True,
                    confidence_score=0.8  # Default confidence for auto-generated tags
                )
                db.add(content_tag)
                tag.usage_count += 1