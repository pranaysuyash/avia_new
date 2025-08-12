#!/bin/bash

# Whisper Advanced Integration Deployment Script
set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker/whisper-advanced/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env.whisper-advanced"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check available disk space (need at least 10GB)
    available_space=$(df / | awk 'NR==2 {print $4}')
    required_space=$((10 * 1024 * 1024)) # 10GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        log_error "Insufficient disk space. Need at least 10GB free."
        exit 1
    fi
    
    # Check available memory (need at least 4GB)
    available_memory=$(free -m | awk 'NR==2{print $7}')
    required_memory=4096 # 4GB in MB
    
    if [ "$available_memory" -lt "$required_memory" ]; then
        log_warning "Low available memory. Whisper Advanced works best with 4GB+ RAM."
    fi
    
    log_success "Prerequisites check passed"
}

# Create environment file if it doesn't exist
create_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_info "Creating environment file..."
        
        cat > "$ENV_FILE" << EOF
# Whisper Advanced Integration Environment Configuration

# Database Configuration
DB_PASSWORD=$(openssl rand -base64 32)

# Security Keys (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# External API Keys (Set these for full functionality)
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
GRAFANA_PASSWORD=admin

# Performance Tuning
WHISPER_MODEL_CACHE_SIZE=3
WHISPER_MAX_CONCURRENT_JOBS=2
WHISPER_WORKER_PROCESSES=1
WHISPER_WORKER_THREADS=4

# Storage Configuration
MAX_FILE_SIZE=26214400
TEMP_FILE_TTL=3600
CLEANUP_TEMP_FILES=true

# Logging
LOG_LEVEL=INFO
EOF
        
        log_success "Environment file created at $ENV_FILE"
        log_warning "Please edit $ENV_FILE and set your API keys before deployment"
    else
        log_info "Environment file already exists"
    fi
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build the main Whisper Advanced image
    docker build -f docker/whisper-advanced/Dockerfile -t whisper-advanced:latest .
    
    if [ $? -eq 0 ]; then
        log_success "Docker images built successfully"
    else
        log_error "Failed to build Docker images"
        exit 1
    fi
}

# Initialize database
init_database() {
    log_info "Initializing database..."
    
    # Start only the database service first
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10
    
    # Run database migrations (if you have them)
    # docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" exec whisper-advanced python -m alembic upgrade head
    
    log_success "Database initialized"
}

# Deploy services
deploy_services() {
    log_info "Deploying Whisper Advanced services..."
    
    # Start all services
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    if [ $? -eq 0 ]; then
        log_success "Services deployed successfully"
    else
        log_error "Failed to deploy services"
        exit 1
    fi
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Wait for services to start
    sleep 30
    
    # Check Whisper Advanced service
    if curl -f http://localhost:8001/whisper-advanced/health > /dev/null 2>&1; then
        log_success "Whisper Advanced service is healthy"
    else
        log_error "Whisper Advanced service health check failed"
        return 1
    fi
    
    # Check Prometheus
    if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
        log_success "Prometheus is healthy"
    else
        log_warning "Prometheus health check failed"
    fi
    
    # Check Grafana
    if curl -f http://localhost:3001/api/health > /dev/null 2>&1; then
        log_success "Grafana is healthy"
    else
        log_warning "Grafana health check failed"
    fi
    
    return 0
}

# Show deployment info
show_deployment_info() {
    log_success "Whisper Advanced Integration deployed successfully!"
    echo
    echo "Service URLs:"
    echo "  Whisper Advanced API: http://localhost:8001"
    echo "  API Documentation: http://localhost:8001/docs"
    echo "  Health Check: http://localhost:8001/whisper-advanced/health"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3001 (admin/admin)"
    echo
    echo "Useful commands:"
    echo "  View logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
    echo "  Stop services: docker-compose -f $DOCKER_COMPOSE_FILE down"
    echo "  Restart services: docker-compose -f $DOCKER_COMPOSE_FILE restart"
    echo
    echo "Configuration file: $ENV_FILE"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" down
    docker system prune -f
    log_success "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting Whisper Advanced Integration deployment..."
    
    check_prerequisites
    create_env_file
    build_images
    init_database
    deploy_services
    
    if health_check; then
        show_deployment_info
    else
        log_error "Deployment completed but health checks failed"
        log_info "Check logs with: docker-compose -f $DOCKER_COMPOSE_FILE logs"
        exit 1
    fi
}

# Command line interface
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "build")
        build_images
        ;;
    "start")
        docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d
        ;;
    "stop")
        docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" down
        ;;
    "restart")
        docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" restart
        ;;
    "logs")
        docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
        ;;
    "health")
        health_check
        ;;
    "cleanup")
        cleanup
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy    - Full deployment (default)"
        echo "  build     - Build Docker images only"
        echo "  start     - Start services"
        echo "  stop      - Stop services"
        echo "  restart   - Restart services"
        echo "  logs      - View service logs"
        echo "  health    - Run health checks"
        echo "  cleanup   - Stop services and clean up"
        echo "  help      - Show this help message"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac