# Fixing Python 3.12 Compatibility Issues

## The Problem
Python 3.12 changed the `ForwardRef._evaluate()` method signature, which breaks older versions of Pydantic v1 that many packages (spaCy, langsmith) still depend on.

## Solutions (Choose One)

### Option 1: Downgrade Python (Recommended for Production)
```bash
# Using pyenv
pyenv install 3.11.9
pyenv local 3.11.9

# Create new virtual environment
python -m venv venv_new
source venv_new/bin/activate
pip install -r requirements.txt
pip install -r requirements_intelligence.txt
```

### Option 2: Update Dependencies (May Break Other Features)
```bash
# Try updating to latest compatible versions
pip install --upgrade pydantic==2.5.0
pip install --upgrade spacy==3.7.4
pip uninstall langsmith  # If not needed
```

### Option 3: Use Compatibility Shim (Temporary Fix)
Create a file `pydantic_compat.py`:
```python
import sys
from typing import ForwardRef

# Monkey-patch ForwardRef for compatibility
if sys.version_info >= (3, 12):
    def patched_evaluate(self, globalns=None, localns=None, recursive_guard=None):
        # Call the new Python 3.12 signature
        return self._evaluate(globalns, localns, recursive_guard=set())
    
    ForwardRef._evaluate = patched_evaluate
```

Then import it before any other imports in your main files.

### Option 4: Use Docker (Isolation)
Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements_intelligence.txt

COPY . .
CMD ["python", "run_api.py"]
```

## Immediate Workaround (Without spaCy)

For testing the intelligence systems without spaCy:

```python
# In advanced_content_intelligence.py, modify the _init_nlp_models method:
def _init_nlp_models(self):
    """Initialize NLP models"""
    try:
        import spacy
        self.nlp = spacy.load("en_core_web_sm")
    except (ImportError, TypeError):
        # Fallback without spaCy
        logger.warning("SpaCy not available, using fallback NLP")
        self.nlp = None
    
    # Rest of the models still work...
```

## Production Recommendation

For production deployment:
1. Use Python 3.11.x until packages update
2. Or use Docker containers with Python 3.11
3. Or wait for spaCy/langsmith to release Python 3.12 compatible versions

## Testing Without Full Dependencies

The intelligence systems can still be tested with mock data:
```python
# test_intelligence_mock.py
from unittest.mock import MagicMock
import asyncio

# Mock the problematic imports
import sys
sys.modules['spacy'] = MagicMock()
sys.modules['transformers'] = MagicMock()

# Now import and test
from business_intelligence_roi import BusinessIntelligenceSystem

# Run tests with mocked dependencies
bi = BusinessIntelligenceSystem(MagicMock())
print("Business Intelligence initialized successfully!")
```

## Who Should Resolve This?

### Development Team (You):
- Choose and implement one of the solutions above
- Update CI/CD pipelines to use Python 3.11
- Document the Python version requirement

### Package Maintainers:
- spaCy team: Update to support Python 3.12 (likely in progress)
- langsmith team: Update Pydantic usage
- Other affected packages: Update dependencies

### Timeline:
- **Immediate**: Use Python 3.11 or Docker
- **Short-term**: Apply compatibility patches
- **Long-term**: Wait for package updates or migrate to alternative packages

## Alternative Packages (If Needed)

Instead of spaCy:
- `nltk` for basic NLP
- `stanza` for advanced NLP
- `transformers` for modern NLP models

Instead of affected packages:
- Remove `langsmith` if not critical
- Use `fastapi` without problematic plugins