#!/usr/bin/env python3
"""
Real-time Translation System for Transcripts
Provides multi-language translation with caching and streaming support
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
import hashlib
from enum import Enum

import redis
from googletrans import Translator
import openai
from deep_translator import GoogleTranslator, MicrosoftTranslator
import langdetect
from functools import lru_cache
import aiohttp
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationProvider(Enum):
    """Available translation providers"""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    OPENAI = "openai"
    DEEPL = "deepl"
    AWS = "aws"

@dataclass
class TranslationRequest:
    """Translation request model"""
    text: str
    source_language: str
    target_language: str
    provider: TranslationProvider = TranslationProvider.GOOGLE
    context: Optional[str] = None
    preserve_formatting: bool = True
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TranslationResult:
    """Translation result model"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    provider: str
    confidence: float
    processing_time: float
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TranscriptSegment:
    """Transcript segment for translation"""
    text: str
    start_time: float
    end_time: float
    speaker: Optional[str] = None
    confidence: float = 1.0

class TranslationCache:
    """Advanced caching system for translations"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_cache = {}
        self.cache_ttl = 86400  # 24 hours
        
    def _generate_key(self, text: str, source: str, target: str, provider: str) -> str:
        """Generate cache key for translation"""
        content = f"{text}:{source}:{target}:{provider}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get(self, text: str, source: str, target: str, provider: str) -> Optional[str]:
        """Get cached translation"""
        key = self._generate_key(text, source, target, provider)
        
        # Check local cache first
        if key in self.local_cache:
            return self.local_cache[key]
        
        # Check Redis if available
        if self.redis_client:
            try:
                cached = self.redis_client.get(f"translation:{key}")
                if cached:
                    translated = cached.decode('utf-8')
                    self.local_cache[key] = translated
                    return translated
            except Exception as e:
                logger.error(f"Redis cache error: {e}")
        
        return None
    
    async def set(self, text: str, source: str, target: str, provider: str, translation: str):
        """Cache translation"""
        key = self._generate_key(text, source, target, provider)
        
        # Update local cache
        self.local_cache[key] = translation
        
        # Update Redis if available
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"translation:{key}",
                    self.cache_ttl,
                    translation
                )
            except Exception as e:
                logger.error(f"Redis cache error: {e}")

class RealtimeTranslationSystem:
    """Main real-time translation system"""
    
    def __init__(self, redis_url: Optional[str] = None):
        # Initialize providers
        self.google_translator = Translator()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Initialize cache
        redis_client = None
        if redis_url:
            try:
                redis_client = redis.from_url(redis_url)
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
        
        self.cache = TranslationCache(redis_client)
        
        # Supported languages
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'pl': 'Polish',
            'tr': 'Turkish',
            'he': 'Hebrew',
            'id': 'Indonesian',
            'vi': 'Vietnamese',
            'th': 'Thai'
        }
        
        # Translation quality thresholds
        self.quality_thresholds = {
            'min_confidence': 0.7,
            'max_segment_length': 500,
            'batch_size': 10
        }
    
    async def detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            detected = langdetect.detect(text)
            return detected
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return 'en'
    
    async def translate_text(
        self,
        request: TranslationRequest
    ) -> TranslationResult:
        """Translate single text"""
        start_time = datetime.now()
        
        # Check cache first
        cached = await self.cache.get(
            request.text,
            request.source_language,
            request.target_language,
            request.provider.value
        )
        
        if cached:
            processing_time = (datetime.now() - start_time).total_seconds()
            return TranslationResult(
                original_text=request.text,
                translated_text=cached,
                source_language=request.source_language,
                target_language=request.target_language,
                provider=request.provider.value,
                confidence=1.0,
                processing_time=processing_time,
                cached=True
            )
        
        # Perform translation
        translated = await self._translate_with_provider(request)
        
        # Cache result
        await self.cache.set(
            request.text,
            request.source_language,
            request.target_language,
            request.provider.value,
            translated
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TranslationResult(
            original_text=request.text,
            translated_text=translated,
            source_language=request.source_language,
            target_language=request.target_language,
            provider=request.provider.value,
            confidence=0.95,
            processing_time=processing_time,
            cached=False
        )
    
    async def _translate_with_provider(self, request: TranslationRequest) -> str:
        """Translate using specified provider"""
        
        if request.provider == TranslationProvider.GOOGLE:
            return await self._translate_google(request)
        elif request.provider == TranslationProvider.MICROSOFT:
            return await self._translate_microsoft(request)
        elif request.provider == TranslationProvider.OPENAI:
            return await self._translate_openai(request)
        else:
            # Fallback to Google
            return await self._translate_google(request)
    
    async def _translate_google(self, request: TranslationRequest) -> str:
        """Translate using Google Translate"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                lambda: self.google_translator.translate(
                    request.text,
                    src=request.source_language,
                    dest=request.target_language
                ).text
            )
            return result
        except Exception as e:
            logger.error(f"Google translation error: {e}")
            return request.text
    
    async def _translate_microsoft(self, request: TranslationRequest) -> str:
        """Translate using Microsoft Translator"""
        try:
            translator = MicrosoftTranslator(
                source=request.source_language,
                target=request.target_language
            )
            return translator.translate(request.text)
        except Exception as e:
            logger.error(f"Microsoft translation error: {e}")
            return request.text
    
    async def _translate_openai(self, request: TranslationRequest) -> str:
        """Translate using OpenAI GPT"""
        try:
            prompt = f"Translate the following text from {request.source_language} to {request.target_language}. Preserve the original formatting and tone:\n\n{request.text}"
            
            if request.context:
                prompt = f"Context: {request.context}\n\n{prompt}"
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=len(request.text) * 2
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI translation error: {e}")
            return request.text
    
    async def translate_transcript(
        self,
        segments: List[TranscriptSegment],
        target_language: str,
        source_language: Optional[str] = None,
        provider: TranslationProvider = TranslationProvider.GOOGLE
    ) -> List[TranscriptSegment]:
        """Translate entire transcript"""
        
        # Auto-detect source language if not provided
        if not source_language and segments:
            sample_text = " ".join([s.text for s in segments[:5]])
            source_language = await self.detect_language(sample_text)
        
        translated_segments = []
        
        # Process in batches for efficiency
        batch_size = self.quality_thresholds['batch_size']
        for i in range(0, len(segments), batch_size):
            batch = segments[i:i + batch_size]
            
            # Translate batch concurrently
            tasks = []
            for segment in batch:
                request = TranslationRequest(
                    text=segment.text,
                    source_language=source_language,
                    target_language=target_language,
                    provider=provider
                )
                tasks.append(self.translate_text(request))
            
            results = await asyncio.gather(*tasks)
            
            # Create translated segments
            for segment, result in zip(batch, results):
                translated_segment = TranscriptSegment(
                    text=result.translated_text,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    speaker=segment.speaker,
                    confidence=segment.confidence * result.confidence
                )
                translated_segments.append(translated_segment)
        
        return translated_segments
    
    async def stream_translation(
        self,
        text_stream: AsyncGenerator[str, None],
        target_language: str,
        source_language: Optional[str] = None,
        provider: TranslationProvider = TranslationProvider.GOOGLE
    ) -> AsyncGenerator[str, None]:
        """Stream translation for real-time text"""
        
        buffer = ""
        sentence_endings = {'.', '!', '?', '。', '！', '？'}
        
        async for chunk in text_stream:
            buffer += chunk
            
            # Check for complete sentences
            for ending in sentence_endings:
                if ending in buffer:
                    sentences = buffer.split(ending)
                    
                    # Translate complete sentences
                    for sentence in sentences[:-1]:
                        if sentence.strip():
                            request = TranslationRequest(
                                text=sentence.strip(),
                                source_language=source_language or 'auto',
                                target_language=target_language,
                                provider=provider
                            )
                            result = await self.translate_text(request)
                            yield result.translated_text + ending + " "
                    
                    # Keep incomplete sentence in buffer
                    buffer = sentences[-1]
        
        # Translate remaining buffer
        if buffer.strip():
            request = TranslationRequest(
                text=buffer.strip(),
                source_language=source_language or 'auto',
                target_language=target_language,
                provider=provider
            )
            result = await self.translate_text(request)
            yield result.translated_text
    
    async def batch_translate(
        self,
        texts: List[str],
        target_languages: List[str],
        source_language: Optional[str] = None,
        provider: TranslationProvider = TranslationProvider.GOOGLE
    ) -> Dict[str, List[str]]:
        """Batch translate to multiple languages"""
        
        results = {}
        
        for target_lang in target_languages:
            translations = []
            
            # Create translation tasks
            tasks = []
            for text in texts:
                request = TranslationRequest(
                    text=text,
                    source_language=source_language or 'auto',
                    target_language=target_lang,
                    provider=provider
                )
                tasks.append(self.translate_text(request))
            
            # Execute translations concurrently
            lang_results = await asyncio.gather(*tasks)
            
            for result in lang_results:
                translations.append(result.translated_text)
            
            results[target_lang] = translations
        
        return results
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return self.supported_languages
    
    async def translate_with_context(
        self,
        text: str,
        context: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> TranslationResult:
        """Translate with additional context for better accuracy"""
        
        request = TranslationRequest(
            text=text,
            source_language=source_language or 'auto',
            target_language=target_language,
            provider=TranslationProvider.OPENAI,  # Use OpenAI for context-aware translation
            context=context
        )
        
        return await self.translate_text(request)
    
    async def translate_subtitles(
        self,
        srt_content: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """Translate SRT subtitle file content"""
        
        lines = srt_content.strip().split('\n')
        translated_lines = []
        
        i = 0
        while i < len(lines):
            # Copy subtitle number
            if lines[i].strip().isdigit():
                translated_lines.append(lines[i])
                i += 1
                
                # Copy timestamp
                if i < len(lines) and '-->' in lines[i]:
                    translated_lines.append(lines[i])
                    i += 1
                    
                    # Translate subtitle text
                    subtitle_text = []
                    while i < len(lines) and lines[i].strip() and not lines[i].strip().isdigit():
                        subtitle_text.append(lines[i])
                        i += 1
                    
                    if subtitle_text:
                        text_to_translate = '\n'.join(subtitle_text)
                        request = TranslationRequest(
                            text=text_to_translate,
                            source_language=source_language or 'auto',
                            target_language=target_language,
                            provider=TranslationProvider.GOOGLE,
                            preserve_formatting=True
                        )
                        result = await self.translate_text(request)
                        translated_lines.append(result.translated_text)
                    
                    # Add empty line between subtitles
                    if i < len(lines):
                        translated_lines.append('')
            else:
                i += 1
        
        return '\n'.join(translated_lines)


# Example usage
async def main():
    """Example usage of translation system"""
    
    # Initialize system
    translator = RealtimeTranslationSystem()
    
    # Example 1: Simple translation
    request = TranslationRequest(
        text="Hello, how are you today?",
        source_language="en",
        target_language="es"
    )
    result = await translator.translate_text(request)
    print(f"Translated: {result.translated_text}")
    
    # Example 2: Transcript translation
    segments = [
        TranscriptSegment("Hello everyone", 0.0, 2.0, "Speaker1"),
        TranscriptSegment("Welcome to the meeting", 2.0, 4.0, "Speaker1"),
        TranscriptSegment("Thank you for joining", 4.0, 6.0, "Speaker2")
    ]
    
    translated = await translator.translate_transcript(
        segments, 
        target_language="fr",
        source_language="en"
    )
    
    for segment in translated:
        print(f"[{segment.speaker}] {segment.text}")
    
    # Example 3: Batch translation
    texts = ["Hello", "Good morning", "Thank you"]
    languages = ["es", "fr", "de"]
    
    batch_results = await translator.batch_translate(
        texts,
        languages,
        source_language="en"
    )
    
    for lang, translations in batch_results.items():
        print(f"\n{lang}: {translations}")

if __name__ == "__main__":
    asyncio.run(main())