#!/bin/bash

# =============================================================================
# Development Environment Setup Script
# Comprehensive setup for the Transcription Platform
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install package if not present (macOS)
install_macos() {
    if command_exists brew; then
        brew install "$1"
    else
        print_error "Homebrew not found. Please install Homebrew first."
        exit 1
    fi
}

# Function to install package if not present (Ubuntu/Debian)
install_ubuntu() {
    sudo apt-get update
    sudo apt-get install -y "$1"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            OS="ubuntu"
        else
            OS="linux"
        fi
    else
        OS="unknown"
    fi
}

# Main setup function
main() {
    echo "🚀 Setting up Comprehensive Transcription Platform Development Environment"
    echo "========================================================================="
    
    detect_os
    print_status "Detected OS: $OS"
    
    # Check Python 3.11+
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python version: $PYTHON_VERSION"
        
        # Check if version is 3.11+
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
            print_success "Python 3.11+ is available"
        else
            print_warning "Python 3.11+ required. Current version: $PYTHON_VERSION"
            if [[ "$OS" == "macos" ]]; then
                print_status "Installing Python 3.11 via Homebrew..."
                install_macos python@3.11
            elif [[ "$OS" == "ubuntu" ]]; then
                print_status "Installing Python 3.11..."
                sudo apt-get update
                sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
            fi
        fi
    else
        print_error "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Check Node.js 18+
    if command_exists node; then
        NODE_VERSION=$(node --version | cut -d'v' -f2)
        print_status "Node.js version: $NODE_VERSION"
    else
        print_warning "Node.js not found. Installing..."
        if [[ "$OS" == "macos" ]]; then
            install_macos node
        elif [[ "$OS" == "ubuntu" ]]; then
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt-get install -y nodejs
        fi
    fi
    
    # Check Docker
    if command_exists docker; then
        print_success "Docker is available"
        
        # Check if Docker is running
        if docker info >/dev/null 2>&1; then
            print_success "Docker is running"
        else
            print_warning "Docker is not running. Please start Docker."
        fi
    else
        print_error "Docker not found. Please install Docker Desktop."
        exit 1
    fi
    
    # Check Docker Compose
    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        print_success "Docker Compose is available"
    else
        print_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    # Install system dependencies
    print_status "Installing system dependencies..."
    
    if [[ "$OS" == "macos" ]]; then
        # macOS dependencies
        if ! command_exists ffmpeg; then
            print_status "Installing ffmpeg..."
            install_macos ffmpeg
        fi
        
        if ! command_exists git; then
            print_status "Installing git..."
            install_macos git
        fi
        
    elif [[ "$OS" == "ubuntu" ]]; then
        # Ubuntu dependencies
        print_status "Installing system packages..."
        sudo apt-get update
        sudo apt-get install -y \
            build-essential \
            curl \
            git \
            ffmpeg \
            libpq-dev \
            python3-pip \
            python3-venv
    fi
    
    # Create Python virtual environment
    if [[ ! -d "venv" ]]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment and install dependencies
    print_status "Installing Python dependencies..."
    source venv/bin/activate
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    # Install requirements
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_warning "requirements.txt not found"
    fi
    
    # Install spaCy models
    print_status "Installing spaCy language models..."
    python -m spacy download en_core_web_sm
    python -m spacy download es_core_news_sm
    python -m spacy download fr_core_news_sm
    python -m spacy download de_core_news_sm
    
    # Setup environment file
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            print_status "Creating .env file from template..."
            cp .env.example .env
            print_warning "Please update .env file with your actual API keys and settings"
        else
            print_warning ".env.example not found. Creating basic .env file..."
            cat > .env << 'EOF'
# Basic environment configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
OPENAI_API_KEY=your-openai-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here
JWT_SECRET_KEY=development-secret-key-minimum-32-characters
DATABASE_URL=postgresql://transcription_user:transcription_pass@localhost:5432/transcription_db
REDIS_URL=redis://localhost:6379/0
EOF
        fi
        print_success ".env file created"
    else
        print_success ".env file already exists"
    fi
    
    # Create necessary directories
    print_status "Creating application directories..."
    mkdir -p uploads models reports monitoring logs temp
    print_success "Directories created"
    
    # Build Docker images
    print_status "Building Docker images..."
    make docker-build || docker-compose build
    print_success "Docker images built"
    
    # Install Git hooks (if available)
    if [[ -f "scripts/pre-commit" ]]; then
        print_status "Installing Git pre-commit hooks..."
        cp scripts/pre-commit .git/hooks/pre-commit
        chmod +x .git/hooks/pre-commit
        print_success "Git hooks installed"
    fi
    
    # Run initial tests
    print_status "Running initial tests to verify setup..."
    if command_exists pytest; then
        python -m pytest test_utils.py -v --tb=short || print_warning "Some tests failed - this is normal for initial setup"
    else
        print_warning "pytest not installed - skipping tests"
    fi
    
    # Final setup summary
    echo
    print_success "🎉 Development environment setup complete!"
    echo
    echo "Next steps:"
    echo "1. Update .env file with your API keys"
    echo "2. Start the development environment: make dev"
    echo "3. Access the applications:"
    echo "   - Streamlit App:     http://localhost:8501"
    echo "   - API:               http://localhost:8000"
    echo "   - Analytics:         http://localhost:8502"
    echo "   - Grafana:           http://localhost:3000"
    echo "   - Prometheus:        http://localhost:9090"
    echo
    echo "Common commands:"
    echo "   make help           - Show all available commands"
    echo "   make dev           - Start development environment"
    echo "   make test          - Run tests"
    echo "   make logs          - View logs"
    echo "   make down          - Stop all services"
    echo
}

# Cleanup function
cleanup() {
    print_status "Cleaning up on exit..."
}

# Trap cleanup function on script exit
trap cleanup EXIT

# Run main function
main "$@"