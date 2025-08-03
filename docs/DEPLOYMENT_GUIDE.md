# Production Deployment Guide

## Overview

This guide covers the complete deployment process for the Video NER application, including CI/CD setup, Docker deployment, monitoring, and maintenance.

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL 15+
- Redis 7+
- Domain name with SSL certificates
- GitHub account (for CI/CD)
- Monitoring stack (Prometheus/Grafana) - optional

## Environment Setup

### 1. Environment Variables

Create a `.env.production` file with the following variables:

```bash
# Database
POSTGRES_USER=transcription_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=transcription_app

# Redis
REDIS_PASSWORD=your_redis_password

# Security
JWT_SECRET_KEY=your_jwt_secret_key
STREAMLIT_SERVER_COOKIE_SECRET=your_cookie_secret
SECURITY_MASTER_KEY=your_master_key

# API Keys
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Monitoring
GRAFANA_PASSWORD=your_grafana_password
SENTRY_DSN=your_sentry_dsn

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 2. SSL Certificates

Place your SSL certificates in the `ssl/` directory:

```
ssl/
├── cert.pem
├── key.pem
└── dhparam.pem
```

## Deployment Steps

### 1. Build and Deploy with Docker Compose

```bash
# Build images
make docker-build-prod

# Deploy services
docker-compose -f docker-compose.production.yml up -d

# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

### 2. Database Setup

```bash
# Run database migrations
make migrate

# Create initial admin user
docker-compose -f docker-compose.production.yml exec api python -m scripts.create_admin
```

### 3. Nginx Configuration

Update `nginx/prod.conf` with your domain:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # API proxy
    location /api {
        proxy_pass http://api:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # WebSocket proxy
    location /ws {
        proxy_pass http://websocket:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
    
    # Streamlit app
    location / {
        proxy_pass http://app:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## CI/CD Pipeline

### GitHub Actions Setup

1. Set up GitHub Secrets:
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`
   - `PRODUCTION_HOST`
   - `PRODUCTION_SSH_KEY`
   - `SLACK_WEBHOOK_URL` (optional)

2. The pipeline will:
   - Run tests on every push
   - Build Docker images on main branch
   - Deploy to production on tags

### Manual Deployment

```bash
# SSH to production server
ssh user@production-server

# Pull latest changes
git pull origin main

# Deploy
make deploy-prod
```

## Monitoring

### 1. Prometheus Metrics

Access Prometheus at `http://your-server:9090`

Key metrics to monitor:
- API request rate and latency
- WebSocket connections
- Database connection pool
- Redis memory usage
- Transcription job queue length

### 2. Grafana Dashboards

Access Grafana at `http://your-server:3000`

Pre-configured dashboards:
- Application Overview
- API Performance
- Database Performance
- Redis Metrics
- System Resources

### 3. Health Checks

```bash
# Check API health
curl https://yourdomain.com/api/health

# Check WebSocket health
wscat -c wss://yourdomain.com/ws/health

# Check database
docker-compose -f docker-compose.production.yml exec db pg_isready
```

## Backup and Recovery

### Automated Backups

Backups run daily at 3 AM via cron:

```bash
# Manual backup
docker-compose -f docker-compose.production.yml exec backup /backup.sh

# List backups
ls -la backups/

# Restore from backup
docker-compose -f docker-compose.production.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB < backups/backup_20250803.sql
```

### Backup Strategy

1. **Database**: Daily full backups, retained for 30 days
2. **Uploads**: Synced to S3/GCS daily
3. **Redis**: AOF persistence enabled
4. **Logs**: Rotated daily, retained for 7 days

## Scaling

### Horizontal Scaling

1. **API Servers**: Add more API containers
   ```yaml
   api:
     scale: 3
   ```

2. **WebSocket Servers**: Use Redis for session sharing
   ```yaml
   websocket:
     scale: 2
   ```

3. **Load Balancing**: Use Nginx upstream configuration

### Vertical Scaling

Adjust resource limits in `docker-compose.production.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 8G
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database logs
   docker-compose -f docker-compose.production.yml logs db
   
   # Test connection
   docker-compose -f docker-compose.production.yml exec api python -c "from database.models import test_connection; test_connection()"
   ```

2. **Memory Issues**
   ```bash
   # Check container stats
   docker stats
   
   # Increase memory limits
   docker-compose -f docker-compose.production.yml up -d --scale api=2
   ```

3. **Disk Space**
   ```bash
   # Clean up Docker
   docker system prune -a
   
   # Check upload directory
   du -sh uploads/
   ```

### Log Analysis

```bash
# API logs
docker-compose -f docker-compose.production.yml logs -f api | grep ERROR

# Structured log search
docker-compose -f docker-compose.production.yml exec api python -m scripts.log_search --level=ERROR --days=1
```

## Security Considerations

1. **Regular Updates**
   ```bash
   # Update base images
   docker-compose -f docker-compose.production.yml pull
   docker-compose -f docker-compose.production.yml up -d
   ```

2. **Security Scanning**
   ```bash
   # Scan for vulnerabilities
   make security
   
   # Check Docker images
   docker scan video-ner-api:latest
   ```

3. **Access Control**
   - Use strong passwords
   - Enable 2FA for admin accounts
   - Regularly rotate API keys
   - Monitor failed login attempts

## Maintenance

### Regular Tasks

1. **Weekly**
   - Review error logs
   - Check disk usage
   - Update dependencies

2. **Monthly**
   - Security patches
   - Performance review
   - Backup restoration test

3. **Quarterly**
   - Full security audit
   - Load testing
   - Disaster recovery drill

### Update Procedure

```bash
# 1. Backup database
make backup

# 2. Pull latest code
git pull origin main

# 3. Build new images
make docker-build-prod

# 4. Run migrations
make migrate

# 5. Deploy with zero downtime
docker-compose -f docker-compose.production.yml up -d --no-deps --scale api=2 api
# Wait for new container to be healthy
docker-compose -f docker-compose.production.yml up -d --no-deps api
```

## Support

For issues and support:
- Check logs: `docker-compose -f docker-compose.production.yml logs`
- Review metrics: Grafana dashboards
- Contact: support@yourdomain.com