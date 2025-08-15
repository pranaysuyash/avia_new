#!/bin/bash
# Code Quality Checker
# Script to run pylint checks for unused imports, variables, and arguments

echo "Running code quality checks..."

# Check if pylint is installed
if ! command -v pylint &> /dev/null
then
    echo "pylint could not be found. Please install it with: pip install pylint"
    exit 1
fi

# Check if in virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Files to check (modify this list as needed)
FILES_TO_CHECK=(
    "action_item_extraction.py"
    "admin_dashboard_ui.py"
    "admin_dashboard.py"
    "advanced_audio_preprocessing.py"
    "advanced_audio_preprocessing_ui.py"
    "nlp_model_configurations.py"
)

# Run checks
echo "Checking for unused imports, variables, and arguments..."
for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        echo "Checking $file:"
        pylint --disable=all --enable=unused-import,unused-variable,unused-argument "$file"
        echo ""
    else
        echo "File $file not found"
    fi
done

echo "Code quality check complete!"