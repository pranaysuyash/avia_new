# Whisper Advanced Integration - Troubleshooting Guide

## 🎯 Overview

This guide helps you diagnose and resolve common issues with the Whisper Advanced Integration system. It covers API errors, performance problems, quality issues, and integration challenges.

## 🚨 Common Issues & Solutions

### API Connection Issues

#### Problem: "Connection refused" or "Network error"
**Symptoms:**
- Cannot connect to API endpoints
- Timeout errors
- Connection refused messages

**Solutions:**
1. **Check API URL**: Ensure you're using the correct base URL
   ```python
   # Correct URLs
   Production: https://api.whisper-advanced.com/v1
   Development: http://localhost:8000/api/v1
   ```

2. **Verify Network Connectivity**:
   ```bash
   # Test basic connectivity
   curl -I https://api.whisper-advanced.com/v1/whisper-advanced/health
   
   # Check DNS resolution
   nslookup api.whisper-advanced.com
   ```

3. **Check Firewall Settings**: Ensure outbound HTTPS (port 443) is allowed

4. **Proxy Configuration**: If behind a corporate proxy:
   ```python
   proxies = {
       'http': 'http://proxy.company.com:8080',
       'https': 'https://proxy.company.com:8080'
   }
   response = requests.post(url, proxies=proxies, ...)
   ```

#### Problem: "401 Unauthorized" errors
**Symptoms:**
- Authentication failed messages
- Invalid token errors

**Solutions:**
1. **Verify API Key**: Check your API key is correct and active
   ```python
   # Test API key
   headers = {"Authorization": f"Bearer {API_KEY}"}
   response = requests.get("https://api.whisper-advanced.com/v1/whisper-advanced/health", headers=headers)
   print(response.status_code)  # Should be 200
   ```

2. **Check Token Format**: Ensure proper Bearer token format
   ```python
   # Correct format
   headers = {"Authorization": f"Bearer {api_key}"}
   
   # Incorrect formats
   headers = {"Authorization": api_key}  # Missing "Bearer"
   headers = {"Authorization": f"Token {api_key}"}  # Wrong prefix
   ```

3. **Token Expiration**: Check if your API key has expired

### File Upload Issues

#### Problem: "File too large" errors
**Symptoms:**
- 413 Payload Too Large errors
- File size exceeded messages

**Solutions:**
1. **Check File Size Limits**:
   - Single file: Maximum 25MB
   - Batch processing: Maximum 250MB total

2. **Compress Audio Files**:
   ```python
   # Using pydub to compress audio
   from pydub import AudioSegment
   
   audio = AudioSegment.from_file("large_file.wav")
   audio = audio.set_frame_rate(16000)  # Reduce sample rate
   audio = audio.set_channels(1)  # Convert to mono
   audio.export("compressed_file.mp3", format="mp3", bitrate="64k")
   ```

3. **Split Large Files**:
   ```python
   def split_audio_file(file_path, chunk_duration_ms=300000):  # 5 minutes
       audio = AudioSegment.from_file(file_path)
       chunks = []
       
       for i in range(0, len(audio), chunk_duration_ms):
           chunk = audio[i:i + chunk_duration_ms]
           chunk_path = f"chunk_{i//chunk_duration_ms}.wav"
           chunk.export(chunk_path, format="wav")
           chunks.append(chunk_path)
       
       return chunks
   ```

#### Problem: "Unsupported file format" errors
**Symptoms:**
- 400 Bad Request with format error
- File type not supported messages

**Solutions:**
1. **Convert to Supported Format**:
   ```python
   from pydub import AudioSegment
   
   # Convert various formats to WAV
   audio = AudioSegment.from_file("audio.m4v")  # Video file
   audio.export("audio.wav", format="wav")
   ```

2. **Supported Formats**: Use these formats for best results:
   - WAV (recommended for quality)
   - MP3 (good for size)
   - M4A (Apple devices)
   - FLAC (lossless)

3. **Check File Headers**: Ensure files aren't corrupted:
   ```python
   import magic
   
   def check_file_type(file_path):
       mime = magic.Magic(mime=True)
       file_type = mime.from_file(file_path)
       print(f"Detected file type: {file_type}")
       return file_type.startswith('audio/')
   ```

### Transcription Quality Issues

#### Problem: Poor transcription accuracy
**Symptoms:**
- Many incorrect words
- Missing words or phrases
- Nonsensical output

**Solutions:**
1. **Improve Audio Quality**:
   ```python
   # Audio preprocessing
   from pydub import AudioSegment
   from pydub.effects import normalize
   
   audio = AudioSegment.from_file("noisy_audio.wav")
   
   # Normalize volume
   audio = normalize(audio)
   
   # Remove silence
   audio = audio.strip_silence(silence_len=1000, silence_thresh=-40)
   
   # Export with consistent settings
   audio.export("clean_audio.wav", format="wav", parameters=["-ar", "16000"])
   ```

2. **Use Appropriate Configuration**:
   ```python
   # For high accuracy
   config = {
       "model": "whisper-1",
       "temperature": 0.0,  # Most deterministic
       "enable_language_detection": True,
       "enable_confidence_analysis": True,
       "confidence_threshold": 0.9
   }
   ```

3. **Add Custom Vocabulary**:
   ```python
   vocabulary = {
       "vocabulary_terms": ["specific", "terms", "from", "your", "domain"],
       "proper_nouns": ["Company", "Names", "Person", "Names"],
       "technical_terms": ["API", "JSON", "HTTP", "REST"],
       "boost_factor": 2.0
   }
   ```

#### Problem: Wrong language detection
**Symptoms:**
- Transcription in wrong language
- Mixed language results
- Low confidence scores

**Solutions:**
1. **Specify Language Explicitly**:
   ```python
   config = {
       "model": "whisper-1",
       "language": "en",  # Force English
       "enable_language_detection": False
   }
   ```

2. **Test Language Detection First**:
   ```python
   # Test language detection separately
   response = requests.post(
       "https://api.whisper-advanced.com/v1/whisper-advanced/detect-language",
       headers=headers,
       files={"audio_file": open("audio.wav", "rb")}
   )
   
   result = response.json()
   print(f"Detected: {result['data']['detected_language']}")
   print(f"Confidence: {result['data']['confidence']}")
   ```

3. **Handle Multi-language Content**:
   ```python
   # For mixed language content
   config = {
       "model": "whisper-1",
       "temperature": 0.1,  # Slightly higher for flexibility
       "enable_language_detection": True,
       "chunk_length_s": 20  # Shorter chunks for language switching
   }
   ```

### Performance Issues

#### Problem: Slow processing times
**Symptoms:**
- Long wait times for results
- Timeout errors
- Processing takes much longer than expected

**Solutions:**
1. **Optimize Audio Files**:
   ```python
   # Reduce file size while maintaining quality
   audio = AudioSegment.from_file("large_file.wav")
   
   # Optimize settings
   audio = audio.set_frame_rate(16000)  # Whisper's native rate
   audio = audio.set_channels(1)  # Mono
   audio = audio.set_sample_width(2)  # 16-bit
   
   audio.export("optimized.wav", format="wav")
   ```

2. **Use Appropriate Settings**:
   ```python
   # Fast processing configuration
   config = {
       "model": "whisper-1",
       "temperature": 0.2,
       "enable_language_detection": False,  # Skip if known
       "enable_confidence_analysis": False,  # Skip if not needed
       "enable_word_timestamps": False,  # Skip if not needed
       "chunk_length_s": 60  # Larger chunks
   }
   ```

3. **Implement Concurrent Processing**:
   ```python
   import concurrent.futures
   
   def process_files_parallel(file_paths, config, max_workers=3):
       with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
           futures = [
               executor.submit(transcribe_audio, path, config)
               for path in file_paths
           ]
           
           results = []
           for future in concurrent.futures.as_completed(futures):
               try:
                   result = future.result(timeout=300)
                   results.append(result)
               except Exception as e:
                   print(f"Error processing file: {e}")
           
           return results
   ```

#### Problem: Rate limiting errors
**Symptoms:**
- 429 Too Many Requests errors
- Rate limit exceeded messages
- Requests being rejected

**Solutions:**
1. **Implement Rate Limiting**:
   ```python
   import time
   from collections import deque
   
   class RateLimiter:
       def __init__(self, max_requests=100, time_window=3600):
           self.max_requests = max_requests
           self.time_window = time_window
           self.requests = deque()
       
       def wait_if_needed(self):
           now = time.time()
           
           # Remove old requests
           while self.requests and self.requests[0] < now - self.time_window:
               self.requests.popleft()
           
           # Check if we need to wait
           if len(self.requests) >= self.max_requests:
               sleep_time = self.requests[0] + self.time_window - now
               if sleep_time > 0:
                   time.sleep(sleep_time)
           
           self.requests.append(now)
   
   rate_limiter = RateLimiter()
   
   def rate_limited_transcribe(file_path, config):
       rate_limiter.wait_if_needed()
       return transcribe_audio(file_path, config)
   ```

2. **Use Exponential Backoff**:
   ```python
   def transcribe_with_backoff(file_path, config, max_retries=5):
       for attempt in range(max_retries):
           try:
               return transcribe_audio(file_path, config)
           except requests.exceptions.HTTPError as e:
               if e.response.status_code == 429:
                   wait_time = (2 ** attempt) + random.uniform(0, 1)
                   print(f"Rate limited. Waiting {wait_time:.1f} seconds...")
                   time.sleep(wait_time)
               else:
                   raise
       
       raise Exception(f"Failed after {max_retries} attempts")
   ```

### Integration Issues

#### Problem: SDK installation failures
**Symptoms:**
- pip install errors
- npm install failures
- Missing dependencies

**Solutions:**
1. **Python SDK Issues**:
   ```bash
   # Update pip first
   pip install --upgrade pip
   
   # Install with verbose output
   pip install -v whisper-advanced-sdk
   
   # If still failing, install dependencies manually
   pip install requests python-multipart aiohttp
   ```

2. **Node.js SDK Issues**:
   ```bash
   # Clear npm cache
   npm cache clean --force
   
   # Install with verbose output
   npm install --verbose whisper-advanced-js
   
   # Try with different registry
   npm install --registry https://registry.npmjs.org/ whisper-advanced-js
   ```

3. **Version Conflicts**:
   ```bash
   # Create virtual environment (Python)
   python -m venv whisper_env
   source whisper_env/bin/activate  # Linux/Mac
   whisper_env\Scripts\activate     # Windows
   
   # Use specific Node version
   nvm use 16  # or your preferred version
   ```

#### Problem: Import/require errors
**Symptoms:**
- Module not found errors
- Import failures
- Undefined references

**Solutions:**
1. **Python Import Issues**:
   ```python
   # Check if module is installed
   import sys
   print(sys.path)
   
   # Try alternative import
   try:
       from whisper_advanced import WhisperClient
   except ImportError:
       # Fallback to direct API calls
       import requests
       import json
   ```

2. **JavaScript Import Issues**:
   ```javascript
   // Try different import styles
   
   // ES6 modules
   import { WhisperClient } from 'whisper-advanced-js';
   
   // CommonJS
   const { WhisperClient } = require('whisper-advanced-js');
   
   // Dynamic import
   const whisperModule = await import('whisper-advanced-js');
   const WhisperClient = whisperModule.WhisperClient;
   ```

## 🔍 Debugging Tools

### API Response Debugging

```python
import json
import requests

def debug_api_call(url, **kwargs):
    """Make API call with detailed debugging"""
    print(f"🔍 Making request to: {url}")
    print(f"📤 Headers: {json.dumps(kwargs.get('headers', {}), indent=2)}")
    
    if 'data' in kwargs:
        print(f"📋 Data: {kwargs['data']}")
    
    try:
        response = requests.post(url, **kwargs)
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            print(f"📥 Response Body: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"📥 Response Body: {response.text[:500]}...")
        
        return response
        
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        raise
```

### Audio File Analysis

```python
import librosa
import numpy as np

def analyze_audio_file(file_path):
    """Analyze audio file properties"""
    try:
        # Load audio file
        audio, sr = librosa.load(file_path, sr=None)
        
        print(f"🎵 Audio Analysis for: {file_path}")
        print(f"📊 Duration: {len(audio) / sr:.2f} seconds")
        print(f"📊 Sample Rate: {sr} Hz")
        print(f"📊 Channels: {1 if audio.ndim == 1 else audio.shape[0]}")
        print(f"📊 File Size: {os.path.getsize(file_path) / 1024 / 1024:.2f} MB")
        
        # Audio quality metrics
        rms = np.sqrt(np.mean(audio**2))
        print(f"📊 RMS Level: {rms:.4f}")
        
        # Check for clipping
        clipping = np.sum(np.abs(audio) > 0.99) / len(audio) * 100
        print(f"📊 Clipping: {clipping:.2f}%")
        
        # Dynamic range
        dynamic_range = 20 * np.log10(np.max(np.abs(audio)) / (np.mean(np.abs(audio)) + 1e-10))
        print(f"📊 Dynamic Range: {dynamic_range:.1f} dB")
        
        return {
            'duration': len(audio) / sr,
            'sample_rate': sr,
            'rms_level': rms,
            'clipping_percent': clipping,
            'dynamic_range_db': dynamic_range
        }
        
    except Exception as e:
        print(f"❌ Error analyzing audio: {str(e)}")
        return None
```

### Configuration Validator

```python
def validate_config(config):
    """Validate Whisper configuration"""
    errors = []
    warnings = []
    
    # Required fields
    if 'model' not in config:
        errors.append("Missing required field: 'model'")
    
    # Temperature validation
    temp = config.get('temperature', 0.0)
    if not 0.0 <= temp <= 1.0:
        errors.append(f"Temperature must be between 0.0 and 1.0, got {temp}")
    
    # Confidence threshold validation
    conf_thresh = config.get('confidence_threshold', 0.8)
    if not 0.0 <= conf_thresh <= 1.0:
        errors.append(f"Confidence threshold must be between 0.0 and 1.0, got {conf_thresh}")
    
    # Chunk length validation
    chunk_len = config.get('chunk_length_s', 30)
    if not 10 <= chunk_len <= 60:
        warnings.append(f"Chunk length {chunk_len}s is outside recommended range (10-60s)")
    
    # Performance warnings
    if config.get('enable_speaker_detection') and config.get('chunk_length_s', 30) > 30:
        warnings.append("Large chunk sizes may reduce speaker detection accuracy")
    
    if config.get('temperature', 0.0) > 0.5 and config.get('enable_confidence_analysis'):
        warnings.append("High temperature may result in lower confidence scores")
    
    # Print results
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("✅ Configuration is valid")
    
    return len(errors) == 0
```

## 📞 Getting Help

### Support Channels

1. **Documentation**: Check the complete API documentation
2. **GitHub Issues**: Report bugs and feature requests
3. **Email Support**: support@whisper-advanced.com
4. **Community Forum**: Join discussions with other developers
5. **Stack Overflow**: Tag questions with `whisper-advanced`

### Before Contacting Support

Please gather this information:

1. **Error Details**:
   - Full error message
   - HTTP status code
   - Request/response details

2. **Environment Information**:
   - Programming language and version
   - SDK version (if using)
   - Operating system

3. **Audio File Information**:
   - File format and size
   - Duration and quality
   - Sample rate and channels

4. **Configuration Used**:
   - Complete configuration object
   - Any custom vocabulary or prompts

5. **Steps to Reproduce**:
   - Minimal code example
   - Expected vs actual behavior

This troubleshooting guide should help resolve most common issues. For complex problems, don't hesitate to reach out to our support team with the information above.