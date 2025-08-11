#!/bin/bash

# Audio Enhancement Service Deployment Script
# Production deployment for audio enhancement pipeline

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="audio-enhancement-service"
DEPLOY_ENV=${1:-production}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"your-registry.com"}
K8S_NAMESPACE=${K8S_NAMESPACE:-"audio-services"}
WORKERS=${WORKERS:-4}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Audio Enhancement Service Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Environment: ${YELLOW}$DEPLOY_ENV${NC}"
echo -e "Service: ${YELLOW}$SERVICE_NAME${NC}"

# Function to check dependencies
check_dependencies() {
    echo -e "\n${YELLOW}Checking dependencies...${NC}"
    
    commands=("docker" "kubectl" "helm")
    for cmd in "${commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            echo -e "${RED}Error: $cmd is not installed${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}All dependencies satisfied${NC}"
}

# Build Docker image
build_docker_image() {
    echo -e "\n${YELLOW}Building Docker image...${NC}"
    
    # Generate version tag
    VERSION=$(git describe --tags --always --dirty)
    IMAGE_TAG="$DOCKER_REGISTRY/$SERVICE_NAME:$VERSION"
    
    # Create Dockerfile if not exists
    if [ ! -f "Dockerfile.audio-enhancement" ]; then
        cat > Dockerfile.audio-enhancement << 'EOF'
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional audio processing libraries
RUN pip install --no-cache-dir \
    noisereduce==2.0.1 \
    pydub==0.25.1 \
    librosa==0.10.0 \
    soundfile==0.12.1 \
    scipy==1.11.0

# Copy application code
COPY api/ ./api/
COPY audio_enhancement_pipeline.py .
COPY advanced_audio_processing.py .
COPY config/ ./config/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV API_PORT=8000
ENV WORKERS=4

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/audio-enhancement/health || exit 1

# Start service
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
EOF
    fi
    
    # Build image
    docker build -f Dockerfile.audio-enhancement -t "$IMAGE_TAG" .
    
    # Tag as latest
    docker tag "$IMAGE_TAG" "$DOCKER_REGISTRY/$SERVICE_NAME:latest"
    
    echo -e "${GREEN}Docker image built: $IMAGE_TAG${NC}"
}

# Push to registry
push_docker_image() {
    echo -e "\n${YELLOW}Pushing image to registry...${NC}"
    
    VERSION=$(git describe --tags --always --dirty)
    IMAGE_TAG="$DOCKER_REGISTRY/$SERVICE_NAME:$VERSION"
    
    docker push "$IMAGE_TAG"
    docker push "$DOCKER_REGISTRY/$SERVICE_NAME:latest"
    
    echo -e "${GREEN}Image pushed successfully${NC}"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    echo -e "\n${YELLOW}Deploying to Kubernetes...${NC}"
    
    VERSION=$(git describe --tags --always --dirty)
    
    # Create namespace if not exists
    kubectl create namespace $K8S_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Create Kubernetes manifests
    cat > k8s-audio-enhancement.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $SERVICE_NAME
  namespace: $K8S_NAMESPACE
  labels:
    app: $SERVICE_NAME
    version: $VERSION
spec:
  replicas: 3
  selector:
    matchLabels:
      app: $SERVICE_NAME
  template:
    metadata:
      labels:
        app: $SERVICE_NAME
        version: $VERSION
    spec:
      containers:
      - name: audio-enhancement
        image: $DOCKER_REGISTRY/$SERVICE_NAME:$VERSION
        ports:
        - containerPort: 8000
        env:
        - name: WORKERS
          value: "$WORKERS"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/v1/audio-enhancement/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/audio-enhancement/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: $SERVICE_NAME
  namespace: $K8S_NAMESPACE
spec:
  selector:
    app: $SERVICE_NAME
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: $SERVICE_NAME-hpa
  namespace: $K8S_NAMESPACE
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: $SERVICE_NAME
  minReplicas: 2
  maxReplicas: 10
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
EOF
    
    # Apply manifests
    kubectl apply -f k8s-audio-enhancement.yaml
    
    # Wait for rollout
    kubectl rollout status deployment/$SERVICE_NAME -n $K8S_NAMESPACE
    
    echo -e "${GREEN}Kubernetes deployment successful${NC}"
}

# Deploy with Helm
deploy_helm() {
    echo -e "\n${YELLOW}Deploying with Helm...${NC}"
    
    # Create Helm chart if not exists
    if [ ! -d "charts/audio-enhancement" ]; then
        helm create charts/audio-enhancement
    fi
    
    # Update values
    cat > charts/audio-enhancement/values.yaml << EOF
replicaCount: 3

image:
  repository: $DOCKER_REGISTRY/$SERVICE_NAME
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: ClusterIP
  port: 80
  targetPort: 8000

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
  hosts:
    - host: audio-enhancement.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: audio-enhancement-tls
      hosts:
        - audio-enhancement.example.com

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

redis:
  enabled: true
  auth:
    enabled: true
    password: "changeme"

postgresql:
  enabled: true
  auth:
    database: audio_enhancement
    username: audio_user
    password: "changeme"

monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true
EOF
    
    # Deploy with Helm
    helm upgrade --install $SERVICE_NAME ./charts/audio-enhancement \
        --namespace $K8S_NAMESPACE \
        --create-namespace \
        --wait
    
    echo -e "${GREEN}Helm deployment successful${NC}"
}

# Setup monitoring
setup_monitoring() {
    echo -e "\n${YELLOW}Setting up monitoring...${NC}"
    
    # Create ServiceMonitor for Prometheus
    cat > servicemonitor.yaml << EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: $SERVICE_NAME
  namespace: $K8S_NAMESPACE
spec:
  selector:
    matchLabels:
      app: $SERVICE_NAME
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
EOF
    
    kubectl apply -f servicemonitor.yaml
    
    echo -e "${GREEN}Monitoring configured${NC}"
}

# Run health checks
run_health_checks() {
    echo -e "\n${YELLOW}Running health checks...${NC}"
    
    # Get service endpoint
    if [ "$DEPLOY_ENV" == "local" ]; then
        ENDPOINT="http://localhost:8000"
    else
        ENDPOINT=$(kubectl get svc $SERVICE_NAME -n $K8S_NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        if [ -z "$ENDPOINT" ]; then
            ENDPOINT=$(kubectl get svc $SERVICE_NAME -n $K8S_NAMESPACE -o jsonpath='{.spec.clusterIP}')
        fi
        ENDPOINT="http://$ENDPOINT"
    fi
    
    # Check health endpoint
    echo -e "Checking health endpoint: $ENDPOINT/api/v1/audio-enhancement/health"
    
    for i in {1..5}; do
        if curl -f "$ENDPOINT/api/v1/audio-enhancement/health" &> /dev/null; then
            echo -e "${GREEN}Health check passed${NC}"
            break
        else
            echo -e "${YELLOW}Waiting for service to be ready... ($i/5)${NC}"
            sleep 10
        fi
    done
}

# Rollback deployment
rollback_deployment() {
    echo -e "\n${RED}Rolling back deployment...${NC}"
    
    kubectl rollout undo deployment/$SERVICE_NAME -n $K8S_NAMESPACE
    kubectl rollout status deployment/$SERVICE_NAME -n $K8S_NAMESPACE
    
    echo -e "${YELLOW}Rollback completed${NC}"
}

# Main deployment flow
main() {
    check_dependencies
    
    case "$DEPLOY_ENV" in
        "production")
            build_docker_image
            push_docker_image
            deploy_kubernetes
            setup_monitoring
            run_health_checks
            ;;
        "staging")
            build_docker_image
            push_docker_image
            deploy_helm
            run_health_checks
            ;;
        "local")
            echo -e "\n${YELLOW}Starting local deployment...${NC}"
            docker-compose -f docker-compose.audio.yml up -d
            run_health_checks
            ;;
        "rollback")
            rollback_deployment
            ;;
        *)
            echo -e "${RED}Unknown environment: $DEPLOY_ENV${NC}"
            echo "Usage: $0 [production|staging|local|rollback]"
            exit 1
            ;;
    esac
    
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Run main function
main