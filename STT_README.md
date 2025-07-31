# Speech-to-Text (STT) Module

## Overview

The STT module provides robust speech-to-text transcription capabilities with automatic fallback between OpenAI Whisper API and local Whisper models. It's designed for high reliability with comprehensive error handling and retry logic.

## Features

- **Dual Processing Modes**: OpenAI Whisper API (primary) with local Whisper model fallback
- **Automatic Retry Logic**: Exponential backoff for API failures and rate limits
- **Confidence Scoring**: Quality assessment for transcription results
- **Timestamped Transcription**: Word-level timestamps for advanced features
- **Comprehensive Error Handling**: User-friendly error messages and graceful degradation
- **Multiple Model Sizes**: Support for different local Whisper model sizes (tiny, base, small, medium, large)

## Installation

```bash
pip install openai openai-whisper numpy
```

## Environment Setup

Set your OpenAI API key in your environment:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or use a `.env` file:

```
OPENAI_API_KEY=your-api-key-here
```

## Usage

### Basic Transcription

```python
from stt import transcribe

# Transcribe with API (fallback to local if API fails)
text = transcribe("audio_file.wav", use_api=True)
print(f"Transcription: {text}")

# Use local model only
text = transcribe("audio_file.wav", use_api=False)
print(f"Local transcription: {text}")
```

### Detailed Transcription

```python
from stt import transcribe_detailed

# Get detailed results with metadata
result = transcribe_detailed("audio_file.wav", use_api=True, model_size="base")
print(f"Text: {result.text}")
print(f"Confidence: {result.confidence:.3f}")
print(f"Processing time: {result.processing_time:.2f}s")
print(f"Model used: {result.model_used}")
print(f"Language: {result.language}")
print(f"Word count: {result.word_count()}")
```

### Timestamped Transcription

```python
from stt import transcribe_with_timestamps

# Get transcription with word-level timestamps
segments = transcribe_with_timestamps("audio_file.wav")
for segment in segments:
    print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s]: {segment['text']}")
    if 'words' in segment:
        for word in segment['words']:
            print(f"  {word['word']} ({word['start']:.2f}s - {word['end']:.2f}s)")
```

### Confidence Assessment

```python
from stt import get_transcription_confidence

# Get confidence score for transcription quality
confidence = get_transcription_confidence("audio_file.wav")
print(f"Transcription confidence: {confidence:.3f}")
```

## API Reference

### Functions

#### `transcribe(audio_path: str, use_api: bool = True) -> str`

Basic transcription function that returns text only.

**Parameters:**
- `audio_path`: Path to audio file
- `use_api`: Whether to try API first (True) or use local model (False)

**Returns:** Transcribed text as string

#### `transcribe_detailed(audio_path: str, use_api: bool = True, model_size: str = "base") -> TranscriptionResult`

Detailed transcription with metadata.

**Parameters:**
- `audio_path`: Path to audio file
- `use_api`: Whether to try API first
- `model_size`: Local model size ('tiny', 'base', 'small', 'medium', 'large')

**Returns:** `TranscriptionResult` object with detailed metadata

#### `transcribe_with_timestamps(audio_path: str) -> List[Dict]`

Transcription with word-level timestamps.

**Parameters:**
- `audio_path`: Path to audio file

**Returns:** List of dictionaries with text, start, and end timestamps

#### `get_transcription_confidence(audio_path: str) -> float`

Assess transcription quality confidence.

**Parameters:**
- `audio_path`: Path to audio file

**Returns:** Confidence score between 0.0 and 1.0

### Data Classes

#### `TranscriptionResult`

```python
@dataclass
class TranscriptionResult:
    text: str                    # Transcribed text
    confidence: float            # Confidence score (0.0-1.0)
    processing_time: float       # Processing time in seconds
    model_used: str             # Model identifier
    language: str = "en"        # Detected language
    
    def word_count(self) -> int:
        """Return word count of transcribed text"""
```

### Exception Classes

#### `TranscriptionError`

Custom exception for transcription-related errors.

```python
class TranscriptionError(Exception):
    def __init__(self, message: str, error_code: str, user_message: str):
        self.message = message          # Technical error message
        self.error_code = error_code    # Error code for programmatic handling
        self.user_message = user_message # User-friendly error message
```

## Error Handling

The module provides comprehensive error handling with specific error codes:

- `FILE_NOT_FOUND`: Audio file doesn't exist
- `API_CLIENT_ERROR`: OpenAI API client not configured
- `RATE_LIMIT_ERROR`: API rate limit exceeded
- `API_ERROR`: General API error
- `LOCAL_MODEL_ERROR`: Local model loading failed
- `LOCAL_TRANSCRIPTION_ERROR`: Local transcription failed
- `TIMESTAMP_TRANSCRIPTION_ERROR`: Timestamped transcription failed

### Graceful Degradation

1. **API Failure → Local Fallback**: If API transcription fails, automatically falls back to local model
2. **Rate Limiting**: Implements exponential backoff with configurable retry attempts
3. **Model Size Fallback**: Can automatically try smaller models if larger ones fail to load

## Performance Considerations

### API vs Local Models

| Aspect | OpenAI API | Local Models |
|--------|------------|--------------|
| Speed | Fast (cloud processing) | Slower (local processing) |
| Accuracy | High | Good (model-dependent) |
| Cost | Per-usage pricing | Free after download |
| Privacy | Data sent to OpenAI | Fully local |
| Offline | Requires internet | Works offline |

### Model Size Comparison

| Model | Size | Speed | Accuracy | Memory |
|-------|------|-------|----------|---------|
| tiny | 39 MB | Fastest | Lower | ~1 GB |
| base | 74 MB | Fast | Good | ~1 GB |
| small | 244 MB | Medium | Better | ~2 GB |
| medium | 769 MB | Slow | High | ~5 GB |
| large | 1550 MB | Slowest | Highest | ~10 GB |

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest test_stt.py -v

# Run with coverage
python -m pytest test_stt.py --cov=stt

# Run integration tests
python -m pytest test_stt.py -m integration

# Run demo
python demo_stt.py
```

## Troubleshooting

### Common Issues

1. **"No module named 'whisper'"**
   ```bash
   pip install openai-whisper
   ```

2. **"OPENAI_API_KEY not found"**
   - Set environment variable or add to `.env` file
   - Module will fall back to local model automatically

3. **"Failed to load local Whisper model"**
   - Ensure sufficient disk space (models are 39MB-1.5GB)
   - Check internet connection for initial model download
   - Try smaller model size

4. **"Rate limit exceeded"**
   - Wait and retry (automatic exponential backoff)
   - Consider using local model for high-volume processing

5. **Poor transcription quality**
   - Check audio quality (16kHz mono WAV recommended)
   - Try larger local model size
   - Use API for better accuracy

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your transcription code here
```

## Integration Examples

### Streamlit Integration

```python
import streamlit as st
from stt import transcribe, TranscriptionError

uploaded_file = st.file_uploader("Upload Audio", type=['wav', 'mp3'])
if uploaded_file and st.button("Transcribe"):
    try:
        with st.spinner("Transcribing..."):
            text = transcribe(uploaded_file.name)
        st.success("Transcription completed!")
        st.text_area("Result", text, height=200)
    except TranscriptionError as e:
        st.error(f"Transcription failed: {e.user_message}")
```

### Batch Processing

```python
import os
from stt import transcribe_detailed, TranscriptionError

def batch_transcribe(audio_dir: str, output_dir: str):
    """Transcribe all audio files in a directory"""
    for filename in os.listdir(audio_dir):
        if filename.endswith(('.wav', '.mp3', '.m4a')):
            audio_path = os.path.join(audio_dir, filename)
            try:
                result = transcribe_detailed(audio_path, use_api=True)
                
                # Save transcription
                output_path = os.path.join(output_dir, f"{filename}.txt")
                with open(output_path, 'w') as f:
                    f.write(result.text)
                
                print(f"✓ {filename}: {result.word_count()} words, "
                      f"{result.confidence:.3f} confidence")
                      
            except TranscriptionError as e:
                print(f"✗ {filename}: {e.user_message}")
```

## Contributing

When contributing to the STT module:

1. **Add tests** for new functionality in `test_stt.py`
2. **Update documentation** for API changes
3. **Follow error handling patterns** with proper exception types
4. **Test both API and local model paths**
5. **Consider performance implications** of changes

## License

This module is part of the Audio/Video Transcription App project.