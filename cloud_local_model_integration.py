#!/usr/bin/env python3
"""
Cloud and Local Model Integration
Implements intelligent fallback between cloud services and local models
"""

import asyncio
import logging
import os
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import aiohttp
# import backoff  # Optional dependency
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    """Model provider types"""
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    SPACY_LOCAL = "spacy_local"
    TRANSFORMERS_LOCAL = "transformers_local"
    CUSTOM_API = "custom_api"

class ProcessingStatus(Enum):
    """Processing status types"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    NETWORK_ERROR = "network_error"
    MODEL_UNAVAILABLE = "model_unavailable"

@dataclass
class ProcessingResult:
    """Result of model processing"""
    status: ProcessingStatus
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    provider_used: Optional[ModelProvider] = None
    model_id: Optional[str] = None
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProviderConfig:
    """Configuration for a model provider"""
    provider: ModelProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_id: str = ""
    max_retries: int = 3
    timeout_seconds: int = 30
    rate_limit_per_minute: int = 60
    priority: int = 5  # 1 = highest priority
    enabled: bool = True
    
    # Cost and quota management
    cost_per_request: float = 0.0
    monthly_quota: Optional[int] = None
    current_usage: int = 0
    
    # Performance tracking
    average_response_time: float = 0.0
    success_rate: float = 1.0
    last_used: Optional[datetime] = None
    
    def is_available(self) -> bool:
        """Check if provider is available for use"""
        if not self.enabled:
            return False
        
        # Check quota
        if self.monthly_quota and self.current_usage >= self.monthly_quota:
            return False
        
        return True
    
    def update_usage(self, success: bool, response_time: float):
        """Update usage statistics"""
        self.current_usage += 1
        self.last_used = datetime.now()
        
        # Update average response time
        if self.average_response_time == 0.0:
            self.average_response_time = response_time
        else:
            self.average_response_time = (self.average_response_time * 0.9) + (response_time * 0.1)
        
        # Update success rate
        if success:
            self.success_rate = (self.success_rate * 0.95) + (1.0 * 0.05)
        else:
            self.success_rate = (self.success_rate * 0.95) + (0.0 * 0.05)

class CloudModelProvider:
    """Base class for cloud model providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize the provider"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def process(self, text: str, task_type: str, **kwargs) -> ProcessingResult:
        """Process text using the cloud provider"""
        start_time = time.time()
        
        try:
            # Prepare request based on task type
            if task_type == "transcription":
                result = await self._process_transcription(text, **kwargs)
            elif task_type == "translation":
                result = await self._process_translation(text, **kwargs)
            elif task_type == "classification":
                result = await self._process_classification(text, **kwargs)
            elif task_type == "entity_extraction":
                result = await self._process_entity_extraction(text, **kwargs)
            elif task_type == "summarization":
                result = await self._process_summarization(text, **kwargs)
            else:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error_message=f"Unsupported task type: {task_type}",
                    processing_time=time.time() - start_time,
                    provider_used=self.config.provider
                )
            
            processing_time = time.time() - start_time
            self.config.update_usage(True, processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data=result,
                processing_time=processing_time,
                provider_used=self.config.provider,
                model_id=self.config.model_id
            )
            
        except asyncio.TimeoutError:
            processing_time = time.time() - start_time
            self.config.update_usage(False, processing_time)
            return ProcessingResult(
                status=ProcessingStatus.TIMEOUT,
                error_message="Request timed out",
                processing_time=processing_time,
                provider_used=self.config.provider
            )
        except Exception as e:
            processing_time = time.time() - start_time
            self.config.update_usage(False, processing_time)
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                processing_time=processing_time,
                provider_used=self.config.provider
            )
    
    async def _process_transcription(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process transcription task - override in subclasses"""
        return {"text": text, "task": "transcription", "provider": self.config.provider.value}
    
    async def _process_translation(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process translation task - override in subclasses"""
        target_language = kwargs.get("target_language", "en")
        return {"translated_text": text, "target_language": target_language, "provider": self.config.provider.value}
    
    async def _process_classification(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process classification task - override in subclasses"""
        labels = kwargs.get("labels", ["positive", "negative", "neutral"])
        return {"predicted_label": labels[0], "confidence": 0.8, "all_scores": {label: 0.8 if label == labels[0] else 0.2 for label in labels}}
    
    async def _process_entity_extraction(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process entity extraction task - override in subclasses"""
        return {"entities": [], "text": text, "provider": self.config.provider.value}
    
    async def _process_summarization(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process summarization task - override in subclasses"""
        max_length = kwargs.get("max_length", 100)
        return {"summary": text[:max_length] + "...", "original_length": len(text), "provider": self.config.provider.value}
    
    def is_healthy(self) -> bool:
        """Check if provider is healthy"""
        return (
            self.config.is_available() and
            self.config.success_rate > 0.5 and
            self.config.average_response_time < 10.0
        )

class OpenAIProvider(CloudModelProvider):
    """OpenAI API provider"""
    
    async def process(self, text: str, task_type: str, **kwargs) -> ProcessingResult:
        """Process text using OpenAI API"""
        start_time = time.time()
        
        try:
            await self.initialize()
            
            if task_type == "ner":
                return await self._process_ner(text, **kwargs)
            elif task_type == "sentiment":
                return await self._process_sentiment(text, **kwargs)
            elif task_type == "classification":
                return await self._process_classification(text, **kwargs)
            else:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error_message=f"Unsupported task type: {task_type}",
                    provider_used=ModelProvider.OPENAI
                )
        
        except asyncio.TimeoutError:
            return ProcessingResult(
                status=ProcessingStatus.TIMEOUT,
                error_message="Request timed out",
                processing_time=time.time() - start_time,
                provider_used=ModelProvider.OPENAI
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                processing_time=time.time() - start_time,
                provider_used=ModelProvider.OPENAI
            )
    
    async def _process_ner(self, text: str, **kwargs) -> ProcessingResult:
        """Process NER using OpenAI"""
        start_time = time.time()
        
        # Simulate OpenAI API call for NER
        prompt = f"""
        Extract named entities from the following text and return them in JSON format:
        
        Text: {text}
        
        Return format:
        {{
            "entities": [
                {{"text": "entity", "label": "PERSON|ORG|GPE|DATE|TIME", "start": 0, "end": 6, "confidence": 0.95}}
            ]
        }}
        """
        
        try:
            # Simulate API call (in real implementation, use OpenAI client)
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Mock response for demo
            entities = [
                {"text": "OpenAI", "label": "ORG", "start": 0, "end": 6, "confidence": 0.95},
                {"text": "today", "label": "DATE", "start": 20, "end": 25, "confidence": 0.88}
            ]
            
            processing_time = time.time() - start_time
            self.config.update_usage(True, processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data={"entities": entities},
                processing_time=processing_time,
                provider_used=ModelProvider.OPENAI,
                model_id=self.config.model_id,
                confidence_score=0.92,
                metadata={"prompt_tokens": len(prompt.split()), "completion_tokens": 50}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.config.update_usage(False, processing_time)
            raise
    
    async def _process_sentiment(self, text: str, **kwargs) -> ProcessingResult:
        """Process sentiment using OpenAI"""
        start_time = time.time()
        
        try:
            # Simulate API call
            await asyncio.sleep(0.08)
            
            # Mock sentiment analysis
            sentiment_score = 0.3  # Slightly positive
            
            processing_time = time.time() - start_time
            self.config.update_usage(True, processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data={
                    "sentiment": {
                        "polarity": sentiment_score,
                        "subjectivity": 0.6,
                        "label": "positive" if sentiment_score > 0 else "negative" if sentiment_score < 0 else "neutral"
                    }
                },
                processing_time=processing_time,
                provider_used=ModelProvider.OPENAI,
                model_id=self.config.model_id,
                confidence_score=0.89
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.config.update_usage(False, processing_time)
            raise
    
    async def _process_classification(self, text: str, **kwargs) -> ProcessingResult:
        """Process text classification using OpenAI"""
        start_time = time.time()
        
        try:
            # Simulate API call
            await asyncio.sleep(0.12)
            
            # Mock classification
            categories = kwargs.get('categories', ['business', 'technology', 'sports', 'politics'])
            predicted_category = 'technology'  # Mock prediction
            
            processing_time = time.time() - start_time
            self.config.update_usage(True, processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data={
                    "classification": {
                        "predicted_class": predicted_category,
                        "confidence": 0.87,
                        "all_scores": {cat: 0.87 if cat == predicted_category else 0.13/(len(categories)-1) for cat in categories}
                    }
                },
                processing_time=processing_time,
                provider_used=ModelProvider.OPENAI,
                model_id=self.config.model_id,
                confidence_score=0.87
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.config.update_usage(False, processing_time)
            raise

class HuggingFaceProvider(CloudModelProvider):
    """Hugging Face API provider"""
    
    async def process(self, text: str, task_type: str, **kwargs) -> ProcessingResult:
        """Process text using Hugging Face API"""
        start_time = time.time()
        
        try:
            await self.initialize()
            
            if task_type == "ner":
                return await self._process_ner(text, **kwargs)
            elif task_type == "sentiment":
                return await self._process_sentiment(text, **kwargs)
            elif task_type == "classification":
                return await self._process_classification(text, **kwargs)
            else:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error_message=f"Unsupported task type: {task_type}",
                    provider_used=ModelProvider.HUGGINGFACE
                )
        
        except asyncio.TimeoutError:
            return ProcessingResult(
                status=ProcessingStatus.TIMEOUT,
                error_message="Request timed out",
                processing_time=time.time() - start_time,
                provider_used=ModelProvider.HUGGINGFACE
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                processing_time=time.time() - start_time,
                provider_used=ModelProvider.HUGGINGFACE
            )
    
    async def _process_ner(self, text: str, **kwargs) -> ProcessingResult:
        """Process NER using Hugging Face"""
        start_time = time.time()
        
        try:
            # Simulate HF API call
            await asyncio.sleep(0.15)
            
            # Mock NER results
            entities = [
                {"text": "Hugging Face", "label": "ORG", "start": 0, "end": 12, "confidence": 0.92},
                {"text": "transformer", "label": "MISC", "start": 25, "end": 36, "confidence": 0.85}
            ]
            
            processing_time = time.time() - start_time
            self.config.update_usage(True, processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data={"entities": entities},
                processing_time=processing_time,
                provider_used=ModelProvider.HUGGINGFACE,
                model_id=self.config.model_id,
                confidence_score=0.89
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.config.update_usage(False, processing_time)
            raise
    
    async def _process_sentiment(self, text: str, **kwargs) -> ProcessingResult:
        """Process sentiment using Hugging Face"""
        start_time = time.time()
        
        try:
            # Simulate API call
            await asyncio.sleep(0.12)
            
            # Mock sentiment analysis
            sentiment_results = [
                {"label": "POSITIVE", "score": 0.75},
                {"label": "NEGATIVE", "score": 0.25}
            ]
            
            processing_time = time.time() - start_time
            self.config.update_usage(True, processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data={
                    "sentiment": {
                        "results": sentiment_results,
                        "predicted_label": sentiment_results[0]["label"],
                        "confidence": sentiment_results[0]["score"]
                    }
                },
                processing_time=processing_time,
                provider_used=ModelProvider.HUGGINGFACE,
                model_id=self.config.model_id,
                confidence_score=0.75
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.config.update_usage(False, processing_time)
            raise
    
    async def _process_classification(self, text: str, **kwargs) -> ProcessingResult:
        """Process classification using Hugging Face"""
        start_time = time.time()
        
        try:
            # Simulate API call
            await asyncio.sleep(0.18)
            
            # Mock classification results
            classification_results = [
                {"label": "technology", "score": 0.82},
                {"label": "business", "score": 0.12},
                {"label": "science", "score": 0.06}
            ]
            
            processing_time = time.time() - start_time
            self.config.update_usage(True, processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data={
                    "classification": {
                        "results": classification_results,
                        "predicted_class": classification_results[0]["label"],
                        "confidence": classification_results[0]["score"]
                    }
                },
                processing_time=processing_time,
                provider_used=ModelProvider.HUGGINGFACE,
                model_id=self.config.model_id,
                confidence_score=0.82
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.config.update_usage(False, processing_time)
            raise

class LocalModelProvider(ABC):
    """Base class for local model providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.model = None
        self.is_loaded = False
    
    async def initialize(self):
        """Initialize the local model"""
        if not self.is_loaded:
            await self._load_model()
            self.is_loaded = True
    
    @abstractmethod
    async def _load_model(self):
        """Load the local model"""
        raise NotImplementedError("Subclasses must implement _load_model method")
    
    @abstractmethod
    async def _process_transcription(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process transcription task"""
        raise NotImplementedError("Subclasses must implement _process_transcription method")
    
    @abstractmethod
    async def _process_translation(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process translation task"""
        raise NotImplementedError("Subclasses must implement _process_translation method")
    
    @abstractmethod
    async def _process_classification(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process classification task"""
        raise NotImplementedError("Subclasses must implement _process_classification method")
    
    @abstractmethod
    async def _process_entity_extraction(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process entity extraction task"""
        raise NotImplementedError("Subclasses must implement _process_entity_extraction method")
    
    @abstractmethod
    async def _process_summarization(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process summarization task"""
        raise NotImplementedError("Subclasses must implement _process_summarization method")
    
    @abstractmethod
    async def _process_transcription(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process transcription task - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _process_transcription method")
    
    @abstractmethod
    async def _process_translation(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process translation task - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _process_translation method")
    
    @abstractmethod
    async def _process_classification(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process classification task - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _process_classification method")
    
    @abstractmethod
    async def _process_entity_extraction(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process entity extraction task - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _process_entity_extraction method")
    
    @abstractmethod
    async def _process_summarization(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process summarization task - override in subclasses"""
        raise NotImplementedError("Subclasses must implement _process_summarization method")
    
    async def process(self, text: str, task_type: str, **kwargs) -> ProcessingResult:
        """Process text using the local model"""
        start_time = time.time()
        
        try:
            await self.initialize()
            
            # Route to specific task processing
            if task_type == "transcription":
                result = await self._process_transcription(text, **kwargs)
            elif task_type == "translation":
                result = await self._process_translation(text, **kwargs)
            elif task_type == "classification":
                result = await self._process_classification(text, **kwargs)
            elif task_type == "entity_extraction":
                result = await self._process_entity_extraction(text, **kwargs)
            elif task_type == "summarization":
                result = await self._process_summarization(text, **kwargs)
            else:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error_message=f"Unsupported task type: {task_type}",
                    processing_time=time.time() - start_time,
                    provider_used=self.config.provider
                )
            
            processing_time = time.time() - start_time
            self.config.update_usage(True, processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data=result,
                processing_time=processing_time,
                provider_used=self.config.provider,
                model_id=self.config.model_id,
                confidence_score=result.get("confidence", 0.9)
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.config.update_usage(False, processing_time)
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                processing_time=processing_time,
                provider_used=self.config.provider
            )
    
    async def _process_transcription(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process transcription locally - override in subclasses"""
        return {"text": text, "task": "transcription", "provider": "local", "confidence": 0.9}
    
    async def _process_translation(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process translation locally - override in subclasses"""
        target_language = kwargs.get("target_language", "en")
        return {"translated_text": f"[LOCAL] {text}", "target_language": target_language, "confidence": 0.8}
    
    async def _process_classification(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process classification locally - override in subclasses"""
        labels = kwargs.get("labels", ["positive", "negative", "neutral"])
        # Simple local classification logic
        if "good" in text.lower() or "great" in text.lower():
            predicted = "positive"
        elif "bad" in text.lower() or "terrible" in text.lower():
            predicted = "negative"
        else:
            predicted = "neutral"
        
        return {
            "predicted_label": predicted,
            "confidence": 0.85,
            "all_scores": {label: 0.85 if label == predicted else 0.15 for label in labels}
        }
    
    async def _process_entity_extraction(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process entity extraction locally - override in subclasses"""
        # Simple entity extraction
        entities = []
        words = text.split()
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2:
                entities.append({
                    "text": word,
                    "label": "PERSON" if any(w in word.lower() for w in ["john", "mary", "mike"]) else "ORG",
                    "start": sum(len(w) + 1 for w in words[:i]),
                    "end": sum(len(w) + 1 for w in words[:i]) + len(word),
                    "confidence": 0.8
                })
        
        return {"entities": entities, "text": text, "provider": "local"}
    
    async def _process_summarization(self, text: str, **kwargs) -> Dict[str, Any]:
        """Process summarization locally - override in subclasses"""
        max_length = kwargs.get("max_length", 100)
        sentences = text.split(".")
        summary = ". ".join(sentences[:2]) if len(sentences) > 2 else text
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return {
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "compression_ratio": len(summary) / len(text),
            "provider": "local"
        }
    
    def is_healthy(self) -> bool:
        """Check if provider is healthy"""
        return self.is_loaded and self.config.is_available()

class SpacyLocalProvider(LocalModelProvider):
    """Local spaCy model provider"""
    
    async def _load_model(self):
        """Load spaCy model"""
        try:
            import spacy
            # Simulate model loading
            await asyncio.sleep(0.5)  # Simulate loading time
            self.model = {"name": self.config.model_id, "loaded": True}
            logger.info(f"Loaded spaCy model: {self.config.model_id}")
        except ImportError:
            raise Exception("spaCy not available")
        except Exception as e:
            raise Exception(f"Failed to load spaCy model: {e}")
    
    async def process(self, text: str, task_type: str, **kwargs) -> ProcessingResult:
        """Process text using local spaCy model"""
        start_time = time.time()
        
        try:
            await self.initialize()
            
            if task_type == "ner":
                return await self._process_ner(text, **kwargs)
            elif task_type == "sentiment":
                return await self._process_sentiment(text, **kwargs)
            elif task_type == "pos":
                return await self._process_pos(text, **kwargs)
            else:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error_message=f"Unsupported task type: {task_type}",
                    provider_used=ModelProvider.SPACY_LOCAL
                )
        
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                processing_time=time.time() - start_time,
                provider_used=ModelProvider.SPACY_LOCAL
            )
    
    async def _process_ner(self, text: str, **kwargs) -> ProcessingResult:
        """Process NER using local spaCy"""
        start_time = time.time()
        
        try:
            # Simulate spaCy processing
            await asyncio.sleep(0.02)  # Very fast local processing
            
            # Mock NER results
            entities = [
                {"text": "spaCy", "label": "ORG", "start": 0, "end": 5, "confidence": 0.88},
                {"text": "local", "label": "MISC", "start": 10, "end": 15, "confidence": 0.75}
            ]
            
            processing_time = time.time() - start_time
            self.config.update_usage(True, processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data={"entities": entities},
                processing_time=processing_time,
                provider_used=ModelProvider.SPACY_LOCAL,
                model_id=self.config.model_id,
                confidence_score=0.82
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.config.update_usage(False, processing_time)
            raise
    
    async def _process_sentiment(self, text: str, **kwargs) -> ProcessingResult:
        """Process sentiment using local spaCy (basic)"""
        start_time = time.time()
        
        try:
            # Simulate basic sentiment analysis
            await asyncio.sleep(0.01)
            
            # Simple rule-based sentiment (mock)
            positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful']
            negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing']
            
            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            if pos_count > neg_count:
                polarity = 0.5
                label = "positive"
            elif neg_count > pos_count:
                polarity = -0.5
                label = "negative"
            else:
                polarity = 0.0
                label = "neutral"
            
            processing_time = time.time() - start_time
            self.config.update_usage(True, processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data={
                    "sentiment": {
                        "polarity": polarity,
                        "subjectivity": 0.5,
                        "label": label,
                        "confidence": 0.6  # Lower confidence for rule-based
                    }
                },
                processing_time=processing_time,
                provider_used=ModelProvider.SPACY_LOCAL,
                model_id=self.config.model_id,
                confidence_score=0.6
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.config.update_usage(False, processing_time)
            raise
    
    async def _process_pos(self, text: str, **kwargs) -> ProcessingResult:
        """Process POS tagging using local spaCy"""
        start_time = time.time()
        
        try:
            # Simulate POS tagging
            await asyncio.sleep(0.015)
            
            # Mock POS results
            tokens = [
                {"text": "This", "pos": "DET", "tag": "DT"},
                {"text": "is", "pos": "AUX", "tag": "VBZ"},
                {"text": "a", "pos": "DET", "tag": "DT"},
                {"text": "test", "pos": "NOUN", "tag": "NN"}
            ]
            
            processing_time = time.time() - start_time
            self.config.update_usage(True, processing_time)
            
            return ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data={"tokens": tokens},
                processing_time=processing_time,
                provider_used=ModelProvider.SPACY_LOCAL,
                model_id=self.config.model_id,
                confidence_score=0.95  # High confidence for POS tagging
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.config.update_usage(False, processing_time)
            raise

class CloudLocalModelIntegrator:
    """Integrates cloud and local models with intelligent fallback"""
    
    def __init__(self):
        self.providers: Dict[str, Union[CloudModelProvider, LocalModelProvider]] = {}
        self.provider_configs: Dict[str, ProviderConfig] = {}
        self.fallback_chains: Dict[str, List[str]] = {}
        
        # Processing statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'fallback_usage': {},
            'provider_usage': {},
            'average_response_times': {},
            'error_types': {}
        }
        
        self._initialize_default_providers()
    
    def _initialize_default_providers(self):
        """Initialize default provider configurations"""
        
        # OpenAI configuration
        openai_config = ProviderConfig(
            provider=ModelProvider.OPENAI,
            api_key=os.getenv('OPENAI_API_KEY'),
            model_id="gpt-3.5-turbo",
            max_retries=3,
            timeout_seconds=30,
            rate_limit_per_minute=60,
            priority=1,  # Highest priority
            enabled=bool(os.getenv('OPENAI_API_KEY')),
            cost_per_request=0.002,
            monthly_quota=10000
        )
        
        # Hugging Face configuration
        hf_config = ProviderConfig(
            provider=ModelProvider.HUGGINGFACE,
            api_key=os.getenv('HUGGINGFACE_API_KEY'),
            base_url="https://api-inference.huggingface.co",
            model_id="distilbert-base-uncased",
            max_retries=2,
            timeout_seconds=25,
            rate_limit_per_minute=100,
            priority=2,
            enabled=bool(os.getenv('HUGGINGFACE_API_KEY')),
            cost_per_request=0.001,
            monthly_quota=50000
        )
        
        # Local spaCy configurations
        spacy_sm_config = ProviderConfig(
            provider=ModelProvider.SPACY_LOCAL,
            model_id="en_core_web_sm",
            priority=3,
            enabled=True,
            cost_per_request=0.0,  # Free local processing
            timeout_seconds=5
        )
        
        spacy_md_config = ProviderConfig(
            provider=ModelProvider.SPACY_LOCAL,
            model_id="en_core_web_md",
            priority=4,
            enabled=True,
            cost_per_request=0.0,
            timeout_seconds=8
        )
        
        spacy_lg_config = ProviderConfig(
            provider=ModelProvider.SPACY_LOCAL,
            model_id="en_core_web_lg",
            priority=5,
            enabled=True,
            cost_per_request=0.0,
            timeout_seconds=12
        )
        
        # Store configurations
        self.provider_configs = {
            'openai': openai_config,
            'huggingface': hf_config,
            'spacy_sm': spacy_sm_config,
            'spacy_md': spacy_md_config,
            'spacy_lg': spacy_lg_config
        }
        
        # Initialize providers
        if openai_config.enabled:
            self.providers['openai'] = OpenAIProvider(openai_config)
        
        if hf_config.enabled:
            self.providers['huggingface'] = HuggingFaceProvider(hf_config)
        
        self.providers['spacy_sm'] = SpacyLocalProvider(spacy_sm_config)
        self.providers['spacy_md'] = SpacyLocalProvider(spacy_md_config)
        self.providers['spacy_lg'] = SpacyLocalProvider(spacy_lg_config)
        
        # Define fallback chains
        self.fallback_chains = {
            'ner': ['openai', 'huggingface', 'spacy_lg', 'spacy_md', 'spacy_sm'],
            'sentiment': ['openai', 'huggingface', 'spacy_sm'],
            'classification': ['openai', 'huggingface'],
            'pos': ['spacy_lg', 'spacy_md', 'spacy_sm'],
            'default': ['spacy_md', 'spacy_sm']
        }
    
    async def process(self, text: str, task_type: str, 
                     preferred_provider: Optional[str] = None,
                     **kwargs) -> ProcessingResult:
        """Process text with intelligent fallback"""
        self.stats['total_requests'] += 1
        start_time = time.time()
        
        # Determine provider order
        provider_order = self._get_provider_order(task_type, preferred_provider)
        
        last_error = None
        
        for provider_name in provider_order:
            if provider_name not in self.providers:
                continue
            
            provider = self.providers[provider_name]
            config = self.provider_configs[provider_name]
            
            # Check if provider is available and healthy
            if not config.is_available():
                logger.warning(f"Provider {provider_name} is not available")
                continue
            
            if hasattr(provider, 'is_healthy') and not provider.is_healthy():
                logger.warning(f"Provider {provider_name} is not healthy")
                continue
            
            try:
                logger.info(f"Attempting to process with provider: {provider_name}")
                result = await provider.process(text, task_type, **kwargs)
                
                if result.status == ProcessingStatus.SUCCESS:
                    # Update statistics
                    self.stats['successful_requests'] += 1
                    self.stats['provider_usage'][provider_name] = \
                        self.stats['provider_usage'].get(provider_name, 0) + 1
                    
                    # Update average response time
                    if provider_name not in self.stats['average_response_times']:
                        self.stats['average_response_times'][provider_name] = result.processing_time
                    else:
                        current_avg = self.stats['average_response_times'][provider_name]
                        self.stats['average_response_times'][provider_name] = \
                            (current_avg * 0.9) + (result.processing_time * 0.1)
                    
                    logger.info(f"Successfully processed with {provider_name} in {result.processing_time:.3f}s")
                    return result
                
                else:
                    # Log the failure and try next provider
                    logger.warning(f"Provider {provider_name} failed: {result.error_message}")
                    last_error = result.error_message
                    
                    # Track fallback usage
                    if provider_name != provider_order[0]:
                        self.stats['fallback_usage'][provider_name] = \
                            self.stats['fallback_usage'].get(provider_name, 0) + 1
                    
                    # Track error types
                    error_key = f"{provider_name}_{result.status.value}"
                    self.stats['error_types'][error_key] = \
                        self.stats['error_types'].get(error_key, 0) + 1
            
            except Exception as e:
                logger.error(f"Exception with provider {provider_name}: {str(e)}")
                last_error = str(e)
                continue
        
        # All providers failed
        self.stats['failed_requests'] += 1
        total_time = time.time() - start_time
        
        return ProcessingResult(
            status=ProcessingStatus.FAILED,
            error_message=f"All providers failed. Last error: {last_error}",
            processing_time=total_time,
            metadata={'attempted_providers': provider_order}
        )
    
    def _get_provider_order(self, task_type: str, preferred_provider: Optional[str] = None) -> List[str]:
        """Get ordered list of providers to try"""
        
        # Start with task-specific fallback chain
        base_order = self.fallback_chains.get(task_type, self.fallback_chains['default'])
        
        # Filter out unavailable providers
        available_providers = [
            p for p in base_order 
            if p in self.providers and self.provider_configs[p].is_available()
        ]
        
        # If preferred provider is specified and available, put it first
        if preferred_provider and preferred_provider in available_providers:
            available_providers.remove(preferred_provider)
            available_providers.insert(0, preferred_provider)
        
        # Sort by priority (lower number = higher priority)
        available_providers.sort(key=lambda p: self.provider_configs[p].priority)
        
        return available_providers
    
    def add_provider(self, name: str, provider: Union[CloudModelProvider, LocalModelProvider], 
                    config: ProviderConfig):
        """Add a custom provider"""
        self.providers[name] = provider
        self.provider_configs[name] = config
        logger.info(f"Added custom provider: {name}")
    
    def update_fallback_chain(self, task_type: str, provider_chain: List[str]):
        """Update fallback chain for a task type"""
        self.fallback_chains[task_type] = provider_chain
        logger.info(f"Updated fallback chain for {task_type}: {provider_chain}")
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        status = {}
        
        for name, config in self.provider_configs.items():
            provider = self.providers.get(name)
            
            status[name] = {
                'provider_type': config.provider.value,
                'model_id': config.model_id,
                'enabled': config.enabled,
                'available': config.is_available(),
                'healthy': provider.is_healthy() if hasattr(provider, 'is_healthy') else True,
                'priority': config.priority,
                'success_rate': config.success_rate,
                'average_response_time': config.average_response_time,
                'current_usage': config.current_usage,
                'monthly_quota': config.monthly_quota,
                'last_used': config.last_used.isoformat() if config.last_used else None
            }
        
        return status
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'total_requests': self.stats['total_requests'],
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'success_rate': self.stats['successful_requests'] / max(self.stats['total_requests'], 1),
            'provider_usage': self.stats['provider_usage'],
            'fallback_usage': self.stats['fallback_usage'],
            'average_response_times': self.stats['average_response_times'],
            'error_types': self.stats['error_types'],
            'provider_status': self.get_provider_status()
        }
    
    async def cleanup(self):
        """Cleanup all providers"""
        for provider in self.providers.values():
            if hasattr(provider, 'cleanup'):
                await provider.cleanup()

# Utility functions
async def create_integrator() -> CloudLocalModelIntegrator:
    """Create and initialize a model integrator"""
    integrator = CloudLocalModelIntegrator()
    
    # Initialize local providers
    for name, provider in integrator.providers.items():
        if isinstance(provider, LocalModelProvider):
            try:
                await provider.initialize()
            except Exception as e:
                logger.warning(f"Failed to initialize {name}: {e}")
                integrator.provider_configs[name].enabled = False
    
    return integrator

# Example usage
async def example_usage():
    """Example usage of cloud-local integration"""
    integrator = await create_integrator()
    
    try:
        # Test different task types
        test_text = "OpenAI and Hugging Face are leading AI companies developing transformer models."
        
        # Test NER
        print("Testing NER...")
        ner_result = await integrator.process(test_text, "ner")
        print(f"NER Result: {ner_result.status.value}")
        if ner_result.data:
            print(f"Entities: {ner_result.data.get('entities', [])}")
        print(f"Provider used: {ner_result.provider_used.value if ner_result.provider_used else 'None'}")
        
        # Test sentiment
        print("\nTesting Sentiment...")
        sentiment_result = await integrator.process(test_text, "sentiment")
        print(f"Sentiment Result: {sentiment_result.status.value}")
        if sentiment_result.data:
            print(f"Sentiment: {sentiment_result.data.get('sentiment', {})}")
        print(f"Provider used: {sentiment_result.provider_used.value if sentiment_result.provider_used else 'None'}")
        
        # Show statistics
        print("\nProcessing Statistics:")
        stats = integrator.get_statistics()
        print(f"Total requests: {stats['total_requests']}")
        print(f"Success rate: {stats['success_rate']:.2f}")
        print(f"Provider usage: {stats['provider_usage']}")
        
    finally:
        await integrator.cleanup()

if __name__ == "__main__":
    asyncio.run(example_usage())