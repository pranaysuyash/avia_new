#!/bin/bash
# Script to install language models for multi-language support

echo "Installing language models for multi-language NER..."
echo "This may take a few minutes..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install major language models
echo "Installing Spanish model..."
python -m spacy download es_core_news_sm

echo "Installing French model..."
python -m spacy download fr_core_news_sm

echo "Installing German model..."
python -m spacy download de_core_news_sm

echo "Installing Italian model..."
python -m spacy download it_core_news_sm

echo "Installing Portuguese model..."
python -m spacy download pt_core_news_sm

echo "Installing Dutch model..."
python -m spacy download nl_core_news_sm

echo "Installing Chinese model..."
python -m spacy download zh_core_web_sm

echo "Installing Japanese model..."
python -m spacy download ja_core_news_sm

echo "✅ Language models installed successfully!"
echo ""
echo "You can now use multi-language entity extraction in the app."
echo "Additional models can be installed as needed from: https://spacy.io/models"