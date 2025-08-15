"""
Content Intent Classification System (Task 289)

This system provides:
- Intent detection and classification for various content types
- Multi-domain intent recognition (business, education, entertainment, technical)
- Confidence scoring and intent hierarchy
- Real-time intent tracking and analytics
- Custom intent model training capabilities
"""

import os
import sqlite3
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib

# Mock ML imports with fallbacks
try:
    import numpy as np
except ImportError:
    np = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
except ImportError:
    TfidfVectorizer = None
    MultinomialNB = None
    Pipeline = None

class IntentDomain(Enum):
    BUSINESS = "business"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    TECHNICAL = "technical"
    MEDICAL = "medical"
    LEGAL = "legal"
    CUSTOMER_SERVICE = "customer_service"
    PERSONAL = "personal"
    NEWS = "news"
    RESEARCH = "research"

class IntentCategory(Enum):
    # Business intents
    MEETING = "meeting"
    PRESENTATION = "presentation"
    NEGOTIATION = "negotiation"
    SALES_CALL = "sales_call"
    TRAINING = "training"
    INTERVIEW = "interview"
    
    # Educational intents
    LECTURE = "lecture"
    TUTORIAL = "tutorial"
    DISCUSSION = "discussion"
    Q_AND_A = "q_and_a"
    ASSESSMENT = "assessment"
    
    # Entertainment intents
    PODCAST = "podcast"
    STORYTELLING = "storytelling"
    COMEDY = "comedy"
    MUSIC_DISCUSSION = "music_discussion"
    
    # Technical intents
    CODE_REVIEW = "code_review"
    TECHNICAL_EXPLANATION = "technical_explanation"
    TROUBLESHOOTING = "troubleshooting"
    DOCUMENTATION = "documentation"
    
    # Medical intents
    CONSULTATION = "consultation"
    DIAGNOSIS = "diagnosis"
    TREATMENT_DISCUSSION = "treatment_discussion"
    
    # Legal intents
    LEGAL_CONSULTATION = "legal_consultation"
    CONTRACT_REVIEW = "contract_review"
    TESTIMONY = "testimony"
    
    # Customer service intents
    SUPPORT_CALL = "support_call"
    COMPLAINT = "complaint"
    INQUIRY = "inquiry"
    FEEDBACK = "feedback"
    
    # Personal intents
    CONVERSATION = "conversation"
    PLANNING = "planning"
    DECISION_MAKING = "decision_making"
    
    # News intents
    NEWS_REPORT = "news_report"
    COMMENTARY = "commentary"
    ANALYSIS = "analysis"
    
    # Research intents
    RESEARCH_INTERVIEW = "research_interview"
    DATA_ANALYSIS = "data_analysis"
    FINDINGS_PRESENTATION = "findings_presentation"

class ConfidenceLevel(Enum):
    VERY_HIGH = "very_high"  # 90-100%
    HIGH = "high"            # 75-89%
    MEDIUM = "medium"        # 50-74%
    LOW = "low"              # 25-49%
    VERY_LOW = "very_low"    # 0-24%

@dataclass
class IntentFeatures:
    """Features extracted from content for intent classification"""
    keyword_matches: Dict[str, float]
    structural_indicators: Dict[str, bool]
    linguistic_patterns: Dict[str, float]
    context_clues: Dict[str, Any]
    speaker_patterns: Dict[str, float]

@dataclass
class IntentPrediction:
    intent_category: IntentCategory
    confidence_score: float
    confidence_level: ConfidenceLevel
    domain: IntentDomain
    supporting_evidence: List[str]
    alternative_intents: List[Tuple[IntentCategory, float]] = field(default_factory=list)

@dataclass
class ContentAnalysis:
    content_id: str
    content_type: str
    primary_intent: IntentPrediction
    secondary_intents: List[IntentPrediction]
    content_summary: str
    key_topics: List[str]
    speaker_roles: Dict[str, List[str]]
    temporal_structure: Dict[str, Any]
    complexity_score: float
    engagement_indicators: Dict[str, float]

@dataclass
class IntentModel:
    model_id: str
    domain: IntentDomain
    training_data_size: int
    accuracy_score: float
    model_version: str
    last_trained: datetime
    feature_importance: Dict[str, float]

class ContentIntentClassificationSystem:
    def __init__(self, database_path: str = "content_intent_system.db"):
        self.database_path = database_path
        self.intent_patterns = self._initialize_intent_patterns()
        self.domain_keywords = self._initialize_domain_keywords()
        self.trained_models = {}
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for storing intent analysis and models"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id TEXT UNIQUE NOT NULL,
            content_type TEXT,
            content_hash TEXT,
            primary_intent TEXT,
            primary_confidence REAL,
            primary_domain TEXT,
            secondary_intents TEXT,
            content_summary TEXT,
            key_topics TEXT,
            speaker_roles TEXT,
            temporal_structure TEXT,
            complexity_score REAL,
            engagement_indicators TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS intent_models (
            model_id TEXT PRIMARY KEY,
            domain TEXT,
            training_data_size INTEGER,
            accuracy_score REAL,
            model_version TEXT,
            last_trained TIMESTAMP,
            feature_importance TEXT,
            model_data BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS intent_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id TEXT,
            predicted_intent TEXT,
            actual_intent TEXT,
            confidence_score REAL,
            feedback_type TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS intent_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            intent_category TEXT,
            prediction_count INTEGER,
            accuracy_rate REAL,
            avg_confidence REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def _initialize_intent_patterns(self) -> Dict[IntentCategory, Dict[str, Any]]:
        """Initialize patterns for different intent categories"""
        return {
            IntentCategory.MEETING: {
                "keywords": ["agenda", "action items", "follow up", "next steps", "meeting", "discuss", "review"],
                "phrases": ["let's start", "moving on", "any questions", "wrap up", "schedule"],
                "structural": ["speaker_transitions", "time_references", "task_assignments"],
                "roles": ["facilitator", "participant", "presenter"]
            },
            
            IntentCategory.PRESENTATION: {
                "keywords": ["slide", "chart", "data", "results", "findings", "demonstrate", "show"],
                "phrases": ["as you can see", "next slide", "in conclusion", "to summarize"],
                "structural": ["visual_references", "sequential_flow", "conclusion_markers"],
                "roles": ["presenter", "audience"]
            },
            
            IntentCategory.LECTURE: {
                "keywords": ["lesson", "chapter", "concept", "theory", "example", "definition", "explain"],
                "phrases": ["today we'll learn", "let me explain", "for example", "remember that"],
                "structural": ["educational_flow", "concept_building", "examples"],
                "roles": ["instructor", "student"]
            },
            
            IntentCategory.TUTORIAL: {
                "keywords": ["step", "instruction", "how to", "process", "method", "procedure"],
                "phrases": ["first step", "next you need", "make sure to", "common mistake"],
                "structural": ["step_by_step", "instructions", "troubleshooting"],
                "roles": ["instructor", "learner"]
            },
            
            IntentCategory.SUPPORT_CALL: {
                "keywords": ["problem", "issue", "help", "assistance", "ticket", "error", "bug"],
                "phrases": ["I'm having trouble", "can you help", "it's not working", "resolve"],
                "structural": ["problem_description", "solution_attempts", "resolution"],
                "roles": ["customer", "support_agent"]
            },
            
            IntentCategory.INTERVIEW: {
                "keywords": ["experience", "background", "skills", "position", "role", "career"],
                "phrases": ["tell me about", "what would you", "your experience with", "why did you"],
                "structural": ["question_answer", "candidate_assessment", "evaluation"],
                "roles": ["interviewer", "candidate"]
            },
            
            IntentCategory.CONSULTATION: {
                "keywords": ["symptoms", "condition", "treatment", "diagnosis", "health", "medical"],
                "phrases": ["how long have you", "any pain", "medical history", "recommend"],
                "structural": ["symptom_discussion", "medical_assessment", "treatment_plan"],
                "roles": ["doctor", "patient"]
            },
            
            IntentCategory.CODE_REVIEW: {
                "keywords": ["code", "function", "variable", "bug", "performance", "refactor"],
                "phrases": ["this code", "we should", "better approach", "code quality"],
                "structural": ["code_analysis", "improvement_suggestions", "technical_discussion"],
                "roles": ["reviewer", "developer"]
            }
        }

    def _initialize_domain_keywords(self) -> Dict[IntentDomain, List[str]]:
        """Initialize domain-specific keywords"""
        return {
            IntentDomain.BUSINESS: [
                "revenue", "profit", "sales", "market", "strategy", "customer", "client",
                "budget", "ROI", "KPI", "metrics", "growth", "competition", "stakeholder"
            ],
            IntentDomain.EDUCATION: [
                "student", "teacher", "curriculum", "assignment", "grade", "exam", "course",
                "learning", "study", "knowledge", "skill", "assessment", "academic"
            ],
            IntentDomain.TECHNICAL: [
                "software", "hardware", "system", "network", "database", "algorithm",
                "programming", "code", "server", "API", "framework", "deployment"
            ],
            IntentDomain.MEDICAL: [
                "patient", "doctor", "treatment", "diagnosis", "symptom", "medicine",
                "therapy", "hospital", "clinic", "health", "medical", "prescription"
            ],
            IntentDomain.LEGAL: [
                "law", "legal", "court", "judge", "attorney", "contract", "rights",
                "case", "lawsuit", "evidence", "testimony", "regulation", "compliance"
            ],
            IntentDomain.CUSTOMER_SERVICE: [
                "customer", "service", "support", "help", "assistance", "problem",
                "issue", "complaint", "feedback", "satisfaction", "resolution"
            ]
        }

    def analyze_content_intent(self, content: str, content_type: str = "transcript",
                             content_id: Optional[str] = None) -> ContentAnalysis:
        """Analyze content to determine intent and extract insights"""
        
        if not content_id:
            content_id = f"content_{hashlib.md5(content.encode()).hexdigest()[:12]}"
        
        # Extract features from content
        features = self._extract_intent_features(content)
        
        # Predict primary intent
        primary_intent = self._predict_intent(content, features)
        
        # Find secondary intents
        secondary_intents = self._find_secondary_intents(content, features, primary_intent)
        
        # Analyze content structure and metadata
        content_summary = self._generate_content_summary(content)
        key_topics = self._extract_key_topics(content)
        speaker_roles = self._analyze_speaker_roles(content, primary_intent)
        temporal_structure = self._analyze_temporal_structure(content)
        complexity_score = self._calculate_complexity_score(content, features)
        engagement_indicators = self._analyze_engagement_indicators(content)
        
        analysis = ContentAnalysis(
            content_id=content_id,
            content_type=content_type,
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            content_summary=content_summary,
            key_topics=key_topics,
            speaker_roles=speaker_roles,
            temporal_structure=temporal_structure,
            complexity_score=complexity_score,
            engagement_indicators=engagement_indicators
        )
        
        # Store analysis in database
        self._store_content_analysis(analysis)
        
        return analysis

    def _extract_intent_features(self, content: str) -> IntentFeatures:
        """Extract features from content for intent classification"""
        
        # Keyword matching
        keyword_matches = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            word_count = len(content.split())
            
            for keyword in patterns["keywords"]:
                count = content.lower().count(keyword.lower())
                score += count / word_count if word_count > 0 else 0
            
            for phrase in patterns["phrases"]:
                count = content.lower().count(phrase.lower())
                score += (count * 2) / word_count if word_count > 0 else 0
            
            keyword_matches[intent.value] = score
        
        # Structural indicators
        structural_indicators = {
            "has_questions": bool(re.search(r'\?', content)),
            "has_time_references": bool(re.search(r'\b(?:today|tomorrow|yesterday|next|last)\b', content, re.IGNORECASE)),
            "has_action_words": bool(re.search(r'\b(?:will|should|must|need to|have to)\b', content, re.IGNORECASE)),
            "has_speaker_changes": content.count(':') > 3 or content.count('\n') > 10,
            "has_technical_terms": bool(re.search(r'\b(?:API|database|server|algorithm|code)\b', content, re.IGNORECASE)),
            "has_business_terms": bool(re.search(r'\b(?:revenue|profit|ROI|KPI|strategy)\b', content, re.IGNORECASE))
        }
        
        # Linguistic patterns
        linguistic_patterns = {
            "avg_sentence_length": self._calculate_avg_sentence_length(content),
            "question_ratio": content.count('?') / len(content.split()) if content.split() else 0,
            "formal_language_score": self._calculate_formality_score(content),
            "technical_complexity": self._calculate_technical_complexity(content),
            "emotional_tone": self._analyze_emotional_tone(content)
        }
        
        # Context clues
        context_clues = {
            "content_length": len(content),
            "word_count": len(content.split()),
            "unique_words": len(set(content.lower().split())),
            "speaker_count": self._estimate_speaker_count(content)
        }
        
        # Speaker patterns
        speaker_patterns = {
            "dialogue_ratio": self._calculate_dialogue_ratio(content),
            "monologue_segments": self._count_monologue_segments(content),
            "interruption_indicators": content.lower().count("excuse me") + content.lower().count("sorry to interrupt")
        }
        
        return IntentFeatures(
            keyword_matches=keyword_matches,
            structural_indicators=structural_indicators,
            linguistic_patterns=linguistic_patterns,
            context_clues=context_clues,
            speaker_patterns=speaker_patterns
        )

    def _predict_intent(self, content: str, features: IntentFeatures) -> IntentPrediction:
        """Predict the primary intent of the content"""
        
        # Calculate scores for each intent category
        intent_scores = {}
        
        # Base score from keyword matching
        for intent, score in features.keyword_matches.items():
            intent_scores[intent] = score
        
        # Adjust scores based on structural indicators
        if features.structural_indicators["has_questions"]:
            intent_scores["q_and_a"] = intent_scores.get("q_and_a", 0) + 0.3
            intent_scores["interview"] = intent_scores.get("interview", 0) + 0.2
            intent_scores["support_call"] = intent_scores.get("support_call", 0) + 0.2
        
        if features.structural_indicators["has_action_words"]:
            intent_scores["meeting"] = intent_scores.get("meeting", 0) + 0.2
            intent_scores["tutorial"] = intent_scores.get("tutorial", 0) + 0.2
            intent_scores["planning"] = intent_scores.get("planning", 0) + 0.2
        
        if features.structural_indicators["has_technical_terms"]:
            intent_scores["code_review"] = intent_scores.get("code_review", 0) + 0.3
            intent_scores["technical_explanation"] = intent_scores.get("technical_explanation", 0) + 0.3
            intent_scores["troubleshooting"] = intent_scores.get("troubleshooting", 0) + 0.2
        
        # Adjust for linguistic patterns
        if features.linguistic_patterns["formal_language_score"] > 0.7:
            intent_scores["presentation"] = intent_scores.get("presentation", 0) + 0.2
            intent_scores["lecture"] = intent_scores.get("lecture", 0) + 0.2
            intent_scores["legal_consultation"] = intent_scores.get("legal_consultation", 0) + 0.1
        
        if features.linguistic_patterns["technical_complexity"] > 0.6:
            intent_scores["technical_explanation"] = intent_scores.get("technical_explanation", 0) + 0.2
            intent_scores["research_interview"] = intent_scores.get("research_interview", 0) + 0.1
        
        # Find best intent
        if not intent_scores:
            best_intent = IntentCategory.CONVERSATION
            confidence = 0.3
        else:
            best_intent_name = max(intent_scores, key=intent_scores.get)
            confidence = min(1.0, intent_scores[best_intent_name])
            try:
                best_intent = IntentCategory(best_intent_name)
            except ValueError:
                best_intent = IntentCategory.CONVERSATION
                confidence = 0.3
        
        # Determine confidence level
        if confidence >= 0.9:
            confidence_level = ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.75:
            confidence_level = ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            confidence_level = ConfidenceLevel.MEDIUM
        elif confidence >= 0.25:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.VERY_LOW
        
        # Determine domain
        domain = self._determine_domain(content, best_intent)
        
        # Find supporting evidence
        supporting_evidence = self._find_supporting_evidence(content, best_intent)
        
        # Find alternative intents
        alternative_intents = []
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        for intent_name, score in sorted_intents[1:4]:  # Top 3 alternatives
            if score > 0.1:
                try:
                    intent_cat = IntentCategory(intent_name)
                    alternative_intents.append((intent_cat, score))
                except ValueError:
                    continue
        
        return IntentPrediction(
            intent_category=best_intent,
            confidence_score=confidence,
            confidence_level=confidence_level,
            domain=domain,
            supporting_evidence=supporting_evidence,
            alternative_intents=alternative_intents
        )

    def _determine_domain(self, content: str, intent: IntentCategory) -> IntentDomain:
        """Determine the domain based on content and intent"""
        
        # Calculate domain scores
        domain_scores = {}
        content_lower = content.lower()
        
        for domain, keywords in self.domain_keywords.items():
            score = sum(content_lower.count(keyword) for keyword in keywords)
            domain_scores[domain] = score / len(content.split()) if content.split() else 0
        
        # Intent-based domain mapping
        intent_domain_map = {
            IntentCategory.MEETING: IntentDomain.BUSINESS,
            IntentCategory.PRESENTATION: IntentDomain.BUSINESS,
            IntentCategory.SALES_CALL: IntentDomain.BUSINESS,
            IntentCategory.LECTURE: IntentDomain.EDUCATION,
            IntentCategory.TUTORIAL: IntentDomain.EDUCATION,
            IntentCategory.CODE_REVIEW: IntentDomain.TECHNICAL,
            IntentCategory.TECHNICAL_EXPLANATION: IntentDomain.TECHNICAL,
            IntentCategory.CONSULTATION: IntentDomain.MEDICAL,
            IntentCategory.SUPPORT_CALL: IntentDomain.CUSTOMER_SERVICE,
            IntentCategory.LEGAL_CONSULTATION: IntentDomain.LEGAL
        }
        
        # Use intent mapping if available and domain score is not significantly higher
        suggested_domain = intent_domain_map.get(intent)
        if suggested_domain and domain_scores:
            max_score_domain = max(domain_scores, key=domain_scores.get)
            max_score = domain_scores[max_score_domain]
            suggested_score = domain_scores.get(suggested_domain, 0)
            
            if suggested_score >= max_score * 0.5:  # Within 50% of max score
                return suggested_domain
            else:
                return max_score_domain
        elif suggested_domain:
            return suggested_domain
        elif domain_scores:
            return max(domain_scores, key=domain_scores.get)
        else:
            return IntentDomain.PERSONAL

    def _find_supporting_evidence(self, content: str, intent: IntentCategory) -> List[str]:
        """Find specific evidence supporting the intent classification"""
        evidence = []
        content_lower = content.lower()
        
        if intent in self.intent_patterns:
            patterns = self.intent_patterns[intent]
            
            # Find keyword matches
            found_keywords = [kw for kw in patterns["keywords"] if kw in content_lower]
            if found_keywords:
                evidence.append(f"Keywords: {', '.join(found_keywords[:3])}")
            
            # Find phrase matches
            found_phrases = [phrase for phrase in patterns["phrases"] if phrase in content_lower]
            if found_phrases:
                evidence.append(f"Phrases: {', '.join(found_phrases[:2])}")
            
            # Add structural evidence
            if intent == IntentCategory.MEETING and ":" in content:
                evidence.append("Multiple speakers detected")
            if intent == IntentCategory.TUTORIAL and re.search(r'\bstep \d+\b', content_lower):
                evidence.append("Step-by-step structure detected")
            if intent == IntentCategory.PRESENTATION and re.search(r'\bslide\b', content_lower):
                evidence.append("Visual presentation indicators")
        
        return evidence[:5]  # Limit to top 5 pieces of evidence

    def _find_secondary_intents(self, content: str, features: IntentFeatures, 
                              primary_intent: IntentPrediction) -> List[IntentPrediction]:
        """Find secondary intents in the content"""
        secondary_intents = []
        
        # Use alternative intents from primary prediction
        for alt_intent, score in primary_intent.alternative_intents:
            if score > 0.3:  # Significant secondary intent
                domain = self._determine_domain(content, alt_intent)
                evidence = self._find_supporting_evidence(content, alt_intent)
                
                confidence_level = ConfidenceLevel.MEDIUM if score > 0.5 else ConfidenceLevel.LOW
                
                secondary_intent = IntentPrediction(
                    intent_category=alt_intent,
                    confidence_score=score,
                    confidence_level=confidence_level,
                    domain=domain,
                    supporting_evidence=evidence
                )
                secondary_intents.append(secondary_intent)
        
        return secondary_intents[:3]  # Limit to top 3 secondary intents

    def _generate_content_summary(self, content: str) -> str:
        """Generate a brief summary of the content"""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 2:
            return content[:200] + "..." if len(content) > 200 else content
        
        # Take first and last sentence, plus middle if content is long
        summary_parts = [sentences[0]]
        if len(sentences) > 4:
            summary_parts.append(sentences[len(sentences)//2])
        summary_parts.append(sentences[-1])
        
        summary = " ".join(summary_parts)
        return summary[:300] + "..." if len(summary) > 300 else summary

    def _extract_key_topics(self, content: str) -> List[str]:
        """Extract key topics from content"""
        # Simple keyword extraction based on frequency and relevance
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        
        # Filter out common words
        stop_words = {'that', 'this', 'with', 'from', 'they', 'been', 'have', 'were', 'said', 'each', 'which', 'their', 'time', 'will', 'about', 'would', 'there', 'could', 'other', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only', 'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before', 'here', 'through', 'when', 'where', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own', 'same', 'than', 'too', 'very'}
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Count frequency
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top topics
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10] if freq > 1]

    def _analyze_speaker_roles(self, content: str, primary_intent: IntentPrediction) -> Dict[str, List[str]]:
        """Analyze and identify speaker roles based on content and intent"""
        roles = {}
        
        # Intent-based role suggestions
        intent_roles = {
            IntentCategory.MEETING: ["facilitator", "participant", "decision_maker"],
            IntentCategory.PRESENTATION: ["presenter", "audience"],
            IntentCategory.LECTURE: ["instructor", "student"],
            IntentCategory.INTERVIEW: ["interviewer", "candidate"],
            IntentCategory.CONSULTATION: ["consultant", "client"],
            IntentCategory.SUPPORT_CALL: ["agent", "customer"]
        }
        
        suggested_roles = intent_roles.get(primary_intent.intent_category, ["speaker", "listener"])
        
        # Simple speaker detection based on patterns
        speaker_count = self._estimate_speaker_count(content)
        
        if speaker_count == 1:
            roles["single_speaker"] = suggested_roles[:1]
        elif speaker_count == 2:
            roles["speaker_1"] = [suggested_roles[0]] if suggested_roles else ["primary_speaker"]
            roles["speaker_2"] = [suggested_roles[1]] if len(suggested_roles) > 1 else ["secondary_speaker"]
        else:
            for i in range(min(speaker_count, 5)):
                role = suggested_roles[i] if i < len(suggested_roles) else f"participant_{i+1}"
                roles[f"speaker_{i+1}"] = [role]
        
        return roles

    def _analyze_temporal_structure(self, content: str) -> Dict[str, Any]:
        """Analyze the temporal structure and flow of content"""
        structure = {
            "has_clear_beginning": False,
            "has_clear_ending": False,
            "has_transitions": False,
            "estimated_duration_minutes": 0,
            "content_segments": []
        }
        
        # Check for beginning markers
        beginning_markers = ["welcome", "hello", "good morning", "let's start", "today we", "first"]
        for marker in beginning_markers:
            if marker in content.lower()[:200]:
                structure["has_clear_beginning"] = True
                break
        
        # Check for ending markers
        ending_markers = ["thank you", "goodbye", "in conclusion", "to summarize", "that's all", "see you"]
        for marker in ending_markers:
            if marker in content.lower()[-200:]:
                structure["has_clear_ending"] = True
                break
        
        # Check for transitions
        transition_markers = ["next", "moving on", "furthermore", "however", "meanwhile", "later"]
        transition_count = sum(content.lower().count(marker) for marker in transition_markers)
        structure["has_transitions"] = transition_count > 2
        
        # Estimate duration (rough approximation: 150 words per minute average speech)
        word_count = len(content.split())
        structure["estimated_duration_minutes"] = round(word_count / 150, 1)
        
        # Simple content segmentation
        segments = content.split('\n\n') if '\n\n' in content else content.split('. ')
        structure["content_segments"] = len([seg for seg in segments if len(seg.strip()) > 50])
        
        return structure

    def _calculate_complexity_score(self, content: str, features: IntentFeatures) -> float:
        """Calculate content complexity score (0-10)"""
        score = 5.0  # Base score
        
        # Vocabulary complexity
        words = content.split()
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            score += (avg_word_length - 5) * 0.5  # Adjust based on average word length
        
        # Technical complexity
        score += features.linguistic_patterns["technical_complexity"] * 2
        
        # Sentence complexity
        avg_sentence_length = features.linguistic_patterns["avg_sentence_length"]
        if avg_sentence_length > 20:
            score += 1
        elif avg_sentence_length < 10:
            score -= 1
        
        # Unique vocabulary ratio
        unique_words = features.context_clues["unique_words"]
        total_words = features.context_clues["word_count"]
        if total_words > 0:
            vocab_ratio = unique_words / total_words
            if vocab_ratio > 0.7:
                score += 1
            elif vocab_ratio < 0.4:
                score -= 1
        
        return max(0, min(10, score))

    def _analyze_engagement_indicators(self, content: str) -> Dict[str, float]:
        """Analyze indicators of audience engagement"""
        indicators = {}
        content_lower = content.lower()
        
        # Question engagement
        question_count = content.count('?')
        indicators["question_engagement"] = min(1.0, question_count / 10)
        
        # Emotional language
        emotional_words = ["excited", "amazing", "wonderful", "terrible", "frustrated", "happy", "sad", "angry"]
        emotion_count = sum(content_lower.count(word) for word in emotional_words)
        indicators["emotional_engagement"] = min(1.0, emotion_count / 5)
        
        # Interactive elements
        interactive_phrases = ["what do you think", "any questions", "let me know", "your thoughts", "feedback"]
        interaction_count = sum(content_lower.count(phrase) for phrase in interactive_phrases)
        indicators["interactive_engagement"] = min(1.0, interaction_count / 3)
        
        # Energy level (exclamation marks, caps, enthusiasm words)
        energy_count = content.count('!') + len(re.findall(r'\b[A-Z]{2,}\b', content))
        enthusiasm_words = ["great", "excellent", "fantastic", "awesome", "brilliant"]
        energy_count += sum(content_lower.count(word) for word in enthusiasm_words)
        indicators["energy_level"] = min(1.0, energy_count / 8)
        
        return indicators

    # Helper methods for feature extraction
    def _calculate_avg_sentence_length(self, content: str) -> float:
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0
        total_words = sum(len(sentence.split()) for sentence in sentences)
        return total_words / len(sentences)

    def _calculate_formality_score(self, content: str) -> float:
        formal_indicators = ["furthermore", "however", "therefore", "consequently", "nevertheless"]
        informal_indicators = ["gonna", "wanna", "kinda", "yeah", "ok", "cool"]
        
        formal_count = sum(content.lower().count(word) for word in formal_indicators)
        informal_count = sum(content.lower().count(word) for word in informal_indicators)
        
        total_indicators = formal_count + informal_count
        if total_indicators == 0:
            return 0.5  # Neutral
        
        return formal_count / total_indicators

    def _calculate_technical_complexity(self, content: str) -> float:
        technical_words = ["algorithm", "database", "server", "API", "framework", "protocol", "implementation", "optimization", "architecture", "methodology"]
        tech_count = sum(content.lower().count(word) for word in technical_words)
        word_count = len(content.split())
        return min(1.0, tech_count / max(1, word_count / 100))

    def _analyze_emotional_tone(self, content: str) -> float:
        positive_words = ["good", "great", "excellent", "happy", "pleased", "satisfied", "wonderful"]
        negative_words = ["bad", "terrible", "awful", "sad", "angry", "frustrated", "disappointed"]
        
        positive_count = sum(content.lower().count(word) for word in positive_words)
        negative_count = sum(content.lower().count(word) for word in negative_words)
        
        total_emotional = positive_count + negative_count
        if total_emotional == 0:
            return 0.5  # Neutral
        
        return positive_count / total_emotional

    def _estimate_speaker_count(self, content: str) -> int:
        # Simple heuristics for speaker count estimation
        colon_count = content.count(':')
        newline_count = content.count('\n')
        
        if colon_count > 5:  # Dialogue format
            return min(5, colon_count // 3)
        elif newline_count > 10:
            return min(4, newline_count // 8)
        else:
            return 1

    def _calculate_dialogue_ratio(self, content: str) -> float:
        total_length = len(content)
        if total_length == 0:
            return 0
        
        # Estimate dialogue based on speaker indicators
        dialogue_indicators = content.count(':') + content.count('"') // 2
        return min(1.0, dialogue_indicators / max(1, total_length / 100))

    def _count_monologue_segments(self, content: str) -> int:
        # Count long segments without speaker changes
        segments = content.split('\n')
        long_segments = [seg for seg in segments if len(seg) > 200 and ':' not in seg]
        return len(long_segments)

    def _store_content_analysis(self, analysis: ContentAnalysis):
        """Store content analysis in database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO content_analyses (
            content_id, content_type, content_hash, primary_intent, primary_confidence,
            primary_domain, secondary_intents, content_summary, key_topics,
            speaker_roles, temporal_structure, complexity_score, engagement_indicators
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis.content_id,
            analysis.content_type,
            hashlib.md5(analysis.content_summary.encode()).hexdigest(),
            analysis.primary_intent.intent_category.value,
            analysis.primary_intent.confidence_score,
            analysis.primary_intent.domain.value,
            json.dumps([{
                "intent": intent.intent_category.value,
                "confidence": intent.confidence_score,
                "domain": intent.domain.value
            } for intent in analysis.secondary_intents]),
            analysis.content_summary,
            json.dumps(analysis.key_topics),
            json.dumps(analysis.speaker_roles),
            json.dumps(analysis.temporal_structure),
            analysis.complexity_score,
            json.dumps(analysis.engagement_indicators)
        ))
        
        conn.commit()
        conn.close()

    def get_intent_analytics(self) -> Dict[str, Any]:
        """Get analytics about intent predictions"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Overall statistics
        cursor.execute("SELECT COUNT(*) FROM content_analyses")
        total_analyses = cursor.fetchone()[0]
        
        # Intent distribution
        cursor.execute('''
        SELECT primary_intent, COUNT(*) as count, AVG(primary_confidence) as avg_confidence
        FROM content_analyses 
        GROUP BY primary_intent 
        ORDER BY count DESC
        ''')
        intent_distribution = {row[0]: {"count": row[1], "avg_confidence": row[2]} 
                             for row in cursor.fetchall()}
        
        # Domain distribution
        cursor.execute('''
        SELECT primary_domain, COUNT(*) as count 
        FROM content_analyses 
        GROUP BY primary_domain 
        ORDER BY count DESC
        ''')
        domain_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Confidence distribution
        cursor.execute('''
        SELECT 
            SUM(CASE WHEN primary_confidence >= 0.9 THEN 1 ELSE 0 END) as very_high,
            SUM(CASE WHEN primary_confidence >= 0.75 AND primary_confidence < 0.9 THEN 1 ELSE 0 END) as high,
            SUM(CASE WHEN primary_confidence >= 0.5 AND primary_confidence < 0.75 THEN 1 ELSE 0 END) as medium,
            SUM(CASE WHEN primary_confidence >= 0.25 AND primary_confidence < 0.5 THEN 1 ELSE 0 END) as low,
            SUM(CASE WHEN primary_confidence < 0.25 THEN 1 ELSE 0 END) as very_low
        FROM content_analyses
        ''')
        confidence_dist = cursor.fetchone()
        confidence_distribution = {
            "very_high": confidence_dist[0],
            "high": confidence_dist[1],
            "medium": confidence_dist[2],
            "low": confidence_dist[3],
            "very_low": confidence_dist[4]
        }
        
        conn.close()
        
        return {
            "total_analyses": total_analyses,
            "intent_distribution": intent_distribution,
            "domain_distribution": domain_distribution,
            "confidence_distribution": confidence_distribution,
            "supported_intents": [intent.value for intent in IntentCategory],
            "supported_domains": [domain.value for domain in IntentDomain]
        }

    def search_content_by_intent(self, intent_category: IntentCategory, 
                                domain: Optional[IntentDomain] = None,
                                min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """Search for content by intent category and domain"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        query = '''
        SELECT content_id, content_summary, primary_confidence, primary_domain, key_topics
        FROM content_analyses 
        WHERE primary_intent = ? AND primary_confidence >= ?
        '''
        params = [intent_category.value, min_confidence]
        
        if domain:
            query += " AND primary_domain = ?"
            params.append(domain.value)
        
        query += " ORDER BY primary_confidence DESC"
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "content_id": row[0],
                "summary": row[1],
                "confidence": row[2],
                "domain": row[3],
                "key_topics": json.loads(row[4]) if row[4] else []
            })
        
        conn.close()
        return results


def demo_content_intent_classification():
    """Demonstrate the content intent classification system"""
    print("🧠 Content Intent Classification System Demo")
    print("=" * 50)
    
    # Initialize system
    system = ContentIntentClassificationSystem()
    
    # Test content samples
    test_contents = [
        {
            "id": "meeting_001",
            "type": "transcript",
            "content": """
            Alright everyone, let's start today's planning meeting. First on our agenda is the quarterly review. 
            Sarah, can you walk us through the sales numbers? We need to discuss the budget allocation for Q4 
            and identify action items for the next quarter. Any questions before we move to the next topic?
            """
        },
        {
            "id": "lecture_001", 
            "type": "transcript",
            "content": """
            Today we'll learn about machine learning algorithms. Let me explain the concept of supervised learning.
            Supervised learning is when we train a model using labeled data. For example, if we want to classify 
            emails as spam or not spam, we need examples of both types. The algorithm learns patterns from these 
            examples and can then make predictions on new, unseen data.
            """
        },
        {
            "id": "support_001",
            "type": "transcript", 
            "content": """
            Customer: Hi, I'm having trouble with my account login. It keeps saying my password is incorrect 
            but I'm sure it's right. Agent: I'm sorry to hear you're having this issue. Let me help you 
            resolve this. Can you confirm the email address associated with your account? I'll reset your 
            password and send you a new temporary one.
            """
        },
        {
            "id": "interview_001",
            "type": "transcript",
            "content": """
            Interviewer: Tell me about your experience with Python development. What projects have you worked on?
            Candidate: I've been developing in Python for about 4 years. My most recent project involved building 
            a data analysis pipeline using pandas and scikit-learn. I also have experience with web frameworks 
            like Django and Flask. Would you like me to elaborate on any specific project?
            """
        },
        {
            "id": "tutorial_001",
            "type": "transcript",
            "content": """
            Step 1: First, open your code editor and create a new Python file. Step 2: Import the necessary 
            libraries - we'll need requests and json for this tutorial. Step 3: Now we'll write a function 
            to make an API call. Make sure to handle exceptions properly. A common mistake is not checking 
            the response status before processing the data.
            """
        }
    ]
    
    print("📋 Analyzing sample content...")
    analyses = []
    
    for content_data in test_contents:
        print(f"\n🔍 Analyzing: {content_data['id']}")
        
        analysis = system.analyze_content_intent(
            content_data["content"],
            content_data["type"],
            content_data["id"]
        )
        analyses.append(analysis)
        
        print(f"Primary Intent: {analysis.primary_intent.intent_category.value}")
        print(f"Domain: {analysis.primary_intent.domain.value}")
        print(f"Confidence: {analysis.primary_intent.confidence_score:.2f} ({analysis.primary_intent.confidence_level.value})")
        print(f"Supporting Evidence: {', '.join(analysis.primary_intent.supporting_evidence)}")
        
        if analysis.secondary_intents:
            print(f"Secondary Intents: {', '.join([intent.intent_category.value for intent in analysis.secondary_intents])}")
        
        print(f"Key Topics: {', '.join(analysis.key_topics[:5])}")
        print(f"Complexity Score: {analysis.complexity_score:.1f}/10")
        print(f"Speaker Roles: {list(analysis.speaker_roles.keys())}")
        
        if analysis.temporal_structure.get("estimated_duration_minutes"):
            print(f"Estimated Duration: {analysis.temporal_structure['estimated_duration_minutes']} minutes")
    
    # Show analytics
    print(f"\n📊 Intent Analytics:")
    analytics = system.get_intent_analytics()
    
    print(f"Total Analyses: {analytics['total_analyses']}")
    print(f"\nIntent Distribution:")
    for intent, data in list(analytics['intent_distribution'].items())[:5]:
        print(f"  {intent}: {data['count']} (avg confidence: {data['avg_confidence']:.2f})")
    
    print(f"\nDomain Distribution:")
    for domain, count in list(analytics['domain_distribution'].items())[:5]:
        print(f"  {domain}: {count}")
    
    print(f"\nConfidence Distribution:")
    for level, count in analytics['confidence_distribution'].items():
        print(f"  {level}: {count}")
    
    # Search functionality demo
    print(f"\n🔎 Search Demo - Finding Meeting Content:")
    meeting_results = system.search_content_by_intent(
        IntentCategory.MEETING,
        domain=IntentDomain.BUSINESS,
        min_confidence=0.5
    )
    
    for result in meeting_results:
        print(f"  Content ID: {result['content_id']}")
        print(f"  Summary: {result['summary'][:100]}...")
        print(f"  Confidence: {result['confidence']:.2f}")
        print()
    
    # Feature insights
    print(f"📈 Feature Insights:")
    if analyses:
        avg_complexity = sum(a.complexity_score for a in analyses) / len(analyses)
        print(f"Average Content Complexity: {avg_complexity:.1f}/10")
        
        high_confidence = sum(1 for a in analyses if a.primary_intent.confidence_score > 0.7)
        print(f"High Confidence Predictions: {high_confidence}/{len(analyses)}")
        
        domains_found = set(a.primary_intent.domain.value for a in analyses)
        print(f"Domains Detected: {', '.join(domains_found)}")
    
    # System capabilities summary
    print(f"\n🛠️  System Capabilities:")
    print(f"Supported Intent Categories: {len(IntentCategory)} categories")
    print(f"Supported Domains: {len(IntentDomain)} domains")
    print(f"Confidence Levels: {len(ConfidenceLevel)} levels")
    print(f"Feature Types: Keyword matching, structural analysis, linguistic patterns")
    print(f"Analytics: Intent distribution, confidence tracking, search capabilities")
    
    print(f"\n✅ Content intent classification demonstration complete!")
    print(f"Database: {system.database_path}")


if __name__ == "__main__":
    demo_content_intent_classification()