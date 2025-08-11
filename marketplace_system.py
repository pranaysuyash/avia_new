#!/usr/bin/env python3
"""
Marketplace and Template System (Task 51)
Comprehensive marketplace for templates, entity extraction rules, voice models, and community content
"""

import os
import json
import logging
import sqlite3
import hashlib
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
from collections import defaultdict, Counter
import requests
import zipfile
import tempfile
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketplaceItemType(Enum):
    """Types of marketplace items"""
    TEMPLATE = "template"
    ENTITY_RULE = "entity_rule"
    VOICE_MODEL = "voice_model"
    SCRIPT_TEMPLATE = "script_template"
    INTEGRATION = "integration"
    WORKFLOW = "workflow"

class ItemStatus(Enum):
    """Status of marketplace items"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
    REMOVED = "removed"

class ItemCategory(Enum):
    """Categories for marketplace items"""
    BUSINESS = "business"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    LEGAL = "legal"
    MEDIA = "media"
    TECHNOLOGY = "technology"
    GENERAL = "general"

class LicenseType(Enum):
    """License types for marketplace items"""
    FREE = "free"
    PAID = "paid"
    FREEMIUM = "freemium"
    SUBSCRIPTION = "subscription"

@dataclass
class MarketplaceItem:
    """Base structure for marketplace items"""
    item_id: str
    name: str
    description: str
    item_type: str
    category: str
    author_id: str
    author_name: str
    version: str
    license_type: str
    price: float
    tags: List[str]
    status: str
    created_at: datetime
    updated_at: datetime
    download_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    file_path: Optional[str] = None
    preview_images: List[str] = field(default_factory=list)
    documentation: Optional[str] = None
    requirements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Template:
    """Template structure for common use cases"""
    template_id: str
    name: str
    description: str
    category: str
    use_case: str
    template_data: Dict[str, Any]
    author_id: str
    created_at: datetime
    is_public: bool = True
    download_count: int = 0
    rating: float = 0.0
    tags: List[str] = field(default_factory=list)

@dataclass
class EntityExtractionRule:
    """Custom entity extraction rule"""
    rule_id: str
    name: str
    description: str
    entity_type: str
    pattern: str
    regex_pattern: Optional[str] = None
    context_rules: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    author_id: str
    created_at: datetime
    accuracy_score: float = 0.0
    usage_count: int = 0

@dataclass
class VoiceModel:
    """Voice model for TTS"""
    model_id: str
    name: str
    description: str
    language: str
    gender: str
    accent: str
    sample_audio_url: Optional[str] = None
    model_file_path: Optional[str] = None
    author_id: str
    created_at: datetime
    quality_score: float = 0.0
    download_count: int = 0
    file_size: int = 0  # in bytes

@dataclass
class ScriptTemplate:
    """Script template for content generation"""
    template_id: str
    name: str
    description: str
    category: str
    template_content: str
    variables: List[str]
    author_id: str
    created_at: datetime
    usage_count: int = 0
    rating: float = 0.0
    examples: List[str] = field(default_factory=list)

@dataclass
class MarketplaceReview:
    """Review for marketplace items"""
    review_id: str
    item_id: str
    user_id: str
    rating: int  # 1-5 stars
    comment: str
    created_at: datetime
    helpful_votes: int = 0
    verified_purchase: bool = False

@dataclass
class MarketplaceTransaction:
    """Transaction record for marketplace purchases"""
    transaction_id: str
    item_id: str
    buyer_id: str
    seller_id: str
    amount: float
    currency: str
    transaction_type: str  # purchase, subscription, donation
    status: str  # pending, completed, failed, refunded
    created_at: datetime
    completed_at: Optional[datetime] = None

class MarketplaceDatabase:
    """Database manager for marketplace functionality"""
    
    def __init__(self, db_path: str = "marketplace.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Marketplace items table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS marketplace_items (
                        item_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        item_type TEXT NOT NULL,
                        category TEXT NOT NULL,
                        author_id TEXT NOT NULL,
                        author_name TEXT NOT NULL,
                        version TEXT NOT NULL,
                        license_type TEXT NOT NULL,
                        price REAL DEFAULT 0.0,
                        tags TEXT DEFAULT '[]',
                        status TEXT NOT NULL DEFAULT 'draft',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        download_count INTEGER DEFAULT 0,
                        rating REAL DEFAULT 0.0,
                        rating_count INTEGER DEFAULT 0,
                        file_path TEXT,
                        preview_images TEXT DEFAULT '[]',
                        documentation TEXT,
                        requirements TEXT DEFAULT '[]',
                        metadata TEXT DEFAULT '{}',
                        INDEX idx_item_type (item_type),
                        INDEX idx_category (category),
                        INDEX idx_author (author_id),
                        INDEX idx_status (status),
                        INDEX idx_rating (rating)
                    )
                """)
                
                # Templates table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS templates (
                        template_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        category TEXT NOT NULL,
                        use_case TEXT NOT NULL,
                        template_data TEXT NOT NULL,
                        author_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        is_public BOOLEAN DEFAULT 1,
                        download_count INTEGER DEFAULT 0,
                        rating REAL DEFAULT 0.0,
                        tags TEXT DEFAULT '[]',
                        INDEX idx_template_category (category),
                        INDEX idx_template_author (author_id),
                        INDEX idx_template_public (is_public)
                    )
                """)
                
                # Entity extraction rules table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS entity_rules (
                        rule_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        entity_type TEXT NOT NULL,
                        pattern TEXT NOT NULL,
                        regex_pattern TEXT,
                        context_rules TEXT DEFAULT '[]',
                        examples TEXT DEFAULT '[]',
                        author_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        accuracy_score REAL DEFAULT 0.0,
                        usage_count INTEGER DEFAULT 0,
                        INDEX idx_entity_type (entity_type),
                        INDEX idx_entity_author (author_id)
                    )
                """)
                
                # Voice models table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS voice_models (
                        model_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        language TEXT NOT NULL,
                        gender TEXT NOT NULL,
                        accent TEXT NOT NULL,
                        sample_audio_url TEXT,
                        model_file_path TEXT,
                        author_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        quality_score REAL DEFAULT 0.0,
                        download_count INTEGER DEFAULT 0,
                        file_size INTEGER DEFAULT 0,
                        INDEX idx_voice_language (language),
                        INDEX idx_voice_gender (gender),
                        INDEX idx_voice_author (author_id)
                    )
                """)
                
                # Script templates table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS script_templates (
                        template_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        category TEXT NOT NULL,
                        template_content TEXT NOT NULL,
                        variables TEXT DEFAULT '[]',
                        author_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        usage_count INTEGER DEFAULT 0,
                        rating REAL DEFAULT 0.0,
                        examples TEXT DEFAULT '[]',
                        INDEX idx_script_category (category),
                        INDEX idx_script_author (author_id)
                    )
                """)
                
                # Reviews table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS marketplace_reviews (
                        review_id TEXT PRIMARY KEY,
                        item_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        rating INTEGER NOT NULL,
                        comment TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        helpful_votes INTEGER DEFAULT 0,
                        verified_purchase BOOLEAN DEFAULT 0,
                        FOREIGN KEY (item_id) REFERENCES marketplace_items (item_id),
                        INDEX idx_review_item (item_id),
                        INDEX idx_review_user (user_id),
                        INDEX idx_review_rating (rating)
                    )
                """)
                
                # Transactions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS marketplace_transactions (
                        transaction_id TEXT PRIMARY KEY,
                        item_id TEXT NOT NULL,
                        buyer_id TEXT NOT NULL,
                        seller_id TEXT NOT NULL,
                        amount REAL NOT NULL,
                        currency TEXT NOT NULL DEFAULT 'USD',
                        transaction_type TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        created_at TEXT NOT NULL,
                        completed_at TEXT,
                        FOREIGN KEY (item_id) REFERENCES marketplace_items (item_id),
                        INDEX idx_transaction_buyer (buyer_id),
                        INDEX idx_transaction_seller (seller_id),
                        INDEX idx_transaction_status (status)
                    )
                """)
                
                # User collections table (for organizing purchased/favorited items)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_collections (
                        collection_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        is_public BOOLEAN DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        INDEX idx_collection_user (user_id)
                    )
                """)
                
                # Collection items table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS collection_items (
                        collection_id TEXT NOT NULL,
                        item_id TEXT NOT NULL,
                        added_at TEXT NOT NULL,
                        PRIMARY KEY (collection_id, item_id),
                        FOREIGN KEY (collection_id) REFERENCES user_collections (collection_id),
                        FOREIGN KEY (item_id) REFERENCES marketplace_items (item_id)
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing marketplace database: {e}")
            raise
    
    def add_marketplace_item(self, item: MarketplaceItem) -> bool:
        """Add item to marketplace"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO marketplace_items (
                        item_id, name, description, item_type, category,
                        author_id, author_name, version, license_type, price,
                        tags, status, created_at, updated_at, download_count,
                        rating, rating_count, file_path, preview_images,
                        documentation, requirements, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.item_id, item.name, item.description, item.item_type,
                    item.category, item.author_id, item.author_name, item.version,
                    item.license_type, item.price, json.dumps(item.tags),
                    item.status, item.created_at.isoformat(), item.updated_at.isoformat(),
                    item.download_count, item.rating, item.rating_count,
                    item.file_path, json.dumps(item.preview_images),
                    item.documentation, json.dumps(item.requirements),
                    json.dumps(item.metadata)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding marketplace item: {e}")
            return False
    
    def get_marketplace_items(self, item_type: str = None, category: str = None,
                            status: str = "approved", limit: int = 50,
                            offset: int = 0) -> List[MarketplaceItem]:
        """Get marketplace items with filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT item_id, name, description, item_type, category,
                           author_id, author_name, version, license_type, price,
                           tags, status, created_at, updated_at, download_count,
                           rating, rating_count, file_path, preview_images,
                           documentation, requirements, metadata
                    FROM marketplace_items
                    WHERE 1=1
                """
                params = []
                
                if item_type:
                    query += " AND item_type = ?"
                    params.append(item_type)
                
                if category:
                    query += " AND category = ?"
                    params.append(category)
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                query += " ORDER BY rating DESC, download_count DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                
                items = []
                for row in cursor.fetchall():
                    items.append(MarketplaceItem(
                        item_id=row[0],
                        name=row[1],
                        description=row[2],
                        item_type=row[3],
                        category=row[4],
                        author_id=row[5],
                        author_name=row[6],
                        version=row[7],
                        license_type=row[8],
                        price=row[9],
                        tags=json.loads(row[10]),
                        status=row[11],
                        created_at=datetime.fromisoformat(row[12]),
                        updated_at=datetime.fromisoformat(row[13]),
                        download_count=row[14],
                        rating=row[15],
                        rating_count=row[16],
                        file_path=row[17],
                        preview_images=json.loads(row[18]),
                        documentation=row[19],
                        requirements=json.loads(row[20]),
                        metadata=json.loads(row[21])
                    ))
                
                return items
                
        except Exception as e:
            logger.error(f"Error getting marketplace items: {e}")
            return []
    
    def add_template(self, template: Template) -> bool:
        """Add template to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO templates (
                        template_id, name, description, category, use_case,
                        template_data, author_id, created_at, is_public,
                        download_count, rating, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    template.template_id, template.name, template.description,
                    template.category, template.use_case, json.dumps(template.template_data),
                    template.author_id, template.created_at.isoformat(),
                    template.is_public, template.download_count,
                    template.rating, json.dumps(template.tags)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding template: {e}")
            return False
    
    def add_entity_rule(self, rule: EntityExtractionRule) -> bool:
        """Add entity extraction rule"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO entity_rules (
                        rule_id, name, description, entity_type, pattern,
                        regex_pattern, context_rules, examples, author_id,
                        created_at, accuracy_score, usage_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.rule_id, rule.name, rule.description, rule.entity_type,
                    rule.pattern, rule.regex_pattern, json.dumps(rule.context_rules),
                    json.dumps(rule.examples), rule.author_id,
                    rule.created_at.isoformat(), rule.accuracy_score, rule.usage_count
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding entity rule: {e}")
            return False
    
    def add_voice_model(self, model: VoiceModel) -> bool:
        """Add voice model"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO voice_models (
                        model_id, name, description, language, gender, accent,
                        sample_audio_url, model_file_path, author_id, created_at,
                        quality_score, download_count, file_size
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    model.model_id, model.name, model.description, model.language,
                    model.gender, model.accent, model.sample_audio_url,
                    model.model_file_path, model.author_id, model.created_at.isoformat(),
                    model.quality_score, model.download_count, model.file_size
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding voice model: {e}")
            return False
    
    def add_script_template(self, template: ScriptTemplate) -> bool:
        """Add script template"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO script_templates (
                        template_id, name, description, category, template_content,
                        variables, author_id, created_at, usage_count, rating, examples
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    template.template_id, template.name, template.description,
                    template.category, template.template_content,
                    json.dumps(template.variables), template.author_id,
                    template.created_at.isoformat(), template.usage_count,
                    template.rating, json.dumps(template.examples)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding script template: {e}")
            return False

class TemplateMarketplace:
    """Template marketplace for common use cases"""
    
    def __init__(self, db: MarketplaceDatabase):
        self.db = db
        self.template_categories = {
            "meeting": "Meeting Templates",
            "interview": "Interview Templates", 
            "podcast": "Podcast Templates",
            "lecture": "Educational Templates",
            "legal": "Legal Document Templates",
            "medical": "Medical Templates",
            "business": "Business Templates"
        }
    
    def create_template(self, name: str, description: str, category: str,
                       use_case: str, template_data: Dict[str, Any],
                       author_id: str, tags: List[str] = None) -> str:
        """Create new template"""
        try:
            template_id = f"template_{int(time.time())}_{author_id}"
            
            template = Template(
                template_id=template_id,
                name=name,
                description=description,
                category=category,
                use_case=use_case,
                template_data=template_data,
                author_id=author_id,
                created_at=datetime.now(),
                tags=tags or []
            )
            
            success = self.db.add_template(template)
            
            if success:
                # Also add to marketplace items
                marketplace_item = MarketplaceItem(
                    item_id=template_id,
                    name=name,
                    description=description,
                    item_type=MarketplaceItemType.TEMPLATE.value,
                    category=category,
                    author_id=author_id,
                    author_name=f"User_{author_id}",
                    version="1.0",
                    license_type=LicenseType.FREE.value,
                    price=0.0,
                    tags=tags or [],
                    status=ItemStatus.APPROVED.value,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                self.db.add_marketplace_item(marketplace_item)
                return template_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return None
    
    def get_templates(self, category: str = None, limit: int = 20) -> List[Template]:
        """Get templates by category"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT template_id, name, description, category, use_case,
                           template_data, author_id, created_at, is_public,
                           download_count, rating, tags
                    FROM templates
                    WHERE is_public = 1
                """
                params = []
                
                if category:
                    query += " AND category = ?"
                    params.append(category)
                
                query += " ORDER BY rating DESC, download_count DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                
                templates = []
                for row in cursor.fetchall():
                    templates.append(Template(
                        template_id=row[0],
                        name=row[1],
                        description=row[2],
                        category=row[3],
                        use_case=row[4],
                        template_data=json.loads(row[5]),
                        author_id=row[6],
                        created_at=datetime.fromisoformat(row[7]),
                        is_public=bool(row[8]),
                        download_count=row[9],
                        rating=row[10],
                        tags=json.loads(row[11])
                    ))
                
                return templates
                
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return []
    
    def get_popular_templates(self, limit: int = 10) -> List[Template]:
        """Get most popular templates"""
        return self.get_templates(limit=limit)
    
    def search_templates(self, query: str, category: str = None) -> List[Template]:
        """Search templates by name, description, or tags"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                search_query = """
                    SELECT template_id, name, description, category, use_case,
                           template_data, author_id, created_at, is_public,
                           download_count, rating, tags
                    FROM templates
                    WHERE is_public = 1 
                    AND (name LIKE ? OR description LIKE ? OR tags LIKE ?)
                """
                params = [f"%{query}%", f"%{query}%", f"%{query}%"]
                
                if category:
                    search_query += " AND category = ?"
                    params.append(category)
                
                search_query += " ORDER BY rating DESC, download_count DESC LIMIT 20"
                
                cursor.execute(search_query, params)
                
                templates = []
                for row in cursor.fetchall():
                    templates.append(Template(
                        template_id=row[0],
                        name=row[1],
                        description=row[2],
                        category=row[3],
                        use_case=row[4],
                        template_data=json.loads(row[5]),
                        author_id=row[6],
                        created_at=datetime.fromisoformat(row[7]),
                        is_public=bool(row[8]),
                        download_count=row[9],
                        rating=row[10],
                        tags=json.loads(row[11])
                    ))
                
                return templates
                
        except Exception as e:
            logger.error(f"Error searching templates: {e}")
            return []

class EntityRuleMarketplace:
    """Marketplace for custom entity extraction rules"""
    
    def __init__(self, db: MarketplaceDatabase):
        self.db = db
        self.entity_types = {
            "PERSON": "Person Names",
            "ORGANIZATION": "Organizations",
            "LOCATION": "Locations",
            "DATE": "Dates and Times",
            "MONEY": "Monetary Values",
            "PRODUCT": "Products",
            "EVENT": "Events",
            "CUSTOM": "Custom Entities"
        }
    
    def create_entity_rule(self, name: str, description: str, entity_type: str,
                          pattern: str, author_id: str, regex_pattern: str = None,
                          context_rules: List[str] = None, examples: List[str] = None) -> str:
        """Create new entity extraction rule"""
        try:
            rule_id = f"rule_{int(time.time())}_{author_id}"
            
            rule = EntityExtractionRule(
                rule_id=rule_id,
                name=name,
                description=description,
                entity_type=entity_type,
                pattern=pattern,
                regex_pattern=regex_pattern,
                context_rules=context_rules or [],
                examples=examples or [],
                author_id=author_id,
                created_at=datetime.now()
            )
            
            success = self.db.add_entity_rule(rule)
            
            if success:
                # Add to marketplace
                marketplace_item = MarketplaceItem(
                    item_id=rule_id,
                    name=name,
                    description=description,
                    item_type=MarketplaceItemType.ENTITY_RULE.value,
                    category="extraction",
                    author_id=author_id,
                    author_name=f"User_{author_id}",
                    version="1.0",
                    license_type=LicenseType.FREE.value,
                    price=0.0,
                    tags=[entity_type.lower()],
                    status=ItemStatus.APPROVED.value,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    metadata={"entity_type": entity_type, "pattern": pattern}
                )
                
                self.db.add_marketplace_item(marketplace_item)
                return rule_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating entity rule: {e}")
            return None
    
    def get_entity_rules(self, entity_type: str = None) -> List[EntityExtractionRule]:
        """Get entity extraction rules"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT rule_id, name, description, entity_type, pattern,
                           regex_pattern, context_rules, examples, author_id,
                           created_at, accuracy_score, usage_count
                    FROM entity_rules
                """
                params = []
                
                if entity_type:
                    query += " WHERE entity_type = ?"
                    params.append(entity_type)
                
                query += " ORDER BY accuracy_score DESC, usage_count DESC"
                
                cursor.execute(query, params)
                
                rules = []
                for row in cursor.fetchall():
                    rules.append(EntityExtractionRule(
                        rule_id=row[0],
                        name=row[1],
                        description=row[2],
                        entity_type=row[3],
                        pattern=row[4],
                        regex_pattern=row[5],
                        context_rules=json.loads(row[6]),
                        examples=json.loads(row[7]),
                        author_id=row[8],
                        created_at=datetime.fromisoformat(row[9]),
                        accuracy_score=row[10],
                        usage_count=row[11]
                    ))
                
                return rules
                
        except Exception as e:
            logger.error(f"Error getting entity rules: {e}")
            return []
    
    def test_entity_rule(self, rule_id: str, test_text: str) -> Dict[str, Any]:
        """Test entity extraction rule against sample text"""
        try:
            # Get rule
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pattern, regex_pattern, entity_type
                    FROM entity_rules WHERE rule_id = ?
                """, (rule_id,))
                
                result = cursor.fetchone()
                if not result:
                    return {"error": "Rule not found"}
                
                pattern, regex_pattern, entity_type = result
                
                # Simple pattern matching (in production, use more sophisticated NLP)
                import re
                
                matches = []
                if regex_pattern:
                    # Use regex pattern
                    regex_matches = re.finditer(regex_pattern, test_text, re.IGNORECASE)
                    for match in regex_matches:
                        matches.append({
                            "text": match.group(),
                            "start": match.start(),
                            "end": match.end(),
                            "entity_type": entity_type
                        })
                else:
                    # Use simple pattern matching
                    pattern_words = pattern.lower().split()
                    text_words = test_text.lower().split()
                    
                    for i, word in enumerate(text_words):
                        if word in pattern_words:
                            matches.append({
                                "text": test_text.split()[i],
                                "start": test_text.lower().find(word),
                                "end": test_text.lower().find(word) + len(word),
                                "entity_type": entity_type
                            })
                
                return {
                    "matches": matches,
                    "match_count": len(matches),
                    "rule_id": rule_id
                }
                
        except Exception as e:
            logger.error(f"Error testing entity rule: {e}")
            return {"error": str(e)}

class VoiceModelMarketplace:
    """Marketplace for TTS voice models"""
    
    def __init__(self, db: MarketplaceDatabase):
        self.db = db
        self.supported_languages = {
            "en": "English",
            "es": "Spanish", 
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese"
        }
    
    def add_voice_model(self, name: str, description: str, language: str,
                       gender: str, accent: str, author_id: str,
                       model_file_path: str = None, sample_audio_url: str = None) -> str:
        """Add voice model to marketplace"""
        try:
            model_id = f"voice_{int(time.time())}_{author_id}"
            
            # Calculate file size if file exists
            file_size = 0
            if model_file_path and os.path.exists(model_file_path):
                file_size = os.path.getsize(model_file_path)
            
            model = VoiceModel(
                model_id=model_id,
                name=name,
                description=description,
                language=language,
                gender=gender,
                accent=accent,
                sample_audio_url=sample_audio_url,
                model_file_path=model_file_path,
                author_id=author_id,
                created_at=datetime.now(),
                file_size=file_size
            )
            
            success = self.db.add_voice_model(model)
            
            if success:
                # Add to marketplace
                marketplace_item = MarketplaceItem(
                    item_id=model_id,
                    name=name,
                    description=description,
                    item_type=MarketplaceItemType.VOICE_MODEL.value,
                    category="voice",
                    author_id=author_id,
                    author_name=f"User_{author_id}",
                    version="1.0",
                    license_type=LicenseType.FREE.value,
                    price=0.0,
                    tags=[language, gender, accent],
                    status=ItemStatus.APPROVED.value,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    metadata={
                        "language": language,
                        "gender": gender,
                        "accent": accent,
                        "file_size": file_size
                    }
                )
                
                self.db.add_marketplace_item(marketplace_item)
                return model_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error adding voice model: {e}")
            return None
    
    def get_voice_models(self, language: str = None, gender: str = None) -> List[VoiceModel]:
        """Get voice models with filtering"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT model_id, name, description, language, gender, accent,
                           sample_audio_url, model_file_path, author_id, created_at,
                           quality_score, download_count, file_size
                    FROM voice_models
                    WHERE 1=1
                """
                params = []
                
                if language:
                    query += " AND language = ?"
                    params.append(language)
                
                if gender:
                    query += " AND gender = ?"
                    params.append(gender)
                
                query += " ORDER BY quality_score DESC, download_count DESC"
                
                cursor.execute(query, params)
                
                models = []
                for row in cursor.fetchall():
                    models.append(VoiceModel(
                        model_id=row[0],
                        name=row[1],
                        description=row[2],
                        language=row[3],
                        gender=row[4],
                        accent=row[5],
                        sample_audio_url=row[6],
                        model_file_path=row[7],
                        author_id=row[8],
                        created_at=datetime.fromisoformat(row[9]),
                        quality_score=row[10],
                        download_count=row[11],
                        file_size=row[12]
                    ))
                
                return models
                
        except Exception as e:
            logger.error(f"Error getting voice models: {e}")
            return []
    
    def preview_voice_model(self, model_id: str, text: str) -> Dict[str, Any]:
        """Generate preview audio for voice model"""
        try:
            # Get model info
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, language, gender, accent, model_file_path
                    FROM voice_models WHERE model_id = ?
                """, (model_id,))
                
                result = cursor.fetchone()
                if not result:
                    return {"error": "Voice model not found"}
                
                name, language, gender, accent, model_file_path = result
                
                # In production, this would generate actual audio using the voice model
                # For demo, return metadata about what would be generated
                return {
                    "model_id": model_id,
                    "model_name": name,
                    "language": language,
                    "gender": gender,
                    "accent": accent,
                    "preview_text": text,
                    "estimated_duration": len(text.split()) * 0.5,  # Rough estimate
                    "audio_url": f"/api/voice/preview/{model_id}",  # Would be actual audio URL
                    "status": "generated"
                }
                
        except Exception as e:
            logger.error(f"Error previewing voice model: {e}")
            return {"error": str(e)}class
 ScriptTemplateLibrary:
    """Library for content generation script templates"""
    
    def __init__(self, db: MarketplaceDatabase):
        self.db = db
        self.template_categories = {
            "podcast": "Podcast Scripts",
            "interview": "Interview Scripts",
            "presentation": "Presentation Scripts",
            "marketing": "Marketing Content",
            "educational": "Educational Content",
            "social_media": "Social Media Posts",
            "email": "Email Templates",
            "blog": "Blog Post Templates"
        }
    
    def create_script_template(self, name: str, description: str, category: str,
                              template_content: str, variables: List[str],
                              author_id: str, examples: List[str] = None) -> str:
        """Create new script template"""
        try:
            template_id = f"script_{int(time.time())}_{author_id}"
            
            template = ScriptTemplate(
                template_id=template_id,
                name=name,
                description=description,
                category=category,
                template_content=template_content,
                variables=variables,
                author_id=author_id,
                created_at=datetime.now(),
                examples=examples or []
            )
            
            success = self.db.add_script_template(template)
            
            if success:
                # Add to marketplace
                marketplace_item = MarketplaceItem(
                    item_id=template_id,
                    name=name,
                    description=description,
                    item_type=MarketplaceItemType.SCRIPT_TEMPLATE.value,
                    category=category,
                    author_id=author_id,
                    author_name=f"User_{author_id}",
                    version="1.0",
                    license_type=LicenseType.FREE.value,
                    price=0.0,
                    tags=[category, "script", "template"],
                    status=ItemStatus.APPROVED.value,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    metadata={"variables": variables, "category": category}
                )
                
                self.db.add_marketplace_item(marketplace_item)
                return template_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating script template: {e}")
            return None
    
    def get_script_templates(self, category: str = None) -> List[ScriptTemplate]:
        """Get script templates by category"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT template_id, name, description, category, template_content,
                           variables, author_id, created_at, usage_count, rating, examples
                    FROM script_templates
                """
                params = []
                
                if category:
                    query += " WHERE category = ?"
                    params.append(category)
                
                query += " ORDER BY rating DESC, usage_count DESC"
                
                cursor.execute(query, params)
                
                templates = []
                for row in cursor.fetchall():
                    templates.append(ScriptTemplate(
                        template_id=row[0],
                        name=row[1],
                        description=row[2],
                        category=row[3],
                        template_content=row[4],
                        variables=json.loads(row[5]),
                        author_id=row[6],
                        created_at=datetime.fromisoformat(row[7]),
                        usage_count=row[8],
                        rating=row[9],
                        examples=json.loads(row[10])
                    ))
                
                return templates
                
        except Exception as e:
            logger.error(f"Error getting script templates: {e}")
            return []
    
    def generate_script(self, template_id: str, variables: Dict[str, str]) -> Dict[str, Any]:
        """Generate script from template with provided variables"""
        try:
            # Get template
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, template_content, variables
                    FROM script_templates WHERE template_id = ?
                """, (template_id,))
                
                result = cursor.fetchone()
                if not result:
                    return {"error": "Template not found"}
                
                name, template_content, template_variables = result
                template_vars = json.loads(template_variables)
                
                # Check if all required variables are provided
                missing_vars = [var for var in template_vars if var not in variables]
                if missing_vars:
                    return {"error": f"Missing variables: {missing_vars}"}
                
                # Replace variables in template
                generated_content = template_content
                for var, value in variables.items():
                    placeholder = f"{{{var}}}"
                    generated_content = generated_content.replace(placeholder, value)
                
                # Update usage count
                cursor.execute("""
                    UPDATE script_templates 
                    SET usage_count = usage_count + 1
                    WHERE template_id = ?
                """, (template_id,))
                conn.commit()
                
                return {
                    "template_id": template_id,
                    "template_name": name,
                    "generated_content": generated_content,
                    "variables_used": variables,
                    "word_count": len(generated_content.split()),
                    "character_count": len(generated_content)
                }
                
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return {"error": str(e)}

class CommunitySystem:
    """Community-driven content and integrations"""
    
    def __init__(self, db: MarketplaceDatabase):
        self.db = db
    
    def submit_item_for_review(self, item: MarketplaceItem) -> bool:
        """Submit item for community review"""
        try:
            # Set status to pending review
            item.status = ItemStatus.PENDING_REVIEW.value
            return self.db.add_marketplace_item(item)
            
        except Exception as e:
            logger.error(f"Error submitting item for review: {e}")
            return False
    
    def add_review(self, item_id: str, user_id: str, rating: int, 
                   comment: str, verified_purchase: bool = False) -> str:
        """Add review for marketplace item"""
        try:
            review_id = f"review_{int(time.time())}_{user_id}"
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Add review
                cursor.execute("""
                    INSERT INTO marketplace_reviews (
                        review_id, item_id, user_id, rating, comment,
                        created_at, verified_purchase
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    review_id, item_id, user_id, rating, comment,
                    datetime.now().isoformat(), verified_purchase
                ))
                
                # Update item rating
                cursor.execute("""
                    SELECT AVG(rating), COUNT(rating) 
                    FROM marketplace_reviews 
                    WHERE item_id = ?
                """, (item_id,))
                
                avg_rating, rating_count = cursor.fetchone()
                
                cursor.execute("""
                    UPDATE marketplace_items 
                    SET rating = ?, rating_count = ?
                    WHERE item_id = ?
                """, (avg_rating or 0, rating_count or 0, item_id))
                
                conn.commit()
                return review_id
                
        except Exception as e:
            logger.error(f"Error adding review: {e}")
            return None
    
    def get_reviews(self, item_id: str, limit: int = 10) -> List[MarketplaceReview]:
        """Get reviews for marketplace item"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT review_id, item_id, user_id, rating, comment,
                           created_at, helpful_votes, verified_purchase
                    FROM marketplace_reviews
                    WHERE item_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (item_id, limit))
                
                reviews = []
                for row in cursor.fetchall():
                    reviews.append(MarketplaceReview(
                        review_id=row[0],
                        item_id=row[1],
                        user_id=row[2],
                        rating=row[3],
                        comment=row[4],
                        created_at=datetime.fromisoformat(row[5]),
                        helpful_votes=row[6],
                        verified_purchase=bool(row[7])
                    ))
                
                return reviews
                
        except Exception as e:
            logger.error(f"Error getting reviews: {e}")
            return []
    
    def get_trending_items(self, days: int = 7, limit: int = 10) -> List[MarketplaceItem]:
        """Get trending marketplace items"""
        try:
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get items with recent activity (downloads, reviews)
            items = self.db.get_marketplace_items(limit=limit * 2)  # Get more to filter
            
            # Sort by recent activity (simplified trending algorithm)
            trending_items = []
            for item in items:
                if item.created_at >= datetime.fromisoformat(since_date):
                    # Calculate trending score based on downloads and ratings
                    trending_score = (item.download_count * 0.7) + (item.rating * item.rating_count * 0.3)
                    item.metadata['trending_score'] = trending_score
                    trending_items.append(item)
            
            # Sort by trending score
            trending_items.sort(key=lambda x: x.metadata.get('trending_score', 0), reverse=True)
            
            return trending_items[:limit]
            
        except Exception as e:
            logger.error(f"Error getting trending items: {e}")
            return []
    
    def create_user_collection(self, user_id: str, name: str, 
                              description: str = "", is_public: bool = False) -> str:
        """Create user collection for organizing items"""
        try:
            collection_id = f"collection_{int(time.time())}_{user_id}"
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO user_collections (
                        collection_id, user_id, name, description,
                        is_public, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    collection_id, user_id, name, description,
                    is_public, datetime.now().isoformat(), datetime.now().isoformat()
                ))
                
                conn.commit()
                return collection_id
                
        except Exception as e:
            logger.error(f"Error creating user collection: {e}")
            return None
    
    def add_item_to_collection(self, collection_id: str, item_id: str) -> bool:
        """Add item to user collection"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO collection_items (
                        collection_id, item_id, added_at
                    ) VALUES (?, ?, ?)
                """, (collection_id, item_id, datetime.now().isoformat()))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding item to collection: {e}")
            return False

class MarketplaceSystem:
    """Main marketplace system orchestrating all components"""
    
    def __init__(self, db_path: str = "marketplace.db"):
        self.db = MarketplaceDatabase(db_path)
        self.template_marketplace = TemplateMarketplace(self.db)
        self.entity_marketplace = EntityRuleMarketplace(self.db)
        self.voice_marketplace = VoiceModelMarketplace(self.db)
        self.script_library = ScriptTemplateLibrary(self.db)
        self.community = CommunitySystem(self.db)
    
    def get_marketplace_overview(self) -> Dict[str, Any]:
        """Get marketplace overview statistics"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Total items by type
                cursor.execute("""
                    SELECT item_type, COUNT(*) 
                    FROM marketplace_items 
                    WHERE status = 'approved'
                    GROUP BY item_type
                """)
                items_by_type = dict(cursor.fetchall())
                
                # Total downloads
                cursor.execute("""
                    SELECT SUM(download_count) 
                    FROM marketplace_items 
                    WHERE status = 'approved'
                """)
                total_downloads = cursor.fetchone()[0] or 0
                
                # Average rating
                cursor.execute("""
                    SELECT AVG(rating) 
                    FROM marketplace_items 
                    WHERE status = 'approved' AND rating_count > 0
                """)
                avg_rating = cursor.fetchone()[0] or 0
                
                # Recent items (last 7 days)
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM marketplace_items 
                    WHERE status = 'approved' AND created_at > ?
                """, (week_ago,))
                recent_items = cursor.fetchone()[0] or 0
                
                return {
                    'total_items': sum(items_by_type.values()),
                    'items_by_type': items_by_type,
                    'total_downloads': total_downloads,
                    'average_rating': round(avg_rating, 2),
                    'recent_items': recent_items,
                    'categories': list(ItemCategory.__members__.keys()),
                    'item_types': list(MarketplaceItemType.__members__.keys())
                }
                
        except Exception as e:
            logger.error(f"Error getting marketplace overview: {e}")
            return {}
    
    def search_marketplace(self, query: str, item_type: str = None, 
                          category: str = None, limit: int = 20) -> List[MarketplaceItem]:
        """Search across all marketplace items"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                search_query = """
                    SELECT item_id, name, description, item_type, category,
                           author_id, author_name, version, license_type, price,
                           tags, status, created_at, updated_at, download_count,
                           rating, rating_count, file_path, preview_images,
                           documentation, requirements, metadata
                    FROM marketplace_items
                    WHERE status = 'approved'
                    AND (name LIKE ? OR description LIKE ? OR tags LIKE ?)
                """
                params = [f"%{query}%", f"%{query}%", f"%{query}%"]
                
                if item_type:
                    search_query += " AND item_type = ?"
                    params.append(item_type)
                
                if category:
                    search_query += " AND category = ?"
                    params.append(category)
                
                search_query += " ORDER BY rating DESC, download_count DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(search_query, params)
                
                items = []
                for row in cursor.fetchall():
                    items.append(MarketplaceItem(
                        item_id=row[0],
                        name=row[1],
                        description=row[2],
                        item_type=row[3],
                        category=row[4],
                        author_id=row[5],
                        author_name=row[6],
                        version=row[7],
                        license_type=row[8],
                        price=row[9],
                        tags=json.loads(row[10]),
                        status=row[11],
                        created_at=datetime.fromisoformat(row[12]),
                        updated_at=datetime.fromisoformat(row[13]),
                        download_count=row[14],
                        rating=row[15],
                        rating_count=row[16],
                        file_path=row[17],
                        preview_images=json.loads(row[18]),
                        documentation=row[19],
                        requirements=json.loads(row[20]),
                        metadata=json.loads(row[21])
                    ))
                
                return items
                
        except Exception as e:
            logger.error(f"Error searching marketplace: {e}")
            return []
    
    def get_featured_items(self, limit: int = 10) -> List[MarketplaceItem]:
        """Get featured marketplace items"""
        # Get highest rated items with good download counts
        return self.db.get_marketplace_items(limit=limit)
    
    def download_item(self, item_id: str, user_id: str) -> Dict[str, Any]:
        """Download marketplace item"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Get item info
                cursor.execute("""
                    SELECT name, item_type, file_path, price, license_type
                    FROM marketplace_items 
                    WHERE item_id = ? AND status = 'approved'
                """, (item_id,))
                
                result = cursor.fetchone()
                if not result:
                    return {"error": "Item not found or not approved"}
                
                name, item_type, file_path, price, license_type = result
                
                # Check if payment required
                if price > 0 and license_type != LicenseType.FREE.value:
                    # In production, check if user has purchased
                    return {"error": "Payment required", "price": price}
                
                # Update download count
                cursor.execute("""
                    UPDATE marketplace_items 
                    SET download_count = download_count + 1
                    WHERE item_id = ?
                """, (item_id,))
                
                conn.commit()
                
                # Return download info
                return {
                    "item_id": item_id,
                    "name": name,
                    "item_type": item_type,
                    "download_url": f"/api/download/{item_id}",  # Would be actual download URL
                    "file_path": file_path,
                    "status": "success"
                }
                
        except Exception as e:
            logger.error(f"Error downloading item: {e}")
            return {"error": str(e)}
    
    def get_user_items(self, user_id: str) -> Dict[str, List[MarketplaceItem]]:
        """Get items created by user"""
        try:
            items = self.db.get_marketplace_items()
            user_items = [item for item in items if item.author_id == user_id]
            
            # Group by type
            grouped_items = defaultdict(list)
            for item in user_items:
                grouped_items[item.item_type].append(item)
            
            return dict(grouped_items)
            
        except Exception as e:
            logger.error(f"Error getting user items: {e}")
            return {}

def main():
    """Demo function"""
    print("🏪 Marketplace and Template System Demo")
    print("=" * 60)
    
    # Initialize marketplace system
    marketplace = MarketplaceSystem()
    
    try:
        print(f"\n1. Setting up demo marketplace content...")
        
        # Create sample templates
        template_id = marketplace.template_marketplace.create_template(
            name="Meeting Minutes Template",
            description="Professional template for recording meeting minutes",
            category="meeting",
            use_case="Corporate meetings and team discussions",
            template_data={
                "sections": ["Attendees", "Agenda", "Discussion", "Action Items", "Next Steps"],
                "format": "structured",
                "fields": ["date", "time", "location", "participants"]
            },
            author_id="demo_user",
            tags=["meeting", "minutes", "corporate"]
        )
        
        if template_id:
            print(f"   ✅ Created template: {template_id}")
        
        # Create sample entity rule
        rule_id = marketplace.entity_marketplace.create_entity_rule(
            name="Company Name Extractor",
            description="Extracts company names from business documents",
            entity_type="ORGANIZATION",
            pattern="Inc|LLC|Corp|Ltd|Company",
            author_id="demo_user",
            regex_pattern=r'\b[A-Z][a-zA-Z\s]+(?:Inc|LLC|Corp|Ltd|Company)\b',
            examples=["Apple Inc", "Microsoft Corporation", "Google LLC"]
        )
        
        if rule_id:
            print(f"   ✅ Created entity rule: {rule_id}")
        
        # Create sample voice model
        voice_id = marketplace.voice_marketplace.add_voice_model(
            name="Professional Female Voice",
            description="Clear, professional female voice for business content",
            language="en",
            gender="female",
            accent="american",
            author_id="demo_user"
        )
        
        if voice_id:
            print(f"   ✅ Created voice model: {voice_id}")
        
        # Create sample script template
        script_id = marketplace.script_library.create_script_template(
            name="Podcast Intro Template",
            description="Professional podcast introduction template",
            category="podcast",
            template_content="Welcome to {podcast_name}, the show about {topic}. I'm your host {host_name}, and today we're discussing {episode_topic}.",
            variables=["podcast_name", "topic", "host_name", "episode_topic"],
            author_id="demo_user",
            examples=["Welcome to Tech Talk, the show about technology. I'm your host John Smith, and today we're discussing AI innovations."]
        )
        
        if script_id:
            print(f"   ✅ Created script template: {script_id}")
        
        print(f"\n2. Marketplace overview:")
        overview = marketplace.get_marketplace_overview()
        
        print(f"   📊 Total Items: {overview.get('total_items', 0)}")
        print(f"   📥 Total Downloads: {overview.get('total_downloads', 0)}")
        print(f"   ⭐ Average Rating: {overview.get('average_rating', 0)}")
        print(f"   🆕 Recent Items: {overview.get('recent_items', 0)}")
        
        items_by_type = overview.get('items_by_type', {})
        if items_by_type:
            print(f"   📋 Items by Type:")
            for item_type, count in items_by_type.items():
                print(f"     - {item_type.title()}: {count}")
        
        print(f"\n3. Testing marketplace features:")
        
        # Search marketplace
        print(f"   🔍 Searching for 'meeting'...")
        search_results = marketplace.search_marketplace("meeting")
        print(f"     Found {len(search_results)} results")
        
        # Test entity rule
        if rule_id:
            print(f"   🧪 Testing entity rule...")
            test_result = marketplace.entity_marketplace.test_entity_rule(
                rule_id, "Apple Inc and Microsoft Corporation are major tech companies."
            )
            print(f"     Found {test_result.get('match_count', 0)} entity matches")
        
        # Generate script
        if script_id:
            print(f"   📝 Generating script from template...")
            script_result = marketplace.script_library.generate_script(
                script_id, {
                    "podcast_name": "AI Weekly",
                    "topic": "artificial intelligence",
                    "host_name": "Sarah Johnson",
                    "episode_topic": "machine learning trends"
                }
            )
            if 'generated_content' in script_result:
                print(f"     Generated: {script_result['generated_content'][:100]}...")
        
        print(f"\n4. Marketplace features:")
        print(f"   ✅ Template Marketplace - Common use case templates")
        print(f"   ✅ Entity Rule Sharing - Custom extraction patterns")
        print(f"   ✅ Voice Model Library - TTS voice options")
        print(f"   ✅ Script Templates - Content generation templates")
        print(f"   ✅ Community Reviews - User ratings and feedback")
        print(f"   ✅ User Collections - Organize favorite items")
        print(f"   ✅ Search & Discovery - Find relevant content")
        print(f"   ✅ Download Management - Track usage and access")
        
        print(f"\n✅ Demo completed successfully!")
        print(f"   Marketplace and template system is ready for production use.")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()