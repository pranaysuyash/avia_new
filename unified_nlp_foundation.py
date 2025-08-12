#!/usr/bin/env python3
"""
Unified NLP Foundation for All Collaborative Intelligence Features
Provides enhanced NLP capabilities with fallback mechanisms for all features
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class NLPCapability(Enum):
    """Available NLP capabilities"""
    BASIC_NER = "basic_ner"
    ADVANCED_NER = "advanced_ner"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    EMOTION_DETECTION = "emotion_detection"
    TOPIC_MODELING = "topic_modeling"
    SUMMARIZATION = "summarization"
    QUESTION_DETECTION = "question_detection"
    INTENT_CLASSIFICATION = "intent_classification"
    ENTITY_LINKING = "entity_linking"
    DEPENDENCY_PARSING = "dependency_parsing"
    COREFERENCE_RESOLUTION = "coreference_resolution"

@dataclass
class NLPResult:
    """Unified NLP processing result"""
    text: str
    capabilities_used: List[str]
    entities: List[Dict[str, Any]]
    sentiment: Dict[str, float]
    emotions: Dict[str, float]
    topics: List[Dict[str, Any]]
    summary: Optional[str]
    questions: List[str]
    intent: Optional[str]
    confidence_scores: Dict[str, float]
    processing_time: float
    model_info: Dict[str, str]

class UnifiedNLPFoundation:
    """
    Unified NLP foundation that provides enhanced capabilities to all features
    Uses intelligent fallback mechanisms for maximum compatibility
    """
    
    def __init__(self):
        self.available_capabilities = set()
        self.models = {}
        self.fallback_models = {}
        
        # Initialize all NLP components with fallbacks
        self._initialize_spacy_models()
        self._initialize_transformers()
        self._initialize_openai_integration()
        self._initialize_fallback_systems()
        
        logger.info(f"Unified NLP Foundation initialized with capabilities: {self.available_capabilities}")
    
    def _initialize_spacy_models(self):
        """Initialize spaCy models with intelligent fallback"""
        try:
            import spacy
            
            # Try transformer model first (best accuracy)
            try:
                self.models['spacy_transformer'] = spacy.load("en_core_web_trf")
                self.available_capabilities.update([
                    NLPCapability.ADVANCED_NER,
                    NLPCapability.DEPENDENCY_PARSING,
                    NLPCapability.ENTITY_LINKING
                ])
                logger.info("✅ Loaded spaCy transformer model (en_core_web_trf)")
            except OSError:
                # Fallback to large model
                try:
                    self.models['spacy_large'] = spacy.load("en_core_web_lg")
                    self.available_capabilities.update([
                        NLPCapability.ADVANCED_NER,
                        NLPCapability.DEPENDENCY_PARSING
                    ])
                    logger.info("✅ Loaded spaCy large model (en_core_web_lg)")
                except OSError:
                    # Final fallback to small model
                    self.models['spacy_small'] = spacy.load("en_core_web_sm")
                    self.available_capabilities.add(NLPCapability.BASIC_NER)
                    logger.warning("⚠️ Using spaCy small model - consider installing larger models")
                    
        except ImportError:
            logger.error("❌ spaCy not available - NLP capabilities will be limited")
    
    def _initialize_transformers(self):
        """Initialize Hugging Face transformers with fallbacks"""
        try:
            from transformers import pipeline, AutoTokenizer, AutoModel
            
            # Sentiment analysis
            try:
                self.models['sentiment'] = pipeline("sentiment-analysis", 
                                                   model="cardiffnlp/twitter-roberta-base-sentiment-latest")
                self.available_capabilities.add(NLPCapability.SENTIMENT_ANALYSIS)
                logger.info("✅ Loaded transformer sentiment analysis model")
            except Exception as e:
                logger.warning(f"⚠️ Transformer sentiment model failed: {e}")
            
            # Emotion detection
            try:
                self.models['emotion'] = pipeline("text-classification", 
                                                 model="j-hartmann/emotion-english-distilroberta-base")
                self.available_capabilities.add(NLPCapability.EMOTION_DETECTION)
                logger.info("✅ Loaded transformer emotion detection model")
            except Exception as e:
                logger.warning(f"⚠️ Transformer emotion model failed: {e}")
            
            # Summarization
            try:
                self.models['summarization'] = pipeline("summarization", 
                                                       model="facebook/bart-large-cnn")
                self.available_capabilities.add(NLPCapability.SUMMARIZATION)
                logger.info("✅ Loaded transformer summarization model")
            except Exception as e:
                logger.warning(f"⚠️ Transformer summarization model failed: {e}")
                
        except ImportError:
            logger.warning("⚠️ Transformers not available - using fallback models")
    
    def _initialize_openai_integration(self):
        """Initialize OpenAI integration for advanced capabilities"""
        try:
            import openai
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.models['openai'] = openai
                self.available_capabilities.update([
                    NLPCapability.ADVANCED_NER,
                    NLPCapability.SUMMARIZATION,
                    NLPCapability.INTENT_CLASSIFICATION,
                    NLPCapability.TOPIC_MODELING
                ])
                logger.info("✅ OpenAI integration available")
            else:
                logger.warning("⚠️ OpenAI API key not found")
        except ImportError:
            logger.warning("⚠️ OpenAI not available")
    
    def _initialize_fallback_systems(self):
        """Initialize fallback systems for when advanced models aren't available"""
        try:
            from textblob import TextBlob
            self.fallback_models['textblob'] = TextBlob
            self.available_capabilities.update([
                NLPCapability.SENTIMENT_ANALYSIS,
                NLPCapability.BASIC_NER
            ])
            logger.info("✅ TextBlob fallback available")
        except ImportError:
            logger.warning("⚠️ TextBlob fallback not available")
        
        # Pattern-based fallbacks
        self.fallback_models['patterns'] = {
            'questions': [r'\?', r'^(what|how|why|when|where|who)', r'(can|could|would|should) (you|we|i)'],
            'decisions': [r'(decide|agreed|consensus|vote|choose|final)', r'(let\'s|we will|we should)'],
            'action_items': [r'(todo|action|task|assign)', r'(will|should|need to) (do|complete|finish)']
        }
        self.available_capabilities.update([
            NLPCapability.QUESTION_DETECTION,
            NLPCapability.INTENT_CLASSIFICATION
        ])
        logger.info("✅ Pattern-based fallbacks initialized")    a
sync def process_text(self, text: str, 
                          requested_capabilities: List[NLPCapability] = None,
                          context: Dict[str, Any] = None) -> NLPResult:
        """
        Process text with requested NLP capabilities using best available models
        Falls back gracefully when advanced models aren't available
        """
        start_time = datetime.now()
        
        if requested_capabilities is None:
            requested_capabilities = list(self.available_capabilities)
        
        result = NLPResult(
            text=text,
            capabilities_used=[],
            entities=[],
            sentiment={},
            emotions={},
            topics=[],
            summary=None,
            questions=[],
            intent=None,
            confidence_scores={},
            processing_time=0.0,
            model_info={}
        )
        
        # Process each requested capability
        for capability in requested_capabilities:
            if capability in self.available_capabilities:
                await self._process_capability(text, capability, result, context)
        
        # Calculate processing time
        result.processing_time = (datetime.now() - start_time).total_seconds()
        
        return result
    
    async def _process_capability(self, text: str, capability: NLPCapability, 
                                result: NLPResult, context: Dict[str, Any] = None):
        """Process a specific NLP capability"""
        try:
            if capability == NLPCapability.ADVANCED_NER:
                await self._process_advanced_ner(text, result)
            elif capability == NLPCapability.BASIC_NER:
                await self._process_basic_ner(text, result)
            elif capability == NLPCapability.SENTIMENT_ANALYSIS:
                await self._process_sentiment(text, result)
            elif capability == NLPCapability.EMOTION_DETECTION:
                await self._process_emotions(text, result)
            elif capability == NLPCapability.SUMMARIZATION:
                await self._process_summarization(text, result, context)
            elif capability == NLPCapability.QUESTION_DETECTION:
                await self._process_questions(text, result)
            elif capability == NLPCapability.INTENT_CLASSIFICATION:
                await self._process_intent(text, result)
            elif capability == NLPCapability.TOPIC_MODELING:
                await self._process_topics(text, result)
                
            result.capabilities_used.append(capability.value)
            
        except Exception as e:
            logger.error(f"Error processing {capability.value}: {e}")
    
    async def _process_advanced_ner(self, text: str, result: NLPResult):
        """Process advanced NER using best available model"""
        model_used = None
        
        # Try transformer model first
        if 'spacy_transformer' in self.models:
            doc = self.models['spacy_transformer'](text)
            model_used = 'spacy_transformer'
        elif 'spacy_large' in self.models:
            doc = self.models['spacy_large'](text)
            model_used = 'spacy_large'
        elif 'spacy_small' in self.models:
            doc = self.models['spacy_small'](text)
            model_used = 'spacy_small'
        else:
            return await self._process_basic_ner(text, result)
        
        # Extract entities
        for ent in doc.ents:
            result.entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': getattr(ent, 'confidence', 0.9)
            })
        
        result.model_info['ner'] = model_used
        result.confidence_scores['ner'] = 0.9 if model_used == 'spacy_transformer' else 0.7
    
    async def _process_basic_ner(self, text: str, result: NLPResult):
        """Basic NER using TextBlob fallback"""
        if 'textblob' not in self.fallback_models:
            return
        
        blob = self.fallback_models['textblob'](text)
        
        # Extract noun phrases as basic entities
        for phrase in blob.noun_phrases:
            result.entities.append({
                'text': phrase,
                'label': 'ENTITY',
                'start': text.find(phrase),
                'end': text.find(phrase) + len(phrase),
                'confidence': 0.5
            })
        
        result.model_info['ner'] = 'textblob_fallback'
        result.confidence_scores['ner'] = 0.5
    
    async def _process_sentiment(self, text: str, result: NLPResult):
        """Process sentiment using best available model"""
        # Try transformer model first
        if 'sentiment' in self.models:
            sentiment_result = self.models['sentiment'](text)[0]
            
            # Convert to standardized format
            label = sentiment_result['label'].lower()
            score = sentiment_result['score']
            
            if 'positive' in label:
                result.sentiment = {'polarity': score, 'subjectivity': 0.5}
            elif 'negative' in label:
                result.sentiment = {'polarity': -score, 'subjectivity': 0.5}
            else:
                result.sentiment = {'polarity': 0.0, 'subjectivity': 0.5}
            
            result.model_info['sentiment'] = 'transformer'
            result.confidence_scores['sentiment'] = score
            
        # Fallback to TextBlob
        elif 'textblob' in self.fallback_models:
            blob = self.fallback_models['textblob'](text)
            result.sentiment = {
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity
            }
            result.model_info['sentiment'] = 'textblob_fallback'
            result.confidence_scores['sentiment'] = 0.6
    
    async def _process_emotions(self, text: str, result: NLPResult):
        """Process emotions using best available model"""
        if 'emotion' in self.models:
            emotion_results = self.models['emotion'](text)
            
            # Convert to standardized format
            emotions = {}
            for emotion_result in emotion_results:
                emotions[emotion_result['label'].lower()] = emotion_result['score']
            
            result.emotions = emotions
            result.model_info['emotion'] = 'transformer'
            result.confidence_scores['emotion'] = max(emotions.values()) if emotions else 0.5
        else:
            # Basic emotion inference from sentiment
            if result.sentiment:
                polarity = result.sentiment.get('polarity', 0)
                if polarity > 0.3:
                    result.emotions = {'joy': 0.7, 'neutral': 0.3}
                elif polarity < -0.3:
                    result.emotions = {'anger': 0.7, 'neutral': 0.3}
                else:
                    result.emotions = {'neutral': 0.8, 'joy': 0.1, 'anger': 0.1}
            
            result.model_info['emotion'] = 'sentiment_inference'
            result.confidence_scores['emotion'] = 0.4