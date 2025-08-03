# Validation Centralization Guide

## Overview

This guide documents the centralization of validation logic in the `utils.py` module to improve code maintainability and consistency across the application.

## Centralized Validation Functions

### 1. Email Validation
```python
from utils import validate_email

# Usage
if not validate_email(user_email):
    raise ValueError("Invalid email address")
```

### 2. Phone Number Validation
```python
from utils import validate_phone_number

# Supports various formats: +1234567890, (123) 456-7890, etc.
if not validate_phone_number(phone):
    raise ValueError("Invalid phone number")
```

### 3. URL Validation
```python
from utils import validate_url

# Validates HTTP/HTTPS URLs
if not validate_url(website):
    raise ValueError("Invalid URL")
```

### 4. File Extension Validation
```python
from utils import validate_file_extension, AUDIO_EXTENSIONS, VIDEO_EXTENSIONS

# Check if file has valid audio extension
if not validate_file_extension(filename, AUDIO_EXTENSIONS):
    raise ValueError("Invalid audio file format")
```

### 5. Content Type Validation
```python
from utils import validate_content_type, AUDIO_CONTENT_TYPES

# Supports wildcards like 'audio/*'
if not validate_content_type(content_type, AUDIO_CONTENT_TYPES):
    raise ValueError("Invalid content type")
```

### 6. Language Code Validation
```python
from utils import validate_language_code

# Default supported languages or custom list
if not validate_language_code(lang_code):
    raise ValueError("Unsupported language")

# Custom languages
if not validate_language_code(lang_code, ['en', 'es', 'fr']):
    raise ValueError("Language not in allowed list")
```

### 7. Model Name Validation
```python
from utils import validate_model_name

# Default Whisper models or custom list
if not validate_model_name(model):
    raise ValueError("Invalid model name")
```

### 8. Media File Validation
```python
from utils import validate_media_file

# Validates audio, video, or image files
is_valid, media_type = validate_media_file(filename, content_type)
if not is_valid:
    raise ValueError("Invalid media file")
```

### 9. Filename Sanitization
```python
from utils import sanitize_filename

# Removes dangerous characters and limits length
safe_name = sanitize_filename(user_provided_filename)
```

### 10. JSON Structure Validation
```python
from utils import validate_json_structure

# Check required fields
is_valid, error = validate_json_structure(data, ['name', 'email', 'age'])
if not is_valid:
    raise ValueError(error)
```

### 11. Date Range Validation
```python
from utils import validate_date_range

# Validates ISO format dates and ensures start < end
is_valid, error = validate_date_range(start_date, end_date)
if not is_valid:
    raise ValueError(error)
```

### 12. Pagination Parameters
```python
from utils import validate_pagination_params

# Validates page number and items per page
is_valid, error = validate_pagination_params(page, per_page, max_per_page=100)
if not is_valid:
    raise ValueError(error)
```

## Pre-defined Constants

### File Extensions
- `AUDIO_EXTENSIONS`: ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma', '.opus']
- `VIDEO_EXTENSIONS`: ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v']
- `IMAGE_EXTENSIONS`: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff']
- `DOCUMENT_EXTENSIONS`: ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt']

### Content Types
- `AUDIO_CONTENT_TYPES`: Includes 'audio/*' wildcard
- `VIDEO_CONTENT_TYPES`: Includes 'video/*' wildcard
- `IMAGE_CONTENT_TYPES`: Includes 'image/*' wildcard
- `DOCUMENT_CONTENT_TYPES`: Common document MIME types

## Migration Examples

### Before (in API endpoints):
```python
# In transcription.py
allowed_types = {
    'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
    'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm'
}
allowed_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.avi', '.mov', '.mkv', '.webm'}

if file.content_type not in allowed_types and file_extension not in allowed_extensions:
    raise HTTPException(status_code=415, detail="Unsupported file type")
```

### After (using centralized validation):
```python
from utils import validate_media_file

is_valid, media_type = validate_media_file(file.filename, file.content_type)
if not is_valid or media_type not in ['audio', 'video']:
    raise HTTPException(status_code=415, detail="Unsupported file type")
```

### Before (in Pydantic models):
```python
@validator('language')
def validate_language(cls, v):
    valid_languages = ['auto', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
    if v not in valid_languages:
        raise ValueError(f'Language must be one of {valid_languages}')
    return v
```

### After (using centralized validation):
```python
from utils import validate_language_code

@validator('language')
def validate_language(cls, v):
    if not validate_language_code(v):
        raise ValueError(f'Invalid language code: {v}')
    return v
```

## Benefits

1. **Consistency**: Same validation logic across all modules
2. **Maintainability**: Update validation rules in one place
3. **Reusability**: No duplicate validation code
4. **Testing**: Easier to test validation logic
5. **Security**: Centralized filename sanitization and input validation
6. **Flexibility**: Support for custom validation lists

## Implementation Status

### Completed:
- ✅ Created centralized validation functions in utils.py
- ✅ Added file type validation with pre-defined constants
- ✅ Implemented media file validation (audio, video, image)
- ✅ Added sanitization functions for security
- ✅ Updated api/models.py to use centralized validation
- ✅ Created transcription_centralized.py as example implementation

### To Do:
- [ ] Update all API endpoints to use centralized validation
- [ ] Update Streamlit UI components to use centralized validation
- [ ] Add unit tests for all validation functions
- [ ] Update existing endpoints gradually to avoid breaking changes

## Testing Checklist

- [ ] Test email validation with various formats
- [ ] Test phone number validation with international formats
- [ ] Test file upload with all supported formats
- [ ] Test file upload with unsupported formats
- [ ] Test filename sanitization with malicious inputs
- [ ] Test pagination edge cases
- [ ] Test date range validation with invalid dates
- [ ] Test language and model validation

## Best Practices

1. Always sanitize user-provided filenames before storage
2. Use appropriate validation for the context (strict vs. lenient)
3. Provide clear error messages when validation fails
4. Consider performance for regex-based validations
5. Keep validation lists updated with new formats/types
6. Document any custom validation requirements