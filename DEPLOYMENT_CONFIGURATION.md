# Deployment Configuration
## Video NER Platform - Production Deployment Guide

### Overview
This document provides comprehensive deployment configurations for the Video NER platform, covering all Phase 1-3 implementations across development, staging, and production environments.

---

## 1. Infrastructure Architecture

### 1.1 High-Level Architecture
```mermaid
graph TB
    LB[Load Balancer] --> API[API Gateway]
    LB --> WEB[Web Frontend]
    
    API --> AUTH[Auth Service]
    API --> ENTITY[Entity Extraction]
    API --> LLM[LLM Providers]
    API --> MARKET[Marketplace]
    API --> DUBBING[AI Dubbing]
    API --> OCR[OCR Service]
    API --> MEETING[Meeting Service]
    
    AUTH --> DB[(PostgreSQL)]
    ENTITY --> REDIS[Redis Cache]
    ENTITY --> QUEUE[Celery Queue]
    
    QUEUE --> WORKER1[Worker 1]
    QUEUE --> WORKER2[Worker 2]
    QUEUE --> WORKER3[Worker 3]
    
    DB --> BACKUP[(Backup Storage)]
    
    WEB --> CDN[CloudFront CDN]
    CDN --> S3[S3 Storage]
    
    subgraph "Monitoring"
        PROM[Prometheus]
        GRAF[Grafana]
        ALERT[AlertManager]
    end
    
    API --> PROM
    WORKER1 --> PROM
    WORKER2 --> PROM
    WORKER3 --> PROM
```

### 1.2 Environment Configuration

#### Development Environment
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  api:
    build: 
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - DATABASE_URL=postgresql://dev_user:dev_pass@postgres:5432/video_ner_dev
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    volumes:
      - ./api:/app/api
      - ./uploads:/app/uploads
    depends_on:
      - postgres
      - redis

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql://dev_user:dev_pass@postgres:5432/video_ner_dev
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    volumes:
      - ./api:/app/api
      - ./uploads:/app/uploads
    depends_on:
      - postgres
      - redis

  web:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=video_ner_dev
      - POSTGRES_USER=dev_user
      - POSTGRES_PASSWORD=dev_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data

volumes:
  postgres_dev_data:
  redis_dev_data:
```

#### Production Environment
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  api:
    image: video-ner-api:${VERSION}
    restart: always
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1GB
        reservations:
          cpus: '0.5'
          memory: 512MB
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    image: video-ner-worker:${VERSION}
    restart: always
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '2.0'
          memory: 2GB
        reservations:
          cpus: '1.0'
          memory: 1GB

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: always

networks:
  default:
    external:
      name: video_ner_network
```

---

## 2. Kubernetes Deployment

### 2.1 Kubernetes Manifests

#### API Deployment
```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-ner-api
  namespace: video-ner
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: video-ner-api
  template:
    metadata:
      labels:
        app: video-ner-api
        version: "v1"
    spec:
      containers:
      - name: api
        image: video-ner-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: video-ner-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: video-ner-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: upload-storage
          mountPath: /app/uploads
      volumes:
      - name: upload-storage
        persistentVolumeClaim:
          claimName: video-ner-uploads

---
apiVersion: v1
kind: Service
metadata:
  name: video-ner-api-service
  namespace: video-ner
spec:
  selector:
    app: video-ner-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

#### Worker Deployment
```yaml
# k8s/worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-ner-worker
  namespace: video-ner
spec:
  replicas: 4
  selector:
    matchLabels:
      app: video-ner-worker
  template:
    metadata:
      labels:
        app: video-ner-worker
    spec:
      containers:
      - name: worker
        image: video-ner-worker:latest
        env:
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef:
              name: video-ner-secrets
              key: celery-broker-url
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: video-ner-secrets
              key: database-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: upload-storage
          mountPath: /app/uploads
      volumes:
      - name: upload-storage
        persistentVolumeClaim:
          claimName: video-ner-uploads
```

#### Ingress Configuration
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: video-ner-ingress
  namespace: video-ner
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.video-ner.com
    - app.video-ner.com
    secretName: video-ner-tls
  rules:
  - host: api.video-ner.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: video-ner-api-service
            port:
              number: 80
  - host: app.video-ner.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: video-ner-web-service
            port:
              number: 80
```

### 2.2 Configuration Management

#### ConfigMap
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: video-ner-config
  namespace: video-ner
data:
  # API Configuration
  LOG_LEVEL: "INFO"
  MAX_WORKERS: "4"
  CORS_ORIGINS: "https://app.video-ner.com,https://video-ner.com"
  
  # Cache Configuration
  CACHE_TTL: "3600"
  
  # Rate Limiting
  RATE_LIMIT_REQUESTS: "100"
  RATE_LIMIT_WINDOW: "3600"
  
  # File Upload
  MAX_FILE_SIZE: "52428800"  # 50MB
  ALLOWED_EXTENSIONS: "jpg,jpeg,png,gif,pdf,mp3,wav"
  
  # Processing
  ENTITY_EXTRACTION_TIMEOUT: "300"
  OCR_PROCESSING_TIMEOUT: "600"
  AI_DUBBING_TIMEOUT: "1800"
```

#### Secrets Management
```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: video-ner-secrets
  namespace: video-ner
type: Opaque
data:
  database-url: # base64 encoded
  jwt-secret: # base64 encoded
  encryption-key: # base64 encoded
  celery-broker-url: # base64 encoded
  openai-api-key: # base64 encoded
  anthropic-api-key: # base64 encoded
```

---

## 3. CI/CD Pipeline

### 3.1 GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy Video NER Platform

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/ -v --cov=api --cov-report=xml
    
    - name: Security scan
      run: |
        pip install bandit safety
        bandit -r api/
        safety check
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
    
    - name: Build and push API image
      id: build
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile.api
        push: true
        tags: ${{ steps.meta.outputs.tags }}-api
        labels: ${{ steps.meta.outputs.labels }}
    
    - name: Build and push Worker image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile.worker
        push: true
        tags: ${{ steps.meta.outputs.tags }}-worker
        labels: ${{ steps.meta.outputs.labels }}

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}
    
    - name: Deploy to staging
      run: |
        sed -i 's|IMAGE_TAG|${{ needs.build-and-push.outputs.image-tag }}|g' k8s/staging/*.yaml
        kubectl apply -f k8s/staging/ -n video-ner-staging
        kubectl rollout status deployment/video-ner-api -n video-ner-staging

  integration-tests:
    needs: deploy-staging
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run integration tests
      env:
        STAGING_URL: https://api-staging.video-ner.com
      run: |
        python -m pytest tests/integration/ -v --base-url=$STAGING_URL

  deploy-production:
    needs: [build-and-push, integration-tests]
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.PROD_KUBE_CONFIG }}
    
    - name: Deploy to production
      run: |
        sed -i 's|IMAGE_TAG|${{ needs.build-and-push.outputs.image-tag }}|g' k8s/production/*.yaml
        kubectl apply -f k8s/production/ -n video-ner-prod
        kubectl rollout status deployment/video-ner-api -n video-ner-prod
    
    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: 'Production deployment completed successfully!'
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 4. Database Management

### 4.1 Migration Scripts

```python
# database/migrations/001_phase2_tables.py
"""Add Phase 2 tables for LLM providers, marketplace, and AI dubbing"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_phase2'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # LLM Providers table
    op.create_table('llm_providers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('provider_name', sa.String(50), nullable=False),
        sa.Column('api_key_encrypted', sa.Text(), nullable=False),
        sa.Column('settings', postgresql.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='inactive'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_llm_providers_user_status', 'user_id', 'status')
    )
    
    # Marketplace items table
    op.create_table('marketplace_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=True),
        sa.Column('publisher_id', sa.String(), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False, default=0),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_marketplace_category_rating', 'category', 'rating'),
        sa.Index('idx_marketplace_search', 'name', 'description', postgresql_using='gin')
    )
    
    # AI Dubbing jobs table
    op.create_table('ai_dubbing_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('source_language', sa.String(10), nullable=False),
        sa.Column('target_languages', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('input_text', sa.Text(), nullable=True),
        sa.Column('video_url', sa.String(), nullable=True),
        sa.Column('voice_settings', postgresql.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='queued'),
        sa.Column('progress', sa.Float(), nullable=False, default=0.0),
        sa.Column('result_urls', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_dubbing_jobs_user_status', 'user_id', 'status')
    )

def downgrade():
    op.drop_table('ai_dubbing_jobs')
    op.drop_table('marketplace_items')
    op.drop_table('llm_providers')
```

### 4.2 Database Backup Strategy

```bash
#!/bin/bash
# scripts/backup_database.sh

set -e

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-video_ner_prod}
DB_USER=${DB_USER:-postgres}
BACKUP_DIR=${BACKUP_DIR:-/backups}
RETENTION_DAYS=${RETENTION_DAYS:-30}

# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/video_ner_backup_${TIMESTAMP}.sql"

echo "Starting database backup at $(date)"

# Create compressed backup
pg_dump \
    --host=${DB_HOST} \
    --port=${DB_PORT} \
    --username=${DB_USER} \
    --dbname=${DB_NAME} \
    --format=custom \
    --compress=9 \
    --no-owner \
    --no-privileges \
    --file="${BACKUP_FILE}.custom"

# Create SQL backup for easier restoration
pg_dump \
    --host=${DB_HOST} \
    --port=${DB_PORT} \
    --username=${DB_USER} \
    --dbname=${DB_NAME} \
    --no-owner \
    --no-privileges \
    | gzip > "${BACKUP_FILE}.gz"

# Upload to S3 (optional)
if [ -n "$AWS_S3_BUCKET" ]; then
    aws s3 cp "${BACKUP_FILE}.custom" "s3://${AWS_S3_BUCKET}/database-backups/"
    aws s3 cp "${BACKUP_FILE}.gz" "s3://${AWS_S3_BUCKET}/database-backups/"
fi

# Cleanup old backups
find ${BACKUP_DIR} -name "video_ner_backup_*.sql*" -type f -mtime +${RETENTION_DAYS} -delete

echo "Database backup completed at $(date)"
echo "Backup files: ${BACKUP_FILE}.custom, ${BACKUP_FILE}.gz"
```

---

## 5. Monitoring & Logging

### 5.1 Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'video-ner-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'video-ner-workers'
    static_configs:
      - targets: 
          - 'worker-1:9540'
          - 'worker-2:9540'
          - 'worker-3:9540'
          - 'worker-4:9540'

  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### 5.2 Alert Rules

```yaml
# monitoring/alert_rules.yml
groups:
- name: video-ner-alerts
  rules:
  # API Health
  - alert: APIDown
    expr: up{job="video-ner-api"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Video NER API is down"
      description: "API instance {{ $labels.instance }} is down for more than 1 minute"

  # High Error Rate
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"

  # Database Connection Issues
  - alert: DatabaseConnectionHigh
    expr: postgresql_stat_database_numbackends > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High database connections"
      description: "Database has {{ $value }} active connections"

  # Worker Queue Backup
  - alert: WorkerQueueBackup
    expr: celery_queue_length > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Worker queue backup"
      description: "Queue has {{ $value }} pending tasks"

  # Disk Space
  - alert: DiskSpaceWarning
    expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Low disk space"
      description: "Disk usage is above 90%"
```

### 5.3 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Video NER Platform Dashboard",
    "panels": [
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{ method }} {{ handler }}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Active Workers",
        "type": "stat",
        "targets": [
          {
            "expr": "celery_workers_active"
          }
        ]
      },
      {
        "title": "Processing Queue Length",
        "type": "graph",
        "targets": [
          {
            "expr": "celery_queue_length",
            "legendFormat": "{{ queue }}"
          }
        ]
      }
    ]
  }
}
```

---

## 6. Security Configuration

### 6.1 SSL/TLS Configuration

```nginx
# nginx/ssl.conf
server {
    listen 443 ssl http2;
    server_name api.video-ner.com;
    
    ssl_certificate /etc/nginx/ssl/video-ner.crt;
    ssl_certificate_key /etc/nginx/ssl/video-ner.key;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # File Upload Limits
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}

upstream api_backend {
    least_conn;
    server api-1:8000 weight=3 max_fails=3 fail_timeout=30s;
    server api-2:8000 weight=3 max_fails=3 fail_timeout=30s;
    server api-3:8000 weight=3 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

### 6.2 Network Security

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: video-ner-network-policy
  namespace: video-ner
spec:
  podSelector:
    matchLabels:
      app: video-ner-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to: []  # Allow external API calls
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
```

---

## 7. Environment-Specific Configurations

### 7.1 Development Environment

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/video_ner_dev

# Cache
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# API Keys (Development)
OPENAI_API_KEY=sk-dev-...
ANTHROPIC_API_KEY=sk-ant-dev-...

# Security (Weak keys for development)
JWT_SECRET_KEY=dev-secret-key
ENCRYPTION_KEY=dev-encryption-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# File Upload
MAX_FILE_SIZE=52428800
UPLOAD_DIR=./uploads

# Monitoring
ENABLE_METRICS=false
```

### 7.2 Staging Environment

```bash
# .env.staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://staging_user:secure_pass@db-staging:5432/video_ner_staging

# Cache
REDIS_URL=redis://redis-staging:6379/0
CELERY_BROKER_URL=redis://redis-staging:6379/1

# API Keys (Staging)
OPENAI_API_KEY=${STAGING_OPENAI_API_KEY}
ANTHROPIC_API_KEY=${STAGING_ANTHROPIC_API_KEY}

# Security
JWT_SECRET_KEY=${STAGING_JWT_SECRET}
ENCRYPTION_KEY=${STAGING_ENCRYPTION_KEY}

# CORS
CORS_ORIGINS=https://staging.video-ner.com

# File Upload
MAX_FILE_SIZE=52428800
UPLOAD_DIR=/app/uploads

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
```

### 7.3 Production Environment

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Database (Retrieved from secrets management)
DATABASE_URL=${PROD_DATABASE_URL}

# Cache
REDIS_URL=${PROD_REDIS_URL}
CELERY_BROKER_URL=${PROD_CELERY_BROKER_URL}

# API Keys (From Azure Key Vault)
OPENAI_API_KEY=${PROD_OPENAI_API_KEY}
ANTHROPIC_API_KEY=${PROD_ANTHROPIC_API_KEY}

# Security
JWT_SECRET_KEY=${PROD_JWT_SECRET}
ENCRYPTION_KEY=${PROD_ENCRYPTION_KEY}

# CORS
CORS_ORIGINS=https://app.video-ner.com,https://video-ner.com

# File Upload
MAX_FILE_SIZE=52428800
UPLOAD_DIR=/app/uploads

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_PORT=9090

# Performance
WORKER_PROCESSES=4
WORKER_CONNECTIONS=1000
```

---

## 8. Disaster Recovery Plan

### 8.1 Backup Strategy

```bash
#!/bin/bash
# scripts/disaster_recovery.sh

# Full system backup
backup_system() {
    echo "Starting full system backup..."
    
    # Database backup
    ./scripts/backup_database.sh
    
    # File storage backup
    aws s3 sync /app/uploads/ s3://video-ner-backups/uploads/
    
    # Configuration backup
    kubectl get configmaps,secrets -n video-ner -o yaml > k8s-backup-$(date +%Y%m%d).yaml
    
    echo "System backup completed"
}

# Disaster recovery procedure
disaster_recovery() {
    echo "Starting disaster recovery..."
    
    # Restore database
    if [ -f "$1" ]; then
        pg_restore --host=$DB_HOST --username=$DB_USER --dbname=$DB_NAME --clean --if-exists "$1"
    fi
    
    # Restore file storage
    aws s3 sync s3://video-ner-backups/uploads/ /app/uploads/
    
    # Restore Kubernetes resources
    kubectl apply -f k8s-backup-latest.yaml
    
    echo "Disaster recovery completed"
}

case "$1" in
    backup)
        backup_system
        ;;
    restore)
        disaster_recovery "$2"
        ;;
    *)
        echo "Usage: $0 {backup|restore backup_file}"
        exit 1
        ;;
esac
```

### 8.2 Scaling Strategy

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: video-ner-api-hpa
  namespace: video-ner
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: video-ner-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

---

## 9. Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (unit, integration, security)
- [ ] Code review completed and approved
- [ ] Database migrations reviewed and tested
- [ ] Configuration files updated for target environment
- [ ] Secrets properly configured in secrets management system
- [ ] SSL certificates valid and configured
- [ ] Monitoring and alerting configured
- [ ] Backup procedures tested and verified

### Deployment
- [ ] Deploy to staging environment first
- [ ] Run smoke tests in staging
- [ ] Run full integration test suite
- [ ] Performance testing completed
- [ ] Security scanning completed
- [ ] Deploy to production with blue-green strategy
- [ ] Verify all services are healthy
- [ ] Run production smoke tests

### Post-Deployment
- [ ] Monitor application metrics and logs
- [ ] Verify all features working as expected
- [ ] Check error rates and response times
- [ ] Confirm database connectivity and performance
- [ ] Test critical user workflows
- [ ] Document any issues or rollback procedures
- [ ] Notify stakeholders of successful deployment

---

## 10. Rollback Procedures

### Automated Rollback
```bash
#!/bin/bash
# scripts/rollback.sh

NAMESPACE=${1:-video-ner}
DEPLOYMENT=${2:-video-ner-api}

echo "Rolling back deployment $DEPLOYMENT in namespace $NAMESPACE"

# Rollback to previous version
kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE

# Wait for rollback to complete
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE

# Verify rollback
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT

echo "Rollback completed successfully"
```

### Manual Rollback Steps
1. **Identify the issue** - Check logs and metrics
2. **Stop traffic** - Update load balancer to stop new requests
3. **Database rollback** - If schema changes were made, restore from backup
4. **Application rollback** - Deploy previous known-good version
5. **Verify functionality** - Run smoke tests
6. **Resume traffic** - Gradually restore normal traffic flow
7. **Post-incident review** - Document lessons learned

---

*This deployment configuration ensures a robust, scalable, and secure production environment for the Video NER platform.*