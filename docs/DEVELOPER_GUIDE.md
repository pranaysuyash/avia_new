# Whisper Advanced Integration - Developer Guide

## 🎯 Overview

This guide provides comprehensive information for developers integrating with the Whisper Advanced API, including setup instructions, code examples, best practices, and troubleshooting tips.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ or Node.js 14+
- API key from Whisper Advanced platform
- Basic understanding of REST APIs
- Audio files for testing

### Installation

**Python:**
```bash
pip install requests python-multipart
```

**Node.js:**
```bash
npm install axios form-data
```

### Basic Example

**Python:**
```python
import requests
import json

def transcribe_audio(file_path, api_key):
    url = "https://api.whisper-advanced.com/v1/whisper-advanced/transcribe"
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    config = {
        "model": "whisper-1",
        "temperature": 0.0,
        "enable_word_timestamps": True
    }
    
    with open(file_path, 'rb') as f:
        files = {"audio_file": f}
        data = {"config": json.dumps(config)}
        response = requests.post(url, headers=headers, files=files, data=data)
    
    return response.json()
```

**JavaScript:**
```javascript
async function transcribeAudio(file, apiKey) {
    const formData = new FormData();
    formData.append('audio_file', file);
    formData.append('config', JSON.stringify({
        model: 'whisper-1',
        temperature: 0.0,
        enable_word_timestamps: true
    }));

    const response = await fetch('https://api.whisper-advanced.com/v1/whisper-advanced/transcribe', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${apiKey}` },
        body: formData
    });

    return await response.json();
}
```## 📚 S
DK Documentation

### Python SDK

The Python SDK provides a convenient wrapper around the REST API.

#### Installation
```bash
pip install whisper-advanced-sdk
```

#### Basic Usage
```python
from whisper_advanced import WhisperClient

client = WhisperClient(api_key="your-api-key")

# Transcribe audio file
result = client.transcribe("audio.wav")
print(result.text)

# Detect language
language = client.detect_language("audio.wav")
print(f"Detected: {language.detected_language}")

# Batch processing
results = client.batch_transcribe(["file1.wav", "file2.wav"])
```

### JavaScript SDK

#### Installation
```bash
npm install whisper-advanced-js
```

#### Basic Usage
```javascript
import { WhisperClient } from 'whisper-advanced-js';

const client = new WhisperClient({ apiKey: 'your-api-key' });

// Transcribe audio file
const result = await client.transcribe(audioFile);
console.log(result.text);

// Detect language
const language = await client.detectLanguage(audioFile);
console.log(`Detected: ${language.detectedLanguage}`);
```

## 🔧 Configuration Options

### Model Configuration

```python
config = {
    "model": "whisper-1",                    # Model to use
    "language": "en",                        # Language code or null for auto-detect
    "temperature": 0.0,                      # Sampling temperature (0.0-1.0)
    "enable_language_detection": True,       # Auto-detect language
    "enable_confidence_analysis": True,      # Include confidence scores
    "enable_word_timestamps": True,          # Word-level timestamps
    "enable_speaker_detection": False,       # Speaker diarization
    "confidence_threshold": 0.8,             # Minimum confidence (0.0-1.0)
    "chunk_length_s": 30                     # Chunk length in seconds
}
```

### Custom Vocabulary

```python
vocabulary = {
    "vocabulary_terms": ["whisper", "API", "transcription"],
    "domain_specific_terms": ["neural", "transformer", "embedding"],
    "proper_nouns": ["OpenAI", "GPT", "Microsoft"],
    "technical_terms": ["endpoint", "JSON", "authentication"],
    "boost_factor": 1.5
}
```

### Prompt Configuration

```python
prompts = {
    "context_prompt": "This is a technical discussion about AI",
    "style_prompt": "Use formal language and proper punctuation",
    "domain_prompt": "Machine learning and artificial intelligence",
    "format_prompt": "Include technical terminology and abbreviations"
}
```## 📡 AP
I Integration Patterns

### Synchronous Processing

Best for small files and real-time applications:

```python
def sync_transcribe(file_path, config):
    response = requests.post(
        "https://api.whisper-advanced.com/v1/whisper-advanced/transcribe",
        headers={"Authorization": f"Bearer {API_KEY}"},
        files={"audio_file": open(file_path, 'rb')},
        data={"config": json.dumps(config)}
    )
    return response.json()
```

### Asynchronous Processing

For large files or batch processing:

```python
import asyncio
import aiohttp

async def async_transcribe(session, file_path, config):
    data = aiohttp.FormData()
    data.add_field('audio_file', open(file_path, 'rb'))
    data.add_field('config', json.dumps(config))
    
    async with session.post(
        "https://api.whisper-advanced.com/v1/whisper-advanced/transcribe",
        headers={"Authorization": f"Bearer {API_KEY}"},
        data=data
    ) as response:
        return await response.json()

async def process_multiple_files(file_paths, config):
    async with aiohttp.ClientSession() as session:
        tasks = [async_transcribe(session, path, config) for path in file_paths]
        results = await asyncio.gather(*tasks)
        return results
```

### Batch Processing

Process multiple files efficiently:

```python
def batch_transcribe(file_paths, config):
    files = [('files', open(path, 'rb')) for path in file_paths]
    
    response = requests.post(
        "https://api.whisper-advanced.com/v1/whisper-advanced/batch-transcribe",
        headers={"Authorization": f"Bearer {API_KEY}"},
        files=files,
        data={"config": json.dumps(config)}
    )
    
    # Close file handles
    for _, file_handle in files:
        file_handle.close()
    
    return response.json()
```

## 🔄 Error Handling

### Comprehensive Error Handling

```python
import time
from requests.exceptions import RequestException, Timeout, ConnectionError

class WhisperAPIError(Exception):
    def __init__(self, message, status_code=None, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

def transcribe_with_retry(file_path, config, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://api.whisper-advanced.com/v1/whisper-advanced/transcribe",
                headers={"Authorization": f"Bearer {API_KEY}"},
                files={"audio_file": open(file_path, 'rb')},
                data={"config": json.dumps(config)},
                timeout=300  # 5 minute timeout
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt
                print(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                error_data = response.json()
                raise WhisperAPIError(
                    error_data.get('detail', 'Unknown error'),
                    response.status_code,
                    error_data.get('code')
                )
                
        except (ConnectionError, Timeout) as e:
            if attempt == max_retries - 1:
                raise WhisperAPIError(f"Network error after {max_retries} attempts: {e}")
            wait_time = 2 ** attempt
            print(f"Network error. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    raise WhisperAPIError(f"Failed after {max_retries} attempts")
```