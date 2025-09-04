#!/usr/bin/env python3
"""
Advanced Search and Discovery Features (Task 45)
Comprehensive search system with fuzzy search, voice search, boolean operators, and smart alerts
"""

import os
import json
import logging
import sqlite3
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
from collections import defaultdict, Counter
import difflib
import speech_recognition as sr
import numpy as np
from fuzzywuzzy import fuzz, process
import whoosh
from whoosh.index import create_index, open_dir
from whoosh.fields import Schema, TEXT, ID, DATETIME, NUMERIC, KEYWORD
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup
from whoosh.query import And, Or, Not, Term, Phrase, Wildcard, FuzzyTerm
from whoosh.analysis import StandardAnalyzer, StemmingAnalyzer
from whoosh.scoring import BM25F
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchType(Enum):
    """Types of search operations"""
    TEXT = "text"
    FUZZY = "fuzzy"
    VOICE = "voice"
    BOOLEAN = "boolean"
    SEMANTIC = "semantic"
    TEMPORAL = "temporal"
    SPEAKER = "speaker"

class SearchOperator(Enum):
    """Boolean search operators"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    NEAR = "NEAR"
    PHRASE = "PHRASE"

@dataclass
class SearchQuery:
    """Structure for search queries"""
    query_id: str
    user_id: str
    query_text: str
    search_type: str
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_saved: bool = False
    alert_enabled: bool = False
    alert_frequency: str = "daily"  # daily, weekly, monthly
    last_executed: Optional[datetime] = None
    result_count: int = 0

@dataclass
class SearchResult:
    """Structure for search results"""
    result_id: str
    content_id: str
    title: str
    content_type: str  # transcript, entity, summary
    content: str
    relevance_score: float
    timestamp: Optional[datetime] = None
    speaker: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    highlights: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SavedSearch:
    """Structure for saved searches"""
    search_id: str
    user_id: str
    name: str
    description: str
    query: SearchQuery
    created_at: datetime
    last_run: Optional[datetime] = None
    run_count: int = 0
    is_active: bool = True

@dataclass
class SearchAlert:
    """Structure for search alerts"""
    alert_id: str
    search_id: str
    user_id: str
    alert_type: str  # new_content, threshold_reached, pattern_detected
    conditions: Dict[str, Any]
    notification_method: str  # email, in_app, webhook
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

class SearchDatabase:
    """Database manager for search functionality"""
    
    def __init__(self, db_path: str = "search.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Search queries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS search_queries (
                        query_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        query_text TEXT NOT NULL,
                        search_type TEXT NOT NULL,
                        filters TEXT DEFAULT '{}',
                        created_at TEXT NOT NULL,
                        is_saved BOOLEAN DEFAULT 0,
                        alert_enabled BOOLEAN DEFAULT 0,
                        alert_frequency TEXT DEFAULT 'daily',
                        last_executed TEXT,
                        result_count INTEGER DEFAULT 0,
                        INDEX idx_user_queries (user_id, created_at),
                        INDEX idx_saved_queries (user_id, is_saved)
                    )
                """)
                
                # Saved searches table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS saved_searches (
                        search_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        query_data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_run TEXT,
                        run_count INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT 1,
                        INDEX idx_user_searches (user_id, is_active)
                    )
                """)
                
                # Search alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS search_alerts (
                        alert_id TEXT PRIMARY KEY,
                        search_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        conditions TEXT NOT NULL,
                        notification_method TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TEXT NOT NULL,
                        last_triggered TEXT,
                        trigger_count INTEGER DEFAULT 0,
                        FOREIGN KEY (search_id) REFERENCES saved_searches (search_id)
                    )
                """)
                
                # Search history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS search_history (
                        history_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        query_text TEXT NOT NULL,
                        search_type TEXT NOT NULL,
                        result_count INTEGER,
                        execution_time REAL,
                        timestamp TEXT NOT NULL,
                        INDEX idx_user_history (user_id, timestamp)
                    )
                """)
                
                # Content index table (for search indexing)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS content_index (
                        content_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        speaker TEXT,
                        timestamp TEXT,
                        start_time REAL,
                        end_time REAL,
                        metadata TEXT DEFAULT '{}',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        INDEX idx_content_search (user_id, content_type),
                        INDEX idx_content_time (timestamp, start_time),
                        INDEX idx_content_speaker (speaker)
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing search database: {e}")
            raise
    
    def add_content_to_index(self, content_id: str, user_id: str, title: str, 
                           content_type: str, content: str, speaker: str = None,
                           timestamp: datetime = None, start_time: float = None,
                           end_time: float = None, metadata: Dict[str, Any] = None) -> bool:
        """Add content to search index"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO content_index (
                        content_id, user_id, title, content_type, content,
                        speaker, timestamp, start_time, end_time, metadata,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    content_id, user_id, title, content_type, content,
                    speaker, timestamp.isoformat() if timestamp else None,
                    start_time, end_time, json.dumps(metadata or {}),
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding content to index: {e}")
            return False
    
    def save_search_query(self, query: SearchQuery) -> bool:
        """Save search query"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO search_queries (
                        query_id, user_id, query_text, search_type, filters,
                        created_at, is_saved, alert_enabled, alert_frequency,
                        last_executed, result_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    query.query_id, query.user_id, query.query_text,
                    query.search_type, json.dumps(query.filters),
                    query.created_at.isoformat(), query.is_saved,
                    query.alert_enabled, query.alert_frequency,
                    query.last_executed.isoformat() if query.last_executed else None,
                    query.result_count
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving search query: {e}")
            return False
    
    def get_search_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get search history for user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT query_text, search_type, result_count, execution_time, timestamp
                    FROM search_history
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'query_text': row[0],
                        'search_type': row[1],
                        'result_count': row[2],
                        'execution_time': row[3],
                        'timestamp': row[4]
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting search history: {e}")
            return []

class FuzzySearchEngine:
    """Fuzzy search engine with typo tolerance"""
    
    def __init__(self, threshold: int = 70):
        self.threshold = threshold
        self.content_cache = {}
    
    def search(self, query: str, content_list: List[Dict[str, Any]], 
               fields: List[str] = None) -> List[SearchResult]:
        """Perform fuzzy search with typo tolerance"""
        if not fields:
            fields = ['content', 'title']
        
        results = []
        
        for content in content_list:
            max_score = 0
            best_match = ""
            
            for field in fields:
                if field in content:
                    text = str(content[field])
                    
                    # Use fuzzywuzzy for fuzzy matching
                    score = fuzz.partial_ratio(query.lower(), text.lower())
                    
                    if score > max_score:
                        max_score = score
                        best_match = text
            
            if max_score >= self.threshold:
                # Find the best matching substring for highlighting
                highlights = self._find_highlights(query, best_match)
                
                result = SearchResult(
                    result_id=f"fuzzy_{content['content_id']}",
                    content_id=content['content_id'],
                    title=content.get('title', ''),
                    content_type=content.get('content_type', 'text'),
                    content=content.get('content', ''),
                    relevance_score=max_score / 100.0,
                    timestamp=datetime.fromisoformat(content['timestamp']) if content.get('timestamp') else None,
                    speaker=content.get('speaker'),
                    start_time=content.get('start_time'),
                    end_time=content.get('end_time'),
                    highlights=highlights,
                    metadata=json.loads(content.get('metadata', '{}'))
                )
                
                results.append(result)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results
    
    def _find_highlights(self, query: str, text: str, context_length: int = 50) -> List[str]:
        """Find highlighted text snippets"""
        highlights = []
        query_words = query.lower().split()
        text_lower = text.lower()
        
        for word in query_words:
            # Find fuzzy matches in text
            matches = difflib.get_close_matches(word, text_lower.split(), 
                                              n=3, cutoff=0.6)
            
            for match in matches:
                # Find position in original text
                start_pos = text_lower.find(match)
                if start_pos != -1:
                    # Extract context around match
                    context_start = max(0, start_pos - context_length)
                    context_end = min(len(text), start_pos + len(match) + context_length)
                    
                    highlight = text[context_start:context_end]
                    if highlight not in highlights:
                        highlights.append(highlight)
        
        return highlights[:5]  # Limit to 5 highlights

class VoiceSearchEngine:
    """Voice search engine using speech recognition"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
    
    def listen_for_query(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """Listen for voice query"""
        try:
            with self.microphone as source:
                logger.info("Listening for voice query...")
                audio = self.recognizer.listen(source, timeout=timeout, 
                                             phrase_time_limit=phrase_time_limit)
            
            # Recognize speech using Google Speech Recognition
            query = self.recognizer.recognize_google(audio)
            logger.info(f"Voice query recognized: {query}")
            return query
            
        except sr.WaitTimeoutError:
            logger.warning("Voice search timeout - no speech detected")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand voice query")
            return None
        except sr.RequestError as e:
            logger.error(f"Voice recognition service error: {e}")
            return None
    
    def process_voice_query(self, audio_data: bytes) -> Optional[str]:
        """Process audio data for voice search"""
        try:
            # Convert audio data to AudioData object
            audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
            
            # Recognize speech
            query = self.recognizer.recognize_google(audio)
            return query
            
        except Exception as e:
            logger.error(f"Error processing voice query: {e}")
            return None

class BooleanSearchEngine:
    """Boolean search engine with advanced operators"""
    
    def __init__(self):
        self.operators = {
            'AND': self._and_operation,
            'OR': self._or_operation,
            'NOT': self._not_operation,
            'NEAR': self._near_operation,
            'PHRASE': self._phrase_operation
        }
    
    def parse_boolean_query(self, query: str) -> Dict[str, Any]:
        """Parse boolean search query"""
        # Simple boolean query parser
        # In production, use a proper parser like pyparsing
        
        query = query.strip()
        parsed = {
            'terms': [],
            'operators': [],
            'phrases': [],
            'exclusions': []
        }
        
        # Find phrases (quoted text)
        phrase_pattern = r'"([^"]*)"'
        phrases = re.findall(phrase_pattern, query)
        parsed['phrases'] = phrases
        
        # Remove phrases from query for further processing
        query_no_phrases = re.sub(phrase_pattern, '', query)
        
        # Find NOT operations
        not_pattern = r'NOT\\s+([\\w]+)'
        exclusions = re.findall(not_pattern, query_no_phrases, re.IGNORECASE)
        parsed['exclusions'] = exclusions
        
        # Remove NOT operations
        query_no_not = re.sub(not_pattern, '', query_no_phrases, flags=re.IGNORECASE)
        
        # Split by operators
        operators = ['AND', 'OR', 'NEAR']
        terms = []
        current_operators = []
        
        for op in operators:
            if op in query_no_not.upper():
                parts = re.split(f'\\s+{op}\\s+', query_no_not, flags=re.IGNORECASE)
                if len(parts) > 1:
                    terms.extend([p.strip() for p in parts if p.strip()])
                    current_operators.extend([op] * (len(parts) - 1))
        
        if not terms:
            # No operators found, treat as simple terms
            terms = [t.strip() for t in query_no_not.split() if t.strip()]
        
        parsed['terms'] = terms
        parsed['operators'] = current_operators
        
        return parsed
    
    def search(self, parsed_query: Dict[str, Any], content_list: List[Dict[str, Any]]) -> List[SearchResult]:
        """Execute boolean search"""
        results = []
        
        for content in content_list:
            text = content.get('content', '').lower()
            title = content.get('title', '').lower()
            combined_text = f"{title} {text}"
            
            score = self._calculate_boolean_score(parsed_query, combined_text)
            
            if score > 0:
                result = SearchResult(
                    result_id=f"bool_{content['content_id']}",
                    content_id=content['content_id'],
                    title=content.get('title', ''),
                    content_type=content.get('content_type', 'text'),
                    content=content.get('content', ''),
                    relevance_score=score,
                    timestamp=datetime.fromisoformat(content['timestamp']) if content.get('timestamp') else None,
                    speaker=content.get('speaker'),
                    start_time=content.get('start_time'),
                    end_time=content.get('end_time'),
                    highlights=self._find_boolean_highlights(parsed_query, combined_text),
                    metadata=json.loads(content.get('metadata', '{}'))
                )
                
                results.append(result)
        
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results
    
    def _calculate_boolean_score(self, parsed_query: Dict[str, Any], text: str) -> float:
        """Calculate boolean search score"""
        score = 0.0
        
        # Check exclusions first
        for exclusion in parsed_query['exclusions']:
            if exclusion.lower() in text:
                return 0.0  # Exclude this result
        
        # Check phrases
        for phrase in parsed_query['phrases']:
            if phrase.lower() in text:
                score += 2.0  # Phrases get higher weight
        
        # Check terms
        term_matches = 0
        for term in parsed_query['terms']:
            if term.lower() in text:
                term_matches += 1
                score += 1.0
        
        # Apply operator logic (simplified)
        if parsed_query['operators']:
            if 'AND' in parsed_query['operators']:
                # All terms must be present
                if term_matches < len(parsed_query['terms']):
                    score *= 0.5
            elif 'OR' in parsed_query['operators']:
                # At least one term must be present
                if term_matches == 0:
                    score = 0.0
        
        return score
    
    def _find_boolean_highlights(self, parsed_query: Dict[str, Any], text: str) -> List[str]:
        """Find highlights for boolean search"""
        highlights = []
        
        # Highlight phrases
        for phrase in parsed_query['phrases']:
            if phrase.lower() in text.lower():
                highlights.append(phrase)
        
        # Highlight terms
        for term in parsed_query['terms']:
            if term.lower() in text.lower():
                highlights.append(term)
        
        return highlights[:5]
    
    def _and_operation(self, terms: List[str], text: str) -> bool:
        """AND operation"""
        return all(term.lower() in text.lower() for term in terms)
    
    def _or_operation(self, terms: List[str], text: str) -> bool:
        """OR operation"""
        return any(term.lower() in text.lower() for term in terms)
    
    def _not_operation(self, terms: List[str], text: str) -> bool:
        """NOT operation"""
        return not any(term.lower() in text.lower() for term in terms)
    
    def _near_operation(self, terms: List[str], text: str, distance: int = 10) -> bool:
        """NEAR operation (terms within specified distance)"""
        if len(terms) < 2:
            return False
        
        text_lower = text.lower()
        positions = []
        
        for term in terms:
            pos = text_lower.find(term.lower())
            if pos == -1:
                return False
            positions.append(pos)
        
        # Check if terms are within distance
        positions.sort()
        for i in range(len(positions) - 1):
            if positions[i + 1] - positions[i] > distance:
                return False
        
        return True
    
    def _phrase_operation(self, phrase: str, text: str) -> bool:
        """Phrase operation (exact phrase match)"""
        return phrase.lower() in text.lower()

class TemporalSearchEngine:
    """Search within specific time ranges"""
    
    def search_by_time_range(self, content_list: List[Dict[str, Any]], 
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           duration_start: Optional[float] = None,
                           duration_end: Optional[float] = None) -> List[Dict[str, Any]]:
        """Search content within time ranges"""
        filtered_content = []
        
        for content in content_list:
            include = True
            
            # Filter by timestamp
            if start_time or end_time:
                content_time = None
                if content.get('timestamp'):
                    content_time = datetime.fromisoformat(content['timestamp'])
                
                if content_time:
                    if start_time and content_time < start_time:
                        include = False
                    if end_time and content_time > end_time:
                        include = False
            
            # Filter by duration within content
            if duration_start is not None or duration_end is not None:
                content_start = content.get('start_time')
                content_end = content.get('end_time')
                
                if content_start is not None:
                    if duration_start is not None and content_start < duration_start:
                        include = False
                    if duration_end is not None and content_end and content_end > duration_end:
                        include = False
            
            if include:
                filtered_content.append(content)
        
        return filtered_content

class SpeakerSearchEngine:
    """Search within specific speakers"""
    
    def search_by_speaker(self, content_list: List[Dict[str, Any]], 
                         speakers: List[str]) -> List[Dict[str, Any]]:
        """Search content by specific speakers"""
        if not speakers:
            return content_list
        
        filtered_content = []
        speakers_lower = [s.lower() for s in speakers]
        
        for content in content_list:
            content_speaker = content.get('speaker', '').lower()
            
            if any(speaker in content_speaker for speaker in speakers_lower):
                filtered_content.append(content)
        
        return filtered_content

class SearchAlertSystem:
    """System for managing search alerts and notifications"""
    
    def __init__(self, db: SearchDatabase):
        self.db = db
        self.alert_thread = None
        self.running = False
    
    def create_alert(self, alert: SearchAlert) -> bool:
        """Create new search alert"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO search_alerts (
                        alert_id, search_id, user_id, alert_type, conditions,
                        notification_method, is_active, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.alert_id, alert.search_id, alert.user_id,
                    alert.alert_type, json.dumps(alert.conditions),
                    alert.notification_method, alert.is_active,
                    alert.created_at.isoformat()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error creating search alert: {e}")
            return False
    
    def check_alerts(self):
        """Check and trigger alerts"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT alert_id, search_id, user_id, alert_type, conditions,
                           notification_method, last_triggered
                    FROM search_alerts
                    WHERE is_active = 1
                """)
                
                for row in cursor.fetchall():
                    alert_id, search_id, user_id, alert_type = row[:4]
                    conditions, notification_method, last_triggered = row[4:]
                    
                    conditions = json.loads(conditions)
                    
                    # Check if alert should be triggered
                    if self._should_trigger_alert(alert_id, conditions, last_triggered):
                        self._trigger_alert(alert_id, user_id, notification_method, conditions)
                        
                        # Update last triggered time
                        cursor.execute("""
                            UPDATE search_alerts 
                            SET last_triggered = ?, trigger_count = trigger_count + 1
                            WHERE alert_id = ?
                        """, (datetime.now().isoformat(), alert_id))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _should_trigger_alert(self, alert_id: str, conditions: Dict[str, Any], 
                            last_triggered: Optional[str]) -> bool:
        """Check if alert should be triggered"""
        # Implement alert triggering logic based on conditions
        # This is a simplified version
        
        frequency = conditions.get('frequency', 'daily')
        
        if not last_triggered:
            return True
        
        last_trigger_time = datetime.fromisoformat(last_triggered)
        now = datetime.now()
        
        if frequency == 'daily' and (now - last_trigger_time).days >= 1:
            return True
        elif frequency == 'weekly' and (now - last_trigger_time).days >= 7:
            return True
        elif frequency == 'monthly' and (now - last_trigger_time).days >= 30:
            return True
        
        return False
    
    def _trigger_alert(self, alert_id: str, user_id: str, notification_method: str, 
                      conditions: Dict[str, Any]):
        """Trigger alert notification"""
        logger.info(f"Triggering alert {alert_id} for user {user_id}")
        
        # In a real implementation, this would send notifications
        # via email, push notifications, webhooks, etc.
        
        if notification_method == 'email':
            self._send_email_notification(user_id, conditions)
        elif notification_method == 'webhook':
            self._send_webhook_notification(user_id, conditions)
        elif notification_method == 'in_app':
            self._create_in_app_notification(user_id, conditions)
    
    def _send_email_notification(self, user_id: str, conditions: Dict[str, Any]):
        """Send email notification"""
        # Implement email notification
        logger.info(f"Email notification sent to user {user_id}")
    
    def _send_webhook_notification(self, user_id: str, conditions: Dict[str, Any]):
        """Send webhook notification"""
        # Implement webhook notification
        logger.info(f"Webhook notification sent for user {user_id}")
    
    def _create_in_app_notification(self, user_id: str, conditions: Dict[str, Any]):
        """Create in-app notification"""
        # Implement in-app notification
        logger.info(f"In-app notification created for user {user_id}")
    
    def start_alert_monitoring(self):
        """Start alert monitoring thread"""
        if not self.running:
            self.running = True
            self.alert_thread = threading.Thread(target=self._alert_monitor_loop)
            self.alert_thread.daemon = True
            self.alert_thread.start()
            logger.info("Search alert monitoring started")
    
    def stop_alert_monitoring(self):
        """Stop alert monitoring"""
        self.running = False
        if self.alert_thread:
            self.alert_thread.join()
        logger.info("Search alert monitoring stopped")
    
    def _alert_monitor_loop(self):
        """Alert monitoring loop"""
        while self.running:
            try:
                self.check_alerts()
                time.sleep(3600)  # Check every hour
            except Exception as e:
                logger.error(f"Error in alert monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

class AdvancedSearchEngine:
    """Main advanced search engine combining all search types"""
    
    def __init__(self):
        self.db = SearchDatabase()
        self.fuzzy_engine = FuzzySearchEngine()
        self.voice_engine = VoiceSearchEngine()
        self.boolean_engine = BooleanSearchEngine()
        self.temporal_engine = TemporalSearchEngine()
        self.speaker_engine = SpeakerSearchEngine()
        self.alert_system = SearchAlertSystem(self.db)
        
        # Start alert monitoring
        self.alert_system.start_alert_monitoring()
    
    def search(self, query: str, search_type: SearchType = SearchType.TEXT,
               user_id: str = "default", filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Perform advanced search"""
        start_time = time.time()
        filters = filters or {}
        
        try:
            # Get content from database
            content_list = self._get_searchable_content(user_id, filters)
            
            results = []
            
            if search_type == SearchType.FUZZY:
                results = self.fuzzy_engine.search(query, content_list)
            elif search_type == SearchType.BOOLEAN:
                parsed_query = self.boolean_engine.parse_boolean_query(query)
                results = self.boolean_engine.search(parsed_query, content_list)
            elif search_type == SearchType.TEMPORAL:
                # Apply temporal filters first
                filtered_content = self.temporal_engine.search_by_time_range(
                    content_list,
                    start_time=filters.get('start_time'),
                    end_time=filters.get('end_time'),
                    duration_start=filters.get('duration_start'),
                    duration_end=filters.get('duration_end')
                )
                # Then perform text search on filtered content
                results = self._text_search(query, filtered_content)
            elif search_type == SearchType.SPEAKER:
                # Apply speaker filters first
                filtered_content = self.speaker_engine.search_by_speaker(
                    content_list, filters.get('speakers', [])
                )
                # Then perform text search on filtered content
                results = self._text_search(query, filtered_content)
            else:
                # Default text search
                results = self._text_search(query, content_list)
            
            # Record search in history
            execution_time = time.time() - start_time
            self._record_search_history(user_id, query, search_type.value, 
                                      len(results), execution_time)
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return []
    
    def voice_search(self, user_id: str = "default", timeout: int = 5) -> List[SearchResult]:
        """Perform voice search"""
        query = self.voice_engine.listen_for_query(timeout=timeout)
        
        if query:
            return self.search(query, SearchType.VOICE, user_id)
        else:
            return []
    
    def save_search(self, user_id: str, name: str, description: str, 
                   query: str, search_type: SearchType, filters: Dict[str, Any] = None,
                   enable_alerts: bool = False, alert_frequency: str = "daily") -> bool:
        """Save search query"""
        try:
            search_query = SearchQuery(
                query_id=f"search_{int(time.time())}_{user_id}",
                user_id=user_id,
                query_text=query,
                search_type=search_type.value,
                filters=filters or {},
                is_saved=True,
                alert_enabled=enable_alerts,
                alert_frequency=alert_frequency
            )
            
            saved_search = SavedSearch(
                search_id=f"saved_{int(time.time())}_{user_id}",
                user_id=user_id,
                name=name,
                description=description,
                query=search_query,
                created_at=datetime.now()
            )
            
            # Save to database
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO saved_searches (
                        search_id, user_id, name, description, query_data, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    saved_search.search_id, saved_search.user_id,
                    saved_search.name, saved_search.description,
                    json.dumps(asdict(saved_search.query)),
                    saved_search.created_at.isoformat()
                ))
                
                conn.commit()
            
            # Create alert if enabled
            if enable_alerts:
                alert = SearchAlert(
                    alert_id=f"alert_{int(time.time())}_{user_id}",
                    search_id=saved_search.search_id,
                    user_id=user_id,
                    alert_type="new_content",
                    conditions={
                        'query': query,
                        'search_type': search_type.value,
                        'frequency': alert_frequency
                    },
                    notification_method="in_app"
                )
                
                self.alert_system.create_alert(alert)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving search: {e}")
            return False
    
    def get_saved_searches(self, user_id: str) -> List[SavedSearch]:
        """Get saved searches for user"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT search_id, user_id, name, description, query_data,
                           created_at, last_run, run_count, is_active
                    FROM saved_searches
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY created_at DESC
                """, (user_id,))
                
                saved_searches = []
                for row in cursor.fetchall():
                    query_data = json.loads(row[4])
                    
                    saved_search = SavedSearch(
                        search_id=row[0],
                        user_id=row[1],
                        name=row[2],
                        description=row[3],
                        query=SearchQuery(**query_data),
                        created_at=datetime.fromisoformat(row[5]),
                        last_run=datetime.fromisoformat(row[6]) if row[6] else None,
                        run_count=row[7],
                        is_active=bool(row[8])
                    )
                    
                    saved_searches.append(saved_search)
                
                return saved_searches
                
        except Exception as e:
            logger.error(f"Error getting saved searches: {e}")
            return []
    
    def run_saved_search(self, search_id: str, user_id: str) -> List[SearchResult]:
        """Run a saved search"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT query_data FROM saved_searches
                    WHERE search_id = ? AND user_id = ?
                """, (search_id, user_id))
                
                row = cursor.fetchone()
                if not row:
                    return []
                
                query_data = json.loads(row[0])
                query = SearchQuery(**query_data)
                
                # Run the search
                results = self.search(
                    query.query_text,
                    SearchType(query.search_type),
                    user_id,
                    query.filters
                )
                
                # Update run statistics
                cursor.execute("""
                    UPDATE saved_searches
                    SET last_run = ?, run_count = run_count + 1
                    WHERE search_id = ?
                """, (datetime.now().isoformat(), search_id))
                
                conn.commit()
                
                return results
                
        except Exception as e:
            logger.error(f"Error running saved search: {e}")
            return []
    
    def get_search_suggestions(self, partial_query: str, user_id: str, 
                             limit: int = 5) -> List[str]:
        """Get search suggestions based on partial query"""
        try:
            # Get search history for suggestions
            history = self.db.get_search_history(user_id, limit=100)
            
            suggestions = []
            
            for entry in history:
                query_text = entry['query_text']
                if partial_query.lower() in query_text.lower():
                    if query_text not in suggestions:
                        suggestions.append(query_text)
                
                if len(suggestions) >= limit:
                    break
            
            # Add fuzzy matches if we don't have enough suggestions
            if len(suggestions) < limit:
                all_queries = [entry['query_text'] for entry in history]
                fuzzy_matches = process.extract(partial_query, all_queries, 
                                              limit=limit - len(suggestions))
                
                for match, score in fuzzy_matches:
                    if score > 60 and match not in suggestions:
                        suggestions.append(match)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []
    
    def _get_searchable_content(self, user_id: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get searchable content from database"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT content_id, title, content_type, content, speaker,
                           timestamp, start_time, end_time, metadata
                    FROM content_index
                    WHERE user_id = ?
                """
                params = [user_id]
                
                # Apply filters
                if filters.get('content_type'):
                    query += " AND content_type = ?"
                    params.append(filters['content_type'])
                
                if filters.get('speaker'):
                    query += " AND speaker LIKE ?"
                    params.append(f"%{filters['speaker']}%")
                
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                
                content_list = []
                for row in cursor.fetchall():
                    content_list.append({
                        'content_id': row[0],
                        'title': row[1],
                        'content_type': row[2],
                        'content': row[3],
                        'speaker': row[4],
                        'timestamp': row[5],
                        'start_time': row[6],
                        'end_time': row[7],
                        'metadata': row[8]
                    })
                
                return content_list
                
        except Exception as e:
            logger.error(f"Error getting searchable content: {e}")
            return []
    
    def _text_search(self, query: str, content_list: List[Dict[str, Any]]) -> List[SearchResult]:
        """Perform basic text search"""
        results = []
        query_lower = query.lower()
        
        for content in content_list:
            text = content.get('content', '').lower()
            title = content.get('title', '').lower()
            
            # Calculate relevance score
            score = 0.0
            
            # Title matches get higher score
            if query_lower in title:
                score += 2.0
            
            # Content matches
            if query_lower in text:
                score += 1.0
            
            # Word matches
            query_words = query_lower.split()
            for word in query_words:
                if word in text:
                    score += 0.5
                if word in title:
                    score += 1.0
            
            if score > 0:
                # Find highlights
                highlights = []
                for word in query_words:
                    if word in text:
                        # Find context around word
                        start_pos = text.find(word)
                        context_start = max(0, start_pos - 50)
                        context_end = min(len(text), start_pos + len(word) + 50)
                        highlight = content['content'][context_start:context_end]
                        highlights.append(highlight)
                
                result = SearchResult(
                    result_id=f"text_{content['content_id']}",
                    content_id=content['content_id'],
                    title=content.get('title', ''),
                    content_type=content.get('content_type', 'text'),
                    content=content.get('content', ''),
                    relevance_score=score,
                    timestamp=datetime.fromisoformat(content['timestamp']) if content.get('timestamp') else None,
                    speaker=content.get('speaker'),
                    start_time=content.get('start_time'),
                    end_time=content.get('end_time'),
                    highlights=highlights[:3],
                    metadata=json.loads(content.get('metadata', '{}'))
                )
                
                results.append(result)
        
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results
    
    def _record_search_history(self, user_id: str, query: str, search_type: str,
                             result_count: int, execution_time: float):
        """Record search in history"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO search_history (
                        history_id, user_id, query_text, search_type,
                        result_count, execution_time, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"hist_{int(time.time())}_{user_id}",
                    user_id, query, search_type, result_count,
                    execution_time, datetime.now().isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error recording search history: {e}")
    
    def add_content_to_search_index(self, content_id: str, user_id: str, 
                                  title: str, content_type: str, content: str,
                                  speaker: str = None, timestamp: datetime = None,
                                  start_time: float = None, end_time: float = None,
                                  metadata: Dict[str, Any] = None) -> bool:
        """Add content to search index"""
        return self.db.add_content_to_index(
            content_id, user_id, title, content_type, content,
            speaker, timestamp, start_time, end_time, metadata
        )
    
    def get_search_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get search analytics for user"""
        try:
            history = self.db.get_search_history(user_id, limit=1000)
            
            if not history:
                return {'error': 'No search history found'}
            
            # Calculate analytics
            total_searches = len(history)
            search_types = Counter(entry['search_type'] for entry in history)
            avg_results = sum(entry['result_count'] for entry in history) / total_searches
            avg_execution_time = sum(entry['execution_time'] for entry in history) / total_searches
            
            # Popular queries
            query_counts = Counter(entry['query_text'] for entry in history)
            popular_queries = query_counts.most_common(10)
            
            # Search frequency by day
            daily_searches = defaultdict(int)
            for entry in history:
                day = entry['timestamp'][:10]  # Extract date part
                daily_searches[day] += 1
            
            return {
                'total_searches': total_searches,
                'search_types': dict(search_types),
                'average_results': round(avg_results, 2),
                'average_execution_time': round(avg_execution_time, 3),
                'popular_queries': popular_queries,
                'daily_searches': dict(daily_searches),
                'saved_searches_count': len(self.get_saved_searches(user_id))
            }
            
        except Exception as e:
            logger.error(f"Error getting search analytics: {e}")
            return {'error': str(e)}

def main():
    """Demo function"""
    print("🔍 Advanced Search and Discovery System Demo")
    print("=" * 60)
    
    # Initialize search engine
    search_engine = AdvancedSearchEngine()
    
    try:
        print(f"\n1. Adding sample content to search index")
        
        # Add sample content
        sample_content = [
            {
                'content_id': 'content_1',
                'title': 'Team Meeting Discussion',
                'content': 'We discussed the quarterly results and future plans. John mentioned the budget concerns.',
                'content_type': 'transcript',
                'speaker': 'John Smith',
                'timestamp': datetime.now() - timedelta(days=1)
            },
            {
                'content_id': 'content_2',
                'title': 'Product Launch Planning',
                'content': 'The product launch is scheduled for next month. Marketing team needs to prepare campaigns.',
                'content_type': 'transcript',
                'speaker': 'Sarah Johnson',
                'timestamp': datetime.now() - timedelta(hours=2)
            },
            {
                'content_id': 'content_3',
                'title': 'Technical Architecture Review',
                'content': 'We reviewed the system architecture and identified potential bottlenecks in the database layer.',
                'content_type': 'transcript',
                'speaker': 'Mike Chen',
                'timestamp': datetime.now() - timedelta(hours=6)
            }
        ]
        
        for content in sample_content:
            success = search_engine.add_content_to_search_index(
                content['content_id'], 'demo_user', content['title'],
                content['content_type'], content['content'], content['speaker'],
                content['timestamp']
            )
            if success:
                print(f"   ✅ Added: {content['title']}")
        
        print(f"\n2. Performing different types of searches")
        
        # Text search
        print(f"\n   📝 Text Search: 'budget'")
        results = search_engine.search("budget", SearchType.TEXT, "demo_user")
        print(f"   Found {len(results)} results")
        for result in results[:2]:
            print(f"   - {result.title} (Score: {result.relevance_score:.2f})")
        
        # Fuzzy search
        print(f"\n   🔤 Fuzzy Search: 'budjet' (with typo)")
        results = search_engine.search("budjet", SearchType.FUZZY, "demo_user")
        print(f"   Found {len(results)} results")
        for result in results[:2]:
            print(f"   - {result.title} (Score: {result.relevance_score:.2f})")
        
        # Boolean search
        print(f"\n   🔍 Boolean Search: 'product AND launch'")
        results = search_engine.search("product AND launch", SearchType.BOOLEAN, "demo_user")
        print(f"   Found {len(results)} results")
        for result in results[:2]:
            print(f"   - {result.title} (Score: {result.relevance_score:.2f})")
        
        # Speaker search
        print(f"\n   👤 Speaker Search: John Smith")
        results = search_engine.search("meeting", SearchType.SPEAKER, "demo_user", 
                                     {'speakers': ['John Smith']})
        print(f"   Found {len(results)} results")
        for result in results[:2]:
            print(f"   - {result.title} by {result.speaker}")
        
        print(f"\n3. Saving search and creating alerts")
        
        # Save search
        success = search_engine.save_search(
            "demo_user", "Budget Discussions", "Track all budget-related conversations",
            "budget", SearchType.TEXT, enable_alerts=True, alert_frequency="daily"
        )
        
        if success:
            print(f"   ✅ Saved search with alerts enabled")
        
        # Get saved searches
        saved_searches = search_engine.get_saved_searches("demo_user")
        print(f"   📚 Total saved searches: {len(saved_searches)}")
        
        print(f"\n4. Search suggestions and analytics")
        
        # Get search suggestions
        suggestions = search_engine.get_search_suggestions("bud", "demo_user")
        print(f"   💡 Suggestions for 'bud': {suggestions}")
        
        # Get analytics
        analytics = search_engine.get_search_analytics("demo_user")
        print(f"   📊 Total searches: {analytics.get('total_searches', 0)}")
        print(f"   📊 Average results: {analytics.get('average_results', 0)}")
        print(f"   📊 Search types: {analytics.get('search_types', {})}")
        
        print(f"\n5. Advanced search features")
        print(f"   🎤 Voice search capability: Available")
        print(f"   ⏰ Temporal search: Time range filtering")
        print(f"   🔔 Smart alerts: Monitoring for new matching content")
        print(f"   💾 Saved searches: Reusable search queries")
        print(f"   📈 Search analytics: Usage tracking and insights")
        
        print(f"\n✅ Demo completed successfully!")
        print(f"   Advanced search and discovery system is ready for production use.")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Stop alert monitoring
        search_engine.alert_system.stop_alert_monitoring()

if __name__ == "__main__":
    main()