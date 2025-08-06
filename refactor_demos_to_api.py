#!/usr/bin/env python3
"""
Script to help refactor demo files to use API client
This script analyzes demo files and provides refactoring suggestions
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set

def analyze_demo_file(filepath: str) -> Dict[str, any]:
    """Analyze a demo file to identify what needs refactoring"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Find direct imports that need to be replaced
    direct_imports = {
        'media': re.findall(r'^import media|from media import', content, re.MULTILINE),
        'stt': re.findall(r'^import stt|from stt import', content, re.MULTILINE),
        'ner_basic': re.findall(r'^import ner_basic|from ner_basic import', content, re.MULTILINE),
        'ner_advanced': re.findall(r'^import ner_advanced|from ner_advanced import', content, re.MULTILINE),
        'tts': re.findall(r'^import tts|from tts import', content, re.MULTILINE),
    }
    
    # Count actual imports
    imports_found = {k: len(v) for k, v in direct_imports.items() if v}
    
    # Find function calls that need updating
    function_patterns = {
        'media': [
            r'media\.extract_audio',
            r'media\.get_media_info',
            r'media\.validate_media_file',
        ],
        'stt': [
            r'stt\.transcribe',
            r'transcribe_detailed',
            r'get_transcription_confidence',
        ],
        'ner_basic': [
            r'ner_basic\.extract_entities',
            r'extract_entities',
            r'get_entity_confidence',
        ],
        'tts': [
            r'tts\.synthesize',
            r'synthesize_speech',
            r'list_available_voices',
        ]
    }
    
    functions_found = {}
    for module, patterns in function_patterns.items():
        matches = []
        for pattern in patterns:
            matches.extend(re.findall(pattern, content))
        if matches:
            functions_found[module] = len(matches)
    
    return {
        'filepath': filepath,
        'filename': os.path.basename(filepath),
        'imports': imports_found,
        'functions': functions_found,
        'needs_refactoring': bool(imports_found or functions_found)
    }

def generate_refactoring_template(analysis: Dict[str, any]) -> str:
    """Generate a refactoring template based on analysis"""
    if not analysis['needs_refactoring']:
        return ""
    
    template = f"""
# Refactoring template for {analysis['filename']}

## Required imports:
```python
from api_client import get_api_client
"""
    
    # Add needed wrapper imports
    if any(module in analysis['imports'] or module in analysis['functions'] 
           for module in ['media', 'stt', 'ner_basic', 'ner_advanced', 'tts']):
        template += "from api_wrappers import "
        modules = []
        for module in ['media', 'stt', 'ner_basic', 'ner_advanced', 'tts']:
            if module in analysis['imports'] or module in analysis['functions']:
                modules.append(module)
        template += ", ".join(modules)
    
    template += """
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
    print("Make sure the API server is running\\n")
    return
```

## Function call updates:
"""
    
    # Add specific refactoring suggestions
    if 'media' in analysis['functions']:
        template += """
- Replace `extract_audio(file)` with `media.extract_audio(file)`
- Replace `get_media_info(file)` with `media.get_media_info(file)`
"""
    
    if 'stt' in analysis['functions']:
        template += """
- Replace `transcribe(audio, ...)` with `stt.transcribe(audio, ...)`
- Update result handling - API returns dict with 'text', 'segments', etc.
"""
    
    if 'ner_basic' in analysis['functions']:
        template += """
- Replace `extract_entities(text)` with `ner_basic.extract_entities(text)`
- Results are now list of dicts with 'text', 'type', 'confidence' keys
"""
    
    if 'tts' in analysis['functions']:
        template += """
- Replace `synthesize_speech(text, ...)` with `tts.synthesize(text, ...)`
- Replace `list_available_voices()` with `tts.get_voices()`
"""
    
    return template

def main():
    """Main function to analyze all demo files"""
    print("🔍 Analyzing demo files for API refactoring...\n")
    
    # Find all demo files
    demo_files = sorted(Path('.').glob('demo_*.py'))
    
    # Skip already refactored files
    skip_files = ['demo_stt_api.py', 'demo_ner_basic_api.py', 'demo_tts_api.py', 'demo_media_api.py']
    demo_files = [f for f in demo_files if f.name not in skip_files]
    
    print(f"Found {len(demo_files)} demo files to analyze\n")
    
    needs_refactoring = []
    no_refactoring = []
    
    for demo_file in demo_files:
        analysis = analyze_demo_file(str(demo_file))
        
        if analysis['needs_refactoring']:
            needs_refactoring.append(analysis)
            print(f"✓ {analysis['filename']} - Needs refactoring")
            if analysis['imports']:
                print(f"  Imports: {', '.join(analysis['imports'].keys())}")
            if analysis['functions']:
                print(f"  Functions from: {', '.join(analysis['functions'].keys())}")
        else:
            no_refactoring.append(analysis)
            print(f"- {analysis['filename']} - No direct module usage found")
    
    print(f"\n📊 Summary:")
    print(f"- Files needing refactoring: {len(needs_refactoring)}")
    print(f"- Files not using direct modules: {len(no_refactoring)}")
    
    # Generate refactoring report
    if needs_refactoring:
        print("\n📝 Generating refactoring templates...\n")
        
        report_file = "demo_refactoring_report.md"
        with open(report_file, 'w') as f:
            f.write("# Demo Files API Refactoring Report\n\n")
            f.write(f"Total files to refactor: {len(needs_refactoring)}\n\n")
            
            for analysis in needs_refactoring:
                f.write(f"## {analysis['filename']}\n")
                f.write(generate_refactoring_template(analysis))
                f.write("\n---\n")
        
        print(f"✅ Refactoring report saved to: {report_file}")
    
    # Create a priority list
    print("\n🎯 Refactoring Priority (by usage):")
    
    # Sort by total usage (imports + functions)
    needs_refactoring.sort(
        key=lambda x: sum(x['imports'].values()) + sum(x['functions'].values()),
        reverse=True
    )
    
    for i, analysis in enumerate(needs_refactoring[:10], 1):
        total_usage = sum(analysis['imports'].values()) + sum(analysis['functions'].values())
        print(f"{i}. {analysis['filename']} ({total_usage} references)")

if __name__ == "__main__":
    main()