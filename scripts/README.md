# Scripts

This directory contains utility scripts for maintaining code quality and consistency.

## Contents

### [code_quality_check.sh](code_quality_check.sh)
A script to run pylint checks for unused imports, variables, and arguments across key Python files.

#### Usage
```bash
./scripts/code_quality_check.sh
```

#### What it does
- Activates virtual environment if present
- Runs pylint checks for:
  - Unused imports (`unused-import`)
  - Unused variables (`unused-variable`)
  - Unused arguments (`unused-argument`)
- Checks key Python files in the project
- Provides detailed output for each file

#### Requirements
- `pylint` must be installed
- Python virtual environment (optional, but recommended)

#### Output
The script provides pylint scores for each checked file, helping maintain high code quality standards.