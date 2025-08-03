#!/bin/bash
# Setup script using pipenv for dependency resolution

echo "🚀 Setting up Audio/Video Transcription App with pipenv"
echo "======================================================"

# Check if pipenv is installed
if ! command -v pipenv &> /dev/null; then
    echo "❌ pipenv is not installed. Installing pipenv..."
    pip install pipenv
    echo "✅ pipenv installed successfully"
else
    echo "✅ pipenv is already installed"
fi

# Install dependencies with pipenv
echo "📦 Installing dependencies with pipenv..."
pipenv install

# Install development dependencies
echo "🛠️ Installing development dependencies..."
pipenv install --dev

# Download spaCy models for multi-language support (Task 36)
echo "📚 Downloading spaCy models for multi-language support..."
pipenv run python -m spacy download en_core_web_sm
echo "🌍 Downloading additional language models (optional)..."
pipenv run python -m spacy download es_core_news_sm || echo "⚠️ Spanish model download failed (optional)"
pipenv run python -m spacy download fr_core_news_sm || echo "⚠️ French model download failed (optional)"
pipenv run python -m spacy download de_core_news_sm || echo "⚠️ German model download failed (optional)"
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
echo "To activate the environment:"
echo "  pipenv shell"
echo ""
echo "To run the application:"
echo "  pipenv run streamlit run app.py"
echo "  # or use the script: pipenv run app"
echo ""
echo "To run tests:"
echo "  pipenv run pytest"
echo "  # or use the script: pipenv run test"
echo ""
echo "To run the AI insights demo:"
echo "  pipenv run python demo_ai_content_insights.py"
echo "  # or use the script: pipenv run demo"