# Whisper Advanced Integration - API Documentation

## 🎯 Overview

The Whisper Advanced Integration API provides enterprise-grade speech-to-text transcription with advanced configuration options, audio preprocessing, speaker diarization, and comprehensive quality controls. Built on OpenAI's Whisper models with extensive customization capabilities.

## 🚀 Quick Start

### Base URL
```
Production: https://api.your-domain.com/v1
Development: http://localhost:8000/v1
```

### Authentication
All endpoints require Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
     https://api.your-domain.com/v1/whisper-advanced/health
```

### Basic Example

```python
import requests
import json

# Configuration for high-accuracy transcription
config = {
    "model_size": "large",
    "language": "en",
    "temperature": 0.0,
    "enable_word_timestamps": True,
    "enable_vad": True,
    "enable_diarization": True,
    "max_speakers": 3
}

# Upload and transcribe
with open("meeting.wav", "rb") as f:
    files = {"audio_file": f}
    data = {"config": json.dumps(config)}
    
    response = requests.post(
        "https://api.your-domain.com/v1/whisper-advanced/transcribe",
        headers={"Authorization": "Bearer YOUR_TOKEN"},
        files=files,
        data=data
    )

result = response.json()
print(f"Transcript: {result['data']['text']}")
```

## 📋 API Endpoints

### 1. Health Check

**GET** `/whisper-advanced/health`

Check service health and capabilities.

#### Response
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "components": {
      "whisper_processor": "operational",
      "audio_preprocessor": "operational", 
      "vad_processor": "operational",
      "speaker_diarization": "operational",
      "model_manager": "operational"
    },
    "available_models": ["tiny", "base", "small", "medium", "large"],
    "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar", "hi", "tr", "pl", "nl"],
    "max_file_size_mb": 25,
    "max_duration_minutes": 180,
    "features": {
      "voice_activity_detection": true,
      "speaker_diarization": true,
      "real_time_streaming": true,
      "batch_processing": true,
      "custom_vocabulary": true
    }
  },
  "message": "Whisper Advanced service is healthy"
}
```

### 2. Model Information

**GET** `/whisper-advanced/models`

Get detailed information about available Whisper models.

#### Response
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "name": "tiny",
        "size_mb": 39,
        "parameters": "39M",
        "relative_speed": 32,
        "english_only": false,
        "multilingual": true,
        "recommended_use": "Real-time processing, low-resource environments"
      },
      {
        "name": "base",
        "size_mb": 74,
        "parameters": "74M", 
        "relative_speed": 16,
        "english_only": false,
        "multilingual": true,
        "recommended_use": "Balanced speed and accuracy"
      },
      {
        "name": "small",
        "size_mb": 244,
        "parameters": "244M",
        "relative_speed": 6,
        "english_only": false,
        "multilingual": true,
        "recommended_use": "Good accuracy for most use cases"
      },
      {
        "name": "medium",
        "size_mb": 769,
        "parameters": "769M",
        "relative_speed": 2,
        "english_only": false,
        "multilingual": true,
        "recommended_use": "High accuracy for professional use"
      },
      {
        "name": "large",
        "size_mb": 1550,
        "parameters": "1550M",
        "relative_speed": 1,
        "english_only": false,
        "multilingual": true,
        "recommended_use": "Maximum accuracy for critical applications"
      }
    ]
  }
}
```

### 3. Configuration Presets

**GET** `/whisper-advanced/presets`

Get predefined configuration presets for common use cases.

#### Response
```json
{
  "success": true,
  "data": {
    "presets": {
      "meeting": {
        "name": "Meeting Transcription",
        "description": "Optimized for multi-speaker business meetings",
        "config": {
          "model_size": "medium",
          "temperature": 0.0,
          "enable_vad": true,
          "enable_diarization": true,
          "max_speakers": 8,
          "enable_word_timestamps": true,
          "compression_ratio_threshold": 2.4,
          "logprob_threshold": -1.0,
          "no_speech_threshold": 0.6
        }
      },
      "interview": {
        "name": "Interview Recording",
        "description": "High accuracy for 1-on-1 interviews",
        "config": {
          "model_size": "large",
          "temperature": 0.0,
          "enable_vad": true,
          "enable_diarization": true,
          "max_speakers": 2,
          "enable_word_timestamps": true,
          "beam_size": 5,
          "best_of": 5
        }
      },
      "podcast": {
        "name": "Podcast Production",
        "description": "Optimized for long-form content with multiple speakers",
        "config": {
          "model_size": "medium",
          "temperature": 0.2,
          "enable_vad": true,
          "enable_diarization": true,
          "max_speakers": 4,
          "enable_word_timestamps": true,
          "condition_on_previous_text": true
        }
      },
      "lecture": {
        "name": "Educational Content",
        "description": "Single speaker educational content",
        "config": {
          "model_size": "medium",
          "temperature": 0.0,
          "enable_vad": true,
          "enable_diarization": false,
          "enable_word_timestamps": true,
          "initial_prompt": "This is an educational lecture."
        }
      },
      "realtime": {
        "name": "Real-time Processing",
        "description": "Fast processing for live transcription",
        "config": {
          "model_size": "base",
          "temperature": 0.0,
          "enable_vad": true,
          "enable_diarization": false,
          "beam_size": 1,
          "enable_word_timestamps": false
        }
      }
    }
  }
}
```

### 4. Transcribe Audio

**POST** `/whisper-advanced/transcribe`

Transcribe audio file with advanced configuration options.

#### Request Parameters

**Form Data:**
- `audio_file` (file, required): Audio file to transcribe
- `config` (string, required): JSON configuration object

**Configuration Object:**
```json
{
  "model_size": "medium",
  "language": "en",
  "task": "transcribe",
  "temperature": 0.0,
  "best_of": 1,
  "beam_size": 1,
  "patience": 1.0,
  "length_penalty": 1.0,
  "suppress_tokens": [-1],
  "initial_prompt": null,
  "condition_on_previous_text": true,
  "fp16": true,
  "compression_ratio_threshold": 2.4,
  "logprob_threshold": -1.0,
  "no_speech_threshold": 0.6,
  "enable_word_timestamps": true,
  "prepend_punctuations": "\"'"¿([{-",
  "append_punctuations": "\"'.。,，!！?？:：")]}、",
  "enable_vad": true,
  "vad_threshold": 0.5,
  "enable_diarization": true,
  "max_speakers": 5,
  "enable_audio_enhancement": true,
  "noise_reduction_strength": 0.5,
  "normalize_audio": true,
  "custom_vocabulary": [],
  "boost_vocabulary_weight": 1.5
}
```

#### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_size` | string | "base" | Whisper model size: tiny, base, small, medium, large |
| `language` | string | null | Language code (auto-detect if null) |
| `task` | string | "transcribe" | Task type: "transcribe" or "translate" |
| `temperature` | float | 0.0 | Sampling temperature (0.0-1.0) |
| `best_of` | int | 1 | Number of candidates to generate |
| `beam_size` | int | 1 | Beam search size |
| `patience` | float | 1.0 | Beam search patience |
| `length_penalty` | float | 1.0 | Length penalty for beam search |
| `suppress_tokens` | array | [-1] | Token IDs to suppress |
| `initial_prompt` | string | null | Initial prompt for conditioning |
| `condition_on_previous_text` | bool | true | Use previous text for context |
| `fp16` | bool | true | Use half-precision floating point |
| `compression_ratio_threshold` | float | 2.4 | Compression ratio threshold |
| `logprob_threshold` | float | -1.0 | Log probability threshold |
| `no_speech_threshold` | float | 0.6 | No speech probability threshold |
| `enable_word_timestamps` | bool | true | Generate word-level timestamps |
| `prepend_punctuations` | string | "\"'"¿([{-" | Punctuation to prepend |
| `append_punctuations` | string | "\"'.。,，!！?？:：")]}、" | Punctuation to append |
| `enable_vad` | bool | false | Enable voice activity detection |
| `vad_threshold` | float | 0.5 | VAD sensitivity threshold |
| `enable_diarization` | bool | false | Enable speaker diarization |
| `max_speakers` | int | 5 | Maximum number of speakers |
| `enable_audio_enhancement` | bool | false | Enable audio preprocessing |
| `noise_reduction_strength` | float | 0.5 | Noise reduction strength (0.0-1.0) |
| `normalize_audio` | bool | false | Normalize audio volume |
| `custom_vocabulary` | array | [] | Custom vocabulary words |
| `boost_vocabulary_weight` | float | 1.5 | Weight boost for custom vocabulary |

#### Example Request

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_file=@meeting.wav" \
  -F 'config={"model_size":"medium","enable_diarization":true,"max_speakers":3}' \
  https://api.your-domain.com/v1/whisper-advanced/transcribe
```

#### Response
```json
{
  "success": true,
  "data": {
    "text": "Hello, welcome to today's meeting. Let's start with the quarterly review.",
    "language": "en",
    "language_detection": {
      "detected_language": "en",
      "language_probability": 0.99,
      "all_language_probs": {
        "en": 0.99,
        "es": 0.005,
        "fr": 0.003
      }
    },
    "segments": [
      {
        "id": 0,
        "seek": 0,
        "start": 0.0,
        "end": 3.5,
        "text": "Hello, welcome to today's meeting.",
        "tokens": [50364, 2425, 11, 2928, 281, 965, 311, 3440, 13, 50539],
        "temperature": 0.0,
        "avg_logprob": -0.15,
        "compression_ratio": 1.8,
        "no_speech_prob": 0.01,
        "confidence": 0.95,
        "speaker_id": "SPEAKER_00",
        "words": [
          {
            "word": "Hello",
            "start": 0.0,
            "end": 0.5,
            "confidence": 0.98
          },
          {
            "word": "welcome",
            "start": 0.6,
            "end": 1.1,
            "confidence": 0.96
          }
        ]
      }
    ],
    "speaker_diarization": {
      "num_speakers": 2,
      "speakers": [
        {
          "speaker_id": "SPEAKER_00",
          "total_speaking_time": 45.2,
          "speaking_percentage": 65.3,
          "segments_count": 12
        },
        {
          "speaker_id": "SPEAKER_01", 
          "total_speaking_time": 24.1,
          "speaking_percentage": 34.7,
          "segments_count": 8
        }
      ],
      "speaker_timeline": [
        {
          "start": 0.0,
          "end": 3.5,
          "speaker_id": "SPEAKER_00"
        },
        {
          "start": 3.8,
          "end": 7.2,
          "speaker_id": "SPEAKER_01"
        }
      ]
    },
    "audio_quality": {
      "signal_to_noise_ratio": 18.5,
      "dynamic_range": 45.2,
      "clipping_detected": false,
      "background_noise_level": 0.02,
      "speech_clarity_score": 0.87,
      "recommended_preprocessing": []
    },
    "processing_stats": {
      "processing_time": 12.3,
      "model_used": "medium",
      "audio_duration": 69.2,
      "real_time_factor": 0.18,
      "word_count": 156,
      "character_count": 892,
      "segments_count": 20,
      "average_confidence": 0.91
    },
    "config_used": {
      "model_size": "medium",
      "enable_diarization": true,
      "max_speakers": 3
    }
  },
  "message": "Transcription completed successfully"
}
```

### 5. Language Detection

**POST** `/whisper-advanced/detect-language`

Detect the language of audio content without full transcription.

#### Request Parameters
- `audio_file` (file, required): Audio file for language detection
- `sample_duration` (int, optional): Duration in seconds to analyze (default: 30)

#### Example Request
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_file=@unknown_language.wav" \
  -F "sample_duration=15" \
  https://api.your-domain.com/v1/whisper-advanced/detect-language
```

#### Response
```json
{
  "success": true,
  "data": {
    "detected_language": "es",
    "language_name": "Spanish",
    "confidence": 0.94,
    "all_language_probs": {
      "es": 0.94,
      "en": 0.03,
      "pt": 0.02,
      "fr": 0.01
    },
    "sample_duration": 15.0,
    "processing_time": 2.1
  },
  "message": "Language detection completed"
}
```

### 6. Batch Transcription

**POST** `/whisper-advanced/batch-transcribe`

Process multiple audio files in a single request.

#### Request Parameters
- `audio_files` (files, required): Multiple audio files
- `config` (string, required): JSON configuration object
- `webhook_url` (string, optional): URL for completion notification

#### Example Request
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_files=@file1.wav" \
  -F "audio_files=@file2.wav" \
  -F "audio_files=@file3.wav" \
  -F 'config={"model_size":"medium","enable_diarization":true}' \
  -F "webhook_url=https://your-app.com/webhook" \
  https://api.your-domain.com/v1/whisper-advanced/batch-transcribe
```

#### Response
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_abc123",
    "total_files": 3,
    "estimated_processing_time": 180,
    "status": "queued",
    "files": [
      {
        "file_id": "file_001",
        "filename": "file1.wav",
        "status": "queued",
        "duration": 45.2
      },
      {
        "file_id": "file_002", 
        "filename": "file2.wav",
        "status": "queued",
        "duration": 62.8
      },
      {
        "file_id": "file_003",
        "filename": "file3.wav", 
        "status": "queued",
        "duration": 38.1
      }
    ],
    "webhook_url": "https://your-app.com/webhook"
  },
  "message": "Batch transcription job created"
}
```

### 7. Batch Status

**GET** `/whisper-advanced/batch/{batch_id}/status`

Check the status of a batch transcription job.

#### Response
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_abc123",
    "status": "processing",
    "progress": {
      "completed": 1,
      "processing": 1,
      "queued": 1,
      "failed": 0,
      "total": 3,
      "percentage": 33.3
    },
    "files": [
      {
        "file_id": "file_001",
        "filename": "file1.wav",
        "status": "completed",
        "processing_time": 8.2,
        "result_available": true
      },
      {
        "file_id": "file_002",
        "filename": "file2.wav", 
        "status": "processing",
        "progress_percentage": 45
      },
      {
        "file_id": "file_003",
        "filename": "file3.wav",
        "status": "queued"
      }
    ],
    "estimated_completion": "2024-01-15T14:30:00Z"
  }
}
```

### 8. Batch Results

**GET** `/whisper-advanced/batch/{batch_id}/results`

Retrieve results from a completed batch transcription.

#### Response
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_abc123",
    "status": "completed",
    "results": [
      {
        "file_id": "file_001",
        "filename": "file1.wav",
        "status": "completed",
        "transcription": {
          "text": "This is the transcribed text...",
          "segments": [...],
          "speaker_diarization": {...},
          "processing_stats": {...}
        }
      }
    ],
    "summary": {
      "total_files": 3,
      "successful": 3,
      "failed": 0,
      "total_duration": 146.1,
      "total_processing_time": 26.4,
      "average_confidence": 0.89
    }
  }
}
```

## 🔧 Configuration Guide

### Model Selection Guide

| Use Case | Recommended Model | Reasoning |
|----------|------------------|-----------|
| Real-time transcription | tiny, base | Fast processing, low latency |
| Meeting recordings | medium, large | Good accuracy for business content |
| Podcast production | medium, large | High quality for published content |
| Academic lectures | medium, large | Technical vocabulary accuracy |
| Phone calls | base, small | Optimized for compressed audio |
| Interviews | large | Maximum accuracy for important content |

### Audio Quality Optimization

```json
{
  "enable_audio_enhancement": true,
  "noise_reduction_strength": 0.7,
  "normalize_audio": true,
  "enable_vad": true,
  "vad_threshold": 0.4
}
```

### Speaker Diarization Settings

```json
{
  "enable_diarization": true,
  "max_speakers": 4,
  "speaker_clustering_threshold": 0.7,
  "min_speaker_duration": 1.0
}
```

### Custom Vocabulary

```json
{
  "custom_vocabulary": [
    "API", "Kubernetes", "microservices", 
    "PostgreSQL", "Redis", "FastAPI"
  ],
  "boost_vocabulary_weight": 2.0
}
```

## 📊 Response Formats

### Export Formats

The API supports multiple export formats for transcription results:

#### JSON (Default)
Complete structured data with all metadata.

#### SRT (SubRip)
```
1
00:00:00,000 --> 00:00:03,500
Hello, welcome to today's meeting.

2
00:00:03,800 --> 00:00:07,200
Thank you for joining us today.
```

#### VTT (WebVTT)
```
WEBVTT

00:00:00.000 --> 00:00:03.500
Hello, welcome to today's meeting.

00:00:03.800 --> 00:00:07.200
Thank you for joining us today.
```

#### TXT (Plain Text)
```
Hello, welcome to today's meeting. Thank you for joining us today.
```

## ⚠️ Error Handling

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "INVALID_AUDIO_FORMAT",
    "message": "Unsupported audio format. Please use WAV, MP3, M4A, FLAC, or OGG.",
    "details": {
      "supported_formats": ["wav", "mp3", "m4a", "flac", "ogg"],
      "received_format": "avi"
    }
  },
  "request_id": "req_abc123"
}
```

### Common Error Codes

| Code | HTTP Status | Description | Solution |
|------|-------------|-------------|----------|
| `INVALID_AUDIO_FORMAT` | 400 | Unsupported file format | Use supported formats |
| `FILE_TOO_LARGE` | 400 | File exceeds size limit | Reduce file size or split |
| `AUDIO_TOO_LONG` | 400 | Audio exceeds duration limit | Split into shorter segments |
| `INVALID_CONFIG` | 400 | Invalid configuration parameters | Check parameter values |
| `MODEL_UNAVAILABLE` | 503 | Requested model not available | Try smaller model or retry |
| `PROCESSING_TIMEOUT` | 504 | Processing took too long | Retry with faster settings |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Wait and retry |
| `INSUFFICIENT_CREDITS` | 402 | Not enough API credits | Add credits to account |

## 🔒 Authentication & Rate Limiting

### API Key Management
- Generate API keys in your dashboard
- Include in Authorization header: `Bearer YOUR_API_KEY`
- Keys can be scoped to specific endpoints
- Monitor usage in real-time

### Rate Limits
- **Free Tier**: 100 requests/hour, 10 concurrent
- **Pro Tier**: 1000 requests/hour, 50 concurrent  
- **Enterprise**: Custom limits

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
X-RateLimit-Retry-After: 3600
```

## 📈 Best Practices

### Performance Optimization

1. **Choose appropriate model size**
   - Use smaller models for real-time processing
   - Use larger models for maximum accuracy

2. **Enable VAD for noisy audio**
   - Reduces processing time
   - Improves accuracy by filtering silence

3. **Use batch processing for multiple files**
   - More efficient than individual requests
   - Better resource utilization

4. **Configure appropriate thresholds**
   - Adjust based on audio quality
   - Fine-tune for your specific use case

### Quality Improvement

1. **Audio preprocessing**
   - Enable noise reduction for poor quality audio
   - Normalize volume for consistent results

2. **Custom vocabulary**
   - Add domain-specific terms
   - Include proper nouns and technical terms

3. **Initial prompts**
   - Provide context for better accuracy
   - Include speaker names or topic information

### Cost Optimization

1. **Model selection**
   - Use smallest model that meets accuracy needs
   - Consider processing time vs. accuracy trade-offs

2. **Audio preprocessing**
   - Pre-process audio to reduce file size
   - Remove silence to reduce processing time

3. **Batch processing**
   - Process multiple files together
   - Reduces per-request overhead

## 🔗 SDKs and Libraries

### Python SDK
```bash
pip install whisper-advanced-client
```

```python
from whisper_advanced import WhisperAdvancedClient

client = WhisperAdvancedClient(api_key="your_api_key")
result = client.transcribe("audio.wav", model_size="medium")
```

### JavaScript SDK
```bash
npm install whisper-advanced-js
```

```javascript
import { WhisperAdvancedClient } from 'whisper-advanced-js';

const client = new WhisperAdvancedClient('your_api_key');
const result = await client.transcribe('audio.wav', { model_size: 'medium' });
```

## 📞 Support

- **Documentation**: https://docs.whisper-advanced.com
- **API Status**: https://status.whisper-advanced.com  
- **Support Email**: support@whisper-advanced.com
- **Community Forum**: https://community.whisper-advanced.com

## 📝 Changelog

### v2.1.0 (Latest)
- Added custom vocabulary support
- Improved speaker diarization accuracy
- Enhanced audio preprocessing pipeline
- Added batch processing webhooks

### v2.0.0
- Major API redesign with advanced configuration
- Added speaker diarization
- Implemented voice activity detection
- Enhanced error handling and recovery

### v1.5.0
- Added real-time streaming support
- Improved language detection
- Added audio quality assessment
- Performance optimizations