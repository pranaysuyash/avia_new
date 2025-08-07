"""
AI-Powered Content Suggestions and Auto-completion Service
Provides intelligent suggestions, auto-completion, and content recommendations
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai
import aioredis
from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import Session
import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from collections import Counter, defaultdict

from api.database import User, Transcript, Team, AuditLog
from api.cache.redis_cache import redis_cache
from services.llm_provider_optimization import llm_optimization_service
from services.multi_llm_provider_service import multi_llm_service

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except:
    pass

logger = logging.getLogger(__name__)


class SuggestionType(Enum):
    """Types of suggestions"""
    AUTO_COMPLETE = "auto_complete"
    GRAMMAR_CORRECTION = "grammar_correction"
    STYLE_IMPROVEMENT = "style_improvement"
    CONTENT_EXPANSION = "content_expansion"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    KEYWORD_EXTRACTION = "keyword_extraction"
    TOPIC_SUGGESTION = "topic_suggestion"
    RELATED_CONTENT = "related_content"
    SMART_REPLY = "smart_reply"


class ContentContext(Enum):
    """Context for content generation"""
    TRANSCRIPT = "transcript"
    NOTE = "note"
    EMAIL = "email"
    DOCUMENT = "document"
    CHAT = "chat"
    SEARCH = "search"
    TITLE = "title"
    DESCRIPTION = "description"


@dataclass
class Suggestion:
    """Individual suggestion"""
    id: str
    type: SuggestionType
    text: str
    confidence: float
    metadata: Dict[str, Any]
    created_at: datetime


@dataclass
class AutoCompleteResult:
    """Auto-completion result"""
    completions: List[str]
    confidence_scores: List[float]
    context_aware: bool
    language: str


@dataclass
class ContentSuggestion:
    """Content suggestion result"""
    suggestions: List[Suggestion]
    keywords: List[str]
    topics: List[str]
    related_content: List[Dict[str, Any]]
    generated_at: datetime


@dataclass
class SmartReply:
    """Smart reply suggestion"""
    replies: List[str]
    tones: List[str]  # professional, casual, friendly, etc.
    contexts: List[str]  # acknowledgment, question, request, etc.
    confidence: float


class AISuggestionsService:
    """Service for AI-powered suggestions and auto-completion"""
    
    def __init__(self):
        self.cache_ttl = 3600  # 1 hour cache
        self.min_confidence = 0.7
        self.max_suggestions = 10
        self.context_window = 100  # characters
        
        # Initialize TF-IDF vectorizer for content similarity
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # User preference tracking
        self.user_preferences = defaultdict(lambda: {
            'accepted_suggestions': [],
            'rejected_suggestions': [],
            'common_phrases': Counter(),
            'writing_style': 'neutral'
        })
        
        # Pre-load common patterns
        self.common_patterns = {
            'greetings': ['Hello', 'Hi', 'Good morning', 'Good afternoon', 'Dear'],
            'closings': ['Best regards', 'Sincerely', 'Thank you', 'Kind regards', 'Regards'],
            'transitions': ['However', 'Furthermore', 'Additionally', 'Moreover', 'In conclusion'],
        }
        
        # Start background tasks
        asyncio.create_task(self._update_suggestion_models())
    
    async def get_auto_completions(
        self,
        db: Session,
        user_id: int,
        text: str,
        context: ContentContext,
        max_completions: int = 5,
        language: str = 'en'
    ) -> AutoCompleteResult:
        """
        Get auto-completion suggestions for partial text
        
        Args:
            db: Database session
            user_id: User ID
            text: Partial text to complete
            context: Content context
            max_completions: Maximum number of completions
            language: Language code
            
        Returns:
            AutoCompleteResult with completions
        """
        
        try:
            # Check cache first
            cache_key = f"autocomplete:{user_id}:{hash(text)}:{context.value}"
            cached = await redis_cache.get(cache_key)
            if cached:
                return self._deserialize_autocomplete(cached)
            
            # Get user context and preferences
            user_context = await self._get_user_context(db, user_id)
            
            # Analyze text for context
            text_analysis = self._analyze_text(text)
            
            # Generate completions based on context
            if context == ContentContext.TRANSCRIPT:
                completions = await self._get_transcript_completions(
                    db, user_id, text, text_analysis
                )
            elif context == ContentContext.EMAIL:
                completions = await self._get_email_completions(
                    text, text_analysis, user_context
                )
            elif context == ContentContext.SEARCH:
                completions = await self._get_search_completions(
                    db, text, user_context
                )
            else:
                completions = await self._get_general_completions(
                    text, text_analysis, context
                )
            
            # Apply user preferences
            completions = self._apply_user_preferences(
                completions, user_id, context
            )
            
            # Score and rank completions
            scored_completions = self._score_completions(
                text, completions, text_analysis
            )
            
            # Limit to max completions
            final_completions = scored_completions[:max_completions]
            
            result = AutoCompleteResult(
                completions=[c['text'] for c in final_completions],
                confidence_scores=[c['score'] for c in final_completions],
                context_aware=True,
                language=language
            )
            
            # Cache result
            await redis_cache.set(
                cache_key,
                self._serialize_autocomplete(result),
                expiry=300  # 5 minutes
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get auto-completions: {e}")
            # Return basic completions on error
            return AutoCompleteResult(
                completions=self._get_fallback_completions(text),
                confidence_scores=[0.5] * 3,
                context_aware=False,
                language=language
            )
    
    async def get_content_suggestions(
        self,
        db: Session,
        user_id: int,
        content: str,
        context: ContentContext,
        suggestion_types: List[SuggestionType] = None
    ) -> ContentSuggestion:
        """
        Get comprehensive content suggestions
        
        Args:
            db: Database session
            user_id: User ID
            content: Content to analyze
            context: Content context
            suggestion_types: Specific suggestion types to generate
            
        Returns:
            ContentSuggestion with various suggestions
        """
        
        try:
            # Default suggestion types based on context
            if not suggestion_types:
                suggestion_types = self._get_default_suggestion_types(context)
            
            # Analyze content
            content_analysis = self._analyze_content(content)
            
            # Generate suggestions in parallel
            suggestion_tasks = []
            
            if SuggestionType.GRAMMAR_CORRECTION in suggestion_types:
                suggestion_tasks.append(
                    self._get_grammar_suggestions(content, content_analysis)
                )
            
            if SuggestionType.STYLE_IMPROVEMENT in suggestion_types:
                suggestion_tasks.append(
                    self._get_style_suggestions(content, content_analysis, context)
                )
            
            if SuggestionType.CONTENT_EXPANSION in suggestion_types:
                suggestion_tasks.append(
                    self._get_expansion_suggestions(content, content_analysis)
                )
            
            if SuggestionType.SUMMARIZATION in suggestion_types:
                suggestion_tasks.append(
                    self._get_summary_suggestions(content, content_analysis)
                )
            
            if SuggestionType.KEYWORD_EXTRACTION in suggestion_types:
                suggestion_tasks.append(
                    self._extract_keywords(content, content_analysis)
                )
            
            # Wait for all suggestions
            suggestion_results = await asyncio.gather(*suggestion_tasks)
            
            # Flatten suggestions
            all_suggestions = []
            for suggestions in suggestion_results:
                if isinstance(suggestions, list):
                    all_suggestions.extend(suggestions)
            
            # Extract keywords and topics
            keywords = await self._extract_keywords(content, content_analysis)
            topics = await self._extract_topics(content, keywords)
            
            # Find related content
            related_content = await self._find_related_content(
                db, user_id, content, keywords
            )
            
            return ContentSuggestion(
                suggestions=all_suggestions,
                keywords=keywords,
                topics=topics,
                related_content=related_content,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get content suggestions: {e}")
            return ContentSuggestion(
                suggestions=[],
                keywords=[],
                topics=[],
                related_content=[],
                generated_at=datetime.utcnow()
            )
    
    async def get_smart_replies(
        self,
        db: Session,
        user_id: int,
        message: str,
        context: ContentContext,
        max_replies: int = 3
    ) -> SmartReply:
        """
        Generate smart reply suggestions
        
        Args:
            db: Database session
            user_id: User ID
            message: Message to reply to
            context: Content context
            max_replies: Maximum number of replies
            
        Returns:
            SmartReply with suggested responses
        """
        
        try:
            # Analyze message
            message_analysis = self._analyze_message(message)
            
            # Determine message intent
            intent = self._determine_intent(message, message_analysis)
            
            # Get user's reply history for personalization
            user_style = await self._get_user_reply_style(db, user_id)
            
            # Generate replies based on intent and context
            if intent == 'question':
                replies = await self._generate_question_replies(
                    message, message_analysis, context
                )
            elif intent == 'request':
                replies = await self._generate_request_replies(
                    message, message_analysis, context
                )
            elif intent == 'acknowledgment':
                replies = await self._generate_acknowledgment_replies(
                    message, message_analysis
                )
            else:
                replies = await self._generate_general_replies(
                    message, message_analysis, context
                )
            
            # Personalize replies based on user style
            personalized_replies = self._personalize_replies(
                replies, user_style
            )
            
            # Limit and score replies
            final_replies = personalized_replies[:max_replies]
            
            return SmartReply(
                replies=[r['text'] for r in final_replies],
                tones=[r['tone'] for r in final_replies],
                contexts=[r['context'] for r in final_replies],
                confidence=sum(r['confidence'] for r in final_replies) / len(final_replies)
            )
            
        except Exception as e:
            logger.error(f"Failed to generate smart replies: {e}")
            return SmartReply(
                replies=["Thank you for your message.", "I'll get back to you soon.", "Got it, thanks!"],
                tones=["professional", "professional", "casual"],
                contexts=["acknowledgment", "promise", "acknowledgment"],
                confidence=0.5
            )
    
    async def learn_from_feedback(
        self,
        db: Session,
        user_id: int,
        suggestion_id: str,
        accepted: bool,
        context: ContentContext
    ):
        """
        Learn from user feedback on suggestions
        
        Args:
            db: Database session
            user_id: User ID
            suggestion_id: Suggestion ID
            accepted: Whether suggestion was accepted
            context: Content context
        """
        
        try:
            # Update user preferences
            if accepted:
                self.user_preferences[user_id]['accepted_suggestions'].append(suggestion_id)
            else:
                self.user_preferences[user_id]['rejected_suggestions'].append(suggestion_id)
            
            # Update suggestion model weights
            await self._update_suggestion_weights(
                user_id, suggestion_id, accepted, context
            )
            
            # Log feedback for analytics
            from services.audit_logging_service import audit_service, AuditEventType
            
            audit_service.log_event(
                event_type=AuditEventType.AI_SUGGESTION_FEEDBACK,
                action=f"Suggestion {'accepted' if accepted else 'rejected'}",
                user_id=user_id,
                details={
                    "suggestion_id": suggestion_id,
                    "context": context.value,
                    "accepted": accepted
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to process suggestion feedback: {e}")
    
    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text for context and patterns"""
        
        words = word_tokenize(text.lower())
        
        return {
            'length': len(text),
            'word_count': len(words),
            'last_word': words[-1] if words else '',
            'last_char': text[-1] if text else '',
            'starts_with_capital': text[0].isupper() if text else False,
            'has_punctuation': any(c in text for c in '.!?'),
            'words': words
        }
    
    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Comprehensive content analysis"""
        
        sentences = sent_tokenize(content)
        words = word_tokenize(content.lower())
        
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        filtered_words = [w for w in words if w not in stop_words and w.isalpha()]
        
        # POS tagging
        pos_tags = nltk.pos_tag(words)
        
        return {
            'sentences': sentences,
            'sentence_count': len(sentences),
            'words': words,
            'word_count': len(words),
            'filtered_words': filtered_words,
            'pos_tags': pos_tags,
            'avg_sentence_length': len(words) / max(len(sentences), 1),
            'unique_words': len(set(filtered_words)),
            'readability_score': self._calculate_readability(content, sentences, words)
        }
    
    def _calculate_readability(self, text: str, sentences: List[str], words: List[str]) -> float:
        """Calculate readability score (simplified Flesch Reading Ease)"""
        
        if not sentences or not words:
            return 0.0
        
        # Count syllables (simplified)
        syllable_count = sum(self._count_syllables(word) for word in words)
        
        # Flesch Reading Ease formula
        score = 206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (syllable_count / len(words))
        
        # Normalize to 0-100
        return max(0, min(100, score))
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)"""
        
        word = word.lower()
        count = 0
        vowels = 'aeiouy'
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                count += 1
            previous_was_vowel = is_vowel
        
        if word.endswith('e'):
            count -= 1
        if count == 0:
            count = 1
            
        return count
    
    async def _get_transcript_completions(
        self,
        db: Session,
        user_id: int,
        text: str,
        analysis: Dict[str, Any]
    ) -> List[str]:
        """Get completions for transcript context"""
        
        completions = []
        
        # Get common phrases from user's transcripts
        recent_transcripts = db.query(Transcript).filter(
            Transcript.user_id == user_id
        ).order_by(Transcript.created_at.desc()).limit(10).all()
        
        # Extract common phrases
        common_phrases = Counter()
        for transcript in recent_transcripts:
            if transcript.text:
                # Find phrases starting with the current text
                sentences = sent_tokenize(transcript.text)
                for sentence in sentences:
                    if sentence.lower().startswith(text.lower()):
                        common_phrases[sentence] += 1
        
        # Add most common completions
        for phrase, count in common_phrases.most_common(5):
            completions.append(phrase[len(text):])
        
        # Add context-aware completions using LLM
        if len(completions) < 3:
            llm_completions = await self._get_llm_completions(text, 'transcript')
            completions.extend(llm_completions)
        
        return completions
    
    async def _get_email_completions(
        self,
        text: str,
        analysis: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> List[str]:
        """Get completions for email context"""
        
        completions = []
        
        # Check for common email patterns
        text_lower = text.lower()
        
        # Greetings
        if text_lower.startswith(('hi', 'hello', 'dear', 'good')):
            completions.extend([
                ' team,',
                ' there,',
                ' [Name],',
                ' morning,',
                ' afternoon,'
            ])
        
        # Closings
        elif any(text_lower.startswith(closing.lower()) for closing in self.common_patterns['closings']):
            completions.extend([
                ',\n[Your Name]',
                ',\nBest,\n[Your Name]',
                ' and have a great day!',
            ])
        
        # Common email phrases
        elif text_lower.startswith('thank'):
            completions.extend([
                ' you for your email.',
                ' you for reaching out.',
                ' you for the update.',
                ' you for your time.',
            ])
        elif text_lower.startswith('please'):
            completions.extend([
                ' let me know if you have any questions.',
                ' find attached',
                ' see below for',
                ' feel free to',
            ])
        
        # LLM-based completions
        if len(completions) < 3:
            llm_completions = await self._get_llm_completions(text, 'email')
            completions.extend(llm_completions)
        
        return completions
    
    async def _get_llm_completions(self, text: str, context: str) -> List[str]:
        """Get completions using LLM"""
        
        try:
            # Use the multi-LLM service for better completions
            prompt = f"""Complete the following {context} text. Provide 3 natural continuations.
Text: "{text}"

Provide only the completions, one per line, without the original text."""
            
            response = await multi_llm_service.generate_completion(
                prompt=prompt,
                max_tokens=100,
                temperature=0.7,
                model_preference="fast"
            )
            
            # Parse completions
            completions = response.strip().split('\n')
            return [c.strip() for c in completions if c.strip()][:3]
            
        except Exception as e:
            logger.error(f"Failed to get LLM completions: {e}")
            return []
    
    async def _get_grammar_suggestions(
        self,
        content: str,
        analysis: Dict[str, Any]
    ) -> List[Suggestion]:
        """Get grammar correction suggestions"""
        
        suggestions = []
        
        try:
            # Use LLM for grammar checking
            prompt = f"""Check the following text for grammar errors and provide corrections.
For each error found, provide:
1. The incorrect text
2. The suggested correction
3. Brief explanation

Text: "{content}"

Format: ERROR: [incorrect] -> CORRECTION: [correct] - REASON: [explanation]"""
            
            response = await multi_llm_service.generate_completion(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3,
                model_preference="quality"
            )
            
            # Parse grammar suggestions
            for line in response.strip().split('\n'):
                if 'ERROR:' in line and 'CORRECTION:' in line:
                    try:
                        error_part = line.split('ERROR:')[1].split('->')[0].strip()
                        correction_part = line.split('CORRECTION:')[1].split('-')[0].strip()
                        reason = line.split('REASON:')[1].strip() if 'REASON:' in line else ''
                        
                        suggestions.append(Suggestion(
                            id=f"grammar_{len(suggestions)}",
                            type=SuggestionType.GRAMMAR_CORRECTION,
                            text=content.replace(error_part, correction_part),
                            confidence=0.85,
                            metadata={
                                'error': error_part,
                                'correction': correction_part,
                                'reason': reason
                            },
                            created_at=datetime.utcnow()
                        ))
                    except:
                        continue
            
        except Exception as e:
            logger.error(f"Failed to get grammar suggestions: {e}")
        
        return suggestions
    
    async def _get_style_suggestions(
        self,
        content: str,
        analysis: Dict[str, Any],
        context: ContentContext
    ) -> List[Suggestion]:
        """Get style improvement suggestions"""
        
        suggestions = []
        
        try:
            # Determine target style based on context
            target_style = {
                ContentContext.EMAIL: "professional and concise",
                ContentContext.DOCUMENT: "clear and formal",
                ContentContext.CHAT: "conversational and friendly",
                ContentContext.TRANSCRIPT: "clear and natural"
            }.get(context, "clear and engaging")
            
            prompt = f"""Suggest style improvements for the following text to make it more {target_style}.
Provide 2-3 specific suggestions with examples.

Text: "{content}"

Format each suggestion as:
SUGGESTION: [description]
EXAMPLE: [improved version]"""
            
            response = await multi_llm_service.generate_completion(
                prompt=prompt,
                max_tokens=500,
                temperature=0.7,
                model_preference="quality"
            )
            
            # Parse style suggestions
            current_suggestion = None
            for line in response.strip().split('\n'):
                if line.startswith('SUGGESTION:'):
                    if current_suggestion:
                        suggestions.append(current_suggestion)
                    current_suggestion = {
                        'description': line.replace('SUGGESTION:', '').strip(),
                        'example': ''
                    }
                elif line.startswith('EXAMPLE:') and current_suggestion:
                    example_text = line.replace('EXAMPLE:', '').strip()
                    suggestions.append(Suggestion(
                        id=f"style_{len(suggestions)}",
                        type=SuggestionType.STYLE_IMPROVEMENT,
                        text=example_text,
                        confidence=0.75,
                        metadata={
                            'description': current_suggestion['description'],
                            'original': content
                        },
                        created_at=datetime.utcnow()
                    ))
                    current_suggestion = None
            
        except Exception as e:
            logger.error(f"Failed to get style suggestions: {e}")
        
        return suggestions
    
    async def _extract_keywords(
        self,
        content: str,
        analysis: Dict[str, Any]
    ) -> List[str]:
        """Extract keywords from content"""
        
        keywords = []
        
        try:
            # Use TF-IDF for keyword extraction
            if analysis.get('filtered_words'):
                word_freq = Counter(analysis['filtered_words'])
                # Get top keywords
                keywords = [word for word, _ in word_freq.most_common(10)]
            
            # Enhance with LLM extraction
            if len(keywords) < 5:
                prompt = f"""Extract the 5 most important keywords from this text:
"{content}"

Provide only the keywords, one per line."""
                
                response = await multi_llm_service.generate_completion(
                    prompt=prompt,
                    max_tokens=50,
                    temperature=0.3,
                    model_preference="fast"
                )
                
                llm_keywords = [k.strip() for k in response.strip().split('\n') if k.strip()]
                keywords.extend(llm_keywords)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_keywords = []
            for k in keywords:
                if k.lower() not in seen:
                    seen.add(k.lower())
                    unique_keywords.append(k)
            
            return unique_keywords[:10]
            
        except Exception as e:
            logger.error(f"Failed to extract keywords: {e}")
            return []
    
    async def _find_related_content(
        self,
        db: Session,
        user_id: int,
        content: str,
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """Find related content from user's history"""
        
        related = []
        
        try:
            # Search user's transcripts
            keyword_conditions = [
                Transcript.text.ilike(f'%{keyword}%')
                for keyword in keywords[:5]
            ]
            
            if keyword_conditions:
                related_transcripts = db.query(Transcript).filter(
                    and_(
                        Transcript.user_id == user_id,
                        or_(*keyword_conditions)
                    )
                ).limit(5).all()
                
                for transcript in related_transcripts:
                    # Calculate similarity score
                    similarity = self._calculate_similarity(content, transcript.text or '')
                    
                    related.append({
                        'type': 'transcript',
                        'id': transcript.id,
                        'title': transcript.title or 'Untitled',
                        'excerpt': (transcript.text or '')[:200] + '...',
                        'created_at': transcript.created_at.isoformat(),
                        'similarity': similarity
                    })
            
            # Sort by similarity
            related.sort(key=lambda x: x['similarity'], reverse=True)
            
            return related[:5]
            
        except Exception as e:
            logger.error(f"Failed to find related content: {e}")
            return []
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using cosine similarity"""
        
        try:
            if not text1 or not text2:
                return 0.0
            
            # Vectorize texts
            vectors = self.tfidf_vectorizer.fit_transform([text1, text2])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            
            return float(similarity)
            
        except:
            return 0.0
    
    def _get_fallback_completions(self, text: str) -> List[str]:
        """Get basic fallback completions"""
        
        # Simple pattern-based completions
        text_lower = text.lower()
        
        if text_lower.endswith(' the'):
            return [' following', ' above', ' same', ' next', ' previous']
        elif text_lower.endswith(' i'):
            return [' am', ' will', ' have', ' would', ' think']
        elif text_lower.endswith(' we'):
            return [' are', ' will', ' have', ' need', ' should']
        elif text_lower.endswith(' please'):
            return [' let me know', ' find attached', ' see below', ' note that']
        else:
            # Generic completions
            return [' and', ' to', ' for', ' that', ' with']
    
    def _score_completions(
        self,
        original_text: str,
        completions: List[str],
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Score and rank completions"""
        
        scored = []
        
        for completion in completions:
            score = 1.0
            
            # Length appropriateness
            if len(completion) < 2:
                score *= 0.5
            elif len(completion) > 50:
                score *= 0.8
            
            # Grammatical coherence
            full_text = original_text + completion
            if full_text[-1] not in '.!?,;:':
                score *= 0.9
            
            # Capitalize after period
            if original_text.endswith('.') and completion and not completion[0].isupper():
                score *= 0.8
            
            scored.append({
                'text': completion,
                'score': score
            })
        
        # Sort by score
        scored.sort(key=lambda x: x['score'], reverse=True)
        
        return scored
    
    async def _update_suggestion_models(self):
        """Background task to update suggestion models"""
        
        while True:
            try:
                await asyncio.sleep(3600)  # Update every hour
                
                # Update TF-IDF model with new content
                # In production, this would retrain on recent content
                
                logger.info("Updated suggestion models")
                
            except Exception as e:
                logger.error(f"Failed to update suggestion models: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes
    
    def _serialize_autocomplete(self, result: AutoCompleteResult) -> str:
        """Serialize auto-complete result for caching"""
        
        return json.dumps({
            'completions': result.completions,
            'confidence_scores': result.confidence_scores,
            'context_aware': result.context_aware,
            'language': result.language
        })
    
    def _deserialize_autocomplete(self, data: str) -> AutoCompleteResult:
        """Deserialize cached auto-complete result"""
        
        cached = json.loads(data)
        return AutoCompleteResult(**cached)
    
    async def _get_user_context(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get user context for personalization"""
        
        user = db.query(User).filter(User.id == user_id).first()
        
        return {
            'user_id': user_id,
            'preferences': self.user_preferences.get(user_id, {}),
            'subscription_tier': user.subscription_tier if user else 'free',
            'language': 'en'  # Could be determined from user preferences
        }
    
    def _apply_user_preferences(
        self,
        completions: List[str],
        user_id: int,
        context: ContentContext
    ) -> List[str]:
        """Apply user preferences to completions"""
        
        preferences = self.user_preferences.get(user_id, {})
        
        # Filter out previously rejected patterns
        rejected = preferences.get('rejected_suggestions', [])
        filtered = [c for c in completions if not any(r in c for r in rejected)]
        
        # Prioritize commonly used phrases
        common_phrases = preferences.get('common_phrases', Counter())
        
        # Score based on usage frequency
        scored = []
        for completion in filtered:
            score = sum(
                common_phrases.get(phrase, 0)
                for phrase in common_phrases
                if phrase in completion
            )
            scored.append((completion, score))
        
        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [c for c, _ in scored] + [c for c in completions if c not in filtered]
    
    def _get_default_suggestion_types(self, context: ContentContext) -> List[SuggestionType]:
        """Get default suggestion types based on context"""
        
        defaults = {
            ContentContext.TRANSCRIPT: [
                SuggestionType.GRAMMAR_CORRECTION,
                SuggestionType.SUMMARIZATION,
                SuggestionType.KEYWORD_EXTRACTION
            ],
            ContentContext.EMAIL: [
                SuggestionType.GRAMMAR_CORRECTION,
                SuggestionType.STYLE_IMPROVEMENT,
                SuggestionType.SMART_REPLY
            ],
            ContentContext.DOCUMENT: [
                SuggestionType.GRAMMAR_CORRECTION,
                SuggestionType.STYLE_IMPROVEMENT,
                SuggestionType.CONTENT_EXPANSION,
                SuggestionType.SUMMARIZATION
            ],
            ContentContext.CHAT: [
                SuggestionType.SMART_REPLY,
                SuggestionType.AUTO_COMPLETE
            ]
        }
        
        return defaults.get(context, [SuggestionType.GRAMMAR_CORRECTION])


# Global AI suggestions service instance
ai_suggestions_service = AISuggestionsService()