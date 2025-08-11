#!/usr/bin/env python3
"""
Hybrid Summarization System
Implements Task 123: Build hybrid summarization system

This module provides comprehensive summarization capabilities including:
- Extractive and abstractive summarization combination
- Multi-document summarization
- Query-focused summarization
- Summarization quality assessment
- Personalization based on user preferences
"""

import os
import re
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import statistics
from collections import Counter, defaultdict
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional imports with fallbacks
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("OpenAI not available - some features will be limited")

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("Transformers not available - some features will be limited")

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk.cluster.util import cosine_distance
    HAS_NLTK = True
    
    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
        
except ImportError:
    HAS_NLTK = False
    logger.warning("NLTK not available - using basic text processing")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("Scikit-learn not available - some features will be limited")

class SummarizationType(Enum):
    """Types of summarization"""
    EXTRACTIVE = "extractive"
    ABSTRACTIVE = "abstractive"
    HYBRID = "hybrid"
    QUERY_FOCUSED = "query_focused"
    MULTI_DOCUMENT = "multi_document"

class SummaryLength(Enum):
    """Summary length options"""
    BRIEF = "brief"          # 1-2 sentences
    SHORT = "short"          # 3-5 sentences
    MEDIUM = "medium"        # 1-2 paragraphs
    LONG = "long"           # 3+ paragraphs
    CUSTOM = "custom"        # User-defined length

class SummaryStyle(Enum):
    """Summary style options"""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"
    ACADEMIC = "academic"
    JOURNALISTIC = "journalistic"

@dataclass
class SummarizationRequest:
    """Request configuration for summarization"""
    text: str
    summary_type: SummarizationType = SummarizationType.HYBRID
    length: SummaryLength = SummaryLength.MEDIUM
    style: SummaryStyle = SummaryStyle.FORMAL
    query: Optional[str] = None
    max_sentences: Optional[int] = None
    max_words: Optional[int] = None
    focus_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    preserve_structure: bool = False
    include_quotes: bool = True
    language: str = "en"
    user_preferences: Optional[Dict[str, Any]] = None

@dataclass
class SummaryResult:
    """Result of summarization process"""
    summary: str
    summary_type: SummarizationType
    length: SummaryLength
    style: SummaryStyle
    word_count: int
    sentence_count: int
    compression_ratio: float
    quality_score: float
    key_points: List[str]
    extracted_sentences: List[str]
    confidence_score: float
    processing_time: float
    metadata: Dict[str, Any]
    created_at: datetime

@dataclass
class DocumentSummary:
    """Summary of a single document"""
    document_id: str
    title: Optional[str]
    summary: str
    key_points: List[str]
    word_count: int
    importance_score: float
    topics: List[str]

class TextProcessor:
    """Text processing utilities"""
    
    def __init__(self):
        self.stop_words = set()
        if HAS_NLTK:
            try:
                self.stop_words = set(stopwords.words('english'))
            except:
                pass
        
        # Fallback stop words
        if not self.stop_words:
            self.stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
                'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
                'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
            }
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """Tokenize text into sentences"""
        if HAS_NLTK:
            return sent_tokenize(text)
        
        # Fallback sentence tokenization
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words"""
        if HAS_NLTK:
            return word_tokenize(text.lower())
        
        # Fallback word tokenization
        words = re.findall(r'\b\w+\b', text.lower())
        return words
    
    def remove_stop_words(self, words: List[str]) -> List[str]:
        """Remove stop words from word list"""
        return [word for word in words if word not in self.stop_words]
    
    def calculate_sentence_similarity(self, sent1: str, sent2: str) -> float:
        """Calculate similarity between two sentences"""
        words1 = set(self.remove_stop_words(self.tokenize_words(sent1)))
        words2 = set(self.remove_stop_words(self.tokenize_words(sent2)))
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """Extract keywords from text"""
        words = self.remove_stop_words(self.tokenize_words(text))
        word_freq = Counter(words)
        
        # Filter out very short words
        filtered_words = {word: freq for word, freq in word_freq.items() if len(word) > 2}
        
        return [word for word, _ in Counter(filtered_words).most_common(top_k)]

class ExtractiveSummarizer:
    """Extractive summarization using sentence ranking"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
    
    def summarize(self, text: str, num_sentences: int = 3, 
                 focus_keywords: Optional[List[str]] = None) -> Tuple[str, List[str], float]:
        """
        Generate extractive summary
        
        Returns:
            Tuple of (summary, extracted_sentences, confidence_score)
        """
        sentences = self.text_processor.tokenize_sentences(text)
        
        if len(sentences) <= num_sentences:
            return text, sentences, 1.0
        
        # Calculate sentence scores
        sentence_scores = self._calculate_sentence_scores(sentences, focus_keywords)
        
        # Select top sentences
        top_indices = sorted(range(len(sentence_scores)), 
                           key=lambda i: sentence_scores[i], reverse=True)[:num_sentences]
        
        # Sort by original order
        top_indices.sort()
        
        selected_sentences = [sentences[i] for i in top_indices]
        summary = ' '.join(selected_sentences)
        
        # Calculate confidence based on score distribution
        if sentence_scores:
            top_scores = [sentence_scores[i] for i in sorted(top_indices)]
            avg_score = statistics.mean(sentence_scores)
            confidence = min(1.0, statistics.mean(top_scores) / max(avg_score, 0.1))
        else:
            confidence = 0.5
        
        return summary, selected_sentences, confidence
    
    def _calculate_sentence_scores(self, sentences: List[str], 
                                 focus_keywords: Optional[List[str]] = None) -> List[float]:
        """Calculate importance scores for sentences"""
        scores = []
        
        # Calculate word frequencies
        all_words = []
        for sentence in sentences:
            words = self.text_processor.remove_stop_words(
                self.text_processor.tokenize_words(sentence)
            )
            all_words.extend(words)
        
        word_freq = Counter(all_words)
        
        for sentence in sentences:
            words = self.text_processor.remove_stop_words(
                self.text_processor.tokenize_words(sentence)
            )
            
            if not words:
                scores.append(0.0)
                continue
            
            # Base score: sum of word frequencies
            score = sum(word_freq[word] for word in words) / len(words)
            
            # Boost for focus keywords
            if focus_keywords:
                keyword_boost = sum(1 for word in words if word.lower() in 
                                  [kw.lower() for kw in focus_keywords])
                score += keyword_boost * 2
            
            # Position boost (earlier sentences get slight boost)
            position_boost = 1.0 - (sentences.index(sentence) / len(sentences)) * 0.1
            score *= position_boost
            
            # Length penalty for very short or very long sentences
            sentence_length = len(words)
            if sentence_length < 5:
                score *= 0.5
            elif sentence_length > 30:
                score *= 0.8
            
            scores.append(score)
        
        return scores

class AbstractiveSummarizer:
    """Abstractive summarization using language models"""
    
    def __init__(self):
        self.openai_client = None
        self.hf_summarizer = None
        
        # Initialize OpenAI client
        if HAS_OPENAI and os.getenv('OPENAI_API_KEY'):
            try:
                self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Initialize Hugging Face summarizer
        if HAS_TRANSFORMERS:
            try:
                self.hf_summarizer = pipeline(
                    "summarization",
                    model="facebook/bart-large-cnn",
                    device=0 if torch.cuda.is_available() else -1
                )
            except Exception as e:
                logger.warning(f"Failed to initialize HF summarizer: {e}")
                try:
                    # Fallback to smaller model
                    self.hf_summarizer = pipeline(
                        "summarization",
                        model="sshleifer/distilbart-cnn-12-6",
                        device=-1
                    )
                except Exception as e2:
                    logger.warning(f"Failed to initialize fallback summarizer: {e2}")
    
    async def summarize(self, text: str, max_length: int = 150, 
                       style: SummaryStyle = SummaryStyle.FORMAL,
                       query: Optional[str] = None) -> Tuple[str, float]:
        """
        Generate abstractive summary
        
        Returns:
            Tuple of (summary, confidence_score)
        """
        # Try OpenAI first
        if self.openai_client:
            try:
                return await self._summarize_with_openai(text, max_length, style, query)
            except Exception as e:
                logger.warning(f"OpenAI summarization failed: {e}")
        
        # Fallback to Hugging Face
        if self.hf_summarizer:
            try:
                return self._summarize_with_huggingface(text, max_length)
            except Exception as e:
                logger.warning(f"HuggingFace summarization failed: {e}")
        
        # Final fallback: return first few sentences
        sentences = text.split('.')[:3]
        fallback_summary = '. '.join(sentences).strip()
        if fallback_summary and not fallback_summary.endswith('.'):
            fallback_summary += '.'
        
        return fallback_summary, 0.3
    
    async def _summarize_with_openai(self, text: str, max_length: int,
                                   style: SummaryStyle, query: Optional[str]) -> Tuple[str, float]:
        """Summarize using OpenAI GPT"""
        style_prompts = {
            SummaryStyle.FORMAL: "Write a formal, professional summary",
            SummaryStyle.CASUAL: "Write a casual, conversational summary",
            SummaryStyle.TECHNICAL: "Write a technical summary with precise terminology",
            SummaryStyle.EXECUTIVE: "Write an executive summary focusing on key decisions and outcomes",
            SummaryStyle.ACADEMIC: "Write an academic summary with analytical insights",
            SummaryStyle.JOURNALISTIC: "Write a journalistic summary with who, what, when, where, why"
        }
        
        prompt = f"{style_prompts.get(style, 'Write a clear summary')} of the following text"
        
        if query:
            prompt += f" focusing on: {query}"
        
        prompt += f" in approximately {max_length} words:\n\n{text}"
        
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional summarization assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_length * 2,  # Allow some buffer
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            confidence = 0.9  # High confidence for GPT
            
            return summary, confidence
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _summarize_with_huggingface(self, text: str, max_length: int) -> Tuple[str, float]:
        """Summarize using Hugging Face transformers"""
        # Chunk text if too long
        max_input_length = 1024
        if len(text) > max_input_length:
            # Take first part of text
            text = text[:max_input_length]
        
        try:
            result = self.hf_summarizer(
                text,
                max_length=max_length,
                min_length=max_length // 3,
                do_sample=False
            )
            
            summary = result[0]['summary_text']
            confidence = 0.7  # Good confidence for BART
            
            return summary, confidence
            
        except Exception as e:
            logger.error(f"HuggingFace summarization error: {e}")
            raise

class HybridSummarizer:
    """Hybrid summarization combining extractive and abstractive approaches"""
    
    def __init__(self):
        self.extractive_summarizer = ExtractiveSummarizer()
        self.abstractive_summarizer = AbstractiveSummarizer()
        self.text_processor = TextProcessor()
    
    async def summarize(self, request: SummarizationRequest) -> SummaryResult:
        """Generate hybrid summary based on request"""
        start_time = datetime.now()
        
        # Determine target length
        target_sentences, target_words = self._determine_target_length(
            request.text, request.length, request.max_sentences, request.max_words
        )
        
        if request.summary_type == SummarizationType.EXTRACTIVE:
            summary, extracted_sentences, confidence = self.extractive_summarizer.summarize(
                request.text, target_sentences, request.focus_keywords
            )
            key_points = self._extract_key_points(summary)
            
        elif request.summary_type == SummarizationType.ABSTRACTIVE:
            summary, confidence = await self.abstractive_summarizer.summarize(
                request.text, target_words, request.style, request.query
            )
            extracted_sentences = []
            key_points = self._extract_key_points(summary)
            
        elif request.summary_type == SummarizationType.HYBRID:
            # First get extractive summary
            extractive_summary, extracted_sentences, ext_confidence = self.extractive_summarizer.summarize(
                request.text, target_sentences * 2, request.focus_keywords  # Get more sentences for abstractive input
            )
            
            # Then apply abstractive summarization to the extractive result
            summary, abs_confidence = await self.abstractive_summarizer.summarize(
                extractive_summary, target_words, request.style, request.query
            )
            
            confidence = (ext_confidence + abs_confidence) / 2
            key_points = self._extract_key_points(summary)
            
        elif request.summary_type == SummarizationType.QUERY_FOCUSED:
            summary, extracted_sentences, confidence = await self._query_focused_summarization(
                request.text, request.query, target_sentences, target_words, request.style
            )
            key_points = self._extract_key_points(summary)
            
        else:
            # Default to hybrid
            extractive_summary, extracted_sentences, ext_confidence = self.extractive_summarizer.summarize(
                request.text, target_sentences, request.focus_keywords
            )
            summary, abs_confidence = await self.abstractive_summarizer.summarize(
                extractive_summary, target_words, request.style
            )
            confidence = (ext_confidence + abs_confidence) / 2
            key_points = self._extract_key_points(summary)
        
        # Apply post-processing
        summary = self._post_process_summary(summary, request)
        
        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        word_count = len(summary.split())
        sentence_count = len(self.text_processor.tokenize_sentences(summary))
        compression_ratio = len(request.text.split()) / max(word_count, 1)
        quality_score = self._assess_quality(summary, request.text, confidence)
        
        return SummaryResult(
            summary=summary,
            summary_type=request.summary_type,
            length=request.length,
            style=request.style,
            word_count=word_count,
            sentence_count=sentence_count,
            compression_ratio=compression_ratio,
            quality_score=quality_score,
            key_points=key_points,
            extracted_sentences=extracted_sentences,
            confidence_score=confidence,
            processing_time=processing_time,
            metadata={
                'original_word_count': len(request.text.split()),
                'original_sentence_count': len(self.text_processor.tokenize_sentences(request.text)),
                'focus_keywords': request.focus_keywords,
                'query': request.query,
                'language': request.language
            },
            created_at=datetime.now()
        )
    
    async def _query_focused_summarization(self, text: str, query: str, 
                                         target_sentences: int, target_words: int,
                                         style: SummaryStyle) -> Tuple[str, List[str], float]:
        """Generate query-focused summary"""
        if not query:
            # Fallback to regular extractive
            return self.extractive_summarizer.summarize(text, target_sentences)
        
        # Extract query keywords
        query_keywords = self.text_processor.extract_keywords(query, top_k=5)
        
        # Get sentences most relevant to query
        sentences = self.text_processor.tokenize_sentences(text)
        sentence_scores = []
        
        for sentence in sentences:
            sentence_words = set(self.text_processor.tokenize_words(sentence))
            query_words = set(self.text_processor.tokenize_words(query))
            
            # Calculate relevance to query
            overlap = len(sentence_words.intersection(query_words))
            relevance_score = overlap / max(len(query_words), 1)
            
            # Boost for query keywords
            keyword_score = sum(1 for word in sentence_words 
                              if word.lower() in [kw.lower() for kw in query_keywords])
            
            total_score = relevance_score + keyword_score * 0.5
            sentence_scores.append(total_score)
        
        # Select top relevant sentences
        top_indices = sorted(range(len(sentence_scores)), 
                           key=lambda i: sentence_scores[i], reverse=True)[:target_sentences * 2]
        
        relevant_sentences = [sentences[i] for i in sorted(top_indices)]
        relevant_text = ' '.join(relevant_sentences)
        
        # Apply abstractive summarization with query focus
        summary, confidence = await self.abstractive_summarizer.summarize(
            relevant_text, target_words, style, query
        )
        
        return summary, relevant_sentences, confidence
    
    def _determine_target_length(self, text: str, length: SummaryLength,
                               max_sentences: Optional[int], max_words: Optional[int]) -> Tuple[int, int]:
        """Determine target length in sentences and words"""
        original_sentences = len(self.text_processor.tokenize_sentences(text))
        original_words = len(text.split())
        
        if max_sentences and max_words:
            return max_sentences, max_words
        
        if length == SummaryLength.BRIEF:
            sentences = min(2, max(1, original_sentences // 10))
            words = min(50, max(20, original_words // 20))
        elif length == SummaryLength.SHORT:
            sentences = min(5, max(2, original_sentences // 8))
            words = min(100, max(50, original_words // 15))
        elif length == SummaryLength.MEDIUM:
            sentences = min(8, max(3, original_sentences // 6))
            words = min(200, max(100, original_words // 10))
        elif length == SummaryLength.LONG:
            sentences = min(15, max(5, original_sentences // 4))
            words = min(400, max(200, original_words // 8))
        else:  # CUSTOM or default
            sentences = max(3, original_sentences // 6)
            words = max(100, original_words // 10)
        
        # Override with explicit limits
        if max_sentences:
            sentences = max_sentences
        if max_words:
            words = max_words
        
        return sentences, words
    
    def _extract_key_points(self, summary: str) -> List[str]:
        """Extract key points from summary"""
        sentences = self.text_processor.tokenize_sentences(summary)
        
        # For now, treat each sentence as a key point
        # In a more advanced implementation, we could use NLP to identify
        # the most important phrases or concepts
        key_points = []
        for sentence in sentences:
            if len(sentence.strip()) > 10:  # Filter out very short sentences
                key_points.append(sentence.strip())
        
        return key_points[:5]  # Limit to top 5 key points
    
    def _post_process_summary(self, summary: str, request: SummarizationRequest) -> str:
        """Apply post-processing to summary"""
        # Remove excluded keywords
        if request.exclude_keywords:
            for keyword in request.exclude_keywords:
                # Simple removal - in practice, you might want more sophisticated handling
                summary = re.sub(rf'\b{re.escape(keyword)}\b', '', summary, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        summary = re.sub(r'\s+', ' ', summary).strip()
        
        # Ensure proper sentence endings
        if summary and not summary.endswith(('.', '!', '?')):
            summary += '.'
        
        return summary
    
    def _assess_quality(self, summary: str, original_text: str, confidence: float) -> float:
        """Assess summary quality"""
        if not summary or not original_text:
            return 0.0
        
        # Basic quality metrics
        summary_words = set(self.text_processor.tokenize_words(summary))
        original_words = set(self.text_processor.tokenize_words(original_text))
        
        # Content coverage (how much of original content is represented)
        if original_words:
            coverage = len(summary_words.intersection(original_words)) / len(original_words)
        else:
            coverage = 0.0
        
        # Length appropriateness (not too short, not too long)
        summary_length = len(summary.split())
        original_length = len(original_text.split())
        compression_ratio = original_length / max(summary_length, 1)
        
        # Ideal compression ratio is between 3:1 and 10:1
        if 3 <= compression_ratio <= 10:
            length_score = 1.0
        elif compression_ratio < 3:
            length_score = compression_ratio / 3
        else:
            length_score = max(0.1, 10 / compression_ratio)
        
        # Combine metrics
        quality_score = (confidence * 0.4 + coverage * 0.3 + length_score * 0.3)
        
        return min(1.0, max(0.0, quality_score))

class MultiDocumentSummarizer:
    """Multi-document summarization"""
    
    def __init__(self):
        self.hybrid_summarizer = HybridSummarizer()
        self.text_processor = TextProcessor()
    
    async def summarize_documents(self, documents: List[Dict[str, str]], 
                                request: SummarizationRequest) -> SummaryResult:
        """Summarize multiple documents"""
        if not documents:
            raise ValueError("No documents provided")
        
        if len(documents) == 1:
            # Single document - use regular summarization
            request.text = documents[0].get('content', '')
            return await self.hybrid_summarizer.summarize(request)
        
        # Multi-document processing
        document_summaries = []
        
        # First, summarize each document individually
        for i, doc in enumerate(documents):
            doc_request = SummarizationRequest(
                text=doc.get('content', ''),
                summary_type=SummarizationType.EXTRACTIVE,  # Use extractive for individual docs
                length=SummaryLength.SHORT,
                style=request.style,
                focus_keywords=request.focus_keywords,
                language=request.language
            )
            
            doc_summary = await self.hybrid_summarizer.summarize(doc_request)
            
            document_summaries.append(DocumentSummary(
                document_id=doc.get('id', f'doc_{i}'),
                title=doc.get('title'),
                summary=doc_summary.summary,
                key_points=doc_summary.key_points,
                word_count=doc_summary.word_count,
                importance_score=doc_summary.quality_score,
                topics=self.text_processor.extract_keywords(doc_summary.summary, top_k=3)
            ))
        
        # Combine summaries and create final summary
        combined_text = ' '.join([ds.summary for ds in document_summaries])
        
        # Create final summary request
        final_request = SummarizationRequest(
            text=combined_text,
            summary_type=request.summary_type,
            length=request.length,
            style=request.style,
            query=request.query,
            max_sentences=request.max_sentences,
            max_words=request.max_words,
            focus_keywords=request.focus_keywords,
            exclude_keywords=request.exclude_keywords,
            language=request.language
        )
        
        final_summary = await self.hybrid_summarizer.summarize(final_request)
        
        # Add multi-document specific metadata
        final_summary.metadata.update({
            'document_count': len(documents),
            'document_summaries': [asdict(ds) for ds in document_summaries],
            'combined_topics': list(set().union(*[ds.topics for ds in document_summaries]))
        })
        
        return final_summary

class SummarizationPersonalizer:
    """Personalize summaries based on user preferences"""
    
    def __init__(self):
        self.user_profiles = {}
    
    def create_user_profile(self, user_id: str, preferences: Dict[str, Any]):
        """Create or update user profile"""
        self.user_profiles[user_id] = {
            'preferred_length': preferences.get('preferred_length', SummaryLength.MEDIUM),
            'preferred_style': preferences.get('preferred_style', SummaryStyle.FORMAL),
            'focus_areas': preferences.get('focus_areas', []),
            'avoid_topics': preferences.get('avoid_topics', []),
            'technical_level': preferences.get('technical_level', 'medium'),  # low, medium, high
            'include_examples': preferences.get('include_examples', True),
            'include_numbers': preferences.get('include_numbers', True),
            'language': preferences.get('language', 'en'),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def personalize_request(self, request: SummarizationRequest, user_id: str) -> SummarizationRequest:
        """Personalize summarization request based on user profile"""
        if user_id not in self.user_profiles:
            return request
        
        profile = self.user_profiles[user_id]
        
        # Apply user preferences
        if not request.length or request.length == SummaryLength.MEDIUM:
            request.length = profile.get('preferred_length', SummaryLength.MEDIUM)
        
        if not request.style or request.style == SummaryStyle.FORMAL:
            request.style = profile.get('preferred_style', SummaryStyle.FORMAL)
        
        # Merge focus keywords
        if profile.get('focus_areas'):
            if request.focus_keywords:
                request.focus_keywords.extend(profile['focus_areas'])
            else:
                request.focus_keywords = profile['focus_areas'].copy()
        
        # Merge exclude keywords
        if profile.get('avoid_topics'):
            if request.exclude_keywords:
                request.exclude_keywords.extend(profile['avoid_topics'])
            else:
                request.exclude_keywords = profile['avoid_topics'].copy()
        
        # Set language
        if not request.language:
            request.language = profile.get('language', 'en')
        
        # Store user preferences in request
        request.user_preferences = profile
        
        return request

class SummarizationService:
    """Main service for summarization operations"""
    
    def __init__(self):
        self.hybrid_summarizer = HybridSummarizer()
        self.multi_doc_summarizer = MultiDocumentSummarizer()
        self.personalizer = SummarizationPersonalizer()
        self.cache = {}  # Simple in-memory cache
    
    async def summarize(self, request: SummarizationRequest, 
                       user_id: Optional[str] = None) -> SummaryResult:
        """Main summarization endpoint"""
        # Apply personalization
        if user_id:
            request = self.personalizer.personalize_request(request, user_id)
        
        # Check cache
        cache_key = self._generate_cache_key(request)
        if cache_key in self.cache:
            logger.info("Returning cached summary")
            return self.cache[cache_key]
        
        # Generate summary
        if request.summary_type == SummarizationType.MULTI_DOCUMENT:
            # This would need documents to be passed separately
            raise ValueError("Multi-document summarization requires documents list")
        else:
            result = await self.hybrid_summarizer.summarize(request)
        
        # Cache result
        self.cache[cache_key] = result
        
        return result
    
    async def summarize_documents(self, documents: List[Dict[str, str]], 
                                request: SummarizationRequest,
                                user_id: Optional[str] = None) -> SummaryResult:
        """Summarize multiple documents"""
        # Apply personalization
        if user_id:
            request = self.personalizer.personalize_request(request, user_id)
        
        return await self.multi_doc_summarizer.summarize_documents(documents, request)
    
    def create_user_profile(self, user_id: str, preferences: Dict[str, Any]):
        """Create user profile for personalization"""
        self.personalizer.create_user_profile(user_id, preferences)
    
    def get_summary_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get predefined summary templates"""
        return {
            'meeting_minutes': {
                'summary_type': SummarizationType.HYBRID,
                'length': SummaryLength.MEDIUM,
                'style': SummaryStyle.FORMAL,
                'focus_keywords': ['decision', 'action', 'deadline', 'responsible'],
                'preserve_structure': True
            },
            'research_paper': {
                'summary_type': SummarizationType.ABSTRACTIVE,
                'length': SummaryLength.LONG,
                'style': SummaryStyle.ACADEMIC,
                'focus_keywords': ['methodology', 'results', 'conclusion'],
                'include_quotes': False
            },
            'news_article': {
                'summary_type': SummarizationType.HYBRID,
                'length': SummaryLength.SHORT,
                'style': SummaryStyle.JOURNALISTIC,
                'focus_keywords': ['who', 'what', 'when', 'where', 'why'],
                'preserve_structure': False
            },
            'technical_document': {
                'summary_type': SummarizationType.EXTRACTIVE,
                'length': SummaryLength.MEDIUM,
                'style': SummaryStyle.TECHNICAL,
                'preserve_structure': True,
                'include_quotes': True
            },
            'executive_brief': {
                'summary_type': SummarizationType.ABSTRACTIVE,
                'length': SummaryLength.SHORT,
                'style': SummaryStyle.EXECUTIVE,
                'focus_keywords': ['impact', 'recommendation', 'decision', 'outcome'],
                'preserve_structure': False
            }
        }
    
    def _generate_cache_key(self, request: SummarizationRequest) -> str:
        """Generate cache key for request"""
        # Create hash of key request parameters
        key_data = {
            'text_hash': hashlib.md5(request.text.encode()).hexdigest(),
            'summary_type': request.summary_type.value,
            'length': request.length.value,
            'style': request.style.value,
            'query': request.query,
            'max_sentences': request.max_sentences,
            'max_words': request.max_words,
            'focus_keywords': sorted(request.focus_keywords) if request.focus_keywords else None,
            'exclude_keywords': sorted(request.exclude_keywords) if request.exclude_keywords else None
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'cache_keys': list(self.cache.keys())
        }
    
    def clear_cache(self):
        """Clear summarization cache"""
        self.cache.clear()

# Example usage and testing functions
async def test_summarization():
    """Test the summarization system"""
    service = SummarizationService()
    
    # Sample text
    sample_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term "artificial intelligence" is often used to describe machines that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and "problem solving".
    
    The scope of AI is disputed: as machines become increasingly capable, tasks considered to require "intelligence" are often removed from the definition of AI, a phenomenon known as the AI effect. A quip in Tesler's Theorem says "AI is whatever hasn't been done yet." For instance, optical character recognition is frequently excluded from things considered to be AI, having become a routine technology. Modern machine learning techniques are a core part of AI. Machine learning algorithms build a model based on sample data, known as "training data", in order to make predictions or decisions without being explicitly programmed to do so.
    
    AI research has been highly successful in developing effective techniques for solving a wide range of problems, from game playing to medical diagnosis. However, some observers argue that progress in AI may be slowing and that the field may be experiencing an "AI winter". Despite these concerns, AI continues to be an active area of research and development, with new breakthroughs and applications emerging regularly.
    """
    
    # Test different summarization types
    test_cases = [
        {
            'name': 'Extractive Summary',
            'request': SummarizationRequest(
                text=sample_text,
                summary_type=SummarizationType.EXTRACTIVE,
                length=SummaryLength.SHORT
            )
        },
        {
            'name': 'Abstractive Summary',
            'request': SummarizationRequest(
                text=sample_text,
                summary_type=SummarizationType.ABSTRACTIVE,
                length=SummaryLength.SHORT,
                style=SummaryStyle.FORMAL
            )
        },
        {
            'name': 'Hybrid Summary',
            'request': SummarizationRequest(
                text=sample_text,
                summary_type=SummarizationType.HYBRID,
                length=SummaryLength.MEDIUM,
                style=SummaryStyle.TECHNICAL
            )
        },
        {
            'name': 'Query-Focused Summary',
            'request': SummarizationRequest(
                text=sample_text,
                summary_type=SummarizationType.QUERY_FOCUSED,
                length=SummaryLength.SHORT,
                query="What is machine learning?"
            )
        }
    ]
    
    print("Testing Hybrid Summarization System")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print("-" * 30)
        
        try:
            result = await service.summarize(test_case['request'])
            
            print(f"Summary: {result.summary}")
            print(f"Word Count: {result.word_count}")
            print(f"Compression Ratio: {result.compression_ratio:.2f}:1")
            print(f"Quality Score: {result.quality_score:.2f}")
            print(f"Confidence: {result.confidence_score:.2f}")
            print(f"Processing Time: {result.processing_time:.2f}s")
            
            if result.key_points:
                print("Key Points:")
                for i, point in enumerate(result.key_points, 1):
                    print(f"  {i}. {point}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_summarization())