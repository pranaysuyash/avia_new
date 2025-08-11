# Whisper Advanced Integration - API Documentation

## 🎯 Overview

The Whisper Advanced Integration API provides powerful speech-to-text capabilities with advanced features including audio preprocessing, custom vocabulary, speaker detection, and comprehensive quality analysis. This RESTful API is built with FastAPI and offers both synchronous and asynchronous processing options.

## 🚀 Quick Start

### Base URL
```
Production: https://your-api-domain.com/api/v1
Development: http://localhost:8000/api/v1
```

### Authentication
All API endpoints require authentication using Bearer tokens:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
     https://your-api-domain.com/api/v1/whisper-advanced/health
```

## 📋 API Endpoints

### 1. Health Check

**GET** `/whisper-advanced/health`

Check the health status of the Whisper Advanced service.

#### Response
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "components": {
      "whisper_transcriber": "operational",
      "openai_api": "available",
      "language_detection": "available",
      "custom_vocabulary": "available"
    },
    "supported_models": 1,
    "supported_languages": 15,
    "max_file_size_mb": 25
  },
  "message": "Whisper advanced service is healthy"
}
```

### 2. Get Available Models

**GET** `/whisper-advanced/models`

Retrieve information about available Whisper models and their capabilities.

#### Response
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "id": "whisper-1",
        "name": "Whisper v1",
        "description": "OpenAI's Whisper model for speech recognition",
        "max_file_size_mb": 25,
        "supported_formats": ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"],
        "features": [
          "Multi-language support",
          "Word-level timestamps",
          "Language detection",
          "Custom prompts",
          "Temperature control"
        ]
      }
    ],
    "supported_languages": [
      {"code": "en", "name": "English"},
      {"code": "es", "name": "Spanish"},
      {"code": "fr", "name": "French"}
    ],
    "response_formats": [
      {
        "format": "json",
        "description": "Detailed JSON response with segments and metadata"
      }
    ]
  }
}
```

### 3. Get Transcription Presets

**GET** `/whisper-advanced/presets`

Get predefined transcription configurations optimized for different use cases.

#### Response
```json
{
  "success": true,
  "data": {
    "presets": [
      {
        "name": "High Accuracy",
        "description": "Maximum accuracy with detailed analysis",
        "config": {
          "model": "whisper-1",
          "temperature": 0.0,
          "enable_language_detection": true,
          "enable_confidence_analysis": true,
          "enable_word_timestamps": true,
          "confidence_threshold": 0.9,
          "chunk_length_s": 30
        }
      },
      {
        "name": "Fast Processing",
        "description": "Optimized for speed with good accuracy",
        "config": {
          "model": "whisper-1",
          "temperature": 0.2,
          "enable_language_detection": false,
          "enable_confidence_analysis": false,
          "enable_word_timestamps": false,
          "confidence_threshold": 0.7,
          "chunk_length_s": 60
        }
      }
    ]
  }
}
```

### 4. Transcribe Audio

**POST** `/whisper-advanced/transcribe`

Transcribe audio files with advanced configuration options.

#### Request Parameters

**Form Data:**
- `audio_file` (file, required): Audio file to transcribe
- `config` (string, required): JSON configuration object
- `custom_vocabulary` (string, optional): JSON custom vocabulary configuration
- `prompt_config` (string, optional): JSON prompt configuration

#### Configuration Object
```json
{
  "model": "whisper-1",
  "language": "en",
  "temperature": 0.0,
  "enable_language_detection": true,
  "enable_confidence_analysis": true,
  "enable_word_timestamps": true,
  "enable_speaker_detection": false,
  "confidence_threshold": 0.8,
  "chunk_length_s": 30
}
```

#### Custom Vocabulary Object
```json
{
  "vocabulary_terms": ["whisper", "transcription", "API"],
  "domain_specific_terms": ["neural", "network", "transformer"],
  "proper_nouns": ["OpenAI", "GPT", "Whisper"],
  "technical_terms": ["endpoint", "authentication", "processing"],
  "boost_factor": 1.5
}
```

#### Prompt Configuration Object
```json
{
  "context_prompt": "This is a technical discussion about AI",
  "style_prompt": "Use formal language",
  "domain_prompt": "Machine learning and AI domain",
  "format_prompt": "Include technical terminology"
}
```

#### Example Request
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "audio_file=@audio.wav" \
  -F 'config={"model":"whisper-1","temperature":0.0,"enable_word_timestamps":true}' \
  https://your-api-domain.com/api/v1/whisper-advanced/transcribe
```

#### Response
```json
{
  "success": true,
  "data": {
    "text": "This is the transcribed text from the audio file.",
    "language": "en",
    "language_confidence": 0.95,
    "segments": [
      {
        "id": 0,
        "start": 0.0,
        "end": 3.0,
        "text": "This is the transcribed text from the audio file.",
        "confidence": 0.95,
        "speaker_id": "speaker_1"
      }
    ],
    "words": [
      {
        "word": "This",
        "start": 0.0,
        "end": 0.3,
        "confidence": 0.98
      }
    ],
    "confidence_analysis": {
      "overall_confidence": 0.95,
      "preprocessing_quality": 0.9,
      "quality_improvement": 0.1
    },
    "processing_time": 1.5,
    "model_used": "whisper-base"
  },
  "message": "Transcription completed successfully"
}
```

### 5. Detect Language

**POST** `/whisper-advanced/detect-language`

Detect the language of an audio file without full transcription.

#### Request Parameters
- `audio_file` (file, required): Audio file for language detection

#### Example Request
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "audio_file=@audio.wav" \
  https://your-api-domain.com/api/v1/whisper-advanced/detect-language
```

#### Response
```json
{
  "success": true,
  "data": {
    "detected_language": "en",
    "confidence": 0.95,
    "alternative_languages": [
      {"es": 0.03},
      {"fr": 0.02}
    ]
  },
  "message": "Language detection completed successfully"
}
```

### 6. Batch Transcribe

**POST** `/whisper-advanced/batch-transcribe`

Process multiple audio files in a single request.

#### Request Parameters
- `files` (array of files, required): Up to 10 audio files
- `config` (string, required): JSON configuration object

#### Example Request
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "files=@audio1.wav" \
  -F "files=@audio2.wav" \
  -F 'config={"model":"whisper-1","temperature":0.0}' \
  https://your-api-domain.com/api/v1/whisper-advanced/batch-transcribe
```

#### Response
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "index": 0,
        "filename": "audio1.wav",
        "status": "success",
        "result": {
          "text": "First file transcription.",
          "language": "en",
          "processing_time": 1.2,
          "word_count": 3,
          "confidence_score": 0.92
        }
      }
    ],
    "summary": {
      "total_files": 2,
      "successful": 2,
      "failed": 0,
      "total_words": 6,
      "average_processing_time": 1.15,
      "total_processing_time": 2.3
    }
  }
}
```

## 🔧 Configuration Options

### Model Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | "whisper-1" | Whisper model to use |
| `language` | string | null | Language code (auto-detect if null) |
| `temperature` | float | 0.0 | Sampling temperature (0.0-1.0) |
| `response_format` | string | "json" | Response format |

### Feature Toggles

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_language_detection` | boolean | true | Enable automatic language detection |
| `enable_confidence_analysis` | boolean | true | Enable confidence scoring |
| `enable_word_timestamps` | boolean | true | Enable word-level timestamps |
| `enable_speaker_detection` | boolean | false | Enable speaker diarization |
| `enable_custom_vocabulary` | boolean | false | Enable custom vocabulary boost |

### Quality Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `confidence_threshold` | float | 0.8 | Minimum confidence threshold (0.0-1.0) |
| `chunk_length_s` | integer | 30 | Audio chunk length in seconds (10-60) |

## 📁 Supported File Formats

### Audio Formats
- **MP3** (.mp3) - Most common format
- **WAV** (.wav) - Uncompressed audio
- **M4A** (.m4a) - Apple audio format
- **FLAC** (.flac) - Lossless compression
- **OGG** (.ogg) - Open source format
- **WEBM** (.webm) - Web audio format
- **AAC** (.aac) - Advanced audio coding

### File Size Limits
- **Single File**: Maximum 25MB per file
- **Batch Processing**: Maximum 10 files, 250MB total

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing token |
| 413 | Payload Too Large - File size exceeds limit |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### Error Response Format
```json
{
  "success": false,
  "error": "Error type",
  "detail": "Detailed error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `FILE_TOO_LARGE` | File exceeds size limit | Use smaller file or compress audio |
| `UNSUPPORTED_FORMAT` | Audio format not supported | Convert to supported format |
| `INVALID_CONFIG` | Configuration validation failed | Check parameter values and types |
| `PROCESSING_FAILED` | Transcription processing error | Retry with different settings |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait and retry with backoff |

## 🔐 Authentication

### API Key Authentication
Include your API key in the Authorization header:

```bash
Authorization: Bearer YOUR_API_TOKEN
```

### Rate Limiting
- **Free Tier**: 100 requests per hour
- **Pro Tier**: 1000 requests per hour
- **Enterprise**: Custom limits

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 📊 Response Metadata

### Processing Information
All successful responses include processing metadata:

```json
{
  "processing_time": 1.5,
  "model_used": "whisper-base",
  "config_used": {...},
  "quality_metrics": {
    "overall_confidence": 0.95,
    "preprocessing_quality": 0.9,
    "quality_improvement": 0.1
  }
}
```

### Confidence Scoring
Confidence scores are provided at multiple levels:
- **Overall**: Average confidence for entire transcription
- **Segment**: Confidence for each time segment
- **Word**: Individual word confidence (when enabled)

## 🔄 Best Practices

### Audio Quality
1. **Sample Rate**: 16kHz or higher recommended
2. **Format**: WAV or FLAC for best quality
3. **Noise**: Minimize background noise
4. **Volume**: Consistent audio levels

### Configuration Tips
1. **Temperature**: Use 0.0 for deterministic results, higher for creativity
2. **Language**: Specify language when known for better accuracy
3. **Chunks**: Shorter chunks (20-30s) for better speaker detection
4. **Vocabulary**: Include domain-specific terms for technical content

### Performance Optimization
1. **Batch Processing**: Use batch endpoint for multiple files
2. **Preprocessing**: Let the API handle audio preprocessing
3. **Caching**: Cache results for repeated processing
4. **Async**: Use async processing for large files

## 📝 Code Examples

### Python Example
```python
import requests

def transcribe_audio(file_path, api_token):
    url = "https://your-api-domain.com/api/v1/whisper-advanced/transcribe"
    
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    
    config = {
        "model": "whisper-1",
        "temperature": 0.0,
        "enable_word_timestamps": True,
        "enable_confidence_analysis": True
    }
    
    with open(file_path, 'rb') as audio_file:
        files = {"audio_file": audio_file}
        data = {"config": json.dumps(config)}
        
        response = requests.post(url, headers=headers, files=files, data=data)
        
    if response.status_code == 200:
        return response.json()["data"]
    else:
        raise Exception(f"API Error: {response.json()}")

# Usage
result = transcribe_audio("audio.wav", "your-api-token")
print(result["text"])
```

### JavaScript Example
```javascript
async function transcribeAudio(file, apiToken) {
    const formData = new FormData();
    formData.append('audio_file', file);
    formData.append('config', JSON.stringify({
        model: 'whisper-1',
        temperature: 0.0,
        enable_word_timestamps: true,
        enable_confidence_analysis: true
    }));

    const response = await fetch('https://your-api-domain.com/api/v1/whisper-advanced/transcribe', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${apiToken}`
        },
        body: formData
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
    }

    const result = await response.json();
    return result.data;
}

// Usage
const result = await transcribeAudio(audioFile, 'your-api-token');
console.log(result.text);
```

### cURL Example
```bash
#!/bin/bash

API_TOKEN="your-api-token"
AUDIO_FILE="audio.wav"
API_URL="https://your-api-domain.com/api/v1/whisper-advanced/transcribe"

CONFIG='{
  "model": "whisper-1",
  "temperature": 0.0,
  "enable_word_timestamps": true,
  "enable_confidence_analysis": true,
  "enable_speaker_detection": true
}'

curl -X POST \
  -H "Authorization: Bearer $API_TOKEN" \
  -F "audio_file=@$AUDIO_FILE" \
  -F "config=$CONFIG" \
  "$API_URL" | jq '.'
```

## 🔍 Troubleshooting

### Common Issues

1. **File Upload Fails**
   - Check file size (max 25MB)
   - Verify file format is supported
   - Ensure proper form-data encoding

2. **Low Confidence Scores**
   - Improve audio quality
   - Use appropriate language setting
   - Add custom vocabulary for technical terms

3. **Slow Processing**
   - Use smaller chunk sizes
   - Disable unnecessary features
   - Consider batch processing for multiple files

4. **Authentication Errors**
   - Verify API token is valid
   - Check token hasn't expired
   - Ensure proper Authorization header format

### Support
For additional support:
- Email: support@your-domain.com
- Documentation: https://docs.your-domain.com
- Status Page: https://status.your-domain.com