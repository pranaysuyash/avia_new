# Whisper Advanced Integration - Developer Guide

## 🎯 Overview

This comprehensive guide provides developers with everything needed to integrate Whisper Advanced capabilities into applications, including SDKs, code examples, best practices, and advanced integration patterns.

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** or **Node.js 14+**
- **API Key** from Whisper Advanced platform
- **Basic understanding** of REST APIs and audio processing
- **Audio files** for testing (WAV, MP3, M4A, FLAC, OGG)

### Installation

#### Python SDK
```bash
pip install whisper-advanced-client
```

#### JavaScript/Node.js SDK
```bash
npm install whisper-advanced-js
```

#### Direct API Access
No SDK required - use any HTTP client library.

### Basic Example

#### Python
```python
from whisper_advanced import WhisperAdvancedClient
import json

# Initialize client
client = WhisperAdvancedClient(
    api_key="your_api_key_here",
    base_url="https://api.whisper-advanced.com/v1"
)

# Basic transcription
result = client.transcribe(
    audio_file="meeting.wav",
    config={
        "model_size": "medium",
        "enable_diarization": True,
        "max_speakers": 3
    }
)

print(f"Transcript: {result.text}")
print(f"Speakers: {len(result.speaker_diarization.speakers)}")
```

#### JavaScript/Node.js
```javascript
import { WhisperAdvancedClient } from 'whisper-advanced-js';
import fs from 'fs';

// Initialize client
const client = new WhisperAdvancedClient({
    apiKey: 'your_api_key_here',
    baseUrl: 'https://api.whisper-advanced.com/v1'
});

// Basic transcription
const result = await client.transcribe('meeting.wav', {
    model_size: 'medium',
    enable_diarization: true,
    max_speakers: 3
});

console.log(`Transcript: ${result.text}`);
console.log(`Speakers: ${result.speaker_diarization.speakers.length}`);
```

#### cURL (Direct API)
```bash
curl -X POST \
  -H "Authorization: Bearer your_api_key_here" \
  -F "audio_file=@meeting.wav" \
  -F 'config={"model_size":"medium","enable_diarization":true}' \
  https://api.whisper-advanced.com/v1/whisper-advanced/transcribe
```

## 📚 SDK Documentation

### Python SDK

#### Installation and Setup
```python
from whisper_advanced import WhisperAdvancedClient
from whisper_advanced.models import WhisperConfig, TranscriptionResult
from whisper_advanced.exceptions import (
    WhisperAdvancedException,
    AudioFormatException,
    ProcessingTimeoutException,
    RateLimitException
)

# Initialize with configuration
client = WhisperAdvancedClient(
    api_key="your_api_key",
    base_url="https://api.whisper-advanced.com/v1",
    timeout=300,  # 5 minutes
    max_retries=3,
    retry_delay=1.0
)
```

#### Core Methods

##### `transcribe()`
```python
def transcribe(
    self,
    audio_file: Union[str, bytes, BinaryIO],
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> TranscriptionResult:
    """
    Transcribe audio file with advanced configuration.
    
    Args:
        audio_file: Path to file, bytes, or file-like object
        config: Configuration dictionary
        **kwargs: Additional configuration parameters
    
    Returns:
        TranscriptionResult object with full results
    
    Raises:
        AudioFormatException: Unsupported audio format
        ProcessingTimeoutException: Processing took too long
        RateLimitException: Rate limit exceeded
    """
```

**Example:**
```python
# From file path
result = client.transcribe("audio.wav", {
    "model_size": "large",
    "temperature": 0.0,
    "enable_word_timestamps": True
})

# From bytes
with open("audio.wav", "rb") as f:
    audio_bytes = f.read()
result = client.transcribe(audio_bytes, config)

# With kwargs
result = client.transcribe(
    "audio.wav",
    model_size="medium",
    enable_diarization=True,
    max_speakers=5
)
```

##### `detect_language()`
```python
def detect_language(
    self,
    audio_file: Union[str, bytes, BinaryIO],
    sample_duration: int = 30
) -> LanguageDetectionResult:
    """
    Detect language of audio content.
    
    Args:
        audio_file: Audio file to analyze
        sample_duration: Duration in seconds to analyze
    
    Returns:
        LanguageDetectionResult with detected language and confidence
    """
```

**Example:**
```python
language_result = client.detect_language("unknown.wav", sample_duration=15)
print(f"Detected: {language_result.detected_language}")
print(f"Confidence: {language_result.confidence}")
```

##### `batch_transcribe()`
```python
def batch_transcribe(
    self,
    audio_files: List[Union[str, bytes, BinaryIO]],
    config: Optional[Dict[str, Any]] = None,
    webhook_url: Optional[str] = None
) -> BatchTranscriptionJob:
    """
    Process multiple audio files in batch.
    
    Args:
        audio_files: List of audio files to process
        config: Shared configuration for all files
        webhook_url: URL for completion notification
    
    Returns:
        BatchTranscriptionJob with job ID and status
    """
```

**Example:**
```python
files = ["meeting1.wav", "meeting2.wav", "meeting3.wav"]
batch_job = client.batch_transcribe(
    files,
    config={"model_size": "medium"},
    webhook_url="https://myapp.com/webhook"
)

print(f"Batch ID: {batch_job.batch_id}")
print(f"Status: {batch_job.status}")
```

##### `get_batch_status()`
```python
def get_batch_status(self, batch_id: str) -> BatchStatus:
    """Get status of batch transcription job."""
    
status = client.get_batch_status("batch_abc123")
print(f"Progress: {status.progress.percentage}%")
```

##### `get_batch_results()`
```python
def get_batch_results(self, batch_id: str) -> BatchResults:
    """Get results from completed batch job."""
    
results = client.get_batch_results("batch_abc123")
for result in results.results:
    print(f"{result.filename}: {result.transcription.text[:100]}...")
```

#### Configuration Classes

```python
from whisper_advanced.models import WhisperConfig

config = WhisperConfig(
    model_size="medium",
    language="en",
    temperature=0.0,
    enable_word_timestamps=True,
    enable_vad=True,
    enable_diarization=True,
    max_speakers=5,
    custom_vocabulary=["API", "Kubernetes", "PostgreSQL"],
    boost_vocabulary_weight=1.5
)

result = client.transcribe("audio.wav", config.to_dict())
```

#### Error Handling

```python
from whisper_advanced.exceptions import *

try:
    result = client.transcribe("audio.wav")
except AudioFormatException as e:
    print(f"Unsupported format: {e.message}")
    print(f"Supported formats: {e.supported_formats}")
except ProcessingTimeoutException as e:
    print(f"Processing timeout: {e.message}")
    print(f"Try smaller model or shorter audio")
except RateLimitException as e:
    print(f"Rate limit exceeded: {e.message}")
    print(f"Retry after: {e.retry_after} seconds")
except WhisperAdvancedException as e:
    print(f"General error: {e.message}")
    print(f"Error code: {e.error_code}")
```

### JavaScript/Node.js SDK

#### Installation and Setup
```javascript
import { 
    WhisperAdvancedClient,
    WhisperConfig,
    WhisperAdvancedError,
    AudioFormatError,
    ProcessingTimeoutError,
    RateLimitError
} from 'whisper-advanced-js';

// Initialize client
const client = new WhisperAdvancedClient({
    apiKey: 'your_api_key',
    baseUrl: 'https://api.whisper-advanced.com/v1',
    timeout: 300000, // 5 minutes
    maxRetries: 3,
    retryDelay: 1000
});
```

#### Core Methods

##### `transcribe()`
```javascript
async transcribe(
    audioFile: string | Buffer | Blob,
    config?: WhisperConfig | object
): Promise<TranscriptionResult>
```

**Example:**
```javascript
// From file path
const result = await client.transcribe('audio.wav', {
    model_size: 'large',
    temperature: 0.0,
    enable_word_timestamps: true
});

// From Buffer
const fs = require('fs');
const audioBuffer = fs.readFileSync('audio.wav');
const result = await client.transcribe(audioBuffer, config);

// From Blob (browser)
const result = await client.transcribe(audioBlob, {
    model_size: 'medium',
    enable_diarization: true,
    max_speakers: 5
});
```

##### `detectLanguage()`
```javascript
const languageResult = await client.detectLanguage('unknown.wav', {
    sample_duration: 15
});
console.log(`Detected: ${languageResult.detected_language}`);
console.log(`Confidence: ${languageResult.confidence}`);
```

##### `batchTranscribe()`
```javascript
const files = ['meeting1.wav', 'meeting2.wav', 'meeting3.wav'];
const batchJob = await client.batchTranscribe(files, {
    config: { model_size: 'medium' },
    webhook_url: 'https://myapp.com/webhook'
});

console.log(`Batch ID: ${batchJob.batch_id}`);
```

#### Error Handling

```javascript
try {
    const result = await client.transcribe('audio.wav');
} catch (error) {
    if (error instanceof AudioFormatError) {
        console.log(`Unsupported format: ${error.message}`);
        console.log(`Supported: ${error.supportedFormats.join(', ')}`);
    } else if (error instanceof ProcessingTimeoutError) {
        console.log(`Timeout: ${error.message}`);
    } else if (error instanceof RateLimitError) {
        console.log(`Rate limited: ${error.message}`);
        console.log(`Retry after: ${error.retryAfter} seconds`);
    } else {
        console.log(`Error: ${error.message}`);
    }
}
```

## 🔧 Advanced Integration Patterns

### Asynchronous Processing

#### Python with asyncio
```python
import asyncio
from whisper_advanced import AsyncWhisperAdvancedClient

async def process_multiple_files():
    client = AsyncWhisperAdvancedClient(api_key="your_key")
    
    files = ["file1.wav", "file2.wav", "file3.wav"]
    tasks = []
    
    for file in files:
        task = client.transcribe(file, {"model_size": "medium"})
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results):
        print(f"File {files[i]}: {result.text[:100]}...")

# Run async function
asyncio.run(process_multiple_files())
```

#### JavaScript with Promises
```javascript
async function processMultipleFiles() {
    const files = ['file1.wav', 'file2.wav', 'file3.wav'];
    const config = { model_size: 'medium' };
    
    // Process all files concurrently
    const promises = files.map(file => 
        client.transcribe(file, config)
    );
    
    try {
        const results = await Promise.all(promises);
        results.forEach((result, index) => {
            console.log(`File ${files[index]}: ${result.text.substring(0, 100)}...`);
        });
    } catch (error) {
        console.error('Error processing files:', error);
    }
}
```

### Streaming and Real-time Processing

#### WebSocket Integration (JavaScript)
```javascript
import { WhisperAdvancedStream } from 'whisper-advanced-js';

class RealTimeTranscription {
    constructor(apiKey) {
        this.stream = new WhisperAdvancedStream({
            apiKey: apiKey,
            config: {
                model_size: 'base',
                enable_vad: true,
                language: 'en'
            }
        });
        
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        this.stream.on('partial_result', (result) => {
            console.log('Partial:', result.text);
            this.updateUI(result.text, false);
        });
        
        this.stream.on('final_result', (result) => {
            console.log('Final:', result.text);
            this.updateUI(result.text, true);
        });
        
        this.stream.on('error', (error) => {
            console.error('Stream error:', error);
            this.handleError(error);
        });
    }
    
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            
            this.stream.start(stream);
        } catch (error) {
            console.error('Failed to start recording:', error);
        }
    }
    
    stopRecording() {
        this.stream.stop();
    }
    
    updateUI(text, isFinal) {
        // Update your UI with transcription results
        const element = document.getElementById('transcription');
        if (isFinal) {
            element.innerHTML += `<p>${text}</p>`;
        } else {
            element.innerHTML = element.innerHTML.replace(
                /<span class="partial">.*<\/span>$/,
                `<span class="partial">${text}</span>`
            );
        }
    }
}

// Usage
const transcription = new RealTimeTranscription('your_api_key');
transcription.startRecording();
```

### Webhook Integration

#### Setting up Webhook Endpoint (Express.js)
```javascript
const express = require('express');
const crypto = require('crypto');
const app = express();

app.use(express.json());

// Webhook endpoint for batch completion
app.post('/webhook/transcription-complete', (req, res) => {
    // Verify webhook signature (recommended)
    const signature = req.headers['x-whisper-signature'];
    const payload = JSON.stringify(req.body);
    const expectedSignature = crypto
        .createHmac('sha256', process.env.WEBHOOK_SECRET)
        .update(payload)
        .digest('hex');
    
    if (signature !== `sha256=${expectedSignature}`) {
        return res.status(401).send('Invalid signature');
    }
    
    const { batch_id, status, results } = req.body;
    
    if (status === 'completed') {
        console.log(`Batch ${batch_id} completed`);
        
        // Process results
        results.forEach(result => {
            if (result.status === 'completed') {
                console.log(`File ${result.filename} transcribed successfully`);
                // Store result in database, send notification, etc.
                processTranscriptionResult(result);
            } else {
                console.error(`File ${result.filename} failed: ${result.error}`);
            }
        });
    }
    
    res.status(200).send('OK');
});

async function processTranscriptionResult(result) {
    // Save to database
    await saveTranscriptionToDatabase(result);
    
    // Send notification to user
    await sendNotificationToUser(result.user_id, {
        message: `Transcription of ${result.filename} is ready`,
        transcript_id: result.id
    });
    
    // Trigger downstream processing
    await triggerContentAnalysis(result.transcription);
}

app.listen(3000, () => {
    console.log('Webhook server running on port 3000');
});
```

#### Python Flask Webhook
```python
from flask import Flask, request, jsonify
import hmac
import hashlib
import json

app = Flask(__name__)

@app.route('/webhook/transcription-complete', methods=['POST'])
def handle_transcription_webhook():
    # Verify signature
    signature = request.headers.get('X-Whisper-Signature')
    payload = request.get_data()
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if signature != f'sha256={expected_signature}':
        return jsonify({'error': 'Invalid signature'}), 401
    
    data = request.json
    batch_id = data['batch_id']
    status = data['status']
    results = data['results']
    
    if status == 'completed':
        print(f"Batch {batch_id} completed")
        
        for result in results:
            if result['status'] == 'completed':
                process_transcription_result(result)
            else:
                handle_transcription_error(result)
    
    return jsonify({'status': 'received'}), 200

def process_transcription_result(result):
    # Save to database
    save_transcription_to_database(result)
    
    # Send notification
    send_notification_to_user(result['user_id'], {
        'message': f"Transcription of {result['filename']} is ready",
        'transcript_id': result['id']
    })

if __name__ == '__main__':
    app.run(port=3000)
```

### Custom Audio Processing Pipeline

#### Python Audio Preprocessing
```python
import librosa
import numpy as np
from scipy.io import wavfile
import noisereduce as nr

class AudioPreprocessor:
    def __init__(self):
        self.target_sr = 16000  # Whisper's preferred sample rate
    
    def preprocess_audio(self, audio_path, output_path=None):
        """
        Preprocess audio for optimal Whisper performance.
        """
        # Load audio
        audio, sr = librosa.load(audio_path, sr=None)
        
        # Resample to target sample rate
        if sr != self.target_sr:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sr)
        
        # Normalize audio
        audio = self.normalize_audio(audio)
        
        # Reduce noise
        audio = self.reduce_noise(audio)
        
        # Remove silence
        audio = self.remove_silence(audio)
        
        # Save preprocessed audio
        if output_path:
            wavfile.write(output_path, self.target_sr, 
                         (audio * 32767).astype(np.int16))
        
        return audio
    
    def normalize_audio(self, audio):
        """Normalize audio to prevent clipping."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val * 0.95
        return audio
    
    def reduce_noise(self, audio):
        """Apply noise reduction."""
        return nr.reduce_noise(y=audio, sr=self.target_sr)
    
    def remove_silence(self, audio, top_db=20):
        """Remove silence from audio."""
        intervals = librosa.effects.split(
            audio, top_db=top_db, frame_length=2048, hop_length=512
        )
        
        if len(intervals) == 0:
            return audio
        
        # Concatenate non-silent intervals
        trimmed_audio = []
        for interval in intervals:
            trimmed_audio.extend(audio[interval[0]:interval[1]])
        
        return np.array(trimmed_audio)

# Usage
preprocessor = AudioPreprocessor()
client = WhisperAdvancedClient(api_key="your_key")

# Preprocess and transcribe
audio_path = "noisy_meeting.wav"
preprocessed_path = "clean_meeting.wav"

preprocessor.preprocess_audio(audio_path, preprocessed_path)
result = client.transcribe(preprocessed_path, {
    "model_size": "medium",
    "enable_diarization": True
})
```

### Database Integration

#### SQLAlchemy Models (Python)
```python
from sqlalchemy import create_engine, Column, String, Text, Float, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()

class TranscriptionJob(Base):
    __tablename__ = 'transcription_jobs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_size = Column(Integer)
    duration = Column(Float)
    status = Column(String, default='pending')
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)

class TranscriptionResult(Base):
    __tablename__ = 'transcription_results'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, nullable=False)
    transcript_text = Column(Text, nullable=False)
    segments = Column(JSON)
    language = Column(String)
    confidence_score = Column(Float)
    word_count = Column(Integer)
    processing_time = Column(Float)
    model_used = Column(String)
    speaker_diarization = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database operations
class TranscriptionService:
    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def create_job(self, user_id, filename, config):
        job = TranscriptionJob(
            user_id=user_id,
            filename=filename,
            config=config
        )
        self.session.add(job)
        self.session.commit()
        return job
    
    def update_job_status(self, job_id, status, error_message=None):
        job = self.session.query(TranscriptionJob).filter_by(id=job_id).first()
        if job:
            job.status = status
            if error_message:
                job.error_message = error_message
            if status == 'processing':
                job.started_at = datetime.utcnow()
            elif status in ['completed', 'failed']:
                job.completed_at = datetime.utcnow()
            self.session.commit()
    
    def save_result(self, job_id, transcription_result):
        result = TranscriptionResult(
            job_id=job_id,
            transcript_text=transcription_result.text,
            segments=transcription_result.segments,
            language=transcription_result.language,
            confidence_score=transcription_result.processing_stats.average_confidence,
            word_count=transcription_result.processing_stats.word_count,
            processing_time=transcription_result.processing_stats.processing_time,
            model_used=transcription_result.processing_stats.model_used,
            speaker_diarization=transcription_result.speaker_diarization
        )
        self.session.add(result)
        self.session.commit()
        return result

# Usage
service = TranscriptionService('postgresql://user:pass@localhost/transcriptions')
client = WhisperAdvancedClient(api_key="your_key")

# Create job
job = service.create_job(
    user_id="user123",
    filename="meeting.wav",
    config={"model_size": "medium"}
)

# Process transcription
service.update_job_status(job.id, 'processing')
try:
    result = client.transcribe("meeting.wav", job.config)
    service.save_result(job.id, result)
    service.update_job_status(job.id, 'completed')
except Exception as e:
    service.update_job_status(job.id, 'failed', str(e))
```

## 🔒 Authentication and Security

### API Key Management

#### Environment Variables
```python
import os
from whisper_advanced import WhisperAdvancedClient

# Load from environment
api_key = os.getenv('WHISPER_ADVANCED_API_KEY')
if not api_key:
    raise ValueError("API key not found in environment variables")

client = WhisperAdvancedClient(api_key=api_key)
```

#### Configuration Files
```python
import json
from pathlib import Path

def load_config():
    config_path = Path.home() / '.whisper-advanced' / 'config.json'
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    raise FileNotFoundError("Configuration file not found")

config = load_config()
client = WhisperAdvancedClient(api_key=config['api_key'])
```

### Rate Limiting and Retry Logic

#### Python Implementation
```python
import time
import random
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=60.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RateLimitException as e:
                    if attempt == max_retries:
                        raise
                    
                    # Use retry-after header if available
                    delay = e.retry_after if hasattr(e, 'retry_after') else None
                    if not delay:
                        # Exponential backoff with jitter
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        delay += random.uniform(0, delay * 0.1)  # Add jitter
                    
                    print(f"Rate limited, retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                except Exception as e:
                    if attempt == max_retries:
                        raise
                    print(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(base_delay * (2 ** attempt))
            
            return None
        return wrapper
    return decorator

# Usage
@retry_with_backoff(max_retries=3)
def transcribe_with_retry(client, audio_file, config):
    return client.transcribe(audio_file, config)

result = transcribe_with_retry(client, "audio.wav", {"model_size": "medium"})
```

#### JavaScript Implementation
```javascript
class RateLimitHandler {
    constructor(maxRetries = 3, baseDelay = 1000, maxDelay = 60000) {
        this.maxRetries = maxRetries;
        this.baseDelay = baseDelay;
        this.maxDelay = maxDelay;
    }
    
    async executeWithRetry(operation) {
        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                return await operation();
            } catch (error) {
                if (error instanceof RateLimitError) {
                    if (attempt === this.maxRetries) throw error;
                    
                    // Use retry-after header if available
                    let delay = error.retryAfter * 1000 || null;
                    if (!delay) {
                        // Exponential backoff with jitter
                        delay = Math.min(
                            this.baseDelay * Math.pow(2, attempt),
                            this.maxDelay
                        );
                        delay += Math.random() * delay * 0.1; // Add jitter
                    }
                    
                    console.log(`Rate limited, retrying in ${delay/1000}s...`);
                    await this.sleep(delay);
                } else {
                    if (attempt === this.maxRetries) throw error;
                    console.log(`Attempt ${attempt + 1} failed:`, error.message);
                    await this.sleep(this.baseDelay * Math.pow(2, attempt));
                }
            }
        }
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Usage
const rateLimitHandler = new RateLimitHandler();

const result = await rateLimitHandler.executeWithRetry(async () => {
    return await client.transcribe('audio.wav', { model_size: 'medium' });
});
```

## 📊 Performance Optimization

### Concurrent Processing

#### Python ThreadPoolExecutor
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def process_file(client, file_path, config):
    """Process a single file."""
    start_time = time.time()
    try:
        result = client.transcribe(file_path, config)
        processing_time = time.time() - start_time
        return {
            'file': file_path,
            'success': True,
            'result': result,
            'processing_time': processing_time
        }
    except Exception as e:
        processing_time = time.time() - start_time
        return {
            'file': file_path,
            'success': False,
            'error': str(e),
            'processing_time': processing_time
        }

def process_files_concurrently(client, files, config, max_workers=5):
    """Process multiple files concurrently."""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_file, client, file, config): file 
            for file in files
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_file):
            result = future.result()
            results.append(result)
            
            if result['success']:
                print(f"✓ {result['file']} completed in {result['processing_time']:.1f}s")
            else:
                print(f"✗ {result['file']} failed: {result['error']}")
    
    return results

# Usage
client = WhisperAdvancedClient(api_key="your_key")
files = ["file1.wav", "file2.wav", "file3.wav", "file4.wav"]
config = {"model_size": "medium", "enable_diarization": True}

results = process_files_concurrently(client, files, config, max_workers=3)

# Analyze results
successful = [r for r in results if r['success']]
failed = [r for r in results if not r['success']]

print(f"\nProcessed {len(successful)}/{len(files)} files successfully")
print(f"Average processing time: {sum(r['processing_time'] for r in successful) / len(successful):.1f}s")
```

### Caching Strategies

#### Redis Caching
```python
import redis
import json
import hashlib
from datetime import timedelta

class TranscriptionCache:
    def __init__(self, redis_url='redis://localhost:6379/0'):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = timedelta(hours=24)
    
    def _generate_cache_key(self, audio_file_hash, config):
        """Generate cache key from audio hash and config."""
        config_str = json.dumps(config, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()
        return f"transcription:{audio_file_hash}:{config_hash}"
    
    def _hash_audio_file(self, audio_file_path):
        """Generate hash of audio file."""
        hasher = hashlib.md5()
        with open(audio_file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def get_cached_result(self, audio_file_path, config):
        """Get cached transcription result."""
        try:
            audio_hash = self._hash_audio_file(audio_file_path)
            cache_key = self._generate_cache_key(audio_hash, config)
            
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Cache retrieval error: {e}")
        
        return None
    
    def cache_result(self, audio_file_path, config, result, ttl=None):
        """Cache transcription result."""
        try:
            audio_hash = self._hash_audio_file(audio_file_path)
            cache_key = self._generate_cache_key(audio_hash, config)
            
            # Serialize result (you may need to customize this)
            serialized_result = {
                'text': result.text,
                'segments': result.segments,
                'language': result.language,
                'speaker_diarization': result.speaker_diarization,
                'processing_stats': result.processing_stats,
                'cached_at': time.time()
            }
            
            ttl_seconds = int((ttl or self.default_ttl).total_seconds())
            self.redis_client.setex(
                cache_key,
                ttl_seconds,
                json.dumps(serialized_result)
            )
        except Exception as e:
            print(f"Cache storage error: {e}")

# Usage with caching
cache = TranscriptionCache()
client = WhisperAdvancedClient(api_key="your_key")

def transcribe_with_cache(audio_file, config):
    # Check cache first
    cached_result = cache.get_cached_result(audio_file, config)
    if cached_result:
        print(f"Cache hit for {audio_file}")
        return cached_result
    
    # Transcribe if not cached
    print(f"Cache miss for {audio_file}, transcribing...")
    result = client.transcribe(audio_file, config)
    
    # Cache the result
    cache.cache_result(audio_file, config, result)
    
    return result

# Use cached transcription
result = transcribe_with_cache("meeting.wav", {"model_size": "medium"})
```

## 🧪 Testing and Quality Assurance

### Unit Testing

#### Python Unit Tests
```python
import unittest
from unittest.mock import Mock, patch, MagicMock
from whisper_advanced import WhisperAdvancedClient
from whisper_advanced.exceptions import AudioFormatException

class TestWhisperAdvancedClient(unittest.TestCase):
    def setUp(self):
        self.client = WhisperAdvancedClient(api_key="test_key")
    
    @patch('whisper_advanced.client.requests.post')
    def test_transcribe_success(self, mock_post):
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': {
                'text': 'Hello world',
                'segments': [],
                'language': 'en',
                'processing_stats': {
                    'processing_time': 5.2,
                    'model_used': 'medium'
                }
            }
        }
        mock_post.return_value = mock_response
        
        # Test transcription
        result = self.client.transcribe('test.wav', {'model_size': 'medium'})
        
        # Assertions
        self.assertEqual(result.text, 'Hello world')
        self.assertEqual(result.language, 'en')
        mock_post.assert_called_once()
    
    @patch('whisper_advanced.client.requests.post')
    def test_transcribe_invalid_format(self, mock_post):
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'success': False,
            'error': {
                'code': 'INVALID_AUDIO_FORMAT',
                'message': 'Unsupported format'
            }
        }
        mock_post.return_value = mock_response
        
        # Test exception
        with self.assertRaises(AudioFormatException):
            self.client.transcribe('test.avi', {'model_size': 'medium'})
    
    def test_config_validation(self):
        # Test valid config
        valid_config = {
            'model_size': 'medium',
            'temperature': 0.5,
            'enable_diarization': True
        }
        self.assertTrue(self.client._validate_config(valid_config))
        
        # Test invalid config
        invalid_config = {
            'model_size': 'invalid_model',
            'temperature': 2.0  # Out of range
        }
        with self.assertRaises(ValueError):
            self.client._validate_config(invalid_config)

if __name__ == '__main__':
    unittest.main()
```

#### JavaScript Jest Tests
```javascript
import { WhisperAdvancedClient } from 'whisper-advanced-js';
import { AudioFormatError } from 'whisper-advanced-js/exceptions';

// Mock fetch
global.fetch = jest.fn();

describe('WhisperAdvancedClient', () => {
    let client;
    
    beforeEach(() => {
        client = new WhisperAdvancedClient({ apiKey: 'test_key' });
        fetch.mockClear();
    });
    
    test('transcribe success', async () => {
        // Mock successful response
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                success: true,
                data: {
                    text: 'Hello world',
                    segments: [],
                    language: 'en',
                    processing_stats: {
                        processing_time: 5.2,
                        model_used: 'medium'
                    }
                }
            })
        });
        
        const result = await client.transcribe('test.wav', { model_size: 'medium' });
        
        expect(result.text).toBe('Hello world');
        expect(result.language).toBe('en');
        expect(fetch).toHaveBeenCalledTimes(1);
    });
    
    test('transcribe invalid format', async () => {
        // Mock error response
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 400,
            json: async () => ({
                success: false,
                error: {
                    code: 'INVALID_AUDIO_FORMAT',
                    message: 'Unsupported format'
                }
            })
        });
        
        await expect(
            client.transcribe('test.avi', { model_size: 'medium' })
        ).rejects.toThrow(AudioFormatError);
    });
    
    test('config validation', () => {
        const validConfig = {
            model_size: 'medium',
            temperature: 0.5,
            enable_diarization: true
        };
        expect(() => client._validateConfig(validConfig)).not.toThrow();
        
        const invalidConfig = {
            model_size: 'invalid_model',
            temperature: 2.0
        };
        expect(() => client._validateConfig(invalidConfig)).toThrow();
    });
});
```

### Integration Testing

#### End-to-End Test Suite
```python
import os
import pytest
from whisper_advanced import WhisperAdvancedClient

class TestWhisperAdvancedIntegration:
    @classmethod
    def setup_class(cls):
        api_key = os.getenv('WHISPER_ADVANCED_API_KEY')
        if not api_key:
            pytest.skip("API key not available")
        
        cls.client = WhisperAdvancedClient(api_key=api_key)
        cls.test_audio_file = 'test_data/sample_audio.wav'
    
    def test_health_check(self):
        """Test API health endpoint."""
        health = self.client.health_check()
        assert health['status'] == 'healthy'
        assert 'components' in health
    
    def test_basic_transcription(self):
        """Test basic transcription functionality."""
        result = self.client.transcribe(
            self.test_audio_file,
            {'model_size': 'base', 'language': 'en'}
        )
        
        assert result.text is not None
        assert len(result.text) > 0
        assert result.language == 'en'
        assert result.processing_stats.processing_time > 0
    
    def test_speaker_diarization(self):
        """Test speaker diarization feature."""
        result = self.client.transcribe(
            self.test_audio_file,
            {
                'model_size': 'medium',
                'enable_diarization': True,
                'max_speakers': 2
            }
        )
        
        assert result.speaker_diarization is not None
        assert 'speakers' in result.speaker_diarization
        assert len(result.speaker_diarization['speakers']) <= 2
    
    def test_language_detection(self):
        """Test language detection."""
        result = self.client.detect_language(self.test_audio_file)
        
        assert result.detected_language is not None
        assert result.confidence > 0
        assert 'all_language_probs' in result
    
    def test_batch_processing(self):
        """Test batch transcription."""
        files = [self.test_audio_file, self.test_audio_file]  # Same file twice for testing
        
        batch_job = self.client.batch_transcribe(
            files,
            {'model_size': 'base'}
        )
        
        assert batch_job.batch_id is not None
        assert batch_job.total_files == 2
        
        # Wait for completion (in real tests, you might want to poll)
        import time
        time.sleep(30)
        
        results = self.client.get_batch_results(batch_job.batch_id)
        assert len(results.results) == 2
    
    @pytest.mark.parametrize("model_size", ["tiny", "base", "small"])
    def test_different_models(self, model_size):
        """Test different model sizes."""
        result = self.client.transcribe(
            self.test_audio_file,
            {'model_size': model_size}
        )
        
        assert result.text is not None
        assert result.processing_stats.model_used == model_size
    
    def test_custom_vocabulary(self):
        """Test custom vocabulary feature."""
        custom_vocab = ["Kubernetes", "API", "microservices"]
        
        result = self.client.transcribe(
            self.test_audio_file,
            {
                'model_size': 'medium',
                'custom_vocabulary': custom_vocab,
                'boost_vocabulary_weight': 2.0
            }
        )
        
        assert result.text is not None
        # Check if custom vocabulary was applied (this depends on your test audio)
    
    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        with pytest.raises(Exception):
            self.client.transcribe(
                'nonexistent_file.wav',
                {'model_size': 'medium'}
            )
        
        with pytest.raises(Exception):
            self.client.transcribe(
                self.test_audio_file,
                {'model_size': 'invalid_model'}
            )

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

## 🚀 Production Deployment

### Docker Integration

#### Dockerfile for Python Application
```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "app.py"]
```

#### Docker Compose for Development
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - WHISPER_ADVANCED_API_KEY=${WHISPER_ADVANCED_API_KEY}
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:password@postgres:5432/transcriptions
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - redis
      - postgres
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=transcriptions
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

### Monitoring and Logging

#### Application Monitoring
```python
import logging
import time
from functools import wraps
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
TRANSCRIPTION_REQUESTS = Counter('transcription_requests_total', 'Total transcription requests', ['status'])
TRANSCRIPTION_DURATION = Histogram('transcription_duration_seconds', 'Transcription processing time')
API_ERRORS = Counter('api_errors_total', 'Total API errors', ['error_type'])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def monitor_transcription(func):
    """Decorator to monitor transcription operations."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            TRANSCRIPTION_REQUESTS.labels(status='success').inc()
            duration = time.time() - start_time
            TRANSCRIPTION_DURATION.observe(duration)
            
            logger.info(f"Transcription completed in {duration:.2f}s")
            return result
        except Exception as e:
            TRANSCRIPTION_REQUESTS.labels(status='error').inc()
            API_ERRORS.labels(error_type=type(e).__name__).inc()
            
            logger.error(f"Transcription failed: {str(e)}")
            raise
    return wrapper

# Usage
@monitor_transcription
def transcribe_audio(client, audio_file, config):
    return client.transcribe(audio_file, config)

# Metrics endpoint
from flask import Flask, Response
app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')
```

### Load Balancing and Scaling

#### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whisper-advanced-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: whisper-advanced-app
  template:
    metadata:
      labels:
        app: whisper-advanced-app
    spec:
      containers:
      - name: app
        image: your-registry/whisper-advanced-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: WHISPER_ADVANCED_API_KEY
          valueFrom:
            secretKeyRef:
              name: whisper-secrets
              key: api-key
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: whisper-advanced-service
spec:
  selector:
    app: whisper-advanced-app
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: whisper-advanced-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: whisper-advanced-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 🔍 Troubleshooting

### Common Integration Issues

#### Connection Problems
```python
import requests
from whisper_advanced.exceptions import ConnectionError

def diagnose_connection_issues(client):
    """Diagnose common connection problems."""
    try:
        # Test basic connectivity
        response = requests.get(f"{client.base_url}/health", timeout=10)
        print(f"✓ API endpoint reachable (status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API endpoint")
        print("  - Check internet connection")
        print("  - Verify API URL is correct")
        print("  - Check firewall settings")
        return False
    except requests.exceptions.Timeout:
        print("✗ Connection timeout")
        print("  - Check network latency")
        print("  - Increase timeout settings")
        return False
    
    # Test authentication
    try:
        health = client.health_check()
        print("✓ Authentication successful")
        return True
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        print("  - Verify API key is correct")
        print("  - Check API key permissions")
        return False

# Usage
if not diagnose_connection_issues(client):
    print("Please resolve connection issues before proceeding")
```

#### Performance Debugging
```python
import time
import psutil
import logging

class PerformanceProfiler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def profile_transcription(self, client, audio_file, config):
        """Profile transcription performance."""
        # System metrics before
        process = psutil.Process()
        cpu_before = process.cpu_percent()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        
        try:
            result = client.transcribe(audio_file, config)
            
            # System metrics after
            end_time = time.time()
            cpu_after = process.cpu_percent()
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            
            # Calculate metrics
            processing_time = end_time - start_time
            audio_duration = result.processing_stats.get('audio_duration', 0)
            real_time_factor = processing_time / audio_duration if audio_duration > 0 else 0
            
            # Log performance metrics
            self.logger.info(f"Performance Profile:")
            self.logger.info(f"  Processing time: {processing_time:.2f}s")
            self.logger.info(f"  Audio duration: {audio_duration:.2f}s")
            self.logger.info(f"  Real-time factor: {real_time_factor:.2f}x")
            self.logger.info(f"  CPU usage: {cpu_before:.1f}% -> {cpu_after:.1f}%")
            self.logger.info(f"  Memory usage: {memory_before:.1f}MB -> {memory_after:.1f}MB")
            self.logger.info(f"  Model used: {result.processing_stats.get('model_used', 'unknown')}")
            
            return {
                'processing_time': processing_time,
                'real_time_factor': real_time_factor,
                'cpu_usage_delta': cpu_after - cpu_before,
                'memory_usage_delta': memory_after - memory_before,
                'result': result
            }
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise

# Usage
profiler = PerformanceProfiler()
profile_data = profiler.profile_transcription(
    client, 
    "test_audio.wav", 
    {"model_size": "medium"}
)
```

### Debugging Tools

#### Request/Response Logger
```python
import json
import logging
from datetime import datetime

class APILogger:
    def __init__(self, log_file='api_requests.log'):
        self.logger = logging.getLogger('api_logger')
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_request(self, method, url, headers, data=None):
        """Log API request details."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'request',
            'method': method,
            'url': url,
            'headers': {k: v for k, v in headers.items() if k.lower() != 'authorization'},
            'data_size': len(str(data)) if data else 0
        }
        self.logger.info(json.dumps(log_entry))
    
    def log_response(self, status_code, headers, response_data, processing_time):
        """Log API response details."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'response',
            'status_code': status_code,
            'headers': dict(headers),
            'response_size': len(str(response_data)) if response_data else 0,
            'processing_time': processing_time,
            'success': 200 <= status_code < 300
        }
        self.logger.info(json.dumps(log_entry))

# Integration with client
class DebuggingWhisperClient(WhisperAdvancedClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_logger = APILogger()
    
    def _make_request(self, method, endpoint, **kwargs):
        """Override to add logging."""
        url = f"{self.base_url}/{endpoint}"
        headers = kwargs.get('headers', {})
        data = kwargs.get('data')
        
        # Log request
        self.api_logger.log_request(method, url, headers, data)
        
        # Make request with timing
        start_time = time.time()
        response = super()._make_request(method, endpoint, **kwargs)
        processing_time = time.time() - start_time
        
        # Log response
        self.api_logger.log_response(
            response.status_code,
            response.headers,
            response.text,
            processing_time
        )
        
        return response
```

## 📞 Support and Resources

### Getting Help

- **Documentation**: https://docs.whisper-advanced.com/developers
- **API Reference**: https://api-docs.whisper-advanced.com
- **SDK Repository**: https://github.com/whisper-advanced/sdks
- **Community Forum**: https://community.whisper-advanced.com
- **Stack Overflow**: Tag questions with `whisper-advanced`

### Support Channels

- **Technical Support**: developers@whisper-advanced.com
- **Bug Reports**: bugs@whisper-advanced.com
- **Feature Requests**: features@whisper-advanced.com
- **Security Issues**: security@whisper-advanced.com

### Additional Resources

- **Code Examples**: https://github.com/whisper-advanced/examples
- **Video Tutorials**: https://youtube.com/whisper-advanced-dev
- **Webinars**: Monthly developer sessions
- **Blog**: https://blog.whisper-advanced.com/developers

---

This developer guide provides comprehensive coverage of integrating Whisper Advanced capabilities into your applications. For specific use cases or advanced integration patterns not covered here, please reach out to our developer support team.