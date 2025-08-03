# Exception Handling Migration Guide

## Overview

This guide documents the improvements made to exception handling in the API endpoints to replace generic `except Exception:` blocks and dangerous bare `except:` blocks with specific exception handling.

## Files Improved

1. **api/endpoints/analytics.py** → **analytics_improved.py**
2. **api/endpoints/queue.py** → **queue_improved.py**
3. **api/endpoints/transcription.py** → **transcription_improved.py**
4. **api/endpoints/video.py** → **video_improved.py**

## Key Improvements

### 1. Specific Exception Types

Instead of catching all exceptions with `except Exception:`, we now catch specific exceptions:

```python
# Before
try:
    # code
except Exception as e:
    logger.error(f"Error: {e}")
    raise HTTPException(status_code=500, detail="Internal Server Error")

# After
try:
    # code
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    raise HTTPException(status_code=404, detail="File not found")
except PermissionError as e:
    logger.error(f"Permission denied: {e}")
    raise HTTPException(status_code=403, detail="Permission denied")
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
```

### 2. Appropriate HTTP Status Codes

Each exception type now returns an appropriate HTTP status code:

- **400 Bad Request**: `ValueError`, invalid parameters
- **403 Forbidden**: `PermissionError`, access denied
- **404 Not Found**: `FileNotFoundError`, missing resources
- **408 Request Timeout**: `asyncio.TimeoutError`, operation timeouts
- **413 Payload Too Large**: `MemoryError` for file uploads
- **415 Unsupported Media Type**: Invalid file formats
- **422 Unprocessable Entity**: `ValidationError`, invalid data format
- **500 Internal Server Error**: Only for truly unexpected errors
- **503 Service Unavailable**: `ImportError`, `AttributeError` for missing services
- **507 Insufficient Storage**: `OSError` with "No space left", `MemoryError`

### 3. Eliminated Bare Except Blocks

All bare `except:` blocks have been replaced:

```python
# Before (in video.py)
try:
    os.unlink(file_path)
except:
    pass

# After
try:
    os.unlink(file_path)
except FileNotFoundError:
    # File already deleted
    pass
except PermissionError as e:
    logger.warning(f"Cannot delete file {file_path}: Permission denied")
except OSError as e:
    logger.warning(f"Failed to delete file {file_path}: {e}")
```

### 4. Better Error Messages

Error messages now provide more context:

```python
# Before
raise HTTPException(status_code=500, detail="Failed to process")

# After
raise HTTPException(
    status_code=413,
    detail=f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size (2048MB)"
)
```

### 5. Exception Hierarchy

Common exception patterns across all endpoints:

#### File Operations
```python
except FileNotFoundError:
    # 404 Not Found
except PermissionError:
    # 403 Forbidden
except OSError as e:
    if "No space left" in str(e):
        # 507 Insufficient Storage
    else:
        # 500 Internal Server Error
except IOError:
    # 500 Internal Server Error
```

#### Data Processing
```python
except ValueError:
    # 400 Bad Request
except KeyError:
    # 400 Bad Request or continue processing
except TypeError:
    # 400 Bad Request or continue processing
except AttributeError:
    # 503 Service Unavailable (missing API)
```

#### Network/Async Operations
```python
except asyncio.TimeoutError:
    # 408 Request Timeout
except ConnectionError:
    # 503 Service Unavailable
except WebSocketDisconnect:
    # Handle gracefully
```

#### JSON Operations
```python
except json.JSONDecodeError:
    # 400 Bad Request
except json.JSONEncodeError:
    # Log but don't fail request
```

## Migration Steps

1. **Backup Current Files**
   ```bash
   cp api/endpoints/analytics.py api/endpoints/analytics.py.backup
   cp api/endpoints/queue.py api/endpoints/queue.py.backup
   cp api/endpoints/transcription.py api/endpoints/transcription.py.backup
   cp api/endpoints/video.py api/endpoints/video.py.backup
   ```

2. **Replace Files**
   ```bash
   mv api/endpoints/analytics_improved.py api/endpoints/analytics.py
   mv api/endpoints/queue_improved.py api/endpoints/queue.py
   mv api/endpoints/transcription_improved.py api/endpoints/transcription.py
   mv api/endpoints/video_improved.py api/endpoints/video.py
   ```

3. **Update Imports** (if needed)
   No import changes required - the improved files maintain the same API.

4. **Test Endpoints**
   Test each endpoint to ensure proper error handling:
   - Upload invalid file types
   - Upload oversized files
   - Access non-existent resources
   - Trigger timeout scenarios
   - Test with missing services

## Benefits

1. **Better Debugging**: Specific exceptions make it easier to identify issues
2. **Appropriate HTTP Codes**: Clients receive meaningful status codes
3. **No Hidden Errors**: Bare except blocks no longer hide problems
4. **Better User Experience**: Clear, actionable error messages
5. **Improved Logging**: Each exception type is logged appropriately

## Testing Checklist

- [ ] Test file upload with invalid format
- [ ] Test file upload exceeding size limit
- [ ] Test processing non-existent file
- [ ] Test with insufficient disk space
- [ ] Test WebSocket disconnection handling
- [ ] Test timeout scenarios
- [ ] Test with missing API keys/services
- [ ] Test concurrent request handling
- [ ] Test cleanup on errors

## Additional Notes

- The improved files log actual exceptions with `exc_info=True` only for unexpected errors
- Specific exceptions that are expected (like file not found during cleanup) are logged at warning level
- User-facing error messages don't expose internal implementation details
- All file operations include proper cleanup in error cases