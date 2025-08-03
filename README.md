# 🎵 Audio/Video Transcription & Entity Extraction App

A comprehensive enterprise-ready platform that transforms audio and video content into structured, analyzable data with advanced collaboration, security, and technical infrastructure features.

## ✨ Core Features

### 🎯 Media Processing & Analysis
- **🎤 Audio/Video Processing**: Upload MP3, WAV, MP4, M4A files or record live audio
- **📝 Intelligent Transcription**: OpenAI Whisper API with local model fallback
- **🏷️ Triple Analysis Modes**:
  - **Basic Mode**: Fast local NER using spaCy (offline capable)
  - **Advanced Mode**: AI-powered analysis with OpenAI GPT (summaries + enhanced entities)
  - **Medical Mode**: HIPAA-compliant healthcare entity extraction
- **🔧 Admin Panel**: Generate scripted audio content using ElevenLabs TTS

### 👥 Collaboration & Teams
- **🔐 Authentication System**: User registration, login, and profile management
- **👥 Team Workspaces**: Create teams, assign roles, share resources
- **🔗 Sharing & Permissions**: Share transcripts with fine-grained access control
- **✏️ Real-time Annotations**: Collaborate on transcripts with timestamped comments
- **📊 Version Control**: Track changes and restore previous versions
- **🔔 Notifications**: Get alerts for shares, mentions, and updates

### 🏢 Enterprise Features
- **🌍 Multi-language Support**: 50+ languages with automatic detection, code-switching analysis, and real-time translation
- **📊 Advanced Segmentation**: Semantic, structural, temporal, and hybrid segmentation
- **🏷️ AI-powered Tagging**: Automatic content categorization with 12+ tag types
- **📤 Enhanced Export**: 8+ formats including PDF, DOCX, CSV with templates
- **🔍 Batch Processing**: Process multiple files with progress tracking
- **📈 Analytics & Reporting**: Usage metrics and team insights
- **🔎 Advanced Search**: Full-text search with filters, facets, and saved searches
- **🗺️ Visual Search & Discovery**: Interactive content maps, similarity search, and topic clustering
- **🧠 Advanced Content Analysis**: AI-powered emotion detection, bias analysis, complexity scoring, and plagiarism checking
- **🤖 AI Provider Management**: Integrate 20+ AI providers for enhanced TTS, STT, image, and video generation
- **🎙️ Speaker Diarization**: Identify and label different speakers in audio
- **🎵 Advanced Audio Processing**: Noise reduction, voice enhancement, and quality analysis

### 🔧 Technical Infrastructure
- **🚀 REST API**: Complete FastAPI backend with JWT authentication
- **🔌 WebSocket Server**: Real-time updates and live collaboration
- **⚡ Background Jobs**: Async processing with priority queue system
- **📊 Monitoring**: Comprehensive logging, metrics, and health checks
- **🔒 Security**: Data encryption at rest, PII detection, GDPR compliance

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Streamlit)                    │
├─────────────────────────────────────────────────────────────┤
│                    REST API (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│   Authentication │ WebSocket │ Job Queue │ Monitoring       │
├─────────────────────────────────────────────────────────────┤
│              Database │ File Storage │ Cache                │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Option 1: One-Command Deployment (Recommended)

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd audio-video-transcription-app
   ```

2. **Run Application** (Choose your platform)
   
   **macOS/Linux:**
   ```bash
   ./run.sh
   ```
   
   **Windows:**
   ```cmd
   run.bat
   ```
   
   **Cross-platform:**
   ```bash
   python start.py
   ```

3. **Configure API Keys** (if prompted)
   - The startup script will create a `.env` file from the template
   - Edit `.env` with your API keys and restart

4. **Access Application**
   - Open your browser to `http://localhost:8501`

### Option 2: Manual Setup

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd audio-video-transcription-app
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (see Configuration section)
   ```

4. **Run Application**
   ```bash
   streamlit run app.py
   ```

5. **Access Application**
   - Open your browser to `http://localhost:8501`

### Option 2: Docker Deployment

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd audio-video-transcription-app
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Deploy with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access Application**
   - Open your browser to `http://localhost:8501`

## ⚙️ Configuration

### Required API Keys

1. **OpenAI API Key** (Required for transcription and advanced analysis)
   - Sign up at: https://platform.openai.com/
   - Create API key in your dashboard
   - Add to `.env`: `OPENAI_API_KEY=your_key_here`

2. **ElevenLabs API Key** (Required for admin TTS features)
   - Sign up at: https://elevenlabs.io/
   - Get API key from your profile
   - Add to `.env`: `ELEVENLABS_API_KEY=your_key_here`

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Application Settings
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
MAX_FILE_SIZE_MB=100             # Maximum upload size in MB
TEMP_DIR=./temp                  # Temporary files directory

# Optional Admin Panel
ADMIN_PASSWORD=your_secure_password

# AI Model Configuration
WHISPER_MODEL=base               # tiny, base, small, medium, large
SPACY_MODEL=en_core_web_sm       # spaCy model for NER

# Performance Settings
MAX_CONCURRENT_REQUESTS=5        # API request concurrency
REQUEST_TIMEOUT=300              # Request timeout in seconds
```

### Verify Configuration

**Check configuration status:**
```bash
python config.py
```

**Verify deployment readiness:**
```bash
python verify_setup.py
```

These scripts will display your current configuration status and highlight any issues.

### Startup Script Features

The `start.py` script provides automated setup and validation:

- ✅ **Dependency Checking**: Verifies all required packages and models
- ✅ **Environment Setup**: Creates necessary directories and files
- ✅ **Configuration Validation**: Checks API keys and settings
- ✅ **Auto-Installation**: Downloads missing spaCy models automatically
- ✅ **User Guidance**: Provides helpful error messages and setup instructions
- ✅ **Graceful Startup**: Handles configuration issues and user interruption

## 📖 Usage Guide

### Basic Workflow

1. **Upload or Record Audio**
   - Use the file uploader for existing media files
   - Use the audio recorder for live capture
   - Supported formats: MP3, WAV, MP4, M4A (max 100MB)

2. **Choose Analysis Mode**
   - **Basic Mode**: Fast, offline-capable entity extraction using spaCy
   - **Advanced Mode**: AI-powered analysis with content summaries (requires OpenAI API)

3. **Process and Review Results**
   - View full transcript with search functionality
   - Explore extracted entities by category
   - Download results in various formats

### Admin Panel Features

Enable admin mode to access content generation features:

1. **Script Generation**: Create realistic scripts from text prompts
2. **Text-to-Speech**: Convert scripts to natural-sounding audio
3. **Pipeline Testing**: Test generated content through the analysis pipeline

## 🏗️ Architecture

### System Components

```
Frontend (Streamlit) → Backend Modules → External APIs
                    ↓
                 Local Models
```

- **Frontend**: Streamlit web interface with real-time processing
- **Backend Modules**:
  - `media.py`: FFmpeg integration for audio extraction
  - `stt.py`: Speech-to-text with Whisper API/local fallback
  - `ner_basic.py`: spaCy-based entity extraction
  - `ner_advanced.py`: GPT-powered analysis and script generation
  - `tts.py`: ElevenLabs text-to-speech synthesis
  - `utils.py`: File management and utilities
  - `config.py`: Configuration management
  - `errors.py`: Centralized error handling

### Data Flow

1. **Input**: File upload or audio recording
2. **Media Processing**: Audio extraction and format conversion
3. **Transcription**: Speech-to-text conversion
4. **Analysis**: Entity extraction (basic or advanced)
5. **Output**: Formatted results with download options

## 🔧 Technical Infrastructure

### REST API
Access the complete REST API at `http://localhost:8000` when running the API server:

```bash
python run_api.py
```

Features:
- OpenAPI documentation at `/docs`
- JWT authentication with refresh tokens
- Complete CRUD operations for all resources
- Rate limiting and CORS protection

### WebSocket Server
Real-time features available at `ws://localhost:8000/ws`:
- Live transcript updates
- Collaboration events
- Processing notifications

### Background Jobs
Async processing handled by the job queue system:
- Export jobs (PDF, DOCX, CSV)
- Media processing
- Email notifications
- Data cleanup tasks

### Monitoring & Security
- **Logging**: Structured JSON logs in `/logs` directory
- **Metrics**: Application and system metrics collection
- **Health Checks**: `/health` endpoint for monitoring
- **Encryption**: AES-256 encryption for sensitive data
- **Privacy**: PII detection and anonymization

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test module
pytest test_stt.py -v

# Test API endpoints
python test_api.py
```

### Test Data

The application includes sample test files for development:
- `temp/demo_audio.wav`: Sample audio for testing transcription
- `test_data/`: Comprehensive test dataset
- Various test modules for each component

## 🐳 Docker Deployment

### Development

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Considerations

1. **Environment Variables**: Use Docker secrets or external config management
2. **Reverse Proxy**: Add nginx for SSL termination and load balancing
3. **Persistent Storage**: Configure volumes for temp files and logs
4. **Health Monitoring**: Use the built-in health checks
5. **Resource Limits**: Set appropriate CPU and memory limits

### Docker Commands

```bash
# Build image
docker build -t transcription-app .

# Run container
docker run -p 8501:8501 --env-file .env transcription-app

# Check health
docker ps
```

## 🔧 Development

### Project Structure

```
├── app.py                 # Main Streamlit application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose setup
├── README.md            # This file
├── backend modules/     # Core processing modules
│   ├── media.py
│   ├── stt.py
│   ├── ner_basic.py
│   ├── ner_advanced.py
│   ├── tts.py
│   ├── utils.py
│   └── errors.py
├── tests/              # Test modules
└── temp/               # Temporary files (auto-created)
```

### Adding New Features

1. **Backend Module**: Create new module in root directory
2. **Error Handling**: Add custom exceptions to `errors.py`
3. **Configuration**: Add new settings to `config.py`
4. **Tests**: Create corresponding test module
5. **UI Integration**: Update `app.py` with new interface elements

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints for function parameters and returns
- Include docstrings for all public functions
- Handle errors gracefully with user-friendly messages

## 🚨 Troubleshooting

### Common Issues

1. **API Key Errors**
   ```
   Solution: Verify API keys in .env file and check account status
   ```

2. **File Upload Failures**
   ```
   Solution: Check file format, size limits, and temp directory permissions
   ```

3. **Docker Build Issues**
   ```
   Solution: Ensure Docker daemon is running and check system resources
   ```

4. **Transcription Errors**
   ```
   Solution: Verify audio quality and try local Whisper model fallback
   ```

### Debug Mode

Enable debug logging:
```bash
# In .env file
LOG_LEVEL=DEBUG
```

Check logs:
```bash
# Local development
tail -f app.log

# Docker deployment
docker-compose logs -f transcription-app
```

### Performance Optimization

1. **File Size**: Keep uploads under 100MB for optimal performance
2. **Model Selection**: Use smaller Whisper models for faster processing
3. **Concurrent Requests**: Adjust `MAX_CONCURRENT_REQUESTS` based on system resources
4. **Caching**: Enable browser caching for static assets

## 📊 System Requirements

### Minimum Requirements

- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4GB (8GB recommended)
- **Storage**: 2GB free space
- **Network**: Stable internet connection for API calls
- **OS**: Linux, macOS, or Windows with Docker support

### Recommended Requirements

- **CPU**: 4+ cores, 3.0+ GHz
- **RAM**: 8GB+ (16GB for large files)
- **Storage**: 10GB+ free space
- **Network**: High-speed internet for optimal API performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Configuration**: Run `python config.py` to verify setup
- **Issues**: Create GitHub issues for bugs and feature requests
- **Community**: Join discussions in the repository

## 🔮 Roadmap

- [x] **Multi-language transcription support** ✅ (50+ languages, code-switching, translation)
- [ ] Real-time streaming transcription
- [ ] Advanced analytics dashboard
- [ ] API endpoints for programmatic access
- [ ] Mobile app integration
- [ ] Enterprise authentication (SSO)

---

**Made with ❤️ for developers who need powerful audio/video analysis tools**