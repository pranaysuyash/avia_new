# Audio/Video Transcription Application

AI-powered audio/video transcription and entity extraction application with comprehensive admin dashboard and business analytics.

## Project Structure

```
.
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── venv/                 # Python virtual environment
├── action_item_extraction.py
├── admin_dashboard.py
├── admin_dashboard_ui.py
├── advanced_audio_preprocessing.py
├── advanced_audio_preprocessing_ui.py
├── nlp_model_configurations.py
└── ...                   # Other project files
```

## Documentation

See the [docs](docs/) directory for comprehensive documentation:

- [Code Improvement Philosophy](docs/code_improvement_philosophy.md) - Our approach to completing incomplete features
- [Testing Documentation](docs/testing_documentation.md) - How we validate code quality
- [Project Improvement Summary](docs/project_improvement_summary.md) - Summary of enhancements made

## Scripts

See the [scripts](scripts/) directory for utility scripts:

- [Code Quality Checker](scripts/code_quality_check.sh) - Automated pylint checking

## Key Features

### Admin Dashboard & Business Analytics
- User management with search, filtering, and sorting
- Revenue tracking and financial reporting
- System health monitoring and performance tracking
- Customer support ticket management
- Business intelligence and analytics
- Executive reporting and recommendations

### Advanced Audio Preprocessing
- Spectral analysis and audio feature extraction
- Pitch detection and fundamental frequency analysis
- Audio fingerprinting for duplicate detection
- Tempo and rhythm analysis capabilities
- Audio similarity comparison and clustering

### Action Item Extraction
- Intelligent action item extraction from meeting transcripts
- Sentiment analysis and topic extraction
- Priority classification and assignment
- Structured output generation

### NLP Model Management
- Comprehensive model configurations for different spaCy models
- Automated model selection based on requirements
- Performance metrics and capability tracking

## Code Quality

This project follows the "Feature Completion Over Error Suppression" philosophy, ensuring that incomplete features are enhanced rather than simply removed. All key files maintain excellent pylint scores (9.98-10.00/10).

## Getting Started

1. Set up the virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run code quality checks:
   ```bash
   ./scripts/code_quality_check.sh
   ```

3. Explore the documentation in the [docs](docs/) directory for detailed information about the code improvement philosophy and processes used.