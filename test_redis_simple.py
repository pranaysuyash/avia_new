"""
Simple Redis Cache Test
Tests Redis cache functionality without complex dependencies
"""

import redis
import json
import pickle
import os
from datetime import datetime
from typing import Any, Optional


class SimpleRedisCache:
    """Simple Redis cache for testing"""
    
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=False,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            self.connected = True
            print(f"✅ Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            self.connected = False
            self.client = None
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value"""
        try:
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value"""
        if data is None:
            return None
        
        try:
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return pickle.loads(data)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.connected:
            return False
        
        try:
            serialized = self._serialize(value)
            return self.client.set(key, serialized, ex=ttl)
        except Exception as e:
            print(f"❌ Set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.connected:
            return None
        
        try:
            data = self.client.get(key)
            return self._deserialize(data)
        except Exception as e:
            print(f"❌ Get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.connected:
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"❌ Delete error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get Redis statistics"""
        if not self.connected:
            return {"error": "Not connected"}
        
        try:
            info = self.client.info()
            return {
                "memory_used": info.get("used_memory_human", "N/A"),
                "total_keys": self.client.dbsize(),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            return {"error": str(e)}


def test_basic_operations():
    """Test basic Redis operations"""
    print("\n🔍 Testing Basic Operations...")
    
    cache = SimpleRedisCache()
    if not cache.connected:
        return False
    
    # Test string
    key = "test:string"
    value = "Hello, Redis!"
    
    success = cache.set(key, value, ttl=60)
    if not success:
        print(f"❌ Failed to set string")
        return False
    
    retrieved = cache.get(key)
    if retrieved != value:
        print(f"❌ String mismatch: {retrieved} != {value}")
        return False
    
    print(f"✅ String test passed: {retrieved}")
    
    # Test dictionary
    key = "test:dict"
    value = {
        "timestamp": datetime.now().isoformat(),
        "number": 42,
        "list": [1, 2, 3],
        "nested": {"key": "value"}
    }
    
    success = cache.set(key, value, ttl=60)
    if not success:
        print(f"❌ Failed to set dictionary")
        return False
    
    retrieved = cache.get(key)
    if retrieved != value:
        print(f"❌ Dict mismatch: {retrieved} != {value}")
        return False
    
    print(f"✅ Dictionary test passed")
    
    # Test TTL expiration
    key = "test:ttl"
    value = "expires soon"
    
    success = cache.set(key, value, ttl=1)  # 1 second TTL
    if not success:
        print(f"❌ Failed to set TTL test")
        return False
    
    retrieved = cache.get(key)
    if retrieved != value:
        print(f"❌ TTL test immediate retrieval failed")
        return False
    
    print(f"✅ TTL test set successfully")
    
    # Test deletion
    key = "test:delete"
    value = "will be deleted"
    
    cache.set(key, value)
    retrieved = cache.get(key)
    if retrieved != value:
        print(f"❌ Delete test setup failed")
        return False
    
    deleted = cache.delete(key)
    if not deleted:
        print(f"❌ Failed to delete key")
        return False
    
    retrieved = cache.get(key)
    if retrieved is not None:
        print(f"❌ Key still exists after deletion: {retrieved}")
        return False
    
    print(f"✅ Delete test passed")
    
    # Cleanup
    cache.delete("test:string")
    cache.delete("test:dict")
    
    return True


def test_transcription_cache_simulation():
    """Simulate transcription caching"""
    print("\n📝 Testing Transcription Cache Simulation...")
    
    cache = SimpleRedisCache()
    if not cache.connected:
        return False
    
    # Simulate a transcription result
    file_hash = "abc123def456"
    cache_key = f"transcription:{file_hash}:en:whisper-1"
    
    transcription = {
        "transcript_id": "trans_12345",
        "text": "This is a test transcription of an audio file",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.5,
                "text": "This is a test",
                "confidence": 0.92
            },
            {
                "id": 1,
                "start": 2.5,
                "end": 6.0,
                "text": "transcription of an audio file",
                "confidence": 0.88
            }
        ],
        "language": "en",
        "duration": 6.0,
        "created_at": datetime.now().isoformat(),
        "file_hash": file_hash
    }
    
    # Cache the transcription
    success = cache.set(cache_key, transcription, ttl=3600)  # 1 hour
    if not success:
        print("❌ Failed to cache transcription")
        return False
    
    print("✅ Transcription cached successfully")
    
    # Retrieve the transcription
    cached = cache.get(cache_key)
    if cached != transcription:
        print("❌ Cached transcription doesn't match")
        return False
    
    print("✅ Transcription retrieved successfully")
    print(f"   Text: {cached['text'][:50]}...")
    print(f"   Duration: {cached['duration']}s")
    print(f"   Segments: {len(cached['segments'])}")
    
    # Test cache hit performance
    import time
    
    # Multiple retrievals to test performance
    start_time = time.time()
    for _ in range(10):
        cached = cache.get(cache_key)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 10
    
    print(f"✅ Average retrieval time: {avg_time*1000:.2f}ms")
    
    # Cleanup
    cache.delete(cache_key)
    
    return True


def test_performance():
    """Test cache performance"""
    print("\n⚡ Testing Performance...")
    
    cache = SimpleRedisCache()
    if not cache.connected:
        return False
    
    import time
    
    num_ops = 100
    
    # Test write performance
    start_time = time.time()
    
    for i in range(num_ops):
        key = f"perf:write:{i}"
        value = {
            "id": i,
            "data": f"performance_test_data_{i}",
            "timestamp": datetime.now().isoformat()
        }
        cache.set(key, value, ttl=300)
    
    write_time = time.time() - start_time
    write_ops_per_sec = num_ops / write_time
    
    print(f"✅ Write: {num_ops} ops in {write_time:.3f}s ({write_ops_per_sec:.1f} ops/sec)")
    
    # Test read performance
    start_time = time.time()
    read_count = 0
    
    for i in range(num_ops):
        key = f"perf:write:{i}"
        value = cache.get(key)
        if value:
            read_count += 1
    
    read_time = time.time() - start_time
    read_ops_per_sec = num_ops / read_time
    
    print(f"✅ Read: {read_count}/{num_ops} ops in {read_time:.3f}s ({read_ops_per_sec:.1f} ops/sec)")
    
    # Cleanup
    for i in range(num_ops):
        cache.delete(f"perf:write:{i}")
    
    return True


def test_statistics():
    """Test cache statistics"""
    print("\n📊 Testing Statistics...")
    
    cache = SimpleRedisCache()
    if not cache.connected:
        return False
    
    stats = cache.get_stats()
    
    if "error" in stats:
        print(f"❌ Stats error: {stats['error']}")
        return False
    
    print(f"✅ Memory used: {stats['memory_used']}")
    print(f"✅ Total keys: {stats['total_keys']:,}")
    
    if stats['keyspace_hits'] + stats['keyspace_misses'] > 0:
        hit_rate = (stats['keyspace_hits'] / 
                   (stats['keyspace_hits'] + stats['keyspace_misses']) * 100)
        print(f"✅ Hit rate: {hit_rate:.1f}%")
    else:
        print("✅ Hit rate: N/A (no requests yet)")
    
    print(f"✅ Connected clients: {stats['connected_clients']}")
    
    uptime_hours = stats['uptime_seconds'] // 3600
    uptime_minutes = (stats['uptime_seconds'] % 3600) // 60
    print(f"✅ Uptime: {uptime_hours}h {uptime_minutes}m")
    
    return True


def main():
    """Run all tests"""
    print("🚀 Starting Simple Redis Cache Tests")
    print("=" * 50)
    
    tests = [
        ("Basic Operations", test_basic_operations),
        ("Transcription Cache Simulation", test_transcription_cache_simulation),
        ("Performance", test_performance),
        ("Statistics", test_statistics)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
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
        print("🎉 All tests passed! Redis is working correctly.")
        print("\n💡 Next steps:")
        print("1. Run the full application: python run_api.py")
        print("2. Test cached transcription endpoints: /api/v1/transcription/cached/")
        print("3. Monitor cache with: streamlit run cache_metrics_ui.py")
    else:
        print("⚠️ Some tests failed. Make sure Redis is running:")
        print("  docker-compose up redis")
    
    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)