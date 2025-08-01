# Error Handling Guide

This guide explains the comprehensive error handling system implemented in the Audio/Video Transcription App and provides troubleshooting steps for common issues.

## Error Categories

### API Errors
These errors occur when external services (OpenAI, ElevenLabs) are unavailable or misconfigured.

#### Common API Errors:
- **API_KEY_MISSING**: API key not configured
- **API_RATE_LIMIT**: Too many requests sent
- **API_QUOTA_EXCEEDED**: Account billing/quota issues
- **API_SERVICE_UNAVAILABLE**: Service temporarily down
- **API_AUTHENTICATION_ERROR**: Invalid API key

#### Solutions:
1. **Check API Key Configuration**:
   - Verify `.env` file contains correct API keys
   - Ensure no extra spaces or quotes around keys
   - Restart the application after updating keys

2. **Rate Limit Issues**:
   - Wait a few minutes before retrying
   - Consider upgrading your API plan
   - Use offline mode when available

3. **Quota/Billing Issues**:
   - Check your API account billing status
   - Add credits to your account
   - Monitor usage in your API dashboard

### File Processing Errors
These errors occur when there are issues with uploaded files.

#### Common File Errors:
- **FILE_NOT_FOUND**: File doesn't exist or path is incorrect
- **FILE_TOO_LARGE**: File exceeds size limits
- **FILE_CORRUPTED**: File is damaged or unreadable
- **FILE_UNSUPPORTED_FORMAT**: File format not supported
- **FILE_PERMISSION_ERROR**: Cannot access file

#### Solutions:
1. **File Size Issues**:
   - Compress large files before uploading
   - Split long recordings into smaller segments
   - Current limit: 100MB (configurable)

2. **Format Issues**:
   - Supported formats: MP3, WAV, MP4, M4A
   - Convert unsupported formats using tools like FFmpeg
   - Ensure file extensions match actual format

3. **Corrupted Files**:
   - Try re-uploading the file
   - Check original file integrity
   - Convert to a different format

### Media Processing Errors
These errors occur during audio/video processing with FFmpeg.

#### Common Media Errors:
- **MEDIA_EXTRACTION_ERROR**: Cannot extract audio from video
- **MEDIA_CONVERSION_ERROR**: Format conversion failed
- **FFMPEG_ERROR**: FFmpeg processing failed

#### Solutions:
1. **Audio Extraction Issues**:
   - Ensure video file contains audio track
   - Try different video format
   - Check video file integrity

2. **FFmpeg Issues**:
   - Ensure FFmpeg is properly installed
   - Check system permissions
   - Try simpler file formats

### Transcription Errors
These errors occur during speech-to-text processing.

#### Common Transcription Errors:
- **TRANSCRIPTION_FAILED**: General transcription failure
- **LOCAL_MODEL_ERROR**: Offline model issues
- **TRANSCRIPTION_TIMEOUT**: Processing took too long

#### Solutions:
1. **API Transcription Issues**:
   - Switch to offline mode
   - Check internet connection
   - Verify OpenAI API status

2. **Local Model Issues**:
   - Restart the application
   - Check available memory/disk space
   - Reinstall whisper: `pip install openai-whisper`

### Entity Recognition Errors
These errors occur during named entity extraction.

#### Common NER Errors:
- **NER_MODEL_ERROR**: Language model failed to load
- **NER_PROCESSING_ERROR**: Entity extraction failed
- **NER_INVALID_INPUT**: Input text issues

#### Solutions:
1. **spaCy Model Issues**:
   - Install English model: `python -m spacy download en_core_web_sm`
   - Switch to Advanced (AI) mode
   - Restart application

2. **Advanced NER Issues**:
   - Switch to Basic (spaCy) mode
   - Check OpenAI API configuration
   - Break long texts into smaller chunks

### Text-to-Speech Errors
These errors occur during speech synthesis.

#### Common TTS Errors:
- **TTS_SYNTHESIS_ERROR**: Speech generation failed
- **TTS_TEXT_TOO_LONG**: Text exceeds length limits
- **TTS_VOICE_ERROR**: Voice configuration issues

#### Solutions:
1. **Synthesis Issues**:
   - Check ElevenLabs API key
   - Verify account has sufficient credits
   - Try different voice settings

2. **Text Length Issues**:
   - Break long texts into smaller chunks
   - Current limit: 5000 characters
   - Remove unnecessary content

### Network Errors
These errors occur due to connectivity issues.

#### Common Network Errors:
- **NETWORK_CONNECTION_ERROR**: Cannot connect to service
- **NETWORK_TIMEOUT_ERROR**: Request timed out
- **NETWORK_DNS_ERROR**: Cannot resolve server address

#### Solutions:
1. **Connection Issues**:
   - Check internet connection
   - Verify firewall settings
   - Try different network

2. **Timeout Issues**:
   - Use stable internet connection
   - Try again later
   - Use offline modes when available

## Graceful Degradation

The application implements graceful degradation to maintain functionality when services fail:

### API to Local Fallback
- **Transcription**: OpenAI API → Local Whisper model
- **Entity Recognition**: OpenAI GPT → spaCy local processing

### Mode Switching Suggestions
- When Advanced mode fails → Suggests Basic mode
- When API services fail → Suggests offline alternatives
- When local models fail → Suggests API alternatives

## Error Recovery Strategies

### Automatic Retry Logic
- API requests use exponential backoff
- Rate-limited requests wait before retry
- Network errors retry with increasing delays

### User Guidance
- Specific error messages for each scenario
- Actionable suggestions for resolution
- Technical details available for debugging

### Fallback Options
- Multiple processing modes available
- Offline alternatives for most features
- Progressive enhancement approach

## Configuration for Error Handling

### Environment Variables
```bash
# API Configuration
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Application Settings
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=100

# Error Handling
RETRY_MAX_ATTEMPTS=3
RETRY_BACKOFF_FACTOR=2
```

### Logging Configuration
- Error details logged for monitoring
- User-friendly messages displayed in UI
- Technical details available in expandable sections

## Troubleshooting Checklist

### Before Reporting Issues:
1. **Check API Keys**:
   - Verify all required keys are set
   - Ensure keys are valid and active
   - Check account billing status

2. **Verify File Requirements**:
   - File size under 100MB
   - Supported format (MP3, WAV, MP4, M4A)
   - File not corrupted

3. **Test Network Connection**:
   - Stable internet connection
   - No firewall blocking requests
   - DNS resolution working

4. **Try Alternative Modes**:
   - Switch between Basic/Advanced modes
   - Try offline processing
   - Use different file formats

### Getting Help:
1. **Check Error Code**: Note the specific error code displayed
2. **Review Suggestions**: Follow the provided suggestions
3. **Check Logs**: Look at technical details in error expandable sections
4. **Try Alternatives**: Use fallback modes when available

## Error Monitoring

The application tracks error occurrences for monitoring:
- Error frequency tracking
- Common failure patterns
- Performance impact assessment

This helps identify systemic issues and improve reliability over time.