# Running the Transcription Application

## Quick Start

The application has been set up with working scripts to run both the frontend and backend with full features.

### Start the Application

```bash
# Make the script executable (first time only)
chmod +x /Users/pranay/Projects/LLM/video/ner/start-working-app.sh

# Run the application
/Users/pranay/Projects/LLM/video/ner/start-working-app.sh
```

This will start:
- **Frontend**: http://localhost:3000 (React application)
- **Backend**: http://localhost:8000 (FastAPI with authentication)
- **API Docs**: http://localhost:8000/docs (Swagger documentation)

### Test Credentials

```
Email: test@example.com
Password: password
```

## Features Available

### ✅ Authentication System
- **Login**: Use the test credentials above
- **Register**: Create new user accounts
- **Logout**: Properly terminate sessions
- **JWT Tokens**: Secure token-based authentication
- **Protected Routes**: Access control for authenticated users

### ✅ Database Integration
- Connects to PostgreSQL if available
- Falls back to mock data if database is not running
- Retrieves existing transcriptions from database
- Supports full CRUD operations

### ✅ API Endpoints
- `/api/health` - Health check endpoint
- `/api/auth/login` - User login
- `/api/auth/register` - User registration
- `/api/auth/logout` - User logout
- `/api/auth/me` - Get current user
- `/api/transcriptions` - List transcriptions
- `/api/analytics/usage/weekly` - Weekly usage stats
- `/api/transcription/upload` - File upload

### ✅ Frontend Features
- Dashboard with statistics
- Transcription workspace
- File upload interface
- User profile management
- API connection status indicator
- Responsive design

## Stopping the Servers

The start script will display the process IDs. To stop:

```bash
# Using the PIDs shown in the startup message
kill [FRONTEND_PID] [BACKEND_PID]

# Or kill by port
lsof -ti:3000 | xargs kill -9  # Stop frontend
lsof -ti:8000 | xargs kill -9  # Stop backend
```

## Troubleshooting

### Backend Import Errors
If you see import errors for `get_current_user_flexible`, the working backend script (`run_working_backend.py`) provides a fully functional alternative that bypasses these issues.

### Database Connection
- If PostgreSQL is not running, the app will use mock data
- To use real data, ensure PostgreSQL is running:
  ```bash
  # macOS
  brew services start postgresql
  
  # Linux
  sudo systemctl start postgresql
  ```

### TypeScript Warnings
The React app shows TypeScript warnings about react-icons components. These are compilation warnings only and do not affect functionality. The app runs perfectly despite these warnings.

### API Connection Status
- ✅ **"API Connected"** - Backend is running and accessible
- ❌ **"API Disconnected"** - Backend is not running or has errors

## Alternative Startup Scripts

### 1. Simple Test Server (Basic functionality)
```bash
/Users/pranay/Projects/LLM/video/ner/test-servers-simple.sh
```

### 2. Full Backend (May have import issues)
```bash
/Users/pranay/Projects/LLM/video/ner/start-real-app.sh
```

### 3. Working Backend (Recommended)
```bash
/Users/pranay/Projects/LLM/video/ner/start-working-app.sh
```

## Manual Backend Start

If you need to run just the backend:

```bash
cd /Users/pranay/Projects/LLM/video/ner
python run_working_backend.py
```

## Manual Frontend Start

If you need to run just the frontend:

```bash
cd /Users/pranay/Projects/LLM/video/ner/desktop_app/src/renderer
npm start
```

## Testing the Application

1. **Login Flow**:
   - Navigate to http://localhost:3000
   - Click "Sign In" or navigate to login
   - Enter test@example.com / password
   - Verify redirect to dashboard

2. **Check API Connection**:
   - Look for "API Connected" indicator
   - Dashboard should load with data

3. **Test Transcriptions**:
   - Navigate to History or Transcriptions
   - Should see list of transcriptions (mock or real)

4. **Test Logout**:
   - Click on user menu
   - Select logout
   - Verify redirect to login page

## Production Deployment

For production deployment instructions, see:
`/Users/pranay/Projects/LLM/video/ner/claude_work/PRODUCTION_DEPLOYMENT.md`

## API Integration

The backend provides a full REST API with:
- Swagger documentation at http://localhost:8000/docs
- ReDoc documentation at http://localhost:8000/redoc
- OpenAPI schema at http://localhost:8000/openapi.json

## Notes

- The working backend script includes both real database integration and mock data fallback
- Authentication uses JWT tokens stored in localStorage
- CORS is configured for http://localhost:3000
- The backend will auto-reload on code changes when using the startup scripts
- Frontend hot-reloading is enabled for development

Last updated: 2025-08-03