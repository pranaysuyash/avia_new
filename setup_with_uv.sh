#!/bin/bash
# Setup script using uv for fast dependency resolution

echo "🚀 Setting up Audio/Video Transcription App with uv"
echo "=================================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing uv..."
    
    # Install uv using the official installer
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    echo "✅ uv installed successfully"
else
    echo "✅ uv is already installed"
fi

# Create virtual environment with uv
echo "📦 Creating virtual environment..."
uv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies with uv (much faster than pip)
echo "⬇️ Installing dependencies with uv..."
uv pip install -e .

# Install development dependencies
echo "🛠️ Installing development dependencies..."
uv pip install -e ".[dev]"

# Download spaCy models for multi-language support (Task 36)
echo "📚 Downloading spaCy models for multi-language support..."
python -m spacy download en_core_web_sm
echo "🌍 Downloading additional language models (optional)..."
python -m spacy download es_core_news_sm || echo "⚠️ Spanish model download failed (optional)"
python -m spacy download fr_core_news_sm || echo "⚠️ French model download failed (optional)"
python -m spacy download de_core_news_sm || echo "⚠️ German model download failed (optional)"
echo "✅ Core language models installed. Additional models can be installed as needed."

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️ Please edit .env file with your API keys"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the application:"
echo "  streamlit run app.py"
echo ""
echo "To run tests:"
echo "  pytest"
echo ""
echo "To run the AI insights demo:"
echo "  python demo_ai_content_insights.py"