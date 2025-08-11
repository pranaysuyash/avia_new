# Whisper Advanced Integration - Installation Guide

## 🎯 Overview

This guide provides step-by-step instructions for installing and setting up the Whisper Advanced Integration system in different environments.

## 🖥️ System Requirements

### Minimum Requirements
- **CPU**: 2+ cores, 2.0 GHz
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Stable internet connection
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

### Recommended Requirements
- **CPU**: 4+ cores, 3.0 GHz
- **RAM**: 16GB for optimal performance
- **Storage**: 10GB free space (for models and cache)
- **Network**: High-speed broadband
- **GPU**: CUDA-compatible GPU (optional, for acceleration)

## 🐍 Python Environment Setup

### 1. Install Python

**Windows:**
```bash
# Download from python.org or use chocolatey
choco install python

# Verify installation
python --version
```

**macOS:**
```bash
# Using Homebrew
brew install python

# Verify installation
python3 --version
```

**Ubuntu/Debian:**
```bash
# Update package list
sudo apt update

# Install Python
sudo apt install python3 python3-pip python3-venv

# Verify installation
python3 --version
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv whisper_env

# Activate virtual environment
# Windows:
whisper_env\Scripts\activate

# macOS/Linux:
source whisper_env/bin/activate

# Verify activation (should show whisper_env)
which python
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install -r requirements.txt

# Install additional dependencies for development
pip install -r requirements-dev.txt
```

## 🌐 Web Application Setup

### 1. Frontend Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Build for production
npm run build

# Start development server
npm run dev
```

### 2. Backend API Setup

```bash
# Install FastAPI dependencies
pip install fastapi uvicorn python-multipart

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"

# Start API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Database Setup

```bash
# Install database dependencies
pip install sqlalchemy alembic psycopg2-binary

# Initialize database
alembic upgrade head

# Create initial data (optional)
python scripts/init_db.py
```

## 📱 Mobile Application Setup

### 1. React Native Environment

**Install React Native CLI:**
```bash
npm install -g react-native-cli
```

**iOS Setup (macOS only):**
```bash
# Install Xcode from App Store
# Install CocoaPods
sudo gem install cocoapods

# Navigate to mobile directory
cd mobile

# Install dependencies
npm install

# Install iOS dependencies
cd ios && pod install && cd ..
```

**Android Setup:**
```bash
# Install Android Studio
# Set ANDROID_HOME environment variable
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools

# Navigate to mobile directory
cd mobile

# Install dependencies
npm install
```

### 2. Build and Run Mobile App

**iOS:**
```bash
# Run on iOS simulator
npx react-native run-ios

# Run on specific device
npx react-native run-ios --device "iPhone Name"
```

**Android:**
```bash
# Start Android emulator first
# Then run on Android
npx react-native run-android

# Run on specific device
npx react-native run-android --deviceId=device_id
```

## 🐳 Docker Setup

### 1. Using Docker Compose

```bash
# Clone repository
git clone https://github.com/your-org/whisper-advanced-integration.git
cd whisper-advanced-integration

# Copy environment file
cp .env.example .env

# Edit environment variables
nano .env

# Build and start services
docker-compose up --build

# Run in background
docker-compose up -d
```

### 2. Individual Docker Containers

**Backend API:**
```bash
# Build backend image
docker build -t whisper-api -f Dockerfile.api .

# Run backend container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -e ELEVENLABS_API_KEY=your-key \
  whisper-api
```

**Frontend:**
```bash
# Build frontend image
docker build -t whisper-frontend -f Dockerfile.frontend .

# Run frontend container
docker run -p 3000:3000 whisper-frontend
```

## ☁️ Cloud Deployment

### 1. AWS Deployment

**Using AWS ECS:**
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Create ECS cluster
aws ecs create-cluster --cluster-name whisper-cluster

# Deploy using CloudFormation
aws cloudformation deploy \
  --template-file cloudformation/whisper-stack.yaml \
  --stack-name whisper-advanced \
  --capabilities CAPABILITY_IAM
```

**Using AWS Lambda:**
```bash
# Install Serverless Framework
npm install -g serverless

# Deploy serverless functions
serverless deploy --stage production
```

### 2. Google Cloud Platform

```bash
# Install Google Cloud SDK
# Configure authentication
gcloud auth login

# Set project
gcloud config set project your-project-id

# Deploy to Cloud Run
gcloud run deploy whisper-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 3. Microsoft Azure

```bash
# Install Azure CLI
# Login to Azure
az login

# Create resource group
az group create --name whisper-rg --location eastus

# Deploy to Container Instances
az container create \
  --resource-group whisper-rg \
  --name whisper-api \
  --image your-registry/whisper-api:latest \
  --ports 8000
```

## 🔧 Configuration

### 1. Environment Variables

Create `.env` file in project root:

```bash
# API Configuration
OPENAI_API_KEY=your-openai-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key
API_BASE_URL=http://localhost:8000

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/whisper_db

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=whisper.log

# Security Configuration
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret

# File Upload Configuration
MAX_FILE_SIZE_MB=25
UPLOAD_DIR=uploads

# Performance Configuration
WORKER_PROCESSES=4
WORKER_TIMEOUT=300
```

### 2. Application Configuration

Edit `config/settings.py`:

```python
# Whisper Model Configuration
WHISPER_MODELS = {
    "whisper-1": {
        "max_file_size": 25 * 1024 * 1024,  # 25MB
        "supported_formats": ["mp3", "wav", "m4a", "flac"],
        "default_temperature": 0.0
    }
}

# Audio Processing Configuration
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "channels": 1,
    "bit_depth": 16,
    "chunk_size": 1024
}

# Cache Configuration
CACHE_CONFIG = {
    "backend": "redis",
    "timeout": 3600,
    "max_entries": 1000
}
```

## 🧪 Testing Installation

### 1. Run Test Suite

```bash
# Activate virtual environment
source whisper_env/bin/activate

# Run all tests
python run_tests.py --mode all

# Run specific test categories
python run_tests.py --mode unit
python run_tests.py --mode integration
python run_tests.py --mode api
```

### 2. Health Checks

```bash
# Check API health
curl http://localhost:8000/api/v1/whisper-advanced/health

# Check frontend
curl http://localhost:3000

# Check database connection
python -c "from database import engine; print('DB OK' if engine.connect() else 'DB Error')"
```

### 3. Sample Transcription

```bash
# Test with sample audio file
curl -X POST \
  -H "Authorization: Bearer your-api-key" \
  -F "audio_file=@sample.wav" \
  -F 'config={"model":"whisper-1","temperature":0.0}' \
  http://localhost:8000/api/v1/whisper-advanced/transcribe
```

## 🔍 Troubleshooting Installation

### Common Issues

**1. Python Version Conflicts:**
```bash
# Use specific Python version
python3.9 -m venv whisper_env

# Or use pyenv
pyenv install 3.9.0
pyenv local 3.9.0
```

**2. Permission Errors:**
```bash
# Fix permissions on Unix systems
sudo chown -R $USER:$USER whisper_env
chmod +x scripts/*.sh
```

**3. Port Conflicts:**
```bash
# Check what's using port 8000
lsof -i :8000

# Kill process if needed
kill -9 PID

# Use different port
uvicorn api.main:app --port 8001
```

**4. Memory Issues:**
```bash
# Increase swap space (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Monitor memory usage
htop
```

**5. Network Issues:**
```bash
# Test connectivity
ping api.openai.com
curl -I https://api.openai.com/v1/models

# Check firewall
sudo ufw status
```

## 📋 Post-Installation Checklist

- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] API server running
- [ ] Frontend application accessible
- [ ] Health checks passing
- [ ] Sample transcription working
- [ ] Tests passing
- [ ] Logs being generated
- [ ] Error handling working
- [ ] Authentication configured
- [ ] File uploads working
- [ ] Mobile app building (if applicable)

## 🔄 Updates and Maintenance

### Regular Updates

```bash
# Update Python dependencies
pip install --upgrade -r requirements.txt

# Update Node.js dependencies
npm update

# Update system packages (Ubuntu)
sudo apt update && sudo apt upgrade
```

### Backup Procedures

```bash
# Backup database
pg_dump whisper_db > backup_$(date +%Y%m%d).sql

# Backup configuration
tar -czf config_backup.tar.gz config/ .env

# Backup uploaded files
tar -czf uploads_backup.tar.gz uploads/
```

### Monitoring Setup

```bash
# Install monitoring tools
pip install prometheus-client grafana-api

# Setup log rotation
sudo logrotate -f /etc/logrotate.d/whisper

# Monitor disk space
df -h
du -sh uploads/
```

This installation guide provides comprehensive instructions for setting up the Whisper Advanced Integration system in various environments. Follow the steps appropriate for your deployment scenario and refer to the troubleshooting section if you encounter any issues.