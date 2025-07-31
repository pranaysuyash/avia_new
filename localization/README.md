# Localization System Documentation

## Overview

The localization system provides comprehensive multi-language support for the Audio/Video Transcription App, allowing the entire user interface to be displayed in 10 different languages.

## Supported Languages

- 🇬🇧 **English** (en)
- 🇪🇸 **Español** (es) - Spanish
- 🇫🇷 **Français** (fr) - French
- 🇩🇪 **Deutsch** (de) - German
- 🇮🇹 **Italiano** (it) - Italian
- 🇵🇹 **Português** (pt) - Portuguese
- 🇨🇳 **中文** (zh) - Chinese
- 🇯🇵 **日本語** (ja) - Japanese
- 🇰🇷 **한국어** (ko) - Korean
- 🇸🇦 **العربية** (ar) - Arabic

## Features

### 1. **Automatic Language Detection**
- Remembers user's language preference
- Persists across sessions
- Falls back to English if preference not found

### 2. **Complete UI Translation**
- All navigation elements
- Form labels and buttons
- Messages and notifications
- Error and success messages

### 3. **Localized Formatting**
- Date formatting per locale
- Number formatting per locale
- RTL support for Arabic

### 4. **Easy Integration**
- Simple API for getting translations
- Localized UI components
- Minimal code changes required

## Usage

### Basic Translation

```python
from localization import get_text

# Get translated text
title = get_text('app.title')  # Returns "Audio/Video Transcription" in English
```

### Localized Components

```python
from localization.localized_ui import localized_button, localized_header

# Create localized button
if localized_button('auth.login'):
    # Handle login
    pass

# Create localized header
localized_header('results.transcript')
```

### Language Selection

```python
from localization import set_language, get_current_language, render_language_selector

# Set language programmatically
set_language('es')  # Switch to Spanish

# Get current language
current = get_current_language()  # Returns 'es'

# Render language selector widget
render_language_selector()
```

### Page Setup

```python
from localization.localized_ui import render_localized_page_header

# Apply localization settings to page
render_localized_page_header()
```

## Translation Keys

Translation keys follow a hierarchical naming convention:

- `app.*` - Application-level translations
- `nav.*` - Navigation items
- `auth.*` - Authentication-related
- `upload.*` - File upload interface
- `results.*` - Results display
- `teams.*` - Team features
- `action.*` - Common actions
- `message.*` - Status messages
- `settings.*` - Settings interface

## Adding New Translations

### 1. Add Translation Key

Edit `translations.py` and add your new key:

```python
'feature.new_button': {
    'en': 'New Feature',
    'es': 'Nueva Función',
    'fr': 'Nouvelle Fonctionnalité',
    # ... add for all languages
}
```

### 2. Use in Code

```python
button_text = get_text('feature.new_button')
```

### 3. With Parameters

```python
# In translations.py
'message.welcome_user': {
    'en': 'Welcome, {username}!',
    'es': '¡Bienvenido, {username}!',
}

# In code
welcome = get_text('message.welcome_user', username='John')
```

## Localized Formatting

### Dates

```python
from localization.localized_ui import format_localized_date
from datetime import datetime

date = datetime.now()
short_date = format_localized_date(date, 'short')  # 01/31/2025 (en)
long_date = format_localized_date(date, 'long')    # January 31, 2025 (en)
```

### Numbers

```python
from localization.localized_ui import format_localized_number

number = 1234567.89
formatted = format_localized_number(number, 2)  # 1,234,567.89 (en)
                                               # 1.234.567,89 (de)
```

## RTL Support

Arabic language automatically applies RTL (Right-to-Left) styling:

```python
# Automatically applied when Arabic is selected
if get_current_language() == 'ar':
    # RTL styles are applied to the entire app
```

## Translation Management

### Check Translation Coverage

```python
from localization.language_manager import get_language_manager

manager = get_language_manager()
coverage = manager.get_translation_coverage('es')  # Returns percentage
missing = manager.get_missing_translations('es')   # Returns list of missing keys
```

### Export/Import Translations

```python
# Export all translations for a language
translations = manager.export_translations('es')

# Import translations
manager.import_translations('es', translations)
```

## Best Practices

1. **Always use translation keys** instead of hardcoded strings
2. **Keep keys descriptive** and hierarchical
3. **Provide translations for all languages** when adding new keys
4. **Test with different languages** to ensure UI works properly
5. **Consider text length** - some languages need more space
6. **Use parameters** for dynamic content instead of concatenation

## Testing

Run the localization test script:

```bash
streamlit run test_localization.py
```

This will show all localization features in action.

## Troubleshooting

### Translation Not Showing

1. Check if key exists in `translations.py`
2. Verify language code is correct
3. Check for typos in translation key
4. Look for errors in console

### Language Not Persisting

1. Check if preference file is writable: `~/.transcription_app_language.json`
2. Verify session state is initialized
3. Check browser cookies/local storage

### RTL Issues

1. Ensure Arabic ('ar') is selected
2. Check for custom CSS overrides
3. Verify Streamlit version supports RTL

## Future Enhancements

- [ ] Add more languages (Hindi, Russian, etc.)
- [ ] Automatic translation using APIs
- [ ] Locale-specific audio processing
- [ ] Cultural adaptations
- [ ] Pluralization support
- [ ] Context-aware translations