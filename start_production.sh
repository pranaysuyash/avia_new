#!/bin/bash

# Production Startup Script for Audio/Video Transcription App
# This script handles production deployment with proper error handling and logging

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/logs/startup.log"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
ENV_FILE="${SCRIPT_DIR}/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() {
    log "INFO" "${BLUE}$*${NC}"
}

log_warn() {
    log "WARN" "${YELLOW}$*${NC}"
}

log_error() {
    log "ERROR" "${RED}$*${NC}"
}

log_success() {
    log "SUCCESS" "${GREEN}$*${NC}"
}

# Error handler
error_handler() {
    local line_number=$1
    log_error "Script failed at line ${line_number}"
    log_error "Cleaning up..."
    
    # Attempt cleanup
    docker-compose down --remove-orphans 2>/dev/null || true
    
    exit 1
}

trap 'error_handler ${LINENO}' ERR

# Create logs directory
mkdir -p "${SCRIPT_DIR}/logs"

log_info "Starting production deployment of Audio/Video Transcription App"
log_info "Script directory: ${SCRIPT_DIR}"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Validate configuration
validate_configuration() {
    log_info "Validating configuration..."
    
    # Check if .env file exists
    if [[ ! -f "${ENV_FILE}" ]]; then
        log_error ".env file not found at ${ENV_FILE}"
        log_info "Please copy .env.production to .env and configure your settings"
        exit 1
    fi
    
    # Source environment variables
    set -a  # Automatically export all variables
    source "${ENV_FILE}"
    set +a
    
    # Check required variables
    local required_vars=(
        "OPENAI_API_KEY"
        "ELEVENLABS_API_KEY"
        "ADMIN_PASSWORD"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]] || [[ "${!var}" == *"your-"* ]] || [[ "${!var}" == *"here"* ]]; then
            missing_vars+=("${var}")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing or unconfigured required environment variables:"
        for var in "${missing_vars[@]}"; do
            log_error "  - ${var}"
        done
        log_info "Please update your .env file with proper values"
        exit 1
    fi
    
    log_success "Configuration validation passed"
}

# Setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    local ssl_dir="${SCRIPT_DIR}/nginx/ssl"
    mkdir -p "${ssl_dir}"
    
    # Check if certificates exist
    if [[ ! -f "${ssl_dir}/server.crt" ]] || [[ ! -f "${ssl_dir}/server.key" ]]; then
        log_warn "SSL certificates not found, generating self-signed certificates"
        log_warn "For production, please use proper SSL certificates"
        
        # Generate self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "${ssl_dir}/server.key" \
            -out "${ssl_dir}/server.crt" \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" \
            2>/dev/null
        
        log_info "Self-signed SSL certificates generated"
    else
        log_success "SSL certificates found"
    fi
    
    # Set proper permissions
    chmod 600 "${ssl_dir}/server.key"
    chmod 644 "${ssl_dir}/server.crt"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check available disk space (minimum 5GB)
    local available_space=$(df "${SCRIPT_DIR}" | awk 'NR==2 {print $4}')
    local min_space=$((5 * 1024 * 1024))  # 5GB in KB
    
    if [[ ${available_space} -lt ${min_space} ]]; then
        log_error "Insufficient disk space. Available: ${available_space}KB, Required: ${min_space}KB"
        exit 1
    fi
    
    # Check if ports are available
    local ports=("${HTTP_PORT:-80}" "${HTTPS_PORT:-443}" "${APP_PORT:-8501}")
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":${port} "; then
            log_warn "Port ${port} is already in use"
        fi
    done
    
    log_success "Pre-deployment checks passed"
}

# Build and deploy
deploy() {
    log_info "Building and deploying application..."
    
    # Pull latest images
    log_info "Pulling latest base images..."
    docker-compose pull --ignore-pull-failures
    
    # Build application
    log_info "Building application image..."
    docker-compose build --no-cache
    
    # Start services
    log_info "Starting services..."
    if [[ "${ENABLE_MONITORING:-false}" == "true" ]]; then
        docker-compose --profile monitoring up -d
    else
        docker-compose up -d
    fi
    
    log_success "Application deployed successfully"
}

# Health checks
verify_deployment() {
    log_info "Verifying deployment..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ ${attempt} -le ${max_attempts} ]]; do
        log_info "Health check attempt ${attempt}/${max_attempts}..."
        
        if curl -f -s "http://localhost:${APP_PORT:-8501}/health" > /dev/null 2>&1; then
            log_success "Application is healthy"
            break
        fi
        
        if [[ ${attempt} -eq ${max_attempts} ]]; then
            log_error "Application failed to start properly"
            log_info "Checking container logs..."
            docker-compose logs --tail=50 transcription-app
            exit 1
        fi
        
        sleep 10
        ((attempt++))
    done
    
    # Test HTTPS endpoint if nginx is running
    if docker-compose ps nginx | grep -q "Up"; then
        if curl -f -s -k "https://localhost:${HTTPS_PORT:-443}/health" > /dev/null 2>&1; then
            log_success "HTTPS endpoint is accessible"
        else
            log_warn "HTTPS endpoint is not accessible"
        fi
    fi
}

# Display deployment information
show_deployment_info() {
    log_info "Deployment completed successfully!"
    echo
    echo "=== DEPLOYMENT INFORMATION ==="
    echo "Application URL: https://localhost:${HTTPS_PORT:-443}"
    echo "HTTP URL: http://localhost:${HTTP_PORT:-80}"
    echo "Direct App URL: http://localhost:${APP_PORT:-8501}"
    echo
    echo "Health Check: curl http://localhost:${APP_PORT:-8501}/health"
    echo "Detailed Health: curl http://localhost:${APP_PORT:-8501}/health-detailed"
    echo "Metrics: curl http://localhost:${APP_PORT:-8501}/metrics"
    echo
    
    if [[ "${ENABLE_MONITORING:-false}" == "true" ]]; then
        echo "Monitoring URLs:"
        echo "Prometheus: http://localhost:${PROMETHEUS_PORT:-9090}"
        echo "Grafana: http://localhost:${GRAFANA_PORT:-3000}"
        echo
    fi
    
    echo "=== USEFUL COMMANDS ==="
    echo "View logs: docker-compose logs -f transcription-app"
    echo "Stop services: docker-compose down"
    echo "Restart services: docker-compose restart"
    echo "Update deployment: ./start_production.sh"
    echo
    
    echo "=== NEXT STEPS ==="
    echo "1. Configure your domain and SSL certificates for production"
    echo "2. Set up monitoring and alerting"
    echo "3. Configure backup procedures"
    echo "4. Review security settings"
    echo
}

# Cleanup function
cleanup() {
    log_info "Cleaning up old containers and images..."
    docker system prune -f --volumes
    log_success "Cleanup completed"
}

# Main execution
main() {
    log_info "=== PRODUCTION DEPLOYMENT STARTED ==="
    
    check_prerequisites
    validate_configuration
    setup_ssl
    pre_deployment_checks
    
    # Stop existing deployment
    log_info "Stopping existing deployment..."
    docker-compose down --remove-orphans 2>/dev/null || true
    
    deploy
    verify_deployment
    show_deployment_info
    
    log_success "=== PRODUCTION DEPLOYMENT COMPLETED ==="
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log_info "Stopping services..."
        docker-compose down
        log_success "Services stopped"
        ;;
    "restart")
        log_info "Restarting services..."
        docker-compose restart
        log_success "Services restarted"
        ;;
    "logs")
        docker-compose logs -f transcription-app
        ;;
    "health")
        curl -s "http://localhost:${APP_PORT:-8501}/health" | jq . || echo "Health check failed"
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|logs|health|cleanup}"
        echo
        echo "Commands:"
        echo "  deploy   - Deploy the application (default)"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - Show application logs"
        echo "  health   - Check application health"
        echo "  cleanup  - Clean up old containers and images"
        exit 1
        ;;
esac