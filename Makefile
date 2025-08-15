# Makefile for Comprehensive Transcription Platform
.PHONY: help install test lint format type-check security clean docker-build docker-run migrate setup-db run-api run-app
.PHONY: dev prod health monitor logs backup restore quick-start comprehensive-test

# Default target
help: ## Show this help message
	@echo "Comprehensive Transcription Platform - Development Commands"
	@echo "=========================================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Quick Development Commands
dev: docker-build docker-run ## Full development environment setup
	@echo "🚀 Development environment started!"
	@echo "   Streamlit:     http://localhost:8501"
	@echo "   API:           http://localhost:8000"
	@echo "   Analytics:     http://localhost:8502"
	@echo "   Grafana:       http://localhost:3000 (admin/admin123)"
	@echo "   Prometheus:    http://localhost:9090"

quick-start: install docker-run ## Quick start for development

comprehensive-test: ## Run comprehensive test suite
	@echo "🧪 Running comprehensive test suite..."
	@python test_comprehensive_suite.py

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r api_requirements.txt
	python -m spacy download en_core_web_sm
	python -m spacy download es_core_news_sm
	python -m spacy download fr_core_news_sm
	python -m spacy download de_core_news_sm

# Testing
test:
	pytest -v --cov=. --cov-report=term-missing --cov-report=html --cov-report=xml

test-unit:
	pytest -v -m "unit" --cov=. --cov-report=term-missing

test-integration:
	pytest -v -m "integration" --cov=. --cov-report=term-missing

# Code quality
lint:
	flake8 . --config=.flake8
	pylint api/ --rcfile=.pylintrc || true

format:
	black .
	isort .

type-check:
	mypy . --config-file=mypy.ini

# Security
security:
	bandit -r . -f json -o security_report.json
	safety check --json --output safety_report.json || true

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/

# Docker operations
docker-build:
	docker-compose build

docker-build-prod:
	docker build -f Dockerfile.api -t video-ner-api:latest .
	docker build -f Dockerfile -t video-ner-app:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Database operations
migrate:
	alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

setup-db:
	python setup_postgres.py

# Run services
run-api:
	uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

run-api-prod:
	uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 4

run-app:
	streamlit run app.py

run-websocket:
	python -m websocket.enhanced_server

# Development setup
dev-setup: install setup-db migrate
	@echo "Development environment setup complete!"

# Production deployment
deploy-prod:
	@echo "Building production images..."
	$(MAKE) docker-build-prod
	@echo "Running database migrations..."
	$(MAKE) migrate
	@echo "Starting services..."
	docker-compose -f docker-compose.production.yml up -d
	@echo "Production deployment complete!"

# CI/CD helpers
ci-test:
	pytest -v --cov=. --cov-report=xml --cov-report=term-missing --junitxml=test-results.xml

ci-lint:
	flake8 . --config=.flake8 --format=json --output-file=flake8-report.json

ci-security:
	bandit -r . -f json -o bandit-report.json
	safety check --json --output safety-report.json

# Pre-commit hooks
pre-commit:
	pre-commit install
	pre-commit run --all-files