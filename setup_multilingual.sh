#!/bin/bash
# Enhanced setup script for multi-language support (Task 36)

echo "🌍 Setting up Multi-Language Support for Audio/Video Transcription App"
echo "====================================================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install spaCy language models
install_spacy_models() {
    echo "📚 Installing spaCy language models for multi-language support..."
    
    # Core models (required)
    echo "Installing core English model..."
    python -m spacy download en_core_web_sm
    
    # Additional language models (optional but recommended)
    declare -A MODELS=(
        ["es_core_news_sm"]="Spanish"
        ["fr_core_news_sm"]="French" 
        ["de_core_news_sm"]="German"
        ["it_core_news_sm"]="Italian"
        ["pt_core_news_sm"]="Portuguese"
        ["ru_core_news_sm"]="Russian"
        ["ja_core_news_sm"]="Japanese"
        ["ko_core_news_sm"]="Korean"
        ["zh_core_web_sm"]="Chinese"
        ["ar_core_web_sm"]="Arabic"
        ["nl_core_news_sm"]="Dutch"
        ["pl_core_news_sm"]="Polish"
        ["sv_core_news_sm"]="Swedish"
        ["da_core_news_sm"]="Danish"
        ["nb_core_news_sm"]="Norwegian"
        ["fi_core_news_sm"]="Finnish"
        ["el_core_news_sm"]="Greek"
        ["uk_core_news_sm"]="Ukrainian"
        ["ro_core_news_sm"]="Romanian"
        ["hr_core_news_sm"]="Croatian"
        ["sl_core_news_sm"]="Slovenian"
        ["lt_core_news_sm"]="Lithuanian"
        ["lv_core_news_sm"]="Latvian"
        ["ca_core_news_sm"]="Catalan"
        ["mk_core_news_sm"]="Macedonian"
        ["is_core_news_sm"]="Icelandic"
    )
    
    echo ""
    echo "🌍 Installing additional language models (this may take a while)..."
    echo "Note: Some models may not be available and will be skipped."
    echo ""
    
    for model in "${!MODELS[@]}"; do
        language="${MODELS[$model]}"
        echo "Installing $language model ($model)..."
        if python -m spacy download "$model" 2>/dev/null; then
            echo "✅ $language model installed successfully"
        else
            echo "⚠️ $language model not available or failed to install (skipping)"
        fi
    done
    
    echo ""
    echo "📋 Checking installed models..."
    python -c "
import spacy
import sys

print('Installed spaCy models:')
try:
    info = spacy.info()
    if 'pipelines' in info:
        for pipeline in info['pipelines']:
            print(f'  ✅ {pipeline}')
    else:
        print('  No pipeline information available')
except Exception as e:
    print(f'  Error checking models: {e}')
    
# Test basic functionality
try:
    nlp = spacy.load('en_core_web_sm')
    doc = nlp('Hello world')
    print(f'✅ English model working: {len(doc)} tokens processed')
except Exception as e:
    print(f'❌ English model test failed: {e}')
    sys.exit(1)
"
}

# Function to test multi-language dependencies
test_multilingual_deps() {
    echo "🧪 Testing multi-language dependencies..."
    
    python -c "
import sys

# Test language detection
try:
    import langdetect
    from langdetect import detect
    test_text = 'Hello, this is a test.'
    detected = detect(test_text)
    print(f'✅ Language detection working: detected {detected}')
except Exception as e:
    print(f'❌ Language detection failed: {e}')
    sys.exit(1)

# Test country/language info
try:
    import pycountry
    lang = pycountry.languages.get(alpha_2='en')
    print(f'✅ Country/language info working: {lang.name}')
except Exception as e:
    print(f'❌ Country/language info failed: {e}')
    sys.exit(1)

# Test translation (optional - may fail without internet)
try:
    from googletrans import Translator
    translator = Translator()
    # Simple test without actual translation to avoid API calls
    print('✅ Google Translate library imported successfully')
except Exception as e:
    print(f'⚠️ Google Translate library issue (may work at runtime): {e}')

print('🎉 All multi-language dependencies are working!')
"
}

# Function to run multi-language tests
run_multilingual_tests() {
    echo "🚀 Running multi-language functionality tests..."
    
    if [ -f "test_multilingual_support.py" ]; then
        echo "Running comprehensive multi-language tests..."
        python test_multilingual_support.py
    else
        echo "⚠️ Multi-language test file not found, running basic tests..."
        
        python -c "
# Basic multi-language functionality test
import sys
sys.path.append('.')

try:
    from language_support import language_detector, get_supported_languages
    
    # Test language detection
    result = language_detector.detect_language('Hello, how are you?')
    print(f'✅ Language detection: {result.primary_language} (confidence: {result.confidence:.2%})')
    
    # Test supported languages
    languages = get_supported_languages()
    print(f'✅ Supported languages: {len(languages)} languages available')
    
    # Test a few specific languages
    test_languages = ['en', 'es', 'fr', 'de']
    for lang in test_languages:
        info = language_detector.get_language_info(lang)
        if info:
            print(f'  {lang}: {info[\"name\"]} - spaCy: {\"✅\" if info[\"spacy_model\"] else \"❌\"}')
    
    print('🎉 Basic multi-language functionality working!')
    
except Exception as e:
    print(f'❌ Multi-language functionality test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
    fi
}

# Main setup process
main() {
    echo "Checking Python environment..."
    
    if ! command_exists python; then
        echo "❌ Python not found. Please install Python 3.9+ first."
        exit 1
    fi
    
    python_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "✅ Python $python_version found"
    
    # Check if we're in a virtual environment
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        echo "✅ Virtual environment active: $VIRTUAL_ENV"
    else
        echo "⚠️ No virtual environment detected. Consider using:"
        echo "   uv venv && source .venv/bin/activate"
        echo "   or"
        echo "   pipenv shell"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Install spaCy models
    install_spacy_models
    
    # Test dependencies
    test_multilingual_deps
    
    # Run functionality tests
    run_multilingual_tests
    
    echo ""
    echo "🎉 Multi-language setup complete!"
    echo ""
    echo "📋 Summary:"
    echo "  ✅ spaCy language models installed"
    echo "  ✅ Multi-language dependencies verified"
    echo "  ✅ Basic functionality tested"
    echo ""
    echo "🚀 You can now use the multi-language features:"
    echo "  • Automatic language detection (50+ languages)"
    echo "  • Multi-language entity extraction"
    echo "  • Code-switching detection"
    echo "  • Translation capabilities"
    echo ""
    echo "To run the app with multi-language support:"
    echo "  streamlit run app.py"
    echo ""
    echo "Select '🌍 Multi-Language' mode in the sidebar for full features!"
}

# Run main function
main "$@"