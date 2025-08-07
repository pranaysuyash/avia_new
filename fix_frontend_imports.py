#!/usr/bin/env python3
import os
import re

def fix_imports_in_file(file_path):
    """Fix @/components/ui imports to use relative paths"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace @/components/ui/ with ../ui/ for files in components subdirectories
    updated_content = re.sub(
        r"from '@/components/ui/(.*?)'",
        r"from '../ui/\1'",
        content
    )
    
    if updated_content != content:
        with open(file_path, 'w') as f:
            f.write(updated_content)
        print(f"Fixed imports in: {file_path}")

# Fix all TypeScript files in the frontend components directory
frontend_components = "/Users/pranay/Projects/LLM/video/ner/frontend/src/components"
for root, dirs, files in os.walk(frontend_components):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            file_path = os.path.join(root, file)
            fix_imports_in_file(file_path)

print("Import fixes completed!")