# EPIPE Error Fix for Electron App

## Problem
The Electron app was encountering EPIPE (Broken Pipe) errors when attempting to write to console:
```
Error: write EPIPE
at afterWriteDispatched (node:internal/stream_base_commons:159:15)
at writeGeneric (node:internal/stream_base_commons:150:3)
...
```

This error occurs when:
1. The console output stream is closed unexpectedly
2. electron-log tries to write to a non-existent console
3. The app is running in production mode without a console
4. IPC communication breaks between main and renderer processes

## Solution Implemented

### 1. Enhanced electron-log Configuration (`src/main.js`)
- Added EPIPE error handling to electron-log
- Disabled console transport in production mode
- Added error catching with specific EPIPE handling

### 2. Safe Logger Utility (`src/safe-logger.js`)
- Created a wrapper around console methods
- Automatically falls back to file logging when console is unavailable
- Silently handles EPIPE errors without crashing

### 3. Process-Level Error Handlers
- Added uncaughtException handler to catch EPIPE errors
- Added unhandledRejection handler for promise rejections
- Added warning handler to suppress EPIPE warnings

### 4. Updated Logging Calls
- Replaced direct console.log/error calls with safeLogger
- Added safeLogger before executeJavaScript calls
- Updated native-integrations.js to use safe logging

## Files Modified
1. `/desktop_app/src/main.js` - Enhanced error handling and logging configuration
2. `/desktop_app/src/safe-logger.js` - New safe logging utility (created)
3. `/desktop_app/src/native-integrations.js` - Updated to use safe logging

## How It Works

### Safe Logger Flow:
```javascript
1. Try to write to console
2. If EPIPE error occurs:
   - Mark console as unavailable
   - Use electron-log file transport instead
3. Continue logging without interruption
```

### Error Handling Hierarchy:
1. **Safe Logger** - First line of defense, wraps console methods
2. **electron-log** - Catches errors in logging transport
3. **Process handlers** - Catch any uncaught exceptions/rejections

## Testing
To test if the fix works:
1. Run the app in production mode: `npm run build && npm start`
2. Check logs in: `~/Library/Logs/transcription-desktop/main.log` (macOS)
3. No EPIPE errors should appear in the logs
4. App should continue running even if console is unavailable

## Benefits
- ✅ No more EPIPE crashes
- ✅ Graceful fallback to file logging
- ✅ Better debugging in production
- ✅ Cleaner error logs
- ✅ App stability improved

## Future Improvements
- Consider implementing a circular buffer for recent logs
- Add remote logging capability for production debugging
- Implement log rotation to prevent large log files
- Add structured logging with context

## Note
The EPIPE error is now handled gracefully and won't crash the application. Logs will automatically switch to file-based logging when console is unavailable.