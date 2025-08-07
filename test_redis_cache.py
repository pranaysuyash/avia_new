"""
Test Redis Cache Implementation
Tests the complete Redis caching system for transcriptions
"""

import asyncio
import sys
import os
import tempfile
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from api.cache.redis_cache import redis_cache, transcription_cache
from api.config.cache_config import CacheConfig, CacheKeyGenerator
from services.transcription_service_cached import CachedTranscriptionService
from services.vad_service import VADService
from api.database import get_db


async def test_redis_connection():
    """Test Redis connection"""
    print("🔌 Testing Redis Connection...")
    
    if not redis_cache.is_connected():
        print("❌ Redis is not connected!")
        print("💡 Make sure Redis is running: docker-compose up redis")
        return False
    
    # Test basic operations
    test_key = "test:connection"
    test_value = {"timestamp": datetime.now().isoformat(), "test": True}
    
    # Set value
    success = redis_cache.set(test_key, test_value, ttl=60)
    if not success:
        print("❌ Failed to set test value")
        return False
    
    # Get value
    retrieved = redis_cache.get(test_key)
    if retrieved != test_value:
        print(f"❌ Retrieved value doesn't match: {retrieved} != {test_value}")
        return False
    
    # Delete test key
    redis_cache.delete(test_key)
    
    print("✅ Redis connection test passed")
    return True


async def test_transcription_cache():
    """Test transcription caching"""
    print("\n📝 Testing Transcription Cache...")
    
    # Test data
    file_hash = "test_file_hash_12345"
    params = {
        "language": "en",
        "model": "whisper-1",
        "temperature": 0.0
    }
    
    transcription_result = {
        "transcript_id": "test_transcript_123",
        "text": "This is a test transcription",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.5,
                "text": "This is a test",
                "confidence": 0.9
            },
            {
                "id": 1,
                "start": 2.5,
                "end": 5.0,
                "text": "transcription",
                "confidence": 0.95
            }
        ],
        "language": "en",
        "duration": 5.0,
        "created_at": datetime.now().isoformat()
    }
    
    # Test cache miss
    cached = transcription_cache.get_transcription(file_hash, params)
    if cached is not None:
        print(f"⚠️ Unexpected cache hit: {cached}")
    else:
        print("✅ Cache miss as expected")
    
    # Test cache set
    success = transcription_cache.set_transcription(file_hash, params, transcription_result)
    if not success:
        print("❌ Failed to cache transcription")
        return False
    print("✅ Transcription cached successfully")
    
    # Test cache hit
    cached = transcription_cache.get_transcription(file_hash, params)
    if cached != transcription_result:
        print(f"❌ Cached result doesn't match: {json.dumps(cached, indent=2)}")
        return False
    print("✅ Cache hit successful")
    
    # Test cache invalidation
    invalidated = transcription_cache.invalidate_transcription(file_hash)
    print(f"✅ Invalidated {invalidated} cache entries")
    
    # Verify invalidation
    cached = transcription_cache.get_transcription(file_hash, params)
    if cached is not None:
        print(f"❌ Cache not invalidated: {cached}")
        return False
    print("✅ Cache invalidation successful")
    
    return True


async def test_vad_service():
    """Test Voice Activity Detection service"""
    print("\n🎤 Testing VAD Service...")
    
    # Create a test audio file (using a simple sine wave)
    import numpy as np
    import wave
    
    # Generate test audio: 3 seconds at 16kHz
    sample_rate = 16000
    duration = 3.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create audio with speech-like patterns
    # First second: silence, second second: tone, third second: silence
    audio_data = np.zeros_like(t)
    speech_start = int(sample_rate * 1.0)  # Start at 1 second
    speech_end = int(sample_rate * 2.0)    # End at 2 seconds
    audio_data[speech_start:speech_end] = 0.3 * np.sin(2 * np.pi * 440 * t[speech_start:speech_end])
    
    # Convert to 16-bit PCM
    audio_int16 = (audio_data * 32767).astype(np.int16)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        test_audio_path = temp_file.name
    
    try:
        # Test VAD
        vad_service = VADService()
        segments = vad_service.detect_speech_segments(test_audio_path)
        
        print(f"✅ VAD detected {len(segments)} speech segments:")
        for i, segment in enumerate(segments):
            print(f"   Segment {i+1}: {segment['start']:.2f}s - {segment['end']:.2f}s")
        
        # Test speech ratio
        ratio = vad_service.get_speech_ratio(test_audio_path)
        print(f"✅ Speech ratio: {ratio:.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ VAD test failed: {e}")
        return False
        
    finally:
        # Clean up temp file
        if os.path.exists(test_audio_path):
            os.unlink(test_audio_path)


async def test_cache_config():
    """Test cache configuration"""
    print("\n⚙️ Testing Cache Configuration...")
    
    # Test configuration values
    config_tests = [
        ("Redis URL", CacheConfig.get_redis_url()),
        ("Default TTL", CacheConfig.DEFAULT_TTL),
        ("Transcription TTL", CacheConfig.TRANSCRIPTION_TTL),
        ("Max Cache Size", CacheConfig.MAX_CACHE_SIZE_MB),
    ]
    
    for name, value in config_tests:
        print(f"✅ {name}: {value}")
    
    # Test key generators
    trans_key = CacheKeyGenerator.transcription_key("hash123", "params456")
    user_key = CacheKeyGenerator.user_list_key("user123", "transcripts", 0)
    search_key = CacheKeyGenerator.search_key("test query", {"filter": "value"})
    stats_key = CacheKeyGenerator.stats_key("usage", "day")
    
    print(f"✅ Transcription key: {trans_key}")
    print(f"✅ User list key: {user_key}")
    print(f"✅ Search key: {search_key}")
    print(f"✅ Stats key: {stats_key}")
    
    # Test cache size limits
    should_cache_small = CacheConfig.should_cache(1.0, "transcription")  # 1MB
    should_cache_large = CacheConfig.should_cache(100.0, "transcription")  # 100MB
    
    print(f"✅ Should cache 1MB: {should_cache_small}")
    print(f"✅ Should cache 100MB: {should_cache_large}")
    
    return True


async def test_cache_performance():
    """Test cache performance with multiple operations"""
    print("\n⚡ Testing Cache Performance...")
    
    # Test multiple operations
    num_operations = 100
    start_time = asyncio.get_event_loop().time()
    
    # Set operations
    for i in range(num_operations):
        key = f"perf:test:{i}"
        value = {"id": i, "data": f"test_data_{i}", "timestamp": datetime.now().isoformat()}
        redis_cache.set(key, value, ttl=300)
    
    set_time = asyncio.get_event_loop().time() - start_time
    print(f"✅ Set {num_operations} keys in {set_time:.3f}s ({num_operations/set_time:.1f} ops/sec)")
    
    # Get operations
    start_time = asyncio.get_event_loop().time()
    retrieved_count = 0
    
    for i in range(num_operations):
        key = f"perf:test:{i}"
        value = redis_cache.get(key)
        if value:
            retrieved_count += 1
    
    get_time = asyncio.get_event_loop().time() - start_time
    print(f"✅ Retrieved {retrieved_count}/{num_operations} keys in {get_time:.3f}s ({num_operations/get_time:.1f} ops/sec)")
    
    # Bulk operations
    start_time = asyncio.get_event_loop().time()
    keys = [f"perf:test:{i}" for i in range(num_operations)]
    bulk_values = redis_cache.mget(keys)
    bulk_time = asyncio.get_event_loop().time() - start_time
    
    bulk_retrieved = sum(1 for v in bulk_values if v is not None)
    print(f"✅ Bulk retrieved {bulk_retrieved} keys in {bulk_time:.3f}s ({num_operations/bulk_time:.1f} ops/sec)")
    
    # Cleanup
    redis_cache.client.delete(*keys)
    print(f"✅ Cleaned up {num_operations} test keys")
    
    return True


async def test_cache_stats():
    """Test cache statistics and monitoring"""
    print("\n📊 Testing Cache Statistics...")
    
    try:
        if not redis_cache.is_connected():
            print("❌ Redis not connected, skipping stats test")
            return False
        
        info = redis_cache.client.info()
        
        stats = {
            "used_memory_human": info.get("used_memory_human", "N/A"),
            "total_keys": redis_cache.client.dbsize(),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "connected_clients": info.get("connected_clients", 0),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0)
        }
        
        hit_rate = (stats["keyspace_hits"] / 
                   (stats["keyspace_hits"] + stats["keyspace_misses"]) * 100 
                   if (stats["keyspace_hits"] + stats["keyspace_misses"]) > 0 else 0)
        
        print(f"✅ Memory used: {stats['used_memory_human']}")
        print(f"✅ Total keys: {stats['total_keys']:,}")
        print(f"✅ Hit rate: {hit_rate:.1f}%")
        print(f"✅ Connected clients: {stats['connected_clients']}")
        print(f"✅ Uptime: {stats['uptime_in_seconds']//3600}h {(stats['uptime_in_seconds']%3600)//60}m")
        
        return True
        
    except Exception as e:
        print(f"❌ Stats test failed: {e}")
        return False


async def main():
    """Run all cache tests"""
    print("🚀 Starting Redis Cache Test Suite")
    print("=" * 50)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Transcription Cache", test_transcription_cache),
        ("VAD Service", test_vad_service),
        ("Cache Configuration", test_cache_config),
        ("Cache Performance", test_cache_performance),
        ("Cache Statistics", test_cache_stats)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Redis caching is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)