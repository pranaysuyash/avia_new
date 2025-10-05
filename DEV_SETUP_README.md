# Development Setup - AI Media Platform

## Quick Start

### Option 1: Python Script (Recommended)
```bash
python start_dev_stack.py
```

### Option 2: Shell Script
```bash
./start_dev_stack.sh
```

Both scripts will:
1. Start the backend API server on `http://localhost:8000`
2. Start the frontend development server on `http://localhost:5173`
3. Provide live reload for both services
4. Handle graceful shutdown with Ctrl+C

## What's Included

### Backend API Server (`backend_server.py`)
- **FastAPI** server with mock data for development
- **CORS enabled** for frontend development
- **Auto-reload** enabled for development
- **API Documentation** at `http://localhost:8000/docs`

### Frontend Development Server
- **Vite** development server with hot reload
- **Development mode** with fallback data when backend is unavailable
- **TypeScript** compilation and error checking
- **Tailwind CSS** with live updates

## Development Features

### 🔧 Backend API Endpoints
- `GET /api/health` - Health check
- `POST /api/auth/login` - Authentication (dev@example.com / password)
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/dashboard/recent-jobs` - Recent processing jobs
- `GET /api/dashboard/system-status` - System status
- `GET /api/ai/engines/status` - AI engines status
- `POST /api/media_ingestion` - File upload
- And many more...

### 🎨 Frontend Features
- **Development Mode**: Automatically detects if backend is unavailable and shows mock data
- **Real-time Updates**: Dashboard refreshes automatically when backend is available
- **Authentication**: Login with dev@example.com / password
- **Responsive Design**: Works on desktop and mobile
- **Dark/Light Theme**: System theme detection

## Login Credentials

For testing the authentication system:
- **Email**: `dev@example.com`
- **Password**: `password`

## Development Workflow

1. **Start the development stack**:
   ```bash
   python start_dev_stack.py
   ```

2. **Open your browser**:
   - Frontend: http://localhost:5173
   - Backend API Docs: http://localhost:8000/docs

3. **Make changes**:
   - Backend changes auto-reload the API server
   - Frontend changes hot-reload in the browser

4. **Stop the servers**:
   - Press `Ctrl+C` in the terminal

## Development Mode Features

The frontend automatically detects if the backend is unavailable and switches to **Development Mode**:

- ✅ Shows mock data when backend is offline
- ✅ Displays "Development Mode" badge in the UI
- ✅ Automatically switches to real data when backend comes online
- ✅ No authentication required in development mode
- ✅ All UI components work with realistic mock data

## File Structure

```
├── backend_server.py           # Development API server
├── start_dev_stack.py         # Python startup script
├── start_dev_stack.sh         # Shell startup script
├── frontend-v2/               # Modern React frontend
│   ├── src/
│   │   ├── hooks/
│   │   │   ├── useAuth.ts     # Authentication hook
│   │   │   ├── useDashboard.ts # Dashboard data hook
│   │   │   └── useDevelopmentMode.ts # Development mode detection
│   │   ├── lib/
│   │   │   └── api-client.ts  # API client with error handling
│   │   └── components/        # React components
│   └── package.json
└── requirements.txt           # Python dependencies (already installed)
```

## Troubleshooting

### Backend Issues
- **Port 8000 in use**: Kill existing processes with `pkill -f backend_server.py`
- **Import errors**: Make sure you're in the virtual environment (`source venv/bin/activate`)

### Frontend Issues
- **Port 5173 in use**: The script will automatically find an available port
- **Build errors**: Run `npm install` in the `frontend-v2` directory
- **TypeScript errors**: Check the console output for specific error details

### General Issues
- **Permission denied**: Make scripts executable with `chmod +x start_dev_stack.sh`
- **Dependencies missing**: All Python dependencies should already be in your virtual environment

## Production vs Development

| Feature | Development | Production |
|---------|-------------|------------|
| Authentication | Optional (mock user) | Required (real JWT) |
| Data Source | Mock data fallback | Real database |
| API Server | Simple FastAPI | Full backend services |
| Error Handling | Development-friendly | Production-ready |
| Performance | Development optimized | Production optimized |

## Next Steps

1. **Backend Development**: Replace mock endpoints in `backend_server.py` with real implementations
2. **Database Integration**: Connect to actual database instead of mock data
3. **Authentication**: Implement real JWT authentication system
4. **File Processing**: Connect to actual media processing services
5. **Deployment**: Use production-ready servers (Gunicorn, Nginx, etc.)

## Support

If you encounter any issues:
1. Check that you're in the virtual environment
2. Ensure all dependencies are installed (`pip list`)
3. Check the console output for specific error messages
4. Try restarting the development stack