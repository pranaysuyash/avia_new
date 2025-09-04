# Demo Files API Refactoring Report

Total files to refactor: 7

## demo_admin_panel.py

# Refactoring template for demo_admin_panel.py

## Required imports:
```python
from api_client import get_api_client
from api_wrappers import tts
```

## Add API connection check:
```python
# Check API connection
api_client = get_api_client()
try:
    health = api_client._make_request("GET", "/api/v1/health")
    print(f"✅ API Status: {health.get('status', 'unknown')}")
except Exception as e:
    print(f"❌ API Connection Error: {str(e)}")
    print("Make sure the API server is running\n")
    return
```

## Function call updates:

- Replace `synthesize_speech(text, ...)` with `tts.synthesize(text, ...)`
- Replace `list_available_voices()` with `tts.get_voices()`

---
## demo_media.py

# Refactoring template for demo_media.py

## Required imports:
```python
from api_client import get_api_client
from api_wrappers import media
```

## Add API connection check:
```python
# Check API connection
api_client = get_api_client()
try:
    health = api_client._make_request("GET", "/api/v1/health")
    print(f"✅ API Status: {health.get('status', 'unknown')}")
except Exception as e:
    print(f"❌ API Connection Error: {str(e)}")
    print("Make sure the API server is running\n")
    return
```

## Function call updates:

---
## demo_multilingual.py

# Refactoring template for demo_multilingual.py

## Required imports:
```python
from api_client import get_api_client
from api_wrappers import ner_basic
```

## Add API connection check:
```python
# Check API connection
api_client = get_api_client()
try:
    health = api_client._make_request("GET", "/api/v1/health")
    print(f"✅ API Status: {health.get('status', 'unknown')}")
except Exception as e:
    print(f"❌ API Connection Error: {str(e)}")
    print("Make sure the API server is running\n")
    return
```

## Function call updates:

- Replace `extract_entities(text)` with `ner_basic.extract_entities(text)`
- Results are now list of dicts with 'text', 'type', 'confidence' keys

---
## demo_ner_advanced.py

# Refactoring template for demo_ner_advanced.py

## Required imports:
```python
from api_client import get_api_client
from api_wrappers import ner_basic, ner_advanced
```

## Add API connection check:
```python
# Check API connection
api_client = get_api_client()
try:
    health = api_client._make_request("GET", "/api/v1/health")
    print(f"✅ API Status: {health.get('status', 'unknown')}")
except Exception as e:
    print(f"❌ API Connection Error: {str(e)}")
    print("Make sure the API server is running\n")
    return
```

## Function call updates:

- Replace `extract_entities(text)` with `ner_basic.extract_entities(text)`
- Results are now list of dicts with 'text', 'type', 'confidence' keys

---
## demo_ner_basic.py

# Refactoring template for demo_ner_basic.py

## Required imports:
```python
from api_client import get_api_client
from api_wrappers import ner_basic
```

## Add API connection check:
```python
# Check API connection
api_client = get_api_client()
try:
    health = api_client._make_request("GET", "/api/v1/health")
    print(f"✅ API Status: {health.get('status', 'unknown')}")
except Exception as e:
    print(f"❌ API Connection Error: {str(e)}")
    print("Make sure the API server is running\n")
    return
```

## Function call updates:

- Replace `extract_entities(text)` with `ner_basic.extract_entities(text)`
- Results are now list of dicts with 'text', 'type', 'confidence' keys

---
## demo_stt.py

# Refactoring template for demo_stt.py

## Required imports:
```python
from api_client import get_api_client
from api_wrappers import stt
```

## Add API connection check:
```python
# Check API connection
api_client = get_api_client()
try:
    health = api_client._make_request("GET", "/api/v1/health")
    print(f"✅ API Status: {health.get('status', 'unknown')}")
except Exception as e:
    print(f"❌ API Connection Error: {str(e)}")
    print("Make sure the API server is running\n")
    return
```

## Function call updates:

- Replace `transcribe(audio, ...)` with `stt.transcribe(audio, ...)`
- Update result handling - API returns dict with 'text', 'segments', etc.

---
## demo_tts.py

# Refactoring template for demo_tts.py

## Required imports:
```python
from api_client import get_api_client
from api_wrappers import tts
```

## Add API connection check:
```python
# Check API connection
api_client = get_api_client()
try:
    health = api_client._make_request("GET", "/api/v1/health")
    print(f"✅ API Status: {health.get('status', 'unknown')}")
except Exception as e:
    print(f"❌ API Connection Error: {str(e)}")
    print("Make sure the API server is running\n")
    return
```

## Function call updates:

- Replace `synthesize_speech(text, ...)` with `tts.synthesize(text, ...)`
- Replace `list_available_voices()` with `tts.get_voices()`

---
