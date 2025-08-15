"""
Action Item Extraction System
Advanced BERT-NER based system for extracting, analyzing, and managing action items from meeting transcripts.

This replaces the rule-based system with transformer models and enterprise features.
"""

import os
import json
import sqlite3
import logging
import hashlib
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# Core ML libraries
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# Advanced NLP libraries with fallbacks
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    from transformers import (
        AutoTokenizer, AutoModelForTokenClassification, AutoModelForSequenceClassification,
        Trainer, TrainingArguments, pipeline, set_seed, BertTokenizer, BertForTokenClassification,
        DistilBertTokenizer, DistilBertForTokenClassification, RobertaTokenizer, RobertaForTokenClassification
    )
    from datasets import Dataset as HFDataset
    TRANSFORMERS_AVAILABLE = True
    print("✅ Transformers and PyTorch available - Full NER capabilities enabled")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers not available - Using rule-based fallback")

try:
    import spacy
    from spacy import displacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠️ spaCy not available - Using basic entity extraction")

# Date parsing
try:
    import dateutil.parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enums
class ActionItemPriority(Enum):
    """Priority levels for action items"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNSPECIFIED = "unspecified"

class ActionItemStatus(Enum):
    """Status of action items"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class DeadlineType(Enum):
    """Types of deadlines"""
    SPECIFIC_DATE = "specific_date"
    RELATIVE_TIME = "relative_time"
    MEETING_BASED = "meeting_based"
    UNSPECIFIED = "unspecified"

class ExtractionMethod(Enum):
    """Methods used for extraction"""
    BERT_NER = "bert_ner"
    SPACY_NER = "spacy_ner"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"

class EntityType(Enum):
    """Types of entities that can be extracted"""
    ACTION = "ACTION"
    PERSON = "PERSON"
    DEADLINE = "DEADLINE"
    PRIORITY = "PRIORITY"
    STATUS = "STATUS"
    DEPENDENCY = "DEPENDENCY"
    TAG = "TAG"

@dataclass
class EntityExtraction:
    """Represents an extracted entity"""
    text: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    confidence: float
    context: str
    extraction_method: ExtractionMethod

@dataclass
class ActionItemDeadline:
    """Represents a deadline for an action item"""
    deadline_type: DeadlineType
    original_text: str
    parsed_date: Optional[datetime] = None
    relative_days: Optional[int] = None
    confidence: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)
    
    def is_overdue(self, current_date: datetime = None) -> bool:
        """Check if the deadline is overdue"""
        if not current_date:
            current_date = datetime.now()
        
        if self.parsed_date:
            return current_date > self.parsed_date
        
        return False
    
    def days_until_deadline(self, current_date: datetime = None) -> Optional[int]:
        """Calculate days until deadline"""
        if not current_date:
            current_date = datetime.now()
        
        if self.parsed_date:
            delta = self.parsed_date - current_date
            return delta.days
        
        return None

@dataclass
class ActionItemAssignee:
    """Represents an assignee for an action item"""
    name: str
    role: Optional[str] = None
    email: Optional[str] = None
    confidence: float = 0.0
    assignment_method: str = "explicit"  # explicit, implicit, inferred
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ActionItem:
    """Represents a complete action item with all details"""
    id: str
    content: str
    priority: ActionItemPriority
    status: ActionItemStatus
    assignees: List[ActionItemAssignee]
    deadline: Optional[ActionItemDeadline] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.0
    extraction_method: ExtractionMethod = ExtractionMethod.RULE_BASED
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class ActionItemDatabase:
    """Production database for action item tracking"""
    
    def __init__(self, db_path: str = "production_action_items.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS action_items (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    deadline_date TEXT,
                    deadline_text TEXT,
                    confidence REAL,
                    extraction_method TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    context TEXT
                );
                
                CREATE TABLE IF NOT EXISTS assignees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_item_id TEXT,
                    name TEXT NOT NULL,
                    role TEXT,
                    email TEXT,
                    confidence REAL,
                    assignment_method TEXT,
                    context TEXT,
                    FOREIGN KEY (action_item_id) REFERENCES action_items (id)
                );
                
                CREATE TABLE IF NOT EXISTS dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_item_id TEXT,
                    depends_on TEXT,
                    dependency_type TEXT,
                    FOREIGN KEY (action_item_id) REFERENCES action_items (id)
                );
                
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_item_id TEXT,
                    tag TEXT,
                    FOREIGN KEY (action_item_id) REFERENCES action_items (id)
                );
                
                CREATE TABLE IF NOT EXISTS extraction_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    extraction_method TEXT,
                    total_items INTEGER,
                    high_confidence INTEGER,
                    processing_time REAL,
                    created_at TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status);
                CREATE INDEX IF NOT EXISTS idx_action_items_priority ON action_items(priority);
                CREATE INDEX IF NOT EXISTS idx_assignees_name ON assignees(name);
                CREATE INDEX IF NOT EXISTS idx_extraction_metrics_session ON extraction_metrics(session_id);
            """)
    
    def save_action_item(self, action_item: ActionItem):
        """Save an action item to the database"""
        with sqlite3.connect(self.db_path) as conn:
            # Save main action item
            conn.execute("""
                INSERT OR REPLACE INTO action_items 
                (id, content, priority, status, deadline_date, deadline_text, 
                 confidence, extraction_method, created_at, updated_at, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                action_item.id,
                action_item.content,
                action_item.priority.value,
                action_item.status.value,
                action_item.deadline.parsed_date.isoformat() if action_item.deadline and action_item.deadline.parsed_date else None,
                action_item.deadline.original_text if action_item.deadline else None,
                action_item.confidence,
                action_item.extraction_method.value,
                action_item.created_at.isoformat(),
                action_item.updated_at.isoformat(),
                json.dumps(action_item.context)
            ))
            
            # Save assignees
            conn.execute("DELETE FROM assignees WHERE action_item_id = ?", (action_item.id,))
            for assignee in action_item.assignees:
                conn.execute("""
                    INSERT INTO assignees (action_item_id, name, role, email, confidence, assignment_method, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    action_item.id, assignee.name, assignee.role, assignee.email,
                    assignee.confidence, assignee.assignment_method, json.dumps(assignee.context)
                ))
            
            # Save dependencies
            conn.execute("DELETE FROM dependencies WHERE action_item_id = ?", (action_item.id,))
            for dep in action_item.dependencies:
                conn.execute("""
                    INSERT INTO dependencies (action_item_id, depends_on, dependency_type)
                    VALUES (?, ?, ?)
                """, (action_item.id, dep, "explicit"))
            
            # Save tags
            conn.execute("DELETE FROM tags WHERE action_item_id = ?", (action_item.id,))
            for tag in action_item.tags:
                conn.execute("""
                    INSERT INTO tags (action_item_id, tag)
                    VALUES (?, ?)
                """, (action_item.id, tag))
    
    def get_action_items(self, status: Optional[ActionItemStatus] = None) -> List[ActionItem]:
        """Retrieve action items from database"""
        query = "SELECT * FROM action_items"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status.value)
        
        query += " ORDER BY created_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            
            action_items = []
            for row in rows:
                # Get assignees
                assignee_rows = conn.execute(
                    "SELECT * FROM assignees WHERE action_item_id = ?", 
                    (row['id'],)
                ).fetchall()
                
                assignees = [
                    ActionItemAssignee(
                        name=a['name'],
                        role=a['role'],
                        email=a['email'],
                        confidence=a['confidence'] or 0.0,
                        assignment_method=a['assignment_method'] or 'extracted',
                        context=json.loads(a['context'] or '{}')
                    ) for a in assignee_rows
                ]
                
                # Get dependencies
                dep_rows = conn.execute(
                    "SELECT depends_on FROM dependencies WHERE action_item_id = ?", 
                    (row['id'],)
                ).fetchall()
                dependencies = [d['depends_on'] for d in dep_rows]
                
                # Get tags
                tag_rows = conn.execute(
                    "SELECT tag FROM tags WHERE action_item_id = ?", 
                    (row['id'],)
                ).fetchall()
                tags = [t['tag'] for t in tag_rows]
                
                # Create deadline if exists
                deadline = None
                if row['deadline_text']:
                    deadline = ActionItemDeadline(
                        deadline_type=DeadlineType.SPECIFIC_DATE if row['deadline_date'] else DeadlineType.UNSPECIFIED,
                        original_text=row['deadline_text'],
                        parsed_date=datetime.fromisoformat(row['deadline_date']) if row['deadline_date'] else None
                    )
                
                action_item = ActionItem(
                    id=row['id'],
                    content=row['content'],
                    priority=ActionItemPriority(row['priority']),
                    status=ActionItemStatus(row['status']),
                    assignees=assignees,
                    deadline=deadline,
                    dependencies=dependencies,
                    tags=tags,
                    confidence=row['confidence'] or 0.0,
                    extraction_method=ExtractionMethod(row['extraction_method']),
                    context=json.loads(row['context'] or '{}'),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                
                action_items.append(action_item)
            
            return action_items

class BERTActionItemExtractor:
    """BERT-based Named Entity Recognition for action item extraction"""
    
    def __init__(self, model_name: str = "dbmdz/bert-large-cased-finetuned-conll03-english"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.ner_pipeline = None
        self.init_model()
    
    def init_model(self):
        """Initialize BERT NER model"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available - BERT extraction disabled")
            return
        
        try:
            # Use a general-purpose NER model that can be fine-tuned
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            
            # Create NER pipeline
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model,
                tokenizer=self.tokenizer,
                aggregation_strategy="simple",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info(f"✅ BERT NER model initialized: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize BERT NER model: {e}")
            self.tokenizer = None
            self.model = None
            self.ner_pipeline = None
    
    def extract_entities(self, text: str) -> List[EntityExtraction]:
        """Extract entities using BERT NER"""
        if not self.ner_pipeline:
            return []
        
        try:
            entities = self.ner_pipeline(text)
            extractions = []
            
            for entity in entities:
                # Map BERT entity types to our custom types
                entity_type = self._map_entity_type(entity['entity_group'])
                if entity_type:
                    extractions.append(EntityExtraction(
                        text=entity['word'],
                        entity_type=entity_type,
                        start_pos=entity['start'],
                        end_pos=entity['end'],
                        confidence=entity['score'],
                        context=text[max(0, entity['start']-50):entity['end']+50],
                        extraction_method=ExtractionMethod.BERT_NER
                    ))
            
            return extractions
            
        except Exception as e:
            logger.error(f"BERT entity extraction failed: {e}")
            return []
    
    def _map_entity_type(self, bert_entity: str) -> Optional[EntityType]:
        """Map BERT entity types to our custom entity types"""
        mapping = {
            'PER': EntityType.PERSON,
            'PERSON': EntityType.PERSON,
            'DATE': EntityType.DEADLINE,
            'TIME': EntityType.DEADLINE,
            'ORG': None,  # Organizations not directly relevant
            'LOC': None,  # Locations not directly relevant
            'MISC': None  # Miscellaneous entities need further processing
        }
        return mapping.get(bert_entity.upper())

class SpacyActionItemExtractor:
    """spaCy-based entity extraction for action items"""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        self.model_name = model_name
        self.nlp = None
        self.init_model()
    
    def init_model(self):
        """Initialize spaCy model"""
        if not SPACY_AVAILABLE:
            logger.warning("spaCy not available - spaCy extraction disabled")
            return
        
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info(f"✅ spaCy model initialized: {self.model_name}")
        except OSError:
            logger.warning(f"spaCy model {self.model_name} not found - falling back to basic processing")
            self.nlp = None
    
    def extract_entities(self, text: str) -> List[EntityExtraction]:
        """Extract entities using spaCy NER"""
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            extractions = []
            
            for ent in doc.ents:
                entity_type = self._map_entity_type(ent.label_)
                if entity_type:
                    extractions.append(EntityExtraction(
                        text=ent.text,
                        entity_type=entity_type,
                        start_pos=ent.start_char,
                        end_pos=ent.end_char,
                        confidence=0.8,  # spaCy doesn't provide confidence scores
                        context=text[max(0, ent.start_char-50):ent.end_char+50],
                        extraction_method=ExtractionMethod.SPACY_NER
                    ))
            
            return extractions
            
        except Exception as e:
            logger.error(f"spaCy entity extraction failed: {e}")
            return []
    
    def _map_entity_type(self, spacy_label: str) -> Optional[EntityType]:
        """Map spaCy entity labels to our custom entity types"""
        mapping = {
            'PERSON': EntityType.PERSON,
            'DATE': EntityType.DEADLINE,
            'TIME': EntityType.DEADLINE,
            'ORG': None,
            'GPE': None,  # Geopolitical entities not relevant
            'MONEY': None,
            'PERCENT': None,
            'EVENT': None
        }
        return mapping.get(spacy_label)

class RuleBasedActionItemExtractor:
    """Rule-based fallback extractor for action items"""
    
    def __init__(self):
        self.action_patterns = [
            r'\b(?:will|should|must|need to|has to|responsible for)\s+([^.!?]+)',
            r'\b(?:action item|todo|task|assignment):\s*([^.!?]+)',
            r'\b([A-Za-z\s,]+)\s+(?:will|should|must)\s+([^.!?]+)',
            r'\b(?:please|could you|can you)\s+([^.!?]+)',
            r'\b(?:assign|delegate|give)\s+([^.!?]+)\s+to\s+([A-Za-z\s,]+)'
        ]
        
        self.person_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:will|should|must)',
            r'@([A-Za-z0-9_]+)',
            r'\b([A-Z][a-z]+)\s*,?\s*(?:please|could you|can you)',
            r'assign.*?to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        self.deadline_patterns = [
            r'by\s+(next\s+\w+|\w+day|tomorrow|today|\d{1,2}\/\d{1,2})',
            r'due\s+(next\s+\w+|\w+day|tomorrow|today|\d{1,2}\/\d{1,2})',
            r'deadline\s+(next\s+\w+|\w+day|tomorrow|today|\d{1,2}\/\d{1,2})',
            r'before\s+(next\s+\w+|\w+day|tomorrow|today|\d{1,2}\/\d{1,2})',
            r'within\s+(\d+\s+days?|\d+\s+weeks?)'
        ]
        
        self.priority_patterns = [
            r'\b(urgent|critical|asap|immediate|high priority)\b',
            r'\b(low priority|nice to have|when time permits)\b'
        ]
    
    def extract_entities(self, text: str) -> List[EntityExtraction]:
        """Extract entities using rule-based patterns"""
        extractions = []
        
        # Extract persons
        for pattern in self.person_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                extractions.append(EntityExtraction(
                    text=match.group(1),
                    entity_type=EntityType.PERSON,
                    start_pos=match.start(1),
                    end_pos=match.end(1),
                    confidence=0.6,
                    context=text[max(0, match.start()-50):match.end()+50],
                    extraction_method=ExtractionMethod.RULE_BASED
                ))
        
        # Extract deadlines
        for pattern in self.deadline_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                extractions.append(EntityExtraction(
                    text=match.group(1),
                    entity_type=EntityType.DEADLINE,
                    start_pos=match.start(1),
                    end_pos=match.end(1),
                    confidence=0.7,
                    context=text[max(0, match.start()-50):match.end()+50],
                    extraction_method=ExtractionMethod.RULE_BASED
                ))
        
        # Extract priorities
        for pattern in self.priority_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                priority_text = match.group(1).lower()
                extractions.append(EntityExtraction(
                    text=match.group(1),
                    entity_type=EntityType.PRIORITY,
                    start_pos=match.start(1),
                    end_pos=match.end(1),
                    confidence=0.8,
                    context=text[max(0, match.start()-50):match.end()+50],
                    extraction_method=ExtractionMethod.RULE_BASED
                ))
        
        return extractions

class ActionItemExtractionSystem:
    """Main production system for action item extraction"""
    
    def __init__(self, db_path: str = "production_action_items.db"):
        self.db = ActionItemDatabase(db_path)
        self.bert_extractor = BERTActionItemExtractor()
        self.spacy_extractor = SpacyActionItemExtractor()
        self.rule_extractor = RuleBasedActionItemExtractor()
        self.session_id = self._generate_session_id()
        
        logger.info("✅ Production Action Item Extraction System initialized")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    def extract_action_items(self, transcript: str, meeting_id: str = None) -> List[ActionItem]:
        """Extract action items from meeting transcript using multiple methods"""
        start_time = datetime.now()
        
        logger.info(f"Starting action item extraction for meeting {meeting_id}")
        
        # Extract entities using multiple methods
        all_entities = []
        
        # BERT extraction (primary)
        bert_entities = self.bert_extractor.extract_entities(transcript)
        all_entities.extend(bert_entities)
        
        # spaCy extraction (secondary)
        spacy_entities = self.spacy_extractor.extract_entities(transcript)
        all_entities.extend(spacy_entities)
        
        # Rule-based extraction (fallback)
        rule_entities = self.rule_extractor.extract_entities(transcript)
        all_entities.extend(rule_entities)
        
        # Combine entities into action items
        action_items = self._combine_entities_to_actions(all_entities, transcript)
        
        # Save to database
        for action_item in action_items:
            self.db.save_action_item(action_item)
        
        # Log metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        high_confidence_count = sum(1 for ai in action_items if ai.confidence >= 0.75)
        
        self._save_extraction_metrics(
            len(action_items), high_confidence_count, processing_time
        )
        
        logger.info(f"Extracted {len(action_items)} action items ({high_confidence_count} high confidence) in {processing_time:.2f}s")
        
        return action_items
    
    def _combine_entities_to_actions(self, entities: List[EntityExtraction], transcript: str) -> List[ActionItem]:
        """Combine extracted entities into complete action items"""
        action_items = []
        
        # Group entities by proximity and context
        entity_groups = self._group_entities_by_context(entities, transcript)
        
        for group in entity_groups:
            action_item = self._create_action_item_from_group(group, transcript)
            if action_item:
                action_items.append(action_item)
        
        return action_items
    
    def _group_entities_by_context(self, entities: List[EntityExtraction], transcript: str) -> List[List[EntityExtraction]]:
        """Group entities by their context and proximity"""
        # Simple grouping by sentence boundaries
        sentences = re.split(r'[.!?]+', transcript)
        sentence_positions = []
        
        pos = 0
        for sentence in sentences:
            start = transcript.find(sentence, pos)
            if start != -1:
                sentence_positions.append((start, start + len(sentence)))
                pos = start + len(sentence)
        
        groups = []
        for start, end in sentence_positions:
            sentence_entities = [
                e for e in entities 
                if e.start_pos >= start and e.end_pos <= end
            ]
            if sentence_entities:
                groups.append(sentence_entities)
        
        return groups
    
    def _create_action_item_from_group(self, entity_group: List[EntityExtraction], transcript: str) -> Optional[ActionItem]:
        """Create an action item from a group of entities"""
        if not entity_group:
            return None
        
        # Extract different entity types
        persons = [e for e in entity_group if e.entity_type == EntityType.PERSON]
        deadlines = [e for e in entity_group if e.entity_type == EntityType.DEADLINE]
        priorities = [e for e in entity_group if e.entity_type == EntityType.PRIORITY]
        
        # Find the action content (use the context with highest confidence)
        best_entity = max(entity_group, key=lambda e: e.confidence)
        action_content = best_entity.context.strip()
        
        # Create assignees
        assignees = []
        for person in persons:
            assignees.append(ActionItemAssignee(
                name=person.text,
                confidence=person.confidence,
                assignment_method="extracted",
                context={"extraction_method": person.extraction_method.value}
            ))
        
        # Create deadline
        deadline = None
        if deadlines:
            best_deadline = max(deadlines, key=lambda d: d.confidence)
            deadline = self._parse_deadline(best_deadline.text)
        
        # Determine priority
        priority = ActionItemPriority.MEDIUM
        if priorities:
            priority_text = priorities[0].text.lower()
            if any(word in priority_text for word in ['urgent', 'critical', 'asap', 'immediate', 'high']):
                priority = ActionItemPriority.HIGH
            elif any(word in priority_text for word in ['low', 'nice', 'when time']):
                priority = ActionItemPriority.LOW
        
        # Calculate overall confidence
        avg_confidence = sum(e.confidence for e in entity_group) / len(entity_group)
        
        # Determine extraction method
        methods = set(e.extraction_method for e in entity_group)
        if len(methods) > 1:
            extraction_method = ExtractionMethod.HYBRID
        else:
            extraction_method = list(methods)[0]
        
        action_item = ActionItem(
            id=self._generate_action_id(),
            content=action_content,
            priority=priority,
            status=ActionItemStatus.PENDING,
            assignees=assignees,
            deadline=deadline,
            confidence=avg_confidence,
            extraction_method=extraction_method,
            context={
                "session_id": self.session_id,
                "entity_count": len(entity_group),
                "methods_used": [m.value for m in methods]
            }
        )
        
        return action_item
    
    def _parse_deadline(self, deadline_text: str) -> Optional[ActionItemDeadline]:
        """Parse deadline text into structured deadline"""
        if not deadline_text:
            return None
        
        # Try dateutil parsing first
        parsed_date = None
        if DATEUTIL_AVAILABLE:
            try:
                parsed_date = date_parser.parse(deadline_text, fuzzy=True)
            except:
                pass
        
        # Fallback to rule-based parsing
        if not parsed_date:
            parsed_date = self._parse_deadline_rules(deadline_text)
        
        return ActionItemDeadline(
            deadline_type=DeadlineType.SPECIFIC_DATE if parsed_date else DeadlineType.UNSPECIFIED,
            original_text=deadline_text,
            parsed_date=parsed_date,
            confidence=0.8 if parsed_date else 0.3
        )
    
    def _parse_deadline_rules(self, deadline_text: str) -> Optional[datetime]:
        """Rule-based deadline parsing"""
        now = datetime.now()
        text = deadline_text.lower()
        
        if 'tomorrow' in text:
            return now + timedelta(days=1)
        elif 'today' in text:
            return now
        elif 'next week' in text:
            return now + timedelta(weeks=1)
        elif 'next month' in text:
            return now + timedelta(weeks=4)
        elif 'friday' in text:
            # Find next Friday
            days_ahead = 4 - now.weekday()  # Friday is 4
            if days_ahead <= 0:
                days_ahead += 7
            return now + timedelta(days=days_ahead)
        
        # Look for "in X days" pattern
        match = re.search(r'in\s+(\d+)\s+days?', text)
        if match:
            days = int(match.group(1))
            return now + timedelta(days=days)
        
        # Look for "X weeks" pattern
        match = re.search(r'(\d+)\s+weeks?', text)
        if match:
            weeks = int(match.group(1))
            return now + timedelta(weeks=weeks)
        
        return None
    
    def _generate_action_id(self) -> str:
        """Generate unique action item ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_suffix = hashlib.md5(f"{timestamp}{self.session_id}".encode()).hexdigest()[:8]
        return f"action_{timestamp}_{hash_suffix}"
    
    def _save_extraction_metrics(self, total_items: int, high_confidence: int, processing_time: float):
        """Save extraction metrics to database"""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.execute("""
                INSERT INTO extraction_metrics 
                (session_id, extraction_method, total_items, high_confidence, processing_time, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.session_id,
                "production_bert_ner",
                total_items,
                high_confidence,
                processing_time,
                datetime.now().isoformat()
            ))
    
    def get_action_items_by_status(self, status: ActionItemStatus) -> List[ActionItem]:
        """Get action items by status"""
        return self.db.get_action_items(status=status)
    
    def update_action_item_status(self, action_id: str, status: ActionItemStatus):
        """Update action item status"""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.execute("""
                UPDATE action_items SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status.value, datetime.now().isoformat(), action_id))
    
    def get_overdue_action_items(self) -> List[ActionItem]:
        """Get all overdue action items"""
        all_items = self.db.get_action_items()
        overdue_items = []
        
        for item in all_items:
            if item.deadline and item.deadline.is_overdue():
                if item.status != ActionItemStatus.COMPLETED:
                    item.status = ActionItemStatus.OVERDUE
                    overdue_items.append(item)
        
        return overdue_items
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        total_items = len(self.db.get_action_items())
        pending_items = len(self.db.get_action_items(ActionItemStatus.PENDING))
        overdue_items = len(self.get_overdue_action_items())
        
        extraction_methods = {
            "bert_available": self.bert_extractor.ner_pipeline is not None,
            "spacy_available": self.spacy_extractor.nlp is not None,
            "rule_based_available": True
        }
        
        return {
            "system_status": "operational",
            "total_action_items": total_items,
            "pending_items": pending_items,
            "overdue_items": overdue_items,
            "extraction_methods": extraction_methods,
            "database_path": self.db.db_path,
            "current_session": self.session_id
        }

def extract_action_items_from_meeting(transcript: str, meeting_id: str = None) -> List[ActionItem]:
    """Main entry point for action item extraction"""
    system = ActionItemExtractionSystem()
    return system.extract_action_items(transcript, meeting_id)

def main():
    """Demo the production action item extraction system"""
    print("=== Production Action Item Extraction System Demo ===\n")
    
    # Initialize system
    system = ActionItemExtractionSystem()
    
    # Sample meeting transcript
    transcript = """
    [14:00] Project Manager: Welcome to our weekly project review meeting.
    [14:02] Sarah: I'll complete the API documentation review by tomorrow end of day.
    [14:05] John: The dashboard implementation needs to be done by next Friday. Can you handle that, Mike?
    [14:07] Mike: Yes, I'll have the dashboard ready by Friday morning.
    [14:10] Project Manager: Alice, please prepare the client presentation urgently for Monday's meeting.
    [14:12] Alice: I'll work on the presentation this weekend to have it ready.
    [14:15] Project Manager: We also need someone to test the new authentication module.
    [14:17] Sarah: I can test the auth module after I finish the documentation review.
    [14:20] Project Manager: Great. Let's make sure all critical tasks are completed before the client demo.
    """
    
    # Extract action items
    print("Extracting action items...")
    action_items = system.extract_action_items(transcript, "weekly_review_001")
    
    # Display results
    print(f"\n✅ Extracted {len(action_items)} action items:\n")
    
    for i, item in enumerate(action_items, 1):
        print(f"{i}. {item.content}")
        print(f"   Priority: {item.priority.value.title()}")
        print(f"   Status: {item.status.value.title()}")
        print(f"   Confidence: {item.confidence:.2f}")
        print(f"   Method: {item.extraction_method.value}")
        
        if item.assignees:
            assignee_names = [a.name for a in item.assignees]
            print(f"   Assignees: {', '.join(assignee_names)}")
        
        if item.deadline:
            if item.deadline.parsed_date:
                print(f"   Deadline: {item.deadline.parsed_date.strftime('%Y-%m-%d')} ({item.deadline.original_text})")
            else:
                print(f"   Deadline: {item.deadline.original_text}")
        
        print()
    
    # Show system status
    status = system.get_system_status()
    print("=== System Status ===")
    for key, value in status.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()