#!/bin/bash
# Production deployment script for Audio/Video Transcription Platform

set -e

echo "🚀 Starting production deployment..."

# Configuration
export AWS_REGION=${AWS_REGION:-us-west-2}
export CLUSTER_NAME=${CLUSTER_NAME:-transcription-cluster}
export SERVICE_NAME=${SERVICE_NAME:-transcription-service}
export ECR_URI=${ECR_URI}
export ENVIRONMENT=${ENVIRONMENT:-production}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi
    
    if [[ -z "$ECR_URI" ]]; then
        log_error "ECR_URI environment variable is not set"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Build backend image
    log_info "Building backend image..."
    docker build -f Dockerfile.production -t transcription-backend:latest .
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build -f desktop_app/src/renderer/Dockerfile.production -t transcription-frontend:latest ./desktop_app/src/renderer
    
    log_info "Docker images built successfully"
}

# Push images to ECR
push_images() {
    log_info "Pushing images to ECR..."
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI
    
    # Tag and push backend image
    docker tag transcription-backend:latest $ECR_URI/transcription-backend:latest
    docker tag transcription-backend:latest $ECR_URI/transcription-backend:$(git rev-parse --short HEAD)
    docker push $ECR_URI/transcription-backend:latest
    docker push $ECR_URI/transcription-backend:$(git rev-parse --short HEAD)
    
    # Tag and push frontend image
    docker tag transcription-frontend:latest $ECR_URI/transcription-frontend:latest
    docker tag transcription-frontend:latest $ECR_URI/transcription-frontend:$(git rev-parse --short HEAD)
    docker push $ECR_URI/transcription-frontend:latest
    docker push $ECR_URI/transcription-frontend:$(git rev-parse --short HEAD)
    
    log_info "Images pushed to ECR successfully"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Create a temporary container to run migrations
    docker run --rm \
        --env-file .env.production \
        transcription-backend:latest \
        python -c "
import psycopg2
import os
from pathlib import Path

# Read and execute migration script
with open('database/init.sql', 'r') as f:
    migration_sql = f.read()

# Connect to database
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Execute migration
cur.execute(migration_sql)
conn.commit()

print('Database migration completed successfully')
"
    
    log_info "Database migrations completed"
}

# Deploy to ECS
deploy_to_ecs() {
    log_info "Deploying to ECS..."
    
    # Update backend service
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service transcription-backend-service \
        --force-new-deployment \
        --region $AWS_REGION
    
    # Update frontend service
    aws ecs update-service \
        --cluster transcription-frontend-service \
        --service transcription-frontend-service \
        --force-new-deployment \
        --region $AWS_REGION
    
    log_info "ECS deployment initiated"
}

# Wait for deployment completion
wait_for_deployment() {
    log_info "Waiting for deployment to complete..."
    
    aws ecs wait services-stable \
        --cluster $CLUSTER_NAME \
        --services transcription-backend-service transcription-frontend-service \
        --region $AWS_REGION
    
    log_info "Deployment completed successfully"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    sleep 30
    
    # Check backend health
    if curl -f $HEALTH_CHECK_URL/health; then
        log_info "Backend health check passed"
    else
        log_error "Backend health check failed"
        return 1
    fi
    
    # Check frontend health
    if curl -f $FRONTEND_URL/health; then
        log_info "Frontend health check passed"
    else
        log_error "Frontend health check failed"
        return 1
    fi
    
    log_info "All health checks passed"
}

# Rollback function
rollback() {
    log_warn "Initiating rollback..."
    
    # Get previous task definition
    PREVIOUS_TASK_DEF=$(aws ecs describe-services \
        --cluster $CLUSTER_NAME \
        --services transcription-backend-service \
        --query 'services[0].deployments[1].taskDefinition' \
        --output text \
        --region $AWS_REGION)
    
    if [[ "$PREVIOUS_TASK_DEF" != "None" ]]; then
        aws ecs update-service \
            --cluster $CLUSTER_NAME \
            --service transcription-backend-service \
            --task-definition $PREVIOUS_TASK_DEF \
            --region $AWS_REGION
        
        log_info "Rollback initiated"
    else
        log_error "No previous task definition found for rollback"
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary resources..."
    docker system prune -f
    log_info "Cleanup completed"
}

# Main deployment flow
main() {
    case "$1" in
        "build")
            check_prerequisites
            build_images
            ;;
        "push")
            check_prerequisites
            push_images
            ;;
        "migrate")
            run_migrations
            ;;
        "deploy")
            check_prerequisites
            deploy_to_ecs
            wait_for_deployment
            run_health_checks
            ;;
        "rollback")
            rollback
            ;;
        "full")
            check_prerequisites
            build_images
            push_images
            run_migrations
            deploy_to_ecs
            wait_for_deployment
            if ! run_health_checks; then
                log_error "Health checks failed, initiating rollback"
                rollback
                exit 1
            fi
            cleanup
            ;;
        *)
            echo "Usage: $0 {build|push|migrate|deploy|rollback|full}"
            echo ""
            echo "Commands:"
            echo "  build     - Build Docker images"
            echo "  push      - Push images to ECR"
            echo "  migrate   - Run database migrations"
            echo "  deploy    - Deploy to ECS"
            echo "  rollback  - Rollback to previous version"
            echo "  full      - Complete deployment process"
            exit 1
            ;;
    esac
}

# Trap errors and cleanup
trap 'log_error "Deployment failed!"; cleanup; exit 1' ERR

# Run main function
main "$@"

log_info "✅ Deployment process completed successfully!"