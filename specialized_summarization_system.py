#!/usr/bin/env python3
"""
Specialized Summarization System
Task 124: Implement specialized summarization formats including bullet-point,
timeline-based, comparative, visual, and domain-specific summary templates.
"""

import asyncio
import json
import logging
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum

# Optional imports with fallbacks
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SummaryFormat(Enum):
    """Supported summary formats."""
    BULLET_POINT = "bullet_point"
    TIMELINE = "timeline"
    COMPARATIVE = "comparative"
    VISUAL = "visual"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    MEDICAL = "medical"
    LEGAL = "legal"
    EDUCATIONAL = "educational"


class SummaryLength(Enum):
    """Summary length options."""
    SHORT = "short"      # 1-3 sentences
    MEDIUM = "medium"    # 1-2 paragraphs
    LONG = "long"        # 3+ paragraphs
    DETAILED = "detailed"  # Comprehensive


@dataclass
class SummaryRequest:
    """Summary request configuration."""
    text: str
    format_type: SummaryFormat
    length: SummaryLength
    domain: Optional[str] = None
    include_keywords: bool = True
    include_entities: bool = True
    include_sentiment: bool = False
    custom_template: Optional[Dict[str, Any]] = None
    language: str = "en"


@dataclass
class SummaryResult:
    """Summary result with metadata."""
    summary: str
    format_type: SummaryFormat
    length: SummaryLength
    confidence_score: float
    keywords: List[str]
    entities: List[str]
    sentiment: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = None
    processing_time: float = 0.0


class TextProcessor:
    """Advanced text processing utilities."""
    
    def __init__(self):
        self.nlp = None
        self.initialize_nlp()
    
    def initialize_nlp(self):
        """Initialize NLP model if available."""
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load('en_core_web_sm')
            except OSError:
                logger.warning("spaCy English model not available")
                self.nlp = None
        else:
            logger.warning("spaCy not available, using basic text processing")
    
    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        if self.nlp:
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents]
        else:
            # Basic sentence splitting
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities."""
        if self.nlp:
            doc = self.nlp(text)
            return [ent.text for ent in doc.ents]
        else:
            # Basic entity extraction using patterns
            entities = []
            # Simple patterns for names, places, organizations
            name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
            entities.extend(re.findall(name_pattern, text))
            return list(set(entities))
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract key terms using TF-IDF."""
        try:
            # Simple keyword extraction
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            word_freq = {}
            for word in words:
                if word not in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'an', 'a']:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top keywords
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in sorted_words[:max_keywords]]
        
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            return []
    
    def calculate_sentence_importance(self, sentences: List[str], text: str) -> List[float]:
        """Calculate importance scores for sentences."""
        if not sentences:
            return []
        
        try:
            # Use TF-IDF for sentence scoring
            vectorizer = TfidfVectorizer(stop_words='english')
            sentence_vectors = vectorizer.fit_transform(sentences)
            
            # Calculate centrality scores
            similarity_matrix = cosine_similarity(sentence_vectors)
            scores = np.mean(similarity_matrix, axis=1)
            
            return scores.tolist()
        
        except Exception as e:
            logger.error(f"Sentence scoring error: {e}")
            # Fallback: score by position and length
            scores = []
            for i, sentence in enumerate(sentences):
                # Favor earlier sentences and longer sentences
                position_score = 1.0 - (i / len(sentences)) * 0.5
                length_score = min(len(sentence) / 100, 1.0)
                scores.append((position_score + length_score) / 2)
            
            return scores


class BulletPointSummarizer:
    """Generate bullet-point summaries with key insights."""
    
    def __init__(self, text_processor: TextProcessor):
        self.text_processor = text_processor
    
    def summarize(self, text: str, length: SummaryLength, **kwargs) -> str:
        """Generate bullet-point summary."""
        sentences = self.text_processor.extract_sentences(text)
        
        if not sentences:
            return "• No content available for summarization"
        
        # Determine number of points based on length
        num_points = {
            SummaryLength.SHORT: min(3, len(sentences)),
            SummaryLength.MEDIUM: min(5, len(sentences)),
            SummaryLength.LONG: min(8, len(sentences)),
            SummaryLength.DETAILED: min(12, len(sentences))
        }.get(length, 5)
        
        # Get top sentences
        scores = self.text_processor.calculate_sentence_importance(sentences, text)
        top_indices = np.argsort(scores)[-num_points:][::-1]
        
        # Create bullet points
        bullet_points = []
        for idx in sorted(top_indices):
            sentence = sentences[idx].strip()
            if sentence:
                # Clean up sentence
                sentence = self._clean_bullet_point(sentence)
                bullet_points.append(f"• {sentence}")
        
        return "\n".join(bullet_points)
    
    def _clean_bullet_point(self, sentence: str) -> str:
        """Clean and format bullet point."""
        # Remove excessive punctuation
        sentence = re.sub(r'[.!?]+$', '', sentence)
        
        # Ensure proper capitalization
        if sentence:
            sentence = sentence[0].upper() + sentence[1:]
        
        return sentence


class TimelineSummarizer:
    """Generate timeline-based summaries for events."""
    
    def __init__(self, text_processor: TextProcessor):
        self.text_processor = text_processor
    
    def summarize(self, text: str, length: SummaryLength, **kwargs) -> str:
        """Generate timeline summary."""
        # Extract sentences with temporal markers
        sentences = self.text_processor.extract_sentences(text)
        
        # Identify temporal sentences
        temporal_sentences = self._find_temporal_sentences(sentences)
        
        if not temporal_sentences:
            # Fallback to sequential summary
            return self._create_sequential_summary(sentences, length)
        
        # Sort by temporal order (simplified)
        sorted_events = self._sort_temporal_events(temporal_sentences)
        
        # Format as timeline
        return self._format_timeline(sorted_events, length)
    
    def _find_temporal_sentences(self, sentences: List[str]) -> List[Tuple[str, str]]:
        """Find sentences with temporal markers."""
        temporal_patterns = [
            r'\b(first|initially|beginning|start)\b',
            r'\b(then|next|after|following|subsequently)\b',
            r'\b(finally|lastly|ultimately|end|conclusion)\b',
            r'\b(during|while|when|as)\b',
            r'\b(before|prior|earlier)\b',
            r'\b(later|afterwards|eventually)\b',
            r'\b(\d{4}|\d{1,2}/\d{1,2}|\d{1,2}-\d{1,2})\b',  # Dates
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
        ]
        
        temporal_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for pattern in temporal_patterns:
                if re.search(pattern, sentence_lower):
                    temporal_sentences.append((sentence, pattern))
                    break
        
        return temporal_sentences
    
    def _sort_temporal_events(self, temporal_sentences: List[Tuple[str, str]]) -> List[str]:
        """Sort events by temporal order."""
        # Simple ordering based on temporal marker priority
        order_weights = {
            'first': 1, 'initially': 1, 'beginning': 1, 'start': 1,
            'before': 2, 'prior': 2, 'earlier': 2,
            'during': 3, 'while': 3, 'when': 3, 'as': 3,
            'then': 4, 'next': 4, 'after': 4, 'following': 4, 'subsequently': 4,
            'later': 5, 'afterwards': 5, 'eventually': 5,
            'finally': 6, 'lastly': 6, 'ultimately': 6, 'end': 6, 'conclusion': 6
        }
        
        weighted_sentences = []
        for sentence, pattern in temporal_sentences:
            # Find weight for pattern
            weight = 3  # Default middle weight
            for marker, w in order_weights.items():
                if marker in sentence.lower():
                    weight = w
                    break
            
            weighted_sentences.append((weight, sentence))
        
        # Sort by weight and return sentences
        weighted_sentences.sort(key=lambda x: x[0])
        return [sentence for weight, sentence in weighted_sentences]
    
    def _create_sequential_summary(self, sentences: List[str], length: SummaryLength) -> str:
        """Create sequential summary when no temporal markers found."""
        num_points = {
            SummaryLength.SHORT: min(3, len(sentences)),
            SummaryLength.MEDIUM: min(5, len(sentences)),
            SummaryLength.LONG: min(8, len(sentences)),
            SummaryLength.DETAILED: min(12, len(sentences))
        }.get(length, 5)
        
        # Take first N sentences as sequential events
        selected_sentences = sentences[:num_points]
        
        timeline_items = []
        for i, sentence in enumerate(selected_sentences, 1):
            timeline_items.append(f"{i}. {sentence.strip()}")
        
        return "\n".join(timeline_items)
    
    def _format_timeline(self, events: List[str], length: SummaryLength) -> str:
        """Format events as timeline."""
        num_events = {
            SummaryLength.SHORT: min(3, len(events)),
            SummaryLength.MEDIUM: min(5, len(events)),
            SummaryLength.LONG: min(8, len(events)),
            SummaryLength.DETAILED: len(events)
        }.get(length, 5)
        
        timeline_items = []
        for i, event in enumerate(events[:num_events], 1):
            cleaned_event = re.sub(r'^[.!?]+', '', event.strip())
            timeline_items.append(f"⏰ Step {i}: {cleaned_event}")
        
        return "\n".join(timeline_items)


class ComparativeSummarizer:
    """Generate comparative summaries between concepts or documents."""
    
    def __init__(self, text_processor: TextProcessor):
        self.text_processor = text_processor
    
    def summarize(self, text: str, length: SummaryLength, **kwargs) -> str:
        """Generate comparative summary."""
        # Try to identify comparative elements
        comparative_elements = self._find_comparative_elements(text)
        
        if len(comparative_elements) < 2:
            return self._create_contrast_summary(text, length)
        
        return self._format_comparison(comparative_elements, length)
    
    def _find_comparative_elements(self, text: str) -> List[Dict[str, Any]]:
        """Find comparative elements in text."""
        # Look for comparative patterns
        comparative_patterns = [
            r'(compared to|versus|vs\.?|against)',
            r'(while|whereas|however|but|although)',
            r'(on the other hand|in contrast|conversely)',
            r'(better|worse|more|less|higher|lower)',
            r'(advantage|disadvantage|benefit|drawback)',
            r'(similar|different|alike|unlike)'
        ]
        
        sentences = self.text_processor.extract_sentences(text)
        comparative_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for pattern in comparative_patterns:
                if re.search(pattern, sentence_lower):
                    comparative_sentences.append({
                        'sentence': sentence,
                        'type': 'comparison',
                        'pattern': pattern
                    })
                    break
        
        return comparative_sentences
    
    def _create_contrast_summary(self, text: str, length: SummaryLength) -> str:
        """Create contrast-based summary when no explicit comparisons found."""
        sentences = self.text_processor.extract_sentences(text)
        
        if len(sentences) < 2:
            return "📊 Insufficient content for comparative analysis"
        
        # Cluster sentences into themes
        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
            sentence_vectors = vectorizer.fit_transform(sentences)
            
            # Use k-means to find contrasting themes
            n_clusters = min(3, len(sentences) // 2) if len(sentences) >= 4 else 2
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(sentence_vectors)
            
            # Get representative sentences from each cluster
            cluster_sentences = {}
            for i, sentence in enumerate(sentences):
                cluster_id = clusters[i]
                if cluster_id not in cluster_sentences:
                    cluster_sentences[cluster_id] = []
                cluster_sentences[cluster_id].append(sentence)
            
            # Format as comparison
            comparison_points = []
            for cluster_id, cluster_sents in cluster_sentences.items():
                if cluster_sents:
                    # Take most representative sentence
                    representative = cluster_sents[0]  # Simplified
                    comparison_points.append(f"📌 Theme {cluster_id + 1}: {representative}")
            
            return "\n".join(comparison_points)
        
        except Exception as e:
            logger.error(f"Clustering error: {e}")
            # Fallback to simple alternating summary
            summary_points = []
            for i, sentence in enumerate(sentences[:4]):  # Limit to 4 sentences
                summary_points.append(f"{'🔵' if i % 2 == 0 else '🔴'} {sentence}")
            
            return "\n".join(summary_points)
    
    def _format_comparison(self, elements: List[Dict[str, Any]], length: SummaryLength) -> str:
        """Format comparative elements."""
        num_items = {
            SummaryLength.SHORT: min(2, len(elements)),
            SummaryLength.MEDIUM: min(4, len(elements)),
            SummaryLength.LONG: min(6, len(elements)),
            SummaryLength.DETAILED: len(elements)
        }.get(length, 4)
        
        comparison_items = []
        for i, element in enumerate(elements[:num_items]):
            sentence = element['sentence'].strip()
            comparison_items.append(f"⚖️ {sentence}")
        
        return "\n".join(comparison_items)


class VisualSummarizer:
    """Generate visual summaries with charts and graphs descriptions."""
    
    def __init__(self, text_processor: TextProcessor):
        self.text_processor = text_processor
    
    def summarize(self, text: str, length: SummaryLength, **kwargs) -> str:
        """Generate visual summary with suggested visualizations."""
        # Analyze text for data patterns
        data_elements = self._identify_data_elements(text)
        
        if not data_elements:
            return self._create_conceptual_visual(text, length)
        
        return self._suggest_visualizations(data_elements, text, length)
    
    def _identify_data_elements(self, text: str) -> List[Dict[str, Any]]:
        """Identify numerical data and relationships."""
        data_elements = []
        
        # Look for numbers and percentages
        number_pattern = r'\b\d+(?:\.\d+)?%?\b'
        numbers = re.findall(number_pattern, text)
        
        if numbers:
            data_elements.append({
                'type': 'numerical',
                'values': numbers,
                'context': 'quantitative_data'
            })
        
        # Look for comparisons
        comparison_words = ['increase', 'decrease', 'growth', 'decline', 'higher', 'lower', 'more', 'less']
        for word in comparison_words:
            if word in text.lower():
                data_elements.append({
                    'type': 'trend',
                    'direction': word,
                    'context': 'comparative_data'
                })
                break
        
        # Look for categories or lists
        list_pattern = r'(?:first|second|third|fourth|fifth|\d+\.)\s+([^.]+)'
        categories = re.findall(list_pattern, text, re.IGNORECASE)
        
        if categories:
            data_elements.append({
                'type': 'categorical',
                'categories': categories[:5],  # Limit to 5
                'context': 'categorical_data'
            })
        
        return data_elements
    
    def _suggest_visualizations(self, data_elements: List[Dict[str, Any]], text: str, length: SummaryLength) -> str:
        """Suggest appropriate visualizations."""
        suggestions = ["📊 Visual Summary Recommendations:"]
        
        for element in data_elements:
            if element['type'] == 'numerical':
                suggestions.append("📈 Bar Chart: Numerical values comparison")
                suggestions.append(f"   Data: {', '.join(element['values'][:5])}")
            
            elif element['type'] == 'trend':
                suggestions.append("📉 Line Graph: Trend analysis over time")
                suggestions.append(f"   Trend: {element['direction']}")
            
            elif element['type'] == 'categorical':
                suggestions.append("🥧 Pie Chart: Category distribution")
                suggestions.append(f"   Categories: {', '.join(element['categories'][:3])}")
        
        # Add key insights
        keywords = self.text_processor.extract_keywords(text, max_keywords=5)
        if keywords:
            suggestions.append("\n🔍 Key Visual Elements:")
            for keyword in keywords:
                suggestions.append(f"   • {keyword.title()}")
        
        return "\n".join(suggestions)
    
    def _create_conceptual_visual(self, text: str, length: SummaryLength) -> str:
        """Create conceptual visual summary."""
        sentences = self.text_processor.extract_sentences(text)
        keywords = self.text_processor.extract_keywords(text, max_keywords=8)
        
        visual_summary = [
            "🎨 Conceptual Visual Summary:",
            "",
            "📋 Main Concepts:"
        ]
        
        # Create concept map
        for i, keyword in enumerate(keywords[:6]):
            visual_summary.append(f"   {i+1}. {keyword.title()}")
        
        if len(sentences) >= 3:
            visual_summary.extend([
                "",
                "🔗 Relationship Flow:",
                f"   {sentences[0][:50]}...",
                "   ↓",
                f"   {sentences[1][:50]}...",
                "   ↓", 
                f"   {sentences[-1][:50]}..."
            ])
        
        return "\n".join(visual_summary)


class DomainSpecificSummarizer:
    """Generate domain-specific summary templates."""
    
    def __init__(self, text_processor: TextProcessor):
        self.text_processor = text_processor
        
        # Domain-specific templates
        self.templates = {
            'medical': self._medical_template,
            'legal': self._legal_template,
            'technical': self._technical_template,
            'business': self._business_template,
            'educational': self._educational_template
        }
    
    def summarize(self, text: str, domain: str, length: SummaryLength, **kwargs) -> str:
        """Generate domain-specific summary."""
        if domain not in self.templates:
            return f"❌ Unsupported domain: {domain}"
        
        return self.templates[domain](text, length)
    
    def _medical_template(self, text: str, length: SummaryLength) -> str:
        """Medical summary template."""
        sentences = self.text_processor.extract_sentences(text)
        entities = self.text_processor.extract_entities(text)
        
        # Medical-specific patterns
        symptoms = self._extract_medical_terms(text, ['pain', 'fever', 'nausea', 'fatigue', 'swelling'])
        medications = self._extract_medical_terms(text, ['mg', 'tablet', 'dose', 'medication', 'drug'])
        procedures = self._extract_medical_terms(text, ['surgery', 'procedure', 'examination', 'test', 'scan'])
        
        summary_parts = [
            "🏥 Medical Summary:",
            ""
        ]
        
        if symptoms:
            summary_parts.extend([
                "🩺 Symptoms/Findings:",
                *[f"   • {symptom}" for symptom in symptoms[:3]]
            ])
        
        if medications:
            summary_parts.extend([
                "",
                "💊 Medications/Treatment:",
                *[f"   • {med}" for med in medications[:3]]
            ])
        
        if procedures:
            summary_parts.extend([
                "",
                "🔬 Procedures/Tests:",
                *[f"   • {proc}" for proc in procedures[:3]]
            ])
        
        # Add key sentences
        if sentences:
            scores = self.text_processor.calculate_sentence_importance(sentences, text)
            top_sentence_idx = np.argmax(scores)
            summary_parts.extend([
                "",
                "📋 Key Information:",
                f"   {sentences[top_sentence_idx]}"
            ])
        
        return "\n".join(summary_parts)
    
    def _legal_template(self, text: str, length: SummaryLength) -> str:
        """Legal summary template."""
        sentences = self.text_processor.extract_sentences(text)
        
        # Legal-specific terms
        parties = self._extract_legal_terms(text, ['plaintiff', 'defendant', 'party', 'client', 'counsel'])
        issues = self._extract_legal_terms(text, ['claim', 'issue', 'dispute', 'allegation', 'matter'])
        outcomes = self._extract_legal_terms(text, ['ruling', 'decision', 'judgment', 'settlement', 'verdict'])
        
        summary_parts = [
            "⚖️ Legal Summary:",
            ""
        ]
        
        if parties:
            summary_parts.extend([
                "👥 Parties Involved:",
                *[f"   • {party}" for party in parties[:3]]
            ])
        
        if issues:
            summary_parts.extend([
                "",
                "📋 Key Issues:",
                *[f"   • {issue}" for issue in issues[:3]]
            ])
        
        if outcomes:
            summary_parts.extend([
                "",
                "✅ Outcomes/Decisions:",
                *[f"   • {outcome}" for outcome in outcomes[:3]]
            ])
        
        return "\n".join(summary_parts)
    
    def _technical_template(self, text: str, length: SummaryLength) -> str:
        """Technical summary template."""
        sentences = self.text_processor.extract_sentences(text)
        
        # Technical patterns
        systems = self._extract_technical_terms(text, ['system', 'platform', 'framework', 'architecture'])
        features = self._extract_technical_terms(text, ['feature', 'function', 'capability', 'component'])
        specs = self._extract_technical_terms(text, ['requirement', 'specification', 'parameter', 'config'])
        
        summary_parts = [
            "⚙️ Technical Summary:",
            ""
        ]
        
        if systems:
            summary_parts.extend([
                "🖥️ Systems/Platforms:",
                *[f"   • {system}" for system in systems[:3]]
            ])
        
        if features:
            summary_parts.extend([
                "",
                "🔧 Features/Functions:",
                *[f"   • {feature}" for feature in features[:3]]
            ])
        
        if specs:
            summary_parts.extend([
                "",
                "📊 Specifications:",
                *[f"   • {spec}" for spec in specs[:3]]
            ])
        
        return "\n".join(summary_parts)
    
    def _business_template(self, text: str, length: SummaryLength) -> str:
        """Business summary template."""
        sentences = self.text_processor.extract_sentences(text)
        
        # Business patterns
        objectives = self._extract_business_terms(text, ['goal', 'objective', 'target', 'strategy'])
        metrics = self._extract_business_terms(text, ['revenue', 'profit', 'growth', 'performance', 'KPI'])
        actions = self._extract_business_terms(text, ['initiative', 'project', 'plan', 'action', 'decision'])
        
        summary_parts = [
            "💼 Business Summary:",
            ""
        ]
        
        if objectives:
            summary_parts.extend([
                "🎯 Objectives/Goals:",
                *[f"   • {obj}" for obj in objectives[:3]]
            ])
        
        if metrics:
            summary_parts.extend([
                "",
                "📈 Key Metrics:",
                *[f"   • {metric}" for metric in metrics[:3]]
            ])
        
        if actions:
            summary_parts.extend([
                "",
                "⚡ Action Items:",
                *[f"   • {action}" for action in actions[:3]]
            ])
        
        return "\n".join(summary_parts)
    
    def _educational_template(self, text: str, length: SummaryLength) -> str:
        """Educational summary template."""
        sentences = self.text_processor.extract_sentences(text)
        
        # Educational patterns
        concepts = self._extract_educational_terms(text, ['concept', 'principle', 'theory', 'idea'])
        examples = self._extract_educational_terms(text, ['example', 'instance', 'case', 'illustration'])
        outcomes = self._extract_educational_terms(text, ['learning', 'objective', 'outcome', 'skill'])
        
        summary_parts = [
            "📚 Educational Summary:",
            ""
        ]
        
        if concepts:
            summary_parts.extend([
                "💡 Key Concepts:",
                *[f"   • {concept}" for concept in concepts[:3]]
            ])
        
        if examples:
            summary_parts.extend([
                "",
                "📖 Examples:",
                *[f"   • {example}" for example in examples[:3]]
            ])
        
        if outcomes:
            summary_parts.extend([
                "",
                "🎓 Learning Outcomes:",
                *[f"   • {outcome}" for outcome in outcomes[:3]]
            ])
        
        return "\n".join(summary_parts)
    
    def _extract_medical_terms(self, text: str, keywords: List[str]) -> List[str]:
        """Extract medical-related terms."""
        found_terms = []
        for keyword in keywords:
            pattern = rf'\b\w*{keyword}\w*\b'
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_terms.extend(matches)
        
        return list(set(found_terms))[:5]  # Limit and remove duplicates
    
    def _extract_legal_terms(self, text: str, keywords: List[str]) -> List[str]:
        """Extract legal-related terms."""
        return self._extract_medical_terms(text, keywords)  # Same logic
    
    def _extract_technical_terms(self, text: str, keywords: List[str]) -> List[str]:
        """Extract technical-related terms."""
        return self._extract_medical_terms(text, keywords)  # Same logic
    
    def _extract_business_terms(self, text: str, keywords: List[str]) -> List[str]:
        """Extract business-related terms."""
        return self._extract_medical_terms(text, keywords)  # Same logic
    
    def _extract_educational_terms(self, text: str, keywords: List[str]) -> List[str]:
        """Extract education-related terms."""
        return self._extract_medical_terms(text, keywords)  # Same logic


class SpecializedSummarizationSystem:
    """Main system coordinating all summarization formats."""
    
    def __init__(self, db_path: str = "summarization.db"):
        self.db_path = db_path
        self.text_processor = TextProcessor()
        
        # Initialize format-specific summarizers
        self.bullet_point_summarizer = BulletPointSummarizer(self.text_processor)
        self.timeline_summarizer = TimelineSummarizer(self.text_processor)
        self.comparative_summarizer = ComparativeSummarizer(self.text_processor)
        self.visual_summarizer = VisualSummarizer(self.text_processor)
        self.domain_summarizer = DomainSpecificSummarizer(self.text_processor)
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database for summarization data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text_hash TEXT NOT NULL,
                    original_text TEXT NOT NULL,
                    format_type TEXT NOT NULL,
                    length_type TEXT NOT NULL,
                    summary_text TEXT NOT NULL,
                    confidence_score REAL,
                    keywords TEXT,
                    entities TEXT,
                    processing_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS summary_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    domain TEXT NOT NULL,
                    template_config TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    async def summarize(self, request: SummaryRequest) -> SummaryResult:
        """Generate summary based on request configuration."""
        start_time = datetime.now()
        
        try:
            # Select appropriate summarizer
            if request.format_type == SummaryFormat.BULLET_POINT:
                summary_text = self.bullet_point_summarizer.summarize(
                    request.text, request.length
                )
            
            elif request.format_type == SummaryFormat.TIMELINE:
                summary_text = self.timeline_summarizer.summarize(
                    request.text, request.length
                )
            
            elif request.format_type == SummaryFormat.COMPARATIVE:
                summary_text = self.comparative_summarizer.summarize(
                    request.text, request.length
                )
            
            elif request.format_type == SummaryFormat.VISUAL:
                summary_text = self.visual_summarizer.summarize(
                    request.text, request.length
                )
            
            elif request.format_type in [
                SummaryFormat.MEDICAL, SummaryFormat.LEGAL, 
                SummaryFormat.TECHNICAL, SummaryFormat.EDUCATIONAL
            ]:
                domain = request.format_type.value
                summary_text = self.domain_summarizer.summarize(
                    request.text, domain, request.length
                )
            
            else:
                # Default to bullet point
                summary_text = self.bullet_point_summarizer.summarize(
                    request.text, request.length
                )
            
            # Extract metadata
            keywords = []
            entities = []
            
            if request.include_keywords:
                keywords = self.text_processor.extract_keywords(request.text)
            
            if request.include_entities:
                entities = self.text_processor.extract_entities(request.text)
            
            # Calculate confidence (simplified)
            confidence = self._calculate_confidence(request.text, summary_text)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create result
            result = SummaryResult(
                summary=summary_text,
                format_type=request.format_type,
                length=request.length,
                confidence_score=confidence,
                keywords=keywords,
                entities=entities,
                processing_time=processing_time
            )
            
            # Store in database
            self._store_summary(request, result)
            
            return result
        
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return SummaryResult(
                summary=f"Error generating summary: {str(e)}",
                format_type=request.format_type,
                length=request.length,
                confidence_score=0.0,
                keywords=[],
                entities=[],
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _calculate_confidence(self, original_text: str, summary_text: str) -> float:
        """Calculate confidence score for summary quality."""
        try:
            # Simple confidence based on content coverage
            original_words = set(original_text.lower().split())
            summary_words = set(summary_text.lower().split())
            
            if not original_words:
                return 0.0
            
            # Coverage score
            coverage = len(summary_words.intersection(original_words)) / len(original_words)
            
            # Length appropriateness (not too short, not too long)
            length_ratio = len(summary_text) / len(original_text)
            length_score = 1.0 - abs(0.2 - length_ratio)  # Target 20% of original
            length_score = max(0.0, min(1.0, length_score))
            
            # Combined confidence
            confidence = (coverage * 0.7 + length_score * 0.3)
            return min(1.0, confidence)
        
        except Exception as e:
            logger.error(f"Confidence calculation error: {e}")
            return 0.5  # Default moderate confidence
    
    def _store_summary(self, request: SummaryRequest, result: SummaryResult):
        """Store summary in database."""
        try:
            text_hash = str(hash(request.text))
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO summaries 
                    (text_hash, original_text, format_type, length_type, summary_text,
                     confidence_score, keywords, entities, processing_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    text_hash,
                    request.text[:1000],  # Truncate for storage
                    request.format_type.value,
                    request.length.value,
                    result.summary,
                    result.confidence_score,
                    json.dumps(result.keywords),
                    json.dumps(result.entities),
                    result.processing_time
                ))
        
        except Exception as e:
            logger.error(f"Database storage error: {e}")
    
    async def batch_summarize(self, texts: List[str], format_type: SummaryFormat, 
                            length: SummaryLength) -> List[SummaryResult]:
        """Batch summarization for multiple texts."""
        results = []
        
        for text in texts:
            request = SummaryRequest(
                text=text,
                format_type=format_type,
                length=length
            )
            
            result = await self.summarize(request)
            results.append(result)
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.1)
        
        return results
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summarization system statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total summaries
                cursor.execute("SELECT COUNT(*) FROM summaries")
                total_summaries = cursor.fetchone()[0]
                
                # Format distribution
                cursor.execute('''
                    SELECT format_type, COUNT(*) as count
                    FROM summaries
                    GROUP BY format_type
                    ORDER BY count DESC
                ''')
                format_stats = cursor.fetchall()
                
                # Average confidence by format
                cursor.execute('''
                    SELECT format_type, AVG(confidence_score) as avg_confidence
                    FROM summaries
                    GROUP BY format_type
                ''')
                confidence_stats = cursor.fetchall()
                
                # Processing time statistics
                cursor.execute('''
                    SELECT AVG(processing_time), MIN(processing_time), MAX(processing_time)
                    FROM summaries
                ''')
                time_stats = cursor.fetchone()
                
                return {
                    'total_summaries': total_summaries,
                    'format_distribution': format_stats,
                    'confidence_by_format': confidence_stats,
                    'processing_time_stats': {
                        'average': time_stats[0] if time_stats[0] else 0,
                        'minimum': time_stats[1] if time_stats[1] else 0,
                        'maximum': time_stats[2] if time_stats[2] else 0
                    }
                }
        
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {'error': str(e)}
    
    def export_summaries(self, format_filter: Optional[SummaryFormat] = None) -> List[Dict[str, Any]]:
        """Export summaries for analysis."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM summaries"
                params = ()
                
                if format_filter:
                    query += " WHERE format_type = ?"
                    params = (format_filter.value,)
                
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
        
        except Exception as e:
            logger.error(f"Export error: {e}")
            return []


# Example usage and testing
async def main():
    """Example usage of the specialized summarization system."""
    
    # Initialize system
    summarizer = SpecializedSummarizationSystem()
    
    # Example texts for different formats
    test_texts = {
        'educational': """
        Machine learning is a branch of artificial intelligence that focuses on the development of algorithms 
        and statistical models that enable computers to improve their performance on a specific task through 
        experience. The field encompasses various approaches including supervised learning, where algorithms 
        learn from labeled training data, unsupervised learning, which finds hidden patterns in data without 
        labels, and reinforcement learning, where agents learn through interaction with an environment. 
        Applications of machine learning are widespread, including image recognition, natural language 
        processing, recommendation systems, and autonomous vehicles. The key to successful machine learning 
        is having quality data, appropriate algorithms, and sufficient computational resources.
        """,
        
        'medical': """
        The patient presented with acute chest pain radiating to the left arm, accompanied by shortness of 
        breath and diaphoresis. Initial assessment revealed elevated blood pressure of 180/100 mmHg and 
        heart rate of 110 bpm. ECG showed ST-segment elevation in leads V2-V4, consistent with anterior 
        myocardial infarction. Laboratory results indicated elevated troponin levels at 15.2 ng/mL. 
        The patient was immediately started on dual antiplatelet therapy with aspirin 325mg and 
        clopidogrel 600mg loading dose. Emergency cardiac catheterization was performed, revealing 
        100% occlusion of the left anterior descending artery. Successful primary percutaneous 
        coronary intervention was completed with drug-eluting stent placement.
        """,
        
        'business': """
        The quarterly business review revealed mixed results across our product portfolio. Revenue increased 
        by 12% year-over-year, reaching $2.3 million, primarily driven by strong performance in our 
        enterprise software division. However, the consumer products segment experienced a 8% decline, 
        attributed to increased competition and supply chain challenges. Our key performance indicators 
        show customer acquisition cost decreased by 15%, while customer lifetime value improved by 22%. 
        The board approved three strategic initiatives for Q4: launching the new mobile platform, 
        expanding into the European market, and implementing an AI-driven customer support system. 
        These initiatives are expected to require $500K in additional investment but should generate 
        $1.2M in additional revenue within 18 months.
        """
    }
    
    print("📝 Specialized Summarization System Demo")
    print("=" * 50)
    
    # Test different formats
    formats_to_test = [
        (SummaryFormat.BULLET_POINT, "Bullet Point"),
        (SummaryFormat.TIMELINE, "Timeline"),
        (SummaryFormat.VISUAL, "Visual"),
        (SummaryFormat.MEDICAL, "Medical"),
        (SummaryFormat.TECHNICAL, "Technical")
    ]
    
    for text_type, text_content in test_texts.items():
        print(f"\n📚 Testing with {text_type.title()} Content:")
        print(f"Original text: {text_content[:100]}...")
        
        for format_type, format_name in formats_to_test:
            print(f"\n🔍 {format_name} Summary:")
            
            request = SummaryRequest(
                text=text_content,
                format_type=format_type,
                length=SummaryLength.MEDIUM,
                include_keywords=True,
                include_entities=True
            )
            
            result = await summarizer.summarize(request)
            
            print(f"Summary:\n{result.summary}")
            print(f"Confidence: {result.confidence_score:.3f}")
            
            if result.keywords:
                print(f"Keywords: {', '.join(result.keywords[:5])}")
            
            if result.entities:
                print(f"Entities: {', '.join(result.entities[:5])}")
            
            print(f"Processing time: {result.processing_time:.3f}s")
            print("-" * 30)
    
    # Show system statistics
    print(f"\n📊 System Statistics:")
    stats = summarizer.get_summary_statistics()
    print(f"Total summaries generated: {stats.get('total_summaries', 0)}")
    print(f"Format distribution: {stats.get('format_distribution', [])}")
    
    print(f"\n✅ Specialized summarization system demo completed!")


if __name__ == "__main__":
    asyncio.run(main())