#!/usr/bin/env python3
"""
Fix Emergency CSS Override Script
Removes aggressive CSS overrides and applies proper theme management
"""

import re
import os


def fix_emergency_css_in_file(filepath: str):
    """Fix emergency CSS overrides in a file"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find and remove the emergency CSS block
    emergency_pattern = r'# Emergency visibility fix.*?</style>\s*""", unsafe_allow_html=True\)'
    emergency_pattern_multiline = re.compile(emergency_pattern, re.DOTALL)
    
    # Alternative pattern for the exact emergency CSS
    alt_pattern = r'st\.markdown\("""\s*<style>\s*/\* EMERGENCY TEXT VISIBILITY FIX \*/.*?</style>\s*""", unsafe_allow_html=True\)'
    alt_pattern_multiline = re.compile(alt_pattern, re.DOTALL)
    
    # Check if file contains emergency CSS
    if 'EMERGENCY TEXT VISIBILITY FIX' in content:
        print(f"Found emergency CSS in {filepath}")
        
        # Remove the emergency CSS block
        content = emergency_pattern_multiline.sub('', content)
        content = alt_pattern_multiline.sub('', content)
        
        # Also remove any standalone emergency CSS comments
        content = content.replace('# Emergency visibility fix - AGGRESSIVE CSS\n', '')
        content = content.replace('# Emergency visibility CSS\n', '')
        
        # Add import for fixed UI styles if not present
        if 'from ui_styles_fixed import' not in content:
            # Find the imports section
            import_section_end = content.find('\n\n', content.find('import'))
            if import_section_end > 0:
                # Add the import
                new_import = 'from ui_styles_fixed import apply_theme, render_theme_selector\n'
                content = content[:import_section_end] + '\n' + new_import + content[import_section_end:]
        
        # Replace old theme application with new one
        content = content.replace('from theme_manager import theme_manager, apply_custom_theme', 
                                 'from ui_styles_fixed import apply_theme, render_theme_selector')
        content = content.replace('apply_custom_theme()', 'apply_theme()')
        content = content.replace('theme_manager.render_theme_selector()', 'render_theme_selector()')
        
        # Save the fixed file
        backup_path = filepath + '.backup'
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"Created backup at {backup_path}")
        
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {filepath}")
        
        return True
    
    return False


def create_migration_instructions():
    """Create migration instructions for updating the codebase"""
    
    instructions = """
# CSS Emergency Override Fix - Migration Guide

## Overview
This migration removes the aggressive CSS overrides that force all text to be black with !important rules,
and replaces them with a proper theme management system that ensures text visibility through proper contrast ratios.

## Changes Made

### 1. Removed Emergency CSS
The following CSS block has been removed from app.py and test_visibility_fix.py:
```css
/* EMERGENCY TEXT VISIBILITY FIX */
* {
    color: #000000 !important;
}
...
```

### 2. New Theme System (ui_styles_fixed.py)
- Implements WCAG AA compliant color schemes
- Provides three themes: Light, Dark, and High Contrast
- Uses CSS custom properties for easy theming
- Ensures proper text contrast without !important overrides

### 3. Updated Imports
Replace:
```python
from theme_manager import theme_manager, apply_custom_theme
```

With:
```python
from ui_styles_fixed import apply_theme, render_theme_selector
```

### 4. Updated Function Calls
Replace:
```python
apply_custom_theme()
theme_manager.render_theme_selector()
```

With:
```python
apply_theme()
render_theme_selector()
```

## Manual Steps Required

1. Review and test the theme selector in the sidebar
2. Verify text visibility in all three themes
3. Check that all UI components have proper contrast
4. Remove the old theme_manager.py file if no longer needed
5. Update any custom CSS in your components to use the CSS variables

## Benefits

1. **Better Accessibility**: WCAG AA compliant contrast ratios
2. **Cleaner Code**: No more !important overrides
3. **Maintainable**: Centralized theme management
4. **User Choice**: Users can select their preferred theme
5. **Proper Dark Mode**: Real dark mode support, not just inverted colors

## Testing Checklist

- [ ] App loads without CSS errors
- [ ] All text is visible in Light theme
- [ ] All text is visible in Dark theme  
- [ ] All text is visible in High Contrast theme
- [ ] Sidebar text is properly styled
- [ ] Buttons have proper contrast
- [ ] Input fields are styled correctly
- [ ] Alert boxes (info, warning, error) are visible
- [ ] Code blocks have proper syntax highlighting colors
"""
    
    with open('CSS_FIX_MIGRATION.md', 'w') as f:
        f.write(instructions)
    print("Created migration guide: CSS_FIX_MIGRATION.md")


def main():
    """Main function to fix emergency CSS"""
    files_to_fix = ['app.py', 'test_visibility_fix.py']
    
    fixed_count = 0
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            if fix_emergency_css_in_file(filepath):
                fixed_count += 1
        else:
            print(f"File not found: {filepath}")
    
    if fixed_count > 0:
        create_migration_instructions()
        print(f"\nFixed {fixed_count} files")
        print("Please review the changes and test the application")
    else:
        print("\nNo emergency CSS found to fix")


if __name__ == "__main__":
    main()