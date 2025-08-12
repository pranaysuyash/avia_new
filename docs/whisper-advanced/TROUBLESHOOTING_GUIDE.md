# Whisper Advanced Integration - Troubleshooting Guide

## 🎯 Overview

This comprehensive troubleshooting guide helps you diagnose and resolve common issues with the Whisper Advanced Integration system. It covers API errors, performance problems, quality issues, and integration challenges with systematic solutions.

## 🚨 Quick Diagnostic Checklist

Before diving into specific issues, run through this quick checklist:

### ✅ **Basic System Check**
- [ ] API key is valid and has sufficient credits
- [ ] Internet connection is stable (minimum 2 Mbps)
- [ ] Audio file is in supported format (WAV, MP3, M4A, FLAC, OGG)
- [ ] File size is under 25MB limit
- [ ] Audio duration is under 180 minutes
- [ ] System has adequate memory (4GB+ recommended)

### ✅ **Configuration Check**
- [ ] Model size is valid (tiny, base, small, medium, large)
- [ ] Language code is supported (if specified)
- [ ] Temperature is in valid range (0.0-1.0)
- [ ] Speaker count is reasonable (2-10 for diarization)
- [ ] Custom vocabulary contains valid terms

### ✅ **Audio Quality Check**
- [ ] Audio is clear and audible
- [ ] No excessive background noise
- [ ] Speech is not heavily distorted
- [ ] Volume levels are consistent
- [ ] No significant audio clipping

## 🔧 API Connection Issues

### Problem: "Connection refused" or "Network error"

**Symptoms:**
- Cannot connect to API endpoints
- Timeout errors during requests
- Connection refused messages
- DNS resolution failures

**Diagnostic Steps:**

1. **Test Basic Connectivity**
   ```bash
   # Test API endpoint
   curl -I https://api.whisper-advanced.com/v1/whisper-advanced/health
   
   # Test DNS resolution
   nslookup api.whisper-advanced.com
   
   # Test with different DNS
   nslookup api.whisper-advanced.com 8.8.8.8
   ```

2. **Check Network Configuration**
   ```python
   import requests
   import time
   
   def diagnose_network():
       endpoints = [
           "https://api.whisper-advanced.com/v1/whisper-advanced/health",
           "https://google.com",  # Test general connectivity
           "https://httpbin.org/ip"  # Test HTTP requests
       ]
       
       for endpoint in endpoints:
           try:
               start_time = time.time()
               response = requests.get(endpoint, timeout=10)
               latency = time.time() - start_time
               print(f"✓ {endpoint}: {response.status_code} ({latency:.2f}s)")
           except Exception as e:
               print(f"✗ {endpoint}: {e}")
   
   diagnose_network()
   ```

**Solutions:**

1. **Network Issues**
   - Check internet connection stability
   - Try different network (mobile hotspot, different WiFi)
   - Restart router/modem
   - Contact ISP if persistent

2. **Firewall/Proxy Issues**
   ```python
   # Configure proxy if needed
   proxies = {
       'http': 'http://proxy.company.com:8080',
       'https': 'https://proxy.company.com:8080'
   }
   
   response = requests.post(url, proxies=proxies, ...)
   ```

3. **DNS Issues**
   - Use alternative DNS servers (8.8.8.8, 1.1.1.1)
   - Clear DNS cache: `sudo dscacheutil -flushcache` (macOS)
   - Try direct IP if DNS fails

4. **Corporate Network**
   - Whitelist `*.whisper-advanced.com` domains
   - Allow outbound HTTPS (port 443)
   - Configure proxy settings
   - Contact IT department for firewall rules

### Problem: "401 Unauthorized" errors

**Symptoms:**
- Authentication failed messages
- Invalid token errors
- Permission denied responses

**Diagnostic Steps:**

```python
def test_api_key(api_key):
    """Test API key validity."""
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(
            "https://api.whisper-advanced.com/v1/whisper-advanced/health",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✓ API key is valid")
            data = response.json()
            print(f"  Account status: {data.get('data', {}).get('status', 'unknown')}")
            return True
        elif response.status_code == 401:
            print("✗ API key is invalid or expired")
            return False
        else:
            print(f"✗ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing API key: {e}")
        return False

# Test your API key
test_api_key("your_api_key_here")
```

**Solutions:**

1. **Invalid API Key**
   - Verify API key is copied correctly (no extra spaces)
   - Check if key has expired
   - Regenerate key in dashboard
   - Ensure key has required permissions

2. **Account Issues**
   - Check account status in dashboard
   - Verify subscription is active
   - Ensure sufficient credits/quota
   - Contact support for account issues

3. **Key Management**
   ```python
   import os
   
   # Load from environment variable
   api_key = os.getenv('WHISPER_ADVANCED_API_KEY')
   if not api_key:
       raise ValueError("API key not found in environment")
   
   # Validate key format
   if not api_key.startswith('wa_'):
       print("Warning: API key format may be incorrect")
   ```

### Problem: "429 Rate Limit Exceeded"

**Symptoms:**
- Too many requests error
- Rate limit headers in response
- Temporary blocking of requests

**Diagnostic Steps:**

```python
def check_rate_limits(response):
    """Check rate limit headers."""
    headers = response.headers
    
    limit = headers.get('X-RateLimit-Limit')
    remaining = headers.get('X-RateLimit-Remaining')
    reset = headers.get('X-RateLimit-Reset')
    retry_after = headers.get('Retry-After')
    
    print(f"Rate Limit: {remaining}/{limit}")
    if reset:
        import datetime
        reset_time = datetime.datetime.fromtimestamp(int(reset))
        print(f"Resets at: {reset_time}")
    if retry_after:
        print(f"Retry after: {retry_after} seconds")
```

**Solutions:**

1. **Implement Rate Limiting**
   ```python
   import time
   import random
   
   class RateLimiter:
       def __init__(self, max_requests_per_minute=60):
           self.max_requests = max_requests_per_minute
           self.requests = []
       
       def wait_if_needed(self):
           now = time.time()
           # Remove requests older than 1 minute
           self.requests = [req_time for req_time in self.requests 
                           if now - req_time < 60]
           
           if len(self.requests) >= self.max_requests:
               sleep_time = 60 - (now - self.requests[0]) + random.uniform(1, 3)
               print(f"Rate limit reached, sleeping {sleep_time:.1f}s")
               time.sleep(sleep_time)
           
           self.requests.append(now)
   
   # Usage
   rate_limiter = RateLimiter(max_requests_per_minute=50)
   
   for file in files:
       rate_limiter.wait_if_needed()
       result = client.transcribe(file, config)
   ```

2. **Exponential Backoff**
   ```python
   import time
   import random
   
   def transcribe_with_backoff(client, audio_file, config, max_retries=3):
       for attempt in range(max_retries + 1):
           try:
               return client.transcribe(audio_file, config)
           except RateLimitException as e:
               if attempt == max_retries:
                   raise
               
               # Exponential backoff with jitter
               delay = (2 ** attempt) + random.uniform(0, 1)
               print(f"Rate limited, retrying in {delay:.1f}s...")
               time.sleep(delay)
   ```

3. **Batch Processing**
   - Use batch endpoints instead of individual requests
   - Process files during off-peak hours
   - Spread requests over time
   - Consider upgrading to higher tier

## 🎵 Audio Quality Issues

### Problem: Low Transcription Accuracy

**Symptoms:**
- Many incorrect words in transcript
- Missing or wrong punctuation
- Garbled or nonsensical text sections
- Low confidence scores (<70%)

**Diagnostic Steps:**

```python
def analyze_audio_quality(audio_file_path):
    """Analyze audio file quality."""
    import librosa
    import numpy as np
    
    # Load audio
    audio, sr = librosa.load(audio_file_path, sr=None)
    
    # Calculate metrics
    duration = len(audio) / sr
    rms_energy = np.sqrt(np.mean(audio**2))
    zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(audio))
    spectral_centroid = np.mean(librosa.feature.spectral_centroid(audio, sr=sr))
    
    # Detect clipping
    clipping_ratio = np.sum(np.abs(audio) > 0.95) / len(audio)
    
    # Signal-to-noise estimation (simplified)
    noise_floor = np.percentile(np.abs(audio), 10)
    signal_peak = np.percentile(np.abs(audio), 90)
    snr_estimate = 20 * np.log10(signal_peak / (noise_floor + 1e-10))
    
    print(f"Audio Quality Analysis:")
    print(f"  Duration: {duration:.1f}s")
    print(f"  Sample Rate: {sr}Hz")
    print(f"  RMS Energy: {rms_energy:.4f}")
    print(f"  Clipping Ratio: {clipping_ratio:.2%}")
    print(f"  Estimated SNR: {snr_estimate:.1f}dB")
    print(f"  Zero Crossing Rate: {zero_crossing_rate:.4f}")
    print(f"  Spectral Centroid: {spectral_centroid:.1f}Hz")
    
    # Quality assessment
    quality_issues = []
    if clipping_ratio > 0.01:
        quality_issues.append("Audio clipping detected")
    if snr_estimate < 10:
        quality_issues.append("Low signal-to-noise ratio")
    if rms_energy < 0.01:
        quality_issues.append("Very low audio level")
    if duration < 1:
        quality_issues.append("Audio too short")
    
    if quality_issues:
        print(f"\nQuality Issues:")
        for issue in quality_issues:
            print(f"  - {issue}")
    else:
        print(f"\n✓ Audio quality appears good")
    
    return {
        'duration': duration,
        'sample_rate': sr,
        'rms_energy': rms_energy,
        'clipping_ratio': clipping_ratio,
        'snr_estimate': snr_estimate,
        'quality_issues': quality_issues
    }

# Analyze your audio
quality_report = analyze_audio_quality("your_audio.wav")
```

**Solutions:**

1. **Audio Preprocessing**
   ```python
   import librosa
   import numpy as np
   from scipy.io import wavfile
   import noisereduce as nr
   
   def preprocess_audio(input_path, output_path):
       """Preprocess audio for better transcription."""
       # Load audio
       audio, sr = librosa.load(input_path, sr=16000)  # Whisper's preferred rate
       
       # Normalize volume
       audio = audio / np.max(np.abs(audio)) * 0.95
       
       # Reduce noise
       audio = nr.reduce_noise(y=audio, sr=sr)
       
       # Remove silence
       audio, _ = librosa.effects.trim(audio, top_db=20)
       
       # Save preprocessed audio
       wavfile.write(output_path, sr, (audio * 32767).astype(np.int16))
       print(f"Preprocessed audio saved to {output_path}")
   
   # Preprocess before transcription
   preprocess_audio("noisy_audio.wav", "clean_audio.wav")
   result = client.transcribe("clean_audio.wav", config)
   ```

2. **Configuration Optimization**
   ```python
   # High-accuracy configuration
   high_accuracy_config = {
       "model_size": "large",  # Use largest model
       "temperature": 0.0,     # Deterministic output
       "beam_size": 5,         # More thorough search
       "best_of": 5,           # Generate multiple candidates
       "compression_ratio_threshold": 2.4,
       "logprob_threshold": -1.0,
       "no_speech_threshold": 0.6,
       "enable_word_timestamps": True
   }
   
   result = client.transcribe(audio_file, high_accuracy_config)
   ```

3. **Custom Vocabulary**
   ```python
   # Add domain-specific terms
   custom_vocab = [
       "API", "Kubernetes", "PostgreSQL", "microservices",
       "John Smith", "Sarah Johnson",  # Speaker names
       "Q3", "quarterly", "revenue"    # Business terms
   ]
   
   config = {
       "model_size": "medium",
       "custom_vocabulary": custom_vocab,
       "boost_vocabulary_weight": 2.0
   }
   ```

4. **Audio Quality Improvements**
   - **Recording Environment**: Use quiet room, minimize echo
   - **Microphone**: Use quality microphone, maintain consistent distance
   - **Levels**: Avoid clipping, maintain -12dB to -6dB peaks
   - **Format**: Use uncompressed formats (WAV) when possible

### Problem: Speaker Diarization Errors

**Symptoms:**
- Speakers incorrectly identified
- Single speaker split into multiple
- Multiple speakers merged into one
- Inconsistent speaker labels

**Diagnostic Steps:**

```python
def analyze_speaker_diarization(result):
    """Analyze speaker diarization results."""
    if not result.speaker_diarization:
        print("No speaker diarization data available")
        return
    
    speakers = result.speaker_diarization.get('speakers', [])
    timeline = result.speaker_diarization.get('speaker_timeline', [])
    
    print(f"Speaker Diarization Analysis:")
    print(f"  Detected speakers: {len(speakers)}")
    
    for speaker in speakers:
        speaker_id = speaker['speaker_id']
        speaking_time = speaker['total_speaking_time']
        percentage = speaker['speaking_percentage']
        segments = speaker['segments_count']
        
        print(f"  {speaker_id}:")
        print(f"    Speaking time: {speaking_time:.1f}s ({percentage:.1f}%)")
        print(f"    Segments: {segments}")
        print(f"    Avg segment: {speaking_time/segments:.1f}s")
    
    # Analyze speaker changes
    speaker_changes = 0
    prev_speaker = None
    for segment in timeline:
        if prev_speaker and segment['speaker_id'] != prev_speaker:
            speaker_changes += 1
        prev_speaker = segment['speaker_id']
    
    print(f"  Speaker changes: {speaker_changes}")
    
    # Detect potential issues
    issues = []
    if len(speakers) > 10:
        issues.append("Too many speakers detected (possible over-segmentation)")
    
    very_short_segments = sum(1 for s in speakers if s['total_speaking_time'] < 2)
    if very_short_segments > len(speakers) * 0.3:
        issues.append("Many very short speaker segments")
    
    if speaker_changes > len(timeline) * 0.5:
        issues.append("Excessive speaker switching")
    
    if issues:
        print(f"\nPotential Issues:")
        for issue in issues:
            print(f"  - {issue}")

# Analyze diarization results
analyze_speaker_diarization(result)
```

**Solutions:**

1. **Audio Quality Improvements**
   ```python
   # Optimal recording setup for diarization
   diarization_config = {
       "model_size": "medium",
       "enable_diarization": True,
       "max_speakers": 4,  # Set realistic limit
       "enable_vad": True,  # Helps with speaker boundaries
       "vad_threshold": 0.5
   }
   
   # For stereo recordings with speakers on different channels
   stereo_config = {
       "model_size": "medium",
       "enable_diarization": True,
       "max_speakers": 2,
       "speaker_clustering_threshold": 0.8  # Higher threshold for stereo
   }
   ```

2. **Recording Best Practices**
   - Use separate microphones for each speaker when possible
   - Maintain consistent distance from microphones
   - Minimize overlapping speech
   - Record in stereo with speakers on different channels
   - Use directional microphones to reduce crosstalk

3. **Configuration Tuning**
   ```python
   def tune_diarization_config(audio_duration, expected_speakers):
       """Generate optimized diarization config."""
       config = {
           "enable_diarization": True,
           "max_speakers": min(expected_speakers + 1, 8),
           "enable_vad": True
       }
       
       # Adjust based on audio length
       if audio_duration < 60:  # Short audio
           config["speaker_clustering_threshold"] = 0.7
           config["min_speaker_duration"] = 1.0
       elif audio_duration > 1800:  # Long audio (30+ minutes)
           config["speaker_clustering_threshold"] = 0.8
           config["min_speaker_duration"] = 3.0
       else:  # Medium length
           config["speaker_clustering_threshold"] = 0.75
           config["min_speaker_duration"] = 2.0
       
       return config
   
   # Use optimized config
   config = tune_diarization_config(audio_duration=300, expected_speakers=3)
   result = client.transcribe(audio_file, config)
   ```

4. **Post-Processing Corrections**
   ```python
   def merge_short_speaker_segments(segments, min_duration=2.0):
       """Merge very short speaker segments with adjacent ones."""
       merged_segments = []
       
       for segment in segments:
           duration = segment['end'] - segment['start']
           
           if duration < min_duration and merged_segments:
               # Merge with previous segment
               prev_segment = merged_segments[-1]
               prev_segment['end'] = segment['end']
               prev_segment['text'] += ' ' + segment['text']
           else:
               merged_segments.append(segment.copy())
       
       return merged_segments
   
   # Apply post-processing
   cleaned_segments = merge_short_speaker_segments(result.segments)
   ```

## ⚡ Performance Issues

### Problem: Slow Processing Times

**Symptoms:**
- Processing takes much longer than expected
- Timeouts during transcription
- High real-time factors (>2x)
- System becomes unresponsive

**Diagnostic Steps:**

```python
import time
import psutil

def benchmark_transcription(client, audio_file, configs):
    """Benchmark different configurations."""
    results = []
    
    for config_name, config in configs.items():
        print(f"\nTesting {config_name}...")
        
        # System metrics before
        process = psutil.Process()
        cpu_before = process.cpu_percent()
        memory_before = process.memory_info().rss / 1024 / 1024
        
        start_time = time.time()
        
        try:
            result = client.transcribe(audio_file, config)
            processing_time = time.time() - start_time
            
            # System metrics after
            cpu_after = process.cpu_percent()
            memory_after = process.memory_info().rss / 1024 / 1024
            
            audio_duration = result.processing_stats.get('audio_duration', 0)
            real_time_factor = processing_time / audio_duration if audio_duration > 0 else 0
            
            benchmark_result = {
                'config': config_name,
                'processing_time': processing_time,
                'real_time_factor': real_time_factor,
                'cpu_usage': cpu_after - cpu_before,
                'memory_usage': memory_after - memory_before,
                'accuracy_estimate': result.processing_stats.get('average_confidence', 0),
                'success': True
            }
            
            print(f"  ✓ Completed in {processing_time:.1f}s ({real_time_factor:.2f}x)")
            
        except Exception as e:
            benchmark_result = {
                'config': config_name,
                'error': str(e),
                'success': False
            }
            print(f"  ✗ Failed: {e}")
        
        results.append(benchmark_result)
    
    return results

# Test different configurations
configs = {
    'fast': {'model_size': 'tiny', 'beam_size': 1},
    'balanced': {'model_size': 'base', 'beam_size': 1},
    'accurate': {'model_size': 'medium', 'beam_size': 3},
    'max_accuracy': {'model_size': 'large', 'beam_size': 5, 'best_of': 5}
}

benchmark_results = benchmark_transcription(client, "test_audio.wav", configs)
```

**Solutions:**

1. **Model Optimization**
   ```python
   # Speed-optimized configuration
   fast_config = {
       "model_size": "base",        # Smaller model
       "beam_size": 1,              # Greedy decoding
       "enable_word_timestamps": False,  # Skip if not needed
       "enable_diarization": False, # Skip if not needed
       "temperature": 0.0           # Deterministic
   }
   
   # For real-time applications
   realtime_config = {
       "model_size": "tiny",
       "beam_size": 1,
       "enable_word_timestamps": False,
       "enable_diarization": False,
       "enable_vad": True,  # Skip silence
       "vad_threshold": 0.6
   }
   ```

2. **Audio Preprocessing**
   ```python
   def optimize_audio_for_speed(input_path, output_path):
       """Optimize audio file for faster processing."""
       import librosa
       from scipy.io import wavfile
       
       # Load and resample to 16kHz (Whisper's native rate)
       audio, sr = librosa.load(input_path, sr=16000)
       
       # Remove silence to reduce processing time
       audio, _ = librosa.effects.trim(audio, top_db=20)
       
       # Convert to mono if stereo
       if len(audio.shape) > 1:
           audio = librosa.to_mono(audio)
       
       # Save optimized audio
       wavfile.write(output_path, 16000, (audio * 32767).astype(np.int16))
       
       original_duration = librosa.get_duration(filename=input_path)
       new_duration = len(audio) / 16000
       
       print(f"Audio optimized: {original_duration:.1f}s -> {new_duration:.1f}s")
       return output_path
   
   # Use optimized audio
   optimized_file = optimize_audio_for_speed("long_audio.wav", "optimized_audio.wav")
   result = client.transcribe(optimized_file, fast_config)
   ```

3. **Concurrent Processing**
   ```python
   from concurrent.futures import ThreadPoolExecutor
   import time
   
   def process_file_chunk(client, audio_chunk, config):
       """Process a single audio chunk."""
       return client.transcribe(audio_chunk, config)
   
   def parallel_transcription(client, audio_files, config, max_workers=3):
       """Process multiple files in parallel."""
       results = []
       
       with ThreadPoolExecutor(max_workers=max_workers) as executor:
           futures = [
               executor.submit(process_file_chunk, client, file, config)
               for file in audio_files
           ]
           
           for future in futures:
               try:
                   result = future.result(timeout=300)  # 5 minute timeout
                   results.append(result)
               except Exception as e:
                   print(f"Processing failed: {e}")
                   results.append(None)
       
       return results
   
   # Process multiple files concurrently
   files = ["file1.wav", "file2.wav", "file3.wav"]
   results = parallel_transcription(client, files, fast_config, max_workers=2)
   ```

4. **System Optimization**
   ```python
   import gc
   import os
   
   def optimize_system_resources():
       """Optimize system for transcription processing."""
       # Force garbage collection
       gc.collect()
       
       # Set process priority (Unix/Linux)
       if hasattr(os, 'nice'):
           os.nice(-5)  # Higher priority
       
       # Increase file descriptor limits if needed
       try:
           import resource
           soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
           resource.setrlimit(resource.RLIMIT_NOFILE, (min(hard, 4096), hard))
       except:
           pass
       
       print("System optimized for transcription processing")
   
   optimize_system_resources()
   ```

### Problem: Memory Issues

**Symptoms:**
- Out of memory errors
- System becomes slow/unresponsive
- Process killed by system
- Swap usage increases significantly

**Diagnostic Steps:**

```python
import psutil
import gc

def monitor_memory_usage(func, *args, **kwargs):
    """Monitor memory usage during function execution."""
    process = psutil.Process()
    
    # Initial memory
    initial_memory = process.memory_info().rss / 1024 / 1024
    peak_memory = initial_memory
    
    print(f"Initial memory: {initial_memory:.1f}MB")
    
    try:
        # Execute function
        result = func(*args, **kwargs)
        
        # Final memory
        final_memory = process.memory_info().rss / 1024 / 1024
        print(f"Final memory: {final_memory:.1f}MB")
        print(f"Memory delta: {final_memory - initial_memory:.1f}MB")
        
        return result
        
    except MemoryError as e:
        current_memory = process.memory_info().rss / 1024 / 1024
        print(f"Memory error at {current_memory:.1f}MB: {e}")
        raise
    finally:
        # Force cleanup
        gc.collect()

# Monitor transcription memory usage
result = monitor_memory_usage(
    client.transcribe,
    "large_audio.wav",
    {"model_size": "large"}
)
```

**Solutions:**

1. **Memory-Efficient Configuration**
   ```python
   # Low-memory configuration
   low_memory_config = {
       "model_size": "base",        # Smaller model
       "enable_word_timestamps": False,  # Reduces memory
       "beam_size": 1,              # Less memory for beam search
       "best_of": 1                 # Single candidate
   }
   
   # For very large files
   minimal_config = {
       "model_size": "tiny",
       "enable_word_timestamps": False,
       "enable_diarization": False,
       "beam_size": 1
   }
   ```

2. **File Chunking**
   ```python
   import librosa
   from scipy.io import wavfile
   
   def chunk_audio_file(input_path, chunk_duration=300, overlap=30):
       """Split large audio file into smaller chunks."""
       audio, sr = librosa.load(input_path, sr=None)
       
       chunk_samples = int(chunk_duration * sr)
       overlap_samples = int(overlap * sr)
       
       chunks = []
       start = 0
       chunk_num = 0
       
       while start < len(audio):
           end = min(start + chunk_samples, len(audio))
           chunk = audio[start:end]
           
           # Save chunk
           chunk_path = f"chunk_{chunk_num:03d}.wav"
           wavfile.write(chunk_path, sr, (chunk * 32767).astype(np.int16))
           chunks.append(chunk_path)
           
           # Move to next chunk with overlap
           start = end - overlap_samples
           chunk_num += 1
       
       return chunks
   
   def transcribe_large_file(client, large_audio_path, config):
       """Transcribe large file by chunking."""
       # Split into chunks
       chunks = chunk_audio_file(large_audio_path, chunk_duration=300)
       
       all_segments = []
       time_offset = 0
       
       for chunk_path in chunks:
           try:
               result = client.transcribe(chunk_path, config)
               
               # Adjust timestamps
               for segment in result.segments:
                   segment['start'] += time_offset
                   segment['end'] += time_offset
                   all_segments.append(segment)
               
               time_offset += 270  # 300s chunk - 30s overlap
               
               # Cleanup chunk file
               os.remove(chunk_path)
               
           except Exception as e:
               print(f"Error processing {chunk_path}: {e}")
               continue
       
       # Combine results
       full_text = ' '.join(segment['text'] for segment in all_segments)
       
       return {
           'text': full_text,
           'segments': all_segments,
           'processing_method': 'chunked'
       }
   
   # Process large file
   result = transcribe_large_file(client, "very_large_audio.wav", low_memory_config)
   ```

3. **Memory Management**
   ```python
   import gc
   import weakref
   
   class MemoryManagedTranscription:
       def __init__(self, client):
           self.client = client
           self._results_cache = weakref.WeakValueDictionary()
       
       def transcribe_with_cleanup(self, audio_file, config):
           """Transcribe with automatic memory cleanup."""
           try:
               # Force garbage collection before processing
               gc.collect()
               
               # Process transcription
               result = self.client.transcribe(audio_file, config)
               
               # Store in weak reference cache
               cache_key = f"{audio_file}_{hash(str(config))}"
               self._results_cache[cache_key] = result
               
               return result
               
           finally:
               # Force cleanup after processing
               gc.collect()
       
       def clear_cache(self):
           """Clear results cache."""
           self._results_cache.clear()
           gc.collect()
   
   # Use memory-managed transcription
   managed_client = MemoryManagedTranscription(client)
   result = managed_client.transcribe_with_cleanup("audio.wav", config)
   ```

## 🌍 Language Detection Issues

### Problem: Wrong Language Detected

**Symptoms:**
- Incorrect language identification
- Low confidence scores for detection
- Mixed language content problems
- Transcription in wrong language

**Diagnostic Steps:**

```python
def analyze_language_detection(client, audio_file, sample_durations=[15, 30, 60]):
    """Test language detection with different sample durations."""
    print(f"Language Detection Analysis for {audio_file}:")
    
    for duration in sample_durations:
        try:
            result = client.detect_language(audio_file, sample_duration=duration)
            
            print(f"\nSample Duration: {duration}s")
            print(f"  Detected: {result.detected_language} ({result.confidence:.2f})")
            print(f"  Top 3 languages:")
            
            # Sort by probability
            sorted_langs = sorted(
                result.all_language_probs.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            for lang, prob in sorted_langs:
                print(f"    {lang}: {prob:.3f}")
                
        except Exception as e:
            print(f"  Error with {duration}s sample: {e}")

# Analyze language detection
analyze_language_detection(client, "multilingual_audio.wav")
```

**Solutions:**

1. **Manual Language Selection**
   ```python
   # When you know the language
   known_language_config = {
       "model_size": "medium",
       "language": "es",  # Spanish
       "task": "transcribe"
   }
   
   # For translation to English
   translation_config = {
       "model_size": "medium",
       "language": "es",
       "task": "translate"  # Translate to English
   }
   ```

2. **Improved Detection Settings**
   ```python
   def detect_language_robust(client, audio_file):
       """Robust language detection with multiple samples."""
       # Try different sample durations
       durations = [30, 60, 90]
       results = []
       
       for duration in durations:
           try:
               result = client.detect_language(audio_file, sample_duration=duration)
               results.append(result)
           except:
               continue
       
       if not results:
           return None
       
       # Aggregate results
       language_votes = {}
       for result in results:
           lang = result.detected_language
           confidence = result.confidence
           language_votes[lang] = language_votes.get(lang, 0) + confidence
       
       # Get most confident language
       best_language = max(language_votes.items(), key=lambda x: x[1])
       
       print(f"Robust detection: {best_language[0]} (score: {best_language[1]:.2f})")
       return best_language[0]
   
   # Use robust detection
   detected_lang = detect_language_robust(client, "unclear_language.wav")
   if detected_lang:
       config = {"model_size": "medium", "language": detected_lang}
   else:
       config = {"model_size": "medium"}  # Auto-detect
   ```

3. **Mixed Language Handling**
   ```python
   def handle_mixed_language_content(client, audio_file):
       """Handle content with multiple languages."""
       # First, detect primary language
       lang_result = client.detect_language(audio_file, sample_duration=60)
       
       if lang_result.confidence < 0.7:
           print("Low confidence language detection, using auto-detect")
           config = {
               "model_size": "medium",
               # No language specified - auto-detect
               "enable_word_timestamps": True
           }
       else:
           print(f"Primary language: {lang_result.detected_language}")
           config = {
               "model_size": "medium",
               "language": lang_result.detected_language,
               "enable_word_timestamps": True
           }
       
       result = client.transcribe(audio_file, config)
       
       # Analyze segments for language switches
       segments_by_confidence = []
       for segment in result.segments:
           if segment.get('confidence', 1.0) < 0.6:
               segments_by_confidence.append(segment)
       
       if segments_by_confidence:
           print(f"Found {len(segments_by_confidence)} low-confidence segments")
           print("These might be in different languages")
       
       return result
   
   # Handle mixed content
   result = handle_mixed_language_content(client, "mixed_language.wav")
   ```

## 🔧 Configuration Issues

### Problem: Invalid Configuration Parameters

**Symptoms:**
- Configuration validation errors
- Unexpected behavior with settings
- Parameters being ignored
- Default values used instead of specified ones

**Diagnostic Steps:**

```python
def validate_configuration(config):
    """Validate Whisper Advanced configuration."""
    errors = []
    warnings = []
    
    # Model size validation
    valid_models = ["tiny", "base", "small", "medium", "large"]
    if config.get("model_size") not in valid_models:
        errors.append(f"Invalid model_size. Must be one of: {valid_models}")
    
    # Temperature validation
    temp = config.get("temperature", 0.0)
    if not 0.0 <= temp <= 1.0:
        errors.append("Temperature must be between 0.0 and 1.0")
    
    # Language validation
    supported_languages = ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar", "hi", "tr", "pl", "nl"]
    lang = config.get("language")
    if lang and lang not in supported_languages:
        warnings.append(f"Language '{lang}' may not be fully supported")
    
    # Speaker diarization validation
    if config.get("enable_diarization"):
        max_speakers = config.get("max_speakers", 5)
        if max_speakers > 10:
            warnings.append("More than 10 speakers may reduce accuracy")
        if max_speakers < 2:
            errors.append("max_speakers must be at least 2 for diarization")
    
    # Beam search validation
    beam_size = config.get("beam_size", 1)
    if beam_size > 10:
        warnings.append("Large beam_size may significantly slow processing")
    
    # Custom vocabulary validation
    vocab = config.get("custom_vocabulary", [])
    if len(vocab) > 1000:
        warnings.append("Large custom vocabulary may slow processing")
    
    # Report results
    if errors:
        print("Configuration Errors:")
        for error in errors:
            print(f"  ✗ {error}")
    
    if warnings:
        print("Configuration Warnings:")
        for warning in warnings:
            print(f"  ⚠ {warning}")
    
    if not errors and not warnings:
        print("✓ Configuration is valid")
    
    return len(errors) == 0

# Validate your configuration
config = {
    "model_size": "medium",
    "temperature": 0.5,
    "enable_diarization": True,
    "max_speakers": 3,
    "custom_vocabulary": ["API", "Kubernetes"]
}

is_valid = validate_configuration(config)
```

**Solutions:**

1. **Configuration Templates**
   ```python
   class WhisperConfigTemplates:
       @staticmethod
       def meeting_transcription(num_speakers=4):
           return {
               "model_size": "medium",
               "temperature": 0.0,
               "enable_diarization": True,
               "max_speakers": num_speakers,
               "enable_vad": True,
               "enable_word_timestamps": True,
               "compression_ratio_threshold": 2.4,
               "logprob_threshold": -1.0,
               "no_speech_threshold": 0.6
           }
       
       @staticmethod
       def high_accuracy():
           return {
               "model_size": "large",
               "temperature": 0.0,
               "beam_size": 5,
               "best_of": 5,
               "enable_word_timestamps": True,
               "compression_ratio_threshold": 2.4,
               "logprob_threshold": -1.0
           }
       
       @staticmethod
       def fast_processing():
           return {
               "model_size": "base",
               "temperature": 0.0,
               "beam_size": 1,
               "enable_word_timestamps": False,
               "enable_diarization": False
           }
       
       @staticmethod
       def real_time():
           return {
               "model_size": "tiny",
               "temperature": 0.0,
               "beam_size": 1,
               "enable_word_timestamps": False,
               "enable_diarization": False,
               "enable_vad": True,
               "vad_threshold": 0.6
           }
   
   # Use templates
   config = WhisperConfigTemplates.meeting_transcription(num_speakers=3)
   result = client.transcribe("meeting.wav", config)
   ```

2. **Dynamic Configuration**
   ```python
   def create_optimal_config(audio_file_path, use_case="general"):
       """Create optimal configuration based on audio characteristics."""
       import librosa
       
       # Analyze audio
       audio, sr = librosa.load(audio_file_path, sr=None)
       duration = len(audio) / sr
       
       # Base configuration
       config = {
           "temperature": 0.0,
           "enable_word_timestamps": True
       }
       
       # Model selection based on duration and use case
       if duration < 60:  # Short audio
           config["model_size"] = "small"
       elif duration < 600:  # Medium audio (10 minutes)
           config["model_size"] = "medium"
       else:  # Long audio
           config["model_size"] = "base"  # Faster for long content
       
       # Use case specific settings
       if use_case == "meeting":
           config.update({
               "enable_diarization": True,
               "max_speakers": 6,
               "enable_vad": True
           })
       elif use_case == "interview":
           config.update({
               "enable_diarization": True,
               "max_speakers": 2,
               "beam_size": 3
           })
       elif use_case == "lecture":
           config.update({
               "enable_diarization": False,
               "beam_size": 3,
               "initial_prompt": "This is an educational lecture."
           })
       elif use_case == "podcast":
           config.update({
               "enable_diarization": True,
               "max_speakers": 4,
               "temperature": 0.1,
               "condition_on_previous_text": True
           })
       
       print(f"Generated config for {use_case} ({duration:.1f}s audio):")
       for key, value in config.items():
           print(f"  {key}: {value}")
       
       return config
   
   # Generate optimal configuration
   config = create_optimal_config("my_audio.wav", use_case="meeting")
   result = client.transcribe("my_audio.wav", config)
   ```

## 🔍 Debugging Tools

### Comprehensive Diagnostic Tool

```python
import json
import time
import requests
import librosa
import numpy as np
from pathlib import Path

class WhisperAdvancedDiagnostic:
    def __init__(self, client):
        self.client = client
    
    def run_full_diagnostic(self, audio_file, config=None):
        """Run comprehensive diagnostic on audio file and configuration."""
        print("🔍 Whisper Advanced Integration - Full Diagnostic")
        print("=" * 60)
        
        # 1. System Check
        self._check_system()
        
        # 2. API Connectivity
        self._check_api_connectivity()
        
        # 3. Audio File Analysis
        self._analyze_audio_file(audio_file)
        
        # 4. Configuration Validation
        if config:
            self._validate_config(config)
        
        # 5. Test Transcription
        self._test_transcription(audio_file, config)
        
        print("\n✅ Diagnostic complete!")
    
    def _check_system(self):
        """Check system requirements."""
        print("\n1. System Check")
        print("-" * 20)
        
        import psutil
        import platform
        
        # System info
        print(f"OS: {platform.system()} {platform.release()}")
        print(f"Python: {platform.python_version()}")
        
        # Memory
        memory = psutil.virtual_memory()
        print(f"Memory: {memory.total / 1024**3:.1f}GB total, {memory.available / 1024**3:.1f}GB available")
        
        if memory.available < 2 * 1024**3:  # Less than 2GB
            print("⚠️  Warning: Low available memory may cause issues")
        
        # Disk space
        disk = psutil.disk_usage('.')
        print(f"Disk: {disk.free / 1024**3:.1f}GB free")
        
        if disk.free < 1024**3:  # Less than 1GB
            print("⚠️  Warning: Low disk space may cause issues")
    
    def _check_api_connectivity(self):
        """Check API connectivity and authentication."""
        print("\n2. API Connectivity")
        print("-" * 20)
        
        try:
            # Test basic connectivity
            start_time = time.time()
            health = self.client.health_check()
            latency = time.time() - start_time
            
            print(f"✅ API reachable (latency: {latency:.2f}s)")
            print(f"Status: {health.get('status', 'unknown')}")
            
            # Check available models
            models = health.get('available_models', [])
            print(f"Available models: {', '.join(models)}")
            
            # Check features
            features = health.get('features', {})
            print("Available features:")
            for feature, available in features.items():
                status = "✅" if available else "❌"
                print(f"  {status} {feature}")
                
        except Exception as e:
            print(f"❌ API connectivity failed: {e}")
            print("Check your API key and internet connection")
    
    def _analyze_audio_file(self, audio_file):
        """Analyze audio file characteristics."""
        print("\n3. Audio File Analysis")
        print("-" * 20)
        
        if not Path(audio_file).exists():
            print(f"❌ Audio file not found: {audio_file}")
            return
        
        try:
            # File info
            file_size = Path(audio_file).stat().st_size / 1024 / 1024  # MB
            print(f"File: {audio_file}")
            print(f"Size: {file_size:.1f}MB")
            
            if file_size > 25:
                print("⚠️  Warning: File size exceeds 25MB limit")
            
            # Audio analysis
            audio, sr = librosa.load(audio_file, sr=None)
            duration = len(audio) / sr
            
            print(f"Duration: {duration:.1f}s")
            print(f"Sample rate: {sr}Hz")
            print(f"Channels: {1 if len(audio.shape) == 1 else audio.shape[1]}")
            
            if duration > 180 * 60:  # 3 hours
                print("⚠️  Warning: Duration exceeds 180 minute limit")
            
            # Quality metrics
            rms_energy = np.sqrt(np.mean(audio**2))
            clipping_ratio = np.sum(np.abs(audio) > 0.95) / len(audio)
            
            print(f"RMS Energy: {rms_energy:.4f}")
            print(f"Clipping: {clipping_ratio:.2%}")
            
            if rms_energy < 0.01:
                print("⚠️  Warning: Very low audio level")
            if clipping_ratio > 0.01:
                print("⚠️  Warning: Audio clipping detected")
            
        except Exception as e:
            print(f"❌ Audio analysis failed: {e}")
    
    def _validate_config(self, config):
        """Validate configuration."""
        print("\n4. Configuration Validation")
        print("-" * 20)
        
        # Use the validation function from earlier
        is_valid = validate_configuration(config)
        
        if is_valid:
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration has errors")
    
    def _test_transcription(self, audio_file, config):
        """Test transcription with the given configuration."""
        print("\n5. Test Transcription")
        print("-" * 20)
        
        if not config:
            config = {"model_size": "base"}
        
        try:
            start_time = time.time()
            result = self.client.transcribe(audio_file, config)
            processing_time = time.time() - start_time
            
            print(f"✅ Transcription successful")
            print(f"Processing time: {processing_time:.1f}s")
            print(f"Text length: {len(result.text)} characters")
            print(f"Language: {result.language}")
            
            if hasattr(result, 'processing_stats'):
                stats = result.processing_stats
                print(f"Model used: {stats.get('model_used', 'unknown')}")
                print(f"Confidence: {stats.get('average_confidence', 0):.2f}")
            
            # Show first 100 characters of transcript
            preview = result.text[:100] + "..." if len(result.text) > 100 else result.text
            print(f"Preview: {preview}")
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            print("Check audio file format and configuration")

# Usage
diagnostic = WhisperAdvancedDiagnostic(client)
diagnostic.run_full_diagnostic(
    "test_audio.wav",
    {"model_size": "medium", "enable_diarization": True}
)
```

## 📞 Getting Help

### When to Contact Support

Contact support when you encounter:
- Persistent API connectivity issues
- Unexpected billing or usage charges
- Account access problems
- Consistent transcription failures
- Performance issues not resolved by this guide

### Information to Include

When contacting support, include:

1. **Error Details**
   - Exact error messages
   - Error codes and timestamps
   - Request IDs if available

2. **Configuration**
   - Model size and parameters used
   - Audio file characteristics
   - Expected vs. actual behavior

3. **System Information**
   - Operating system and version
   - Programming language and SDK version
   - Network configuration (if relevant)

4. **Reproduction Steps**
   - Minimal code example
   - Sample audio file (if possible)
   - Steps to reproduce the issue

### Support Channels

- **Technical Support**: developers@whisper-advanced.com
- **Bug Reports**: bugs@whisper-advanced.com
- **Feature Requests**: features@whisper-advanced.com
- **Community Forum**: https://community.whisper-advanced.com
- **Documentation**: https://docs.whisper-advanced.com

### Self-Help Resources

- **Status Page**: https://status.whisper-advanced.com
- **API Documentation**: https://api-docs.whisper-advanced.com
- **Code Examples**: https://github.com/whisper-advanced/examples
- **Video Tutorials**: https://youtube.com/whisper-advanced
- **Blog**: https://blog.whisper-advanced.com

---

This troubleshooting guide covers the most common issues encountered with Whisper Advanced Integration. For issues not covered here, please consult our documentation or contact support with detailed information about your specific problem.