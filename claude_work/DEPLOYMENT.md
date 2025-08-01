# Production Deployment Guide

## Overview

This guide covers production deployment of the Audio/Video Transcription and Entity Extraction App with considerations for scaling, monitoring, and security.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Production Configuration](#production-configuration)
3. [Docker Deployment](#docker-deployment)
4. [Scaling Considerations](#scaling-considerations)
5. [Monitoring and Health Checks](#monitoring-and-health-checks)
6. [Security Configuration](#security-configuration)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Valid API keys for OpenAI and ElevenLabs
- SSL certificates (for HTTPS)
- Minimum 2GB RAM, 2 CPU cores
- 10GB available disk space

### Basic Production Deployment

1. **Clone and Configure**
   ```bash
   git clone <repository-url>
   cd audio-video-transcription-app
   cp .env.example .env
   ```

2. **Set Environment Variables**
   ```bash
   # Required API Keys
   OPENAI_API_KEY=sk-your-openai-key-here
   ELEVENLABS_API_KEY=your-elevenlabs-key-here
   
   # Production Settings
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   MAX_FILE_SIZE_MB=100
   ADMIN_PASSWORD=your-secure-admin-password
   
   # Security
   STREAMLIT_COOKIE_SECRET=your-random-secret-key
   ENABLE_CORS=false
   
   # Resource Limits
   CPU_LIMIT=2.0
   MEMORY_LIMIT=2G
   ```

3. **Deploy with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Verify Deployment**
   ```bash
   curl http://localhost:8501/health
   ```

## Production Configuration

### Environment Variables

#### Required Configuration
```bash
# API Keys (Required)
OPENAI_API_KEY=sk-your-openai-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here

# Security (Required for production)
ADMIN_PASSWORD=your-secure-password
STREAMLIT_COOKIE_SECRET=your-random-secret-key
```

#### Optional Configuration
```bash
# Application Settings
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
MAX_FILE_SIZE_MB=100             # Maximum upload size
TEMP_DIR=/app/temp               # Temporary files directory
WHISPER_MODEL=base               # tiny, base, small, medium, large
SPACY_MODEL=en_core_web_sm       # spaCy model name

# Performance Settings
MAX_CONCURRENT_REQUESTS=5        # Concurrent processing limit
REQUEST_TIMEOUT=300              # Request timeout in seconds
CPU_LIMIT=2.0                    # Docker CPU limit
MEMORY_LIMIT=2G                  # Docker memory limit

# Network Settings
APP_PORT=8501                    # Application port
HTTP_PORT=80                     # HTTP port (nginx)
HTTPS_PORT=443                   # HTTPS port (nginx)
ENABLE_CORS=false                # CORS settings

# Monitoring
ENABLE_METRICS=true              # Enable metrics collection
METRICS_PORT=9090                # Metrics endpoint port
PROMETHEUS_PORT=9090             # Prometheus port
GRAFANA_PORT=3000                # Grafana port
GRAFANA_ADMIN_PASSWORD=admin     # Grafana admin password
```

### SSL Configuration

1. **Generate SSL Certificates**
   ```bash
   mkdir -p nginx/ssl
   
   # Self-signed certificate (development)
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/ssl/server.key \
     -out nginx/ssl/server.crt
   
   # Or use Let's Encrypt (production)
   certbot certonly --standalone -d your-domain.com
   cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
   cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
   ```

2. **Configure Nginx**
   ```bash
   # Create nginx configuration
   mkdir -p nginx
   ```

## Docker Deployment

### Single Container Deployment

```bash
# Build and run single container
docker build -t transcription-app .
docker run -d \
  --name transcription-app \
  -p 8501:8501 \
  -e OPENAI_API_KEY=your-key \
  -e ELEVENLABS_API_KEY=your-key \
  -v $(pwd)/temp:/app/temp \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  transcription-app
```

### Multi-Container with Docker Compose

```bash
# Production deployment with all services
docker-compose --profile monitoring up -d

# Basic deployment without monitoring
docker-compose up -d

# Scale the application
docker-compose up -d --scale transcription-app=3
```

### Container Health Checks

The application includes comprehensive health checks:

- **Basic Health**: `GET /health` - Simple status check
- **Detailed Health**: `GET /health-detailed` - Full system status
- **Metrics**: `GET /metrics` - Prometheus-compatible metrics

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer Configuration**
   ```nginx
   upstream transcription_backend {
       server transcription-app-1:8501;
       server transcription-app-2:8501;
       server transcription-app-3:8501;
   }
   
   server {
       listen 80;
       location / {
           proxy_pass http://transcription_backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. **Session Affinity**
   - Use sticky sessions for file uploads
   - Consider shared storage for temp files
   - Implement session state persistence

### Vertical Scaling

1. **Resource Allocation**
   ```yaml
   # docker-compose.yml
   services:
     transcription-app:
       deploy:
         resources:
           limits:
             cpus: '4.0'      # Increase CPU
             memory: 8G       # Increase memory
           reservations:
             cpus: '1.0'
             memory: 1G
   ```

2. **Performance Tuning**
   ```bash
   # Environment variables for performance
   MAX_CONCURRENT_REQUESTS=10    # Increase concurrent processing
   WHISPER_MODEL=small          # Use smaller model for speed
   REQUEST_TIMEOUT=600          # Increase timeout for large files
   ```

### Database Integration (Future)

For high-scale deployments, consider:
- PostgreSQL for user data and session management
- Redis for caching and session storage
- S3-compatible storage for file persistence

## Monitoring and Health Checks

### Health Check Endpoints

1. **Basic Health Check**
   ```bash
   curl http://localhost:8501/health
   # Response: {"status": "ok", "timestamp": "2024-01-01T12:00:00Z"}
   ```

2. **Detailed Health Check**
   ```bash
   curl http://localhost:8501/health-detailed
   # Returns comprehensive system status
   ```

3. **Metrics Endpoint**
   ```bash
   curl http://localhost:8501/metrics
   # Returns Prometheus-compatible metrics
   ```

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'transcription-app'
    static_configs:
      - targets: ['transcription-app:8501']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Grafana Dashboards

Key metrics to monitor:
- Request rate and response time
- CPU and memory usage
- API call success/failure rates
- File processing queue length
- Error rates by type

### Log Aggregation

```bash
# View application logs
docker-compose logs -f transcription-app

# View specific log files
docker exec transcription-app tail -f /app/logs/app.log
docker exec transcription-app tail -f /app/logs/app_errors.log
docker exec transcription-app tail -f /app/logs/app_performance.log
```

## Security Configuration

### API Key Management

1. **Environment Variables**
   ```bash
   # Use Docker secrets in production
   echo "sk-your-openai-key" | docker secret create openai_api_key -
   echo "your-elevenlabs-key" | docker secret create elevenlabs_api_key -
   ```

2. **Key Rotation**
   ```bash
   # Update API keys without downtime
   docker-compose exec transcription-app \
     sh -c 'export OPENAI_API_KEY=new-key && supervisorctl restart app'
   ```

### Network Security

1. **Firewall Configuration**
   ```bash
   # Allow only necessary ports
   ufw allow 80/tcp    # HTTP
   ufw allow 443/tcp   # HTTPS
   ufw deny 8501/tcp   # Block direct app access
   ```

2. **Reverse Proxy Security**
   ```nginx
   # nginx security headers
   add_header X-Frame-Options DENY;
   add_header X-Content-Type-Options nosniff;
   add_header X-XSS-Protection "1; mode=block";
   add_header Strict-Transport-Security "max-age=31536000";
   ```

### Container Security

1. **Non-root User**
   - Application runs as non-root user
   - Read-only filesystem where possible
   - Minimal base image (Python slim)

2. **Security Scanning**
   ```bash
   # Scan for vulnerabilities
   docker scan transcription-app
   
   # Update base images regularly
   docker-compose pull
   docker-compose up -d
   ```

## Performance Optimization

### Application Tuning

1. **Model Selection**
   ```bash
   # Balance accuracy vs speed
   WHISPER_MODEL=base     # Good balance
   WHISPER_MODEL=small    # Faster, less accurate
   WHISPER_MODEL=large    # Slower, more accurate
   ```

2. **Concurrent Processing**
   ```bash
   # Adjust based on available resources
   MAX_CONCURRENT_REQUESTS=5    # Conservative
   MAX_CONCURRENT_REQUESTS=10   # Aggressive (requires more CPU/memory)
   ```

### Infrastructure Optimization

1. **Storage Performance**
   ```bash
   # Use SSD storage for temp files
   # Mount temp directory on fast storage
   -v /fast-ssd/temp:/app/temp
   ```

2. **Network Optimization**
   ```bash
   # Use CDN for static assets
   # Optimize API call patterns
   # Implement request caching
   ```

### Caching Strategy

1. **Model Caching**
   - Cache downloaded models between restarts
   - Use persistent volumes for model storage

2. **Result Caching**
   - Cache transcription results for duplicate files
   - Implement Redis for distributed caching

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   docker stats transcription-app
   
   # Solutions:
   # - Reduce MAX_CONCURRENT_REQUESTS
   # - Use smaller Whisper model
   # - Increase container memory limit
   ```

2. **API Rate Limits**
   ```bash
   # Check API status
   curl http://localhost:8501/health-detailed
   
   # Solutions:
   # - Implement exponential backoff
   # - Use local models as fallback
   # - Monitor API usage
   ```

3. **File Processing Failures**
   ```bash
   # Check logs
   docker-compose logs transcription-app | grep ERROR
   
   # Common causes:
   # - Insufficient disk space
   # - Unsupported file formats
   # - Network connectivity issues
   ```

### Log Analysis

```bash
# Error analysis
grep "ERROR" logs/app.log | tail -20

# Performance analysis
grep "PERFORMANCE" logs/app_performance.log | tail -20

# Security events
grep "SECURITY" logs/app_security.log | tail -20
```

### Health Check Debugging

```bash
# Test health endpoints
curl -v http://localhost:8501/health
curl -v http://localhost:8501/health-detailed
curl -v http://localhost:8501/metrics

# Check container health
docker inspect transcription-app | grep -A 10 Health
```

## Backup and Recovery

### Data Backup

```bash
# Backup configuration
tar -czf config-backup.tar.gz .env docker-compose.yml nginx/

# Backup logs
tar -czf logs-backup.tar.gz logs/

# Backup user data (if applicable)
docker run --rm -v transcription_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/data-backup.tar.gz /data
```

### Disaster Recovery

1. **Service Recovery**
   ```bash
   # Quick restart
   docker-compose restart
   
   # Full rebuild
   docker-compose down
   docker-compose up -d --build
   ```

2. **Data Recovery**
   ```bash
   # Restore from backup
   tar -xzf data-backup.tar.gz
   docker-compose up -d
   ```

## Maintenance

### Regular Tasks

1. **Log Rotation**
   - Logs automatically rotate (configured in utils.py)
   - Monitor disk usage: `df -h`

2. **Security Updates**
   ```bash
   # Update base images monthly
   docker-compose pull
   docker-compose up -d
   
   # Update Python dependencies
   pip-audit  # Check for vulnerabilities
   ```

3. **Performance Monitoring**
   - Review metrics weekly
   - Analyze error patterns
   - Optimize based on usage patterns

### Upgrade Process

1. **Preparation**
   ```bash
   # Backup current deployment
   docker-compose down
   tar -czf deployment-backup.tar.gz .
   ```

2. **Deployment**
   ```bash
   # Pull new version
   git pull origin main
   
   # Update and restart
   docker-compose up -d --build
   ```

3. **Verification**
   ```bash
   # Test health endpoints
   curl http://localhost:8501/health
   
   # Check logs for errors
   docker-compose logs -f transcription-app
   ```

## Support and Resources

### Documentation
- [API Documentation](API.md)
- [Configuration Guide](config.py)
- [Security Best Practices](SECURITY.md)

### Monitoring Resources
- Grafana dashboards in `monitoring/grafana/`
- Prometheus configuration in `monitoring/prometheus.yml`
- Alert rules in `monitoring/alerts/`

### Community
- GitHub Issues: Report bugs and feature requests
- Discussions: Community support and questions
- Wiki: Additional documentation and examples

---

For additional support or questions about production deployment, please refer to the project documentation or open an issue on GitHub.