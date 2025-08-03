# 🚀 Production Deployment Guide

This guide covers deploying the Transcription Platform to production environments.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Database Configuration](#database-configuration)
4. [API Deployment](#api-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Security Configuration](#security-configuration)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Services
- PostgreSQL 15+
- Redis 7+
- MinIO or AWS S3
- Docker & Docker Compose
- Nginx (reverse proxy)
- SSL Certificate (Let's Encrypt)

### System Requirements
- Ubuntu 22.04 LTS or similar
- 4+ CPU cores
- 8GB+ RAM
- 100GB+ storage

## Infrastructure Setup

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install nginx
sudo apt install nginx certbot python3-certbot-nginx -y
```

### 2. Clone Repository

```bash
git clone https://github.com/your-org/transcription-platform.git
cd transcription-platform
```

### 3. Environment Configuration

```bash
# Copy environment templates
cp api/.env.example api/.env

# Edit with production values
nano api/.env
```

**Required Environment Variables:**

```env
# API Configuration
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://transcription_user:secure_password@db:5432/transcription_db

# Security
JWT_SECRET_KEY=your-very-secure-secret-key-minimum-32-characters
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Redis
REDIS_URL=redis://redis:6379/0

# Storage (MinIO/S3)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
STORAGE_BUCKET=transcriptions

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

## Database Configuration

### 1. PostgreSQL Setup

```bash
# Create database backup script
cat > backup-db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec transcription_db pg_dump -U transcription_user transcription_db > backup_$DATE.sql
# Keep only last 7 days of backups
find . -name "backup_*.sql" -mtime +7 -delete
EOF

chmod +x backup-db.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/backup-db.sh") | crontab -
```

### 2. Database Migrations

```bash
# Run migrations
docker-compose exec api python -m alembic upgrade head
```

## API Deployment

### 1. Build and Start Services

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### 2. Nginx Configuration

Create `/etc/nginx/sites-available/transcription-api`:

```nginx
upstream api_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # API endpoints
    location /api {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long uploads
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        
        # File upload size
        client_max_body_size 500M;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/transcription-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. SSL Certificate

```bash
# Get SSL certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Frontend Deployment

### 1. Build Frontend

```bash
cd desktop_app
npm install
npm run build
```

### 2. Nginx Configuration for Frontend

Create `/etc/nginx/sites-available/transcription-app`:

```nginx
server {
    listen 80;
    server_name app.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/app.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.yourdomain.com/privkey.pem;

    root /var/www/transcription-app;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Security Configuration

### 1. Firewall Setup

```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Fail2ban Configuration

```bash
# Install fail2ban
sudo apt install fail2ban -y

# Create jail for API
cat > /etc/fail2ban/jail.d/transcription-api.conf << EOF
[transcription-api]
enabled = true
port = http,https
filter = transcription-api
logpath = /var/log/nginx/access.log
maxretry = 10
findtime = 600
bantime = 3600
EOF

# Create filter
cat > /etc/fail2ban/filter.d/transcription-api.conf << EOF
[Definition]
failregex = ^<HOST> .* "(GET|POST) /api/.* HTTP/.*" 429
ignoreregex =
EOF

# Restart fail2ban
sudo systemctl restart fail2ban
```

## Monitoring & Logging

### 1. Prometheus Setup

Add to `docker-compose.yml`:

```yaml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana:latest
  volumes:
    - grafana_data:/var/lib/grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=secure_password
```

### 2. Application Metrics

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'transcription-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
```

### 3. Log Aggregation

```bash
# Install Loki
docker run -d --name loki -p 3100:3100 grafana/loki:latest

# Configure Promtail
docker run -d --name promtail \
  -v /var/log:/var/log \
  -v ./promtail-config.yml:/etc/promtail/config.yml \
  grafana/promtail:latest
```

## Backup & Recovery

### 1. Automated Backups

Create `/usr/local/bin/backup-all.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup database
docker exec transcription_db pg_dump -U transcription_user transcription_db > $BACKUP_DIR/database.sql

# Backup MinIO data
docker run --rm -v transcription_minio_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/minio.tar.gz -C /data .

# Backup Redis
docker exec transcription_redis redis-cli BGSAVE
docker cp transcription_redis:/data/dump.rdb $BACKUP_DIR/redis.rdb

# Upload to S3 (optional)
# aws s3 sync $BACKUP_DIR s3://your-backup-bucket/$(date +%Y%m%d)/

# Keep only last 30 days
find /backups -type d -mtime +30 -exec rm -rf {} +
```

### 2. Restore Procedures

```bash
# Restore database
docker exec -i transcription_db psql -U transcription_user transcription_db < backup.sql

# Restore MinIO
docker run --rm -v transcription_minio_data:/data -v /path/to/backup:/backup alpine tar xzf /backup/minio.tar.gz -C /data

# Restore Redis
docker cp redis.rdb transcription_redis:/data/dump.rdb
docker restart transcription_redis
```

## Troubleshooting

### Common Issues

1. **API not responding**
   ```bash
   # Check logs
   docker-compose logs -f api
   
   # Restart service
   docker-compose restart api
   ```

2. **Database connection errors**
   ```bash
   # Check PostgreSQL
   docker exec transcription_db pg_isready
   
   # Check connections
   docker exec transcription_db psql -U transcription_user -c "SELECT count(*) FROM pg_stat_activity;"
   ```

3. **Redis connection issues**
   ```bash
   # Test Redis
   docker exec transcription_redis redis-cli ping
   
   # Check memory
   docker exec transcription_redis redis-cli info memory
   ```

4. **Storage issues**
   ```bash
   # Check MinIO
   docker logs transcription_minio
   
   # Test connection
   curl http://localhost:9000/minio/health/live
   ```

### Performance Optimization

1. **Database optimization**
   ```sql
   -- Add indexes
   CREATE INDEX idx_transcripts_user_created ON transcripts(user_id, created_at DESC);
   CREATE INDEX idx_transcripts_team ON transcripts(team_id) WHERE team_id IS NOT NULL;
   
   -- Vacuum and analyze
   VACUUM ANALYZE;
   ```

2. **Redis optimization**
   ```bash
   # Set memory limit
   docker exec transcription_redis redis-cli CONFIG SET maxmemory 2gb
   docker exec transcription_redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

3. **API optimization**
   - Increase worker processes: `gunicorn -w 8`
   - Enable response caching
   - Use CDN for static assets

## Health Checks

Create monitoring script `/usr/local/bin/health-check.sh`:

```bash
#!/bin/bash

# Check API
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.yourdomain.com/api/health)
if [ $API_STATUS -ne 200 ]; then
    echo "API health check failed: $API_STATUS"
    # Send alert
fi

# Check database
DB_STATUS=$(docker exec transcription_db pg_isready -U transcription_user)
if [ $? -ne 0 ]; then
    echo "Database health check failed"
    # Send alert
fi

# Check Redis
REDIS_STATUS=$(docker exec transcription_redis redis-cli ping)
if [ "$REDIS_STATUS" != "PONG" ]; then
    echo "Redis health check failed"
    # Send alert
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage critical: $DISK_USAGE%"
    # Send alert
fi
```

Add to crontab:
```bash
*/5 * * * * /usr/local/bin/health-check.sh
```

## Conclusion

This deployment guide covers the essential steps for deploying the Transcription Platform to production. Remember to:

1. Always test in staging first
2. Monitor logs and metrics regularly
3. Keep backups current
4. Update dependencies regularly
5. Review security settings periodically

For additional support, consult the API documentation at `https://api.yourdomain.com/api/docs`.