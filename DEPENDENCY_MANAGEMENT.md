# Dependency Management Guide

This project supports multiple Python dependency management tools. Choose the one that best fits your workflow:

## 🚀 Option 1: uv (Recommended - Fastest)

**uv** is a modern, extremely fast Python package installer and resolver written in Rust. It's significantly faster than pip and provides excellent dependency resolution.

### Benefits:
- ⚡ **10-100x faster** than pip
- 🔒 **Better dependency resolution** - automatically resolves conflicts
- 📦 **Built-in virtual environment management**
- 🛡️ **Reproducible builds** with lock files
- 🔄 **Drop-in replacement** for pip

### Setup:
```bash
# Run the setup script
./setup_with_uv.sh

# Or manually:
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -e .
uv pip install -e ".[dev]"
```

### Usage:
```bash
# Activate environment
source .venv/bin/activate

# Run the app
streamlit run app.py

# Run tests
pytest

# Run AI insights demo
python demo_ai_content_insights.py
```

## 🐍 Option 2: pipenv (Good for Development)

**pipenv** combines pip and virtualenv functionality and provides excellent dependency management with Pipfile/Pipfile.lock.

### Benefits:
- 📋 **Pipfile format** - more readable than requirements.txt
- 🔒 **Automatic dependency resolution**
- 🛡️ **Security scanning** with `pipenv check`
- 🔄 **Reproducible builds** with Pipfile.lock
- 🎯 **Separate dev/prod dependencies**

### Setup:
```bash
# Run the setup script
./setup_with_pipenv.sh

# Or manually:
pip install pipenv
pipenv install
pipenv install --dev
```

### Usage:
```bash
# Activate environment
pipenv shell

# Run the app
pipenv run streamlit run app.py
# or use the script:
pipenv run app

# Run tests
pipenv run test

# Run AI insights demo
pipenv run demo
```

## 📦 Option 3: pip + venv (Traditional)

Standard Python approach using pip and virtual environments.

### Setup:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Usage:
```bash
# Activate environment
source venv/bin/activate

# Run the app
streamlit run app.py

# Run tests
pytest

# Run AI insights demo
python demo_ai_content_insights.py
```

## 🔧 Dependency Issue Resolution

The project includes specific version constraints to resolve common dependency conflicts:

### spaCy + pydantic Compatibility
```toml
spacy = ">=3.7.0,<3.8.0"
pydantic = ">=1.10.0,<2.0.0"
```

This prevents the `ForwardRef._evaluate()` error you encountered, which occurs when spaCy tries to use pydantic v2 APIs with pydantic v1 syntax.

### Optional Dependencies

The project is organized with optional dependency groups:

- **Core**: Basic transcription and analysis
- **Advanced**: Enhanced speaker diarization (WhisperX, PyTorch)
- **Database**: User management and persistence
- **WebSocket**: Real-time features
- **Dev**: Testing and development tools

Install only what you need:
```bash
# With uv
uv pip install -e ".[advanced,database]"

# With pipenv
pipenv install --categories="packages,advanced,database"
```

## 🏆 Performance Comparison

| Tool | Install Time* | Dependency Resolution | Lock File | Virtual Env |
|------|---------------|----------------------|-----------|-------------|
| **uv** | ~10s | ✅ Excellent | ✅ uv.lock | ✅ Built-in |
| **pipenv** | ~60s | ✅ Good | ✅ Pipfile.lock | ✅ Built-in |
| **pip** | ~45s | ❌ Basic | ❌ Manual | ❌ Manual |

*Approximate times for this project's dependencies

## 🎯 Recommendation

For this project, we recommend **uv** because:

1. **Speed**: Installs dependencies 10x faster
2. **Reliability**: Better at resolving the spaCy/pydantic conflict
3. **Modern**: Built for modern Python development
4. **Compatible**: Drop-in replacement for pip

If you prefer a more traditional approach, **pipenv** is the second-best choice for its excellent dependency management features.

## 🐛 Troubleshooting

### Common Issues:

1. **spaCy model not found**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **pydantic version conflict**:
   - Use the provided pyproject.toml or Pipfile
   - Ensure pydantic < 2.0.0

3. **OpenAI API key missing**:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key

4. **FFmpeg not found**:
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/
   ```

## 📚 Further Reading

- [uv Documentation](https://github.com/astral-sh/uv)
- [pipenv Documentation](https://pipenv.pypa.io/)
- [Python Virtual Environments Guide](https://docs.python.org/3/tutorial/venv.html)