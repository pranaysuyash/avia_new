#!/usr/bin/env python3
"""
Integration tests for Real-time Translation System
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from realtime_translation_system import (
    RealtimeTranslationSystem,
    TranslationRequest,
    TranslationProvider,
    TranscriptSegment,
    TranslationCache
)

# Test fixtures
@pytest.fixture
def translation_system():
    """Create translation system instance"""
    return RealtimeTranslationSystem()

@pytest.fixture
def sample_segments():
    """Create sample transcript segments"""
    return [
        TranscriptSegment("Hello everyone", 0.0, 2.0, "Speaker1"),
        TranscriptSegment("Welcome to the meeting", 2.0, 4.0, "Speaker1"),
        TranscriptSegment("Thank you for joining", 4.0, 6.0, "Speaker2"),
        TranscriptSegment("Let's begin the presentation", 6.0, 8.0, "Speaker2")
    ]

@pytest.fixture
def sample_request():
    """Create sample translation request"""
    return TranslationRequest(
        text="Hello, how are you?",
        source_language="en",
        target_language="es",
        provider=TranslationProvider.GOOGLE
    )

# Cache tests
@pytest.mark.asyncio
async def test_cache_initialization():
    """Test cache initialization"""
    cache = TranslationCache()
    assert cache.local_cache == {}
    assert cache.cache_ttl == 86400

@pytest.mark.asyncio
async def test_cache_key_generation():
    """Test cache key generation"""
    cache = TranslationCache()
    key = cache._generate_key("Hello", "en", "es", "google")
    assert isinstance(key, str)
    assert len(key) == 32  # MD5 hash length

@pytest.mark.asyncio
async def test_cache_set_and_get():
    """Test cache set and get operations"""
    cache = TranslationCache()
    
    # Set value
    await cache.set("Hello", "en", "es", "google", "Hola")
    
    # Get value
    result = await cache.get("Hello", "en", "es", "google")
    assert result == "Hola"
    
    # Get non-existent value
    result = await cache.get("Goodbye", "en", "es", "google")
    assert result is None

# Translation tests
@pytest.mark.asyncio
async def test_language_detection(translation_system):
    """Test language detection"""
    # English
    lang = await translation_system.detect_language("Hello world")
    assert lang == "en"
    
    # Spanish
    lang = await translation_system.detect_language("Hola mundo")
    assert lang == "es"
    
    # French
    lang = await translation_system.detect_language("Bonjour le monde")
    assert lang == "fr"

@pytest.mark.asyncio
async def test_simple_translation(translation_system, sample_request):
    """Test simple text translation"""
    with patch.object(translation_system, '_translate_google', 
                     return_value="Hola, ¿cómo estás?"):
        result = await translation_system.translate_text(sample_request)
        
        assert result.original_text == "Hello, how are you?"
        assert result.translated_text == "Hola, ¿cómo estás?"
        assert result.source_language == "en"
        assert result.target_language == "es"
        assert result.provider == "google"
        assert result.confidence > 0

@pytest.mark.asyncio
async def test_transcript_translation(translation_system, sample_segments):
    """Test transcript translation"""
    with patch.object(translation_system, '_translate_google', 
                     side_effect=["Hola a todos", "Bienvenidos a la reunión", 
                                 "Gracias por unirse", "Comencemos la presentación"]):
        
        translated = await translation_system.translate_transcript(
            segments=sample_segments,
            target_language="es",
            source_language="en"
        )
        
        assert len(translated) == len(sample_segments)
        assert translated[0].text == "Hola a todos"
        assert translated[1].text == "Bienvenidos a la reunión"
        assert translated[0].speaker == "Speaker1"
        assert translated[2].speaker == "Speaker2"
        assert translated[0].start_time == 0.0
        assert translated[0].end_time == 2.0

@pytest.mark.asyncio
async def test_batch_translation(translation_system):
    """Test batch translation to multiple languages"""
    texts = ["Hello", "Goodbye", "Thank you"]
    target_languages = ["es", "fr", "de"]
    
    with patch.object(translation_system, '_translate_google',
                     side_effect=["Hola", "Adiós", "Gracias",
                                 "Bonjour", "Au revoir", "Merci",
                                 "Hallo", "Auf Wiedersehen", "Danke"]):
        
        results = await translation_system.batch_translate(
            texts=texts,
            target_languages=target_languages,
            source_language="en"
        )
        
        assert "es" in results
        assert "fr" in results
        assert "de" in results
        assert results["es"] == ["Hola", "Adiós", "Gracias"]
        assert results["fr"] == ["Bonjour", "Au revoir", "Merci"]
        assert results["de"] == ["Hallo", "Auf Wiedersehen", "Danke"]

@pytest.mark.asyncio
async def test_streaming_translation(translation_system):
    """Test streaming translation"""
    async def text_generator():
        yield "Hello. "
        yield "How are you? "
        yield "Nice to meet you."
    
    with patch.object(translation_system, '_translate_google',
                     side_effect=["Hola", "¿Cómo estás?", "Encantado de conocerte"]):
        
        results = []
        async for translated in translation_system.stream_translation(
            text_generator(),
            target_language="es",
            source_language="en"
        ):
            results.append(translated)
        
        assert len(results) > 0
        assert "Hola" in results[0]

@pytest.mark.asyncio
async def test_subtitle_translation(translation_system):
    """Test SRT subtitle translation"""
    srt_content = """1
00:00:00,000 --> 00:00:02,000
Hello everyone

2
00:00:02,000 --> 00:00:04,000
Welcome to the meeting
"""
    
    with patch.object(translation_system, '_translate_google',
                     side_effect=["Hola a todos", "Bienvenidos a la reunión"]):
        
        translated_srt = await translation_system.translate_subtitles(
            srt_content=srt_content,
            target_language="es",
            source_language="en"
        )
        
        assert "Hola a todos" in translated_srt
        assert "Bienvenidos a la reunión" in translated_srt
        assert "00:00:00,000 --> 00:00:02,000" in translated_srt

@pytest.mark.asyncio
async def test_context_aware_translation(translation_system):
    """Test translation with context"""
    with patch.object(translation_system, '_translate_openai',
                     return_value="Configuración actualizada"):
        
        result = await translation_system.translate_with_context(
            text="Settings updated",
            context="User interface notification message",
            target_language="es",
            source_language="en"
        )
        
        assert result.translated_text == "Configuración actualizada"
        assert result.provider == "openai"

@pytest.mark.asyncio
async def test_caching_behavior(translation_system):
    """Test caching behavior"""
    request = TranslationRequest(
        text="Test caching",
        source_language="en",
        target_language="es",
        provider=TranslationProvider.GOOGLE
    )
    
    with patch.object(translation_system, '_translate_google',
                     return_value="Prueba de caché") as mock_translate:
        
        # First call - should translate
        result1 = await translation_system.translate_text(request)
        assert result1.cached == False
        assert mock_translate.call_count == 1
        
        # Second call - should use cache
        result2 = await translation_system.translate_text(request)
        assert result2.cached == True
        assert mock_translate.call_count == 1  # Not called again
        assert result1.translated_text == result2.translated_text

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling"""
    system = RealtimeTranslationSystem()
    
    # Test with empty text
    request = TranslationRequest(
        text="",
        source_language="en",
        target_language="es"
    )
    
    result = await system.translate_text(request)
    assert result.translated_text == ""
    
    # Test with invalid language code
    with patch.object(system, '_translate_google',
                     side_effect=Exception("Invalid language")):
        
        request = TranslationRequest(
            text="Hello",
            source_language="invalid",
            target_language="es"
        )
        
        result = await system.translate_text(request)
        assert result.translated_text == "Hello"  # Returns original on error

@pytest.mark.asyncio
async def test_provider_selection(translation_system):
    """Test different translation providers"""
    providers = [
        TranslationProvider.GOOGLE,
        TranslationProvider.MICROSOFT,
        TranslationProvider.OPENAI
    ]
    
    for provider in providers:
        request = TranslationRequest(
            text="Test",
            source_language="en",
            target_language="es",
            provider=provider
        )
        
        method_name = f'_translate_{provider.value}'
        with patch.object(translation_system, method_name,
                         return_value="Prueba"):
            
            result = await translation_system.translate_text(request)
            assert result.provider == provider.value

@pytest.mark.asyncio
async def test_supported_languages(translation_system):
    """Test supported languages list"""
    languages = translation_system.get_supported_languages()
    
    assert isinstance(languages, dict)
    assert "en" in languages
    assert "es" in languages
    assert "fr" in languages
    assert languages["en"] == "English"
    assert languages["es"] == "Spanish"

# Performance tests
@pytest.mark.asyncio
async def test_concurrent_translations(translation_system):
    """Test concurrent translation requests"""
    requests = []
    for i in range(10):
        requests.append(TranslationRequest(
            text=f"Test {i}",
            source_language="en",
            target_language="es"
        ))
    
    with patch.object(translation_system, '_translate_google',
                     side_effect=[f"Prueba {i}" for i in range(10)]):
        
        tasks = [translation_system.translate_text(req) for req in requests]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        for i, result in enumerate(results):
            assert result.translated_text == f"Prueba {i}"

@pytest.mark.asyncio
async def test_large_text_handling(translation_system):
    """Test handling of large text"""
    # Create large text (>500 chars)
    large_text = " ".join(["This is a sentence." for _ in range(50)])
    
    request = TranslationRequest(
        text=large_text,
        source_language="en",
        target_language="es"
    )
    
    with patch.object(translation_system, '_translate_google',
                     return_value="Texto traducido largo"):
        
        result = await translation_system.translate_text(request)
        assert result.translated_text == "Texto traducido largo"

# Integration with Redis tests
@pytest.mark.asyncio
async def test_redis_cache_integration():
    """Test Redis cache integration"""
    with patch('redis.from_url') as mock_redis:
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.get.return_value = None
        mock_client.setex.return_value = True
        
        system = RealtimeTranslationSystem(redis_url="redis://localhost:6379")
        cache = system.cache
        
        # Test set
        await cache.set("test", "en", "es", "google", "prueba")
        mock_client.setex.assert_called_once()
        
        # Test get
        mock_client.get.return_value = b"prueba"
        result = await cache.get("test", "en", "es", "google")
        assert result == "prueba"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])