# API Integration Quick Reference

## 🚀 Quick Start

### Start Everything
```bash
./start_with_api.sh
```

### Start Components Individually
```bash
# Terminal 1: API Server
uvicorn api.app:app --reload

# Terminal 2: Streamlit App
streamlit run app.py
```

## 🔧 For Developers

### Using API Wrappers (Recommended)
```python
# Instead of direct imports
from api_wrappers import media, stt, ner_basic, tts

# Use exactly the same way
transcription = stt.transcribe(audio_file)
entities = ner_basic.extract_entities(text)
audio_path = tts.synthesize(text)
```

### Direct API Client Usage
```python
from api_client import get_api_client

api = get_api_client()
response = api.synthesize_speech("Hello world")
```

### Checking API Status
```python
from api_client import get_api_client

api = get_api_client()
health = api._make_request("GET", "/api/v1/health")
print(health.get('status'))  # 'healthy'
```

## 📍 Key Endpoints

### Core Services
- `POST /api/transcription/upload` - Upload & transcribe
- `POST /api/v1/tts/synthesize` - Text to speech
- `POST /api/v1/ner/extract` - Extract entities
- `POST /api/v1/ocr/extract` - Extract text from image
- `POST /api/v1/audio/enhance` - Enhance audio

### Utility Endpoints
- `GET /api/v1/health` - Health check
- `GET /api/docs` - Swagger documentation
- `GET /api/redoc` - ReDoc documentation

## 🔄 Dual Mode Operation

The app automatically detects if the API is available:

```python
# In app.py
try:
    from api_wrappers import stt  # Try API first
    USING_API = True
except ImportError:
    import stt  # Fall back to direct
    USING_API = False
```

## 📝 Creating New Endpoints

1. Create endpoint file in `/api/endpoints/`
2. Define router and models
3. Add to `api/app.py`:
```python
from .endpoints.your_feature import router as your_router
app.include_router(your_router, tags=["Your Feature"])
```

## 🧪 Testing

### Test Integration
```bash
python test_api_integration.py
```

### Test Individual Demos
```bash
python demo_stt_api.py
python demo_ner_basic_api.py
python demo_tts_api.py
```

## 🐛 Troubleshooting

### API Won't Start
```bash
# Check if port is in use
lsof -i :8000

# Kill existing process
kill -9 <PID>
```

### Import Errors
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r api_requirements.txt
```

### Connection Failed
- Check API URL in `.env` or `secrets.toml`
- Default: `http://localhost:8000`
- Verify firewall settings

## 📊 Performance Tips

### API Mode
- Add caching for repeated requests
- Use batch endpoints when available
- Enable compression for large payloads

### Direct Mode
- Better for single-machine setups
- No network overhead
- Ideal for development

## 🔗 Links
- API Docs: http://localhost:8000/api/docs
- App: http://localhost:8501
- Health: http://localhost:8000/api/v1/health