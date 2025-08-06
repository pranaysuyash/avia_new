# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a comprehensive audio/video transcription and analysis platform with enterprise features. The system includes a Streamlit web app, FastAPI backend, Electron desktop app, and React Native mobile app.

## Common Development Commands

### Running the Application

```bash
# Run the API server (development mode without Redis)
python run_api.py

# Run the Streamlit app
streamlit run app.py

# Run both API and Streamlit with Docker
docker-compose up --build

# Run production deployment
make deploy-prod
```

### Testing

```bash
# Run all tests with coverage
pytest -v --cov=. --cov-report=term-missing --cov-report=html

# Run specific test file
pytest test_customer_support.py -v

# Run tests by marker
pytest -m "unit" -v
pytest -m "integration" -v

# Run tests with parallel execution
pytest -n auto
```

### Code Quality

```bash
# Format code
make format  # Runs black and isort

# Lint code
make lint    # Runs flake8 and pylint

# Type checking
make type-check  # Runs mypy

# Security scan
make security    # Runs bandit and safety
```

### Desktop App Development

```bash
cd desktop_app
npm install
npm run dev  # Run in development mode
npm run build-mac  # Build for macOS
npm run build-win  # Build for Windows
```

### Mobile App Development

```bash
cd mobile
npm install
npm run ios     # Run on iOS simulator
npm run android # Run on Android emulator
```

## Architecture Overview

### Core System Structure

The platform follows a modular architecture with clear separation of concerns:

1. **API Layer** (`api/`)
   - FastAPI backend with comprehensive REST endpoints
   - WebSocket support for real-time features
   - Middleware for auth, rate limiting, monitoring, and audit logging
   - Database models using SQLAlchemy with PostgreSQL

2. **Service Layer**
   - `services/transcription_service.py` - Handles audio/video transcription with Whisper
   - `services/audit_logging_service.py` - Centralized audit logging
   - `services/support_service.py` - Customer support backend
   - `services/sales_service.py` - Enterprise sales features
   - `services/marketing_service.py` - Marketing automation

3. **Feature Systems** (Implemented as standalone modules)
   - `compliance_security_system.py` - GDPR, SOC2, audit logging, SSO
   - `customer_support_system.py` - Ticketing, chat, help docs, forums
   - `api_platform_system.py` - Developer platform with API keys
   - `multi_llm_provider_system.py` - Multiple LLM provider support
   - `llm_provider_optimization.py` - Smart LLM routing and caching
   - `multilingual_ai_dubbing_system.py` - AI dubbing capabilities

4. **UI Components**
   - Streamlit apps (`*_ui.py` files) for web interface
   - React components (`frontend/src/components/`)
   - Electron desktop app (`desktop_app/src/renderer/`)
   - React Native mobile app (`mobile/src/`)

### Database Architecture

The system uses PostgreSQL with these key models:
- User authentication and teams
- Transcription sessions and results
- API keys and usage tracking
- Subscription tiers and billing
- Audit logs and compliance records

### Authentication & Security

- JWT-based authentication with refresh tokens
- API key authentication for developer access
- Rate limiting per user/tier
- RBAC (Role-Based Access Control)
- Enterprise SSO (SAML 2.0, OIDC)
- Comprehensive audit logging with encryption

### Key Design Patterns

1. **Middleware Chain**: All API requests pass through auth → rate limit → monitoring → audit → business logic
2. **Repository Pattern**: Database operations abstracted through repository classes
3. **Service Layer**: Business logic separated from API endpoints
4. **Event-Driven**: WebSocket connections for real-time updates
5. **Caching Strategy**: Redis for session data, LLM response caching
6. **Queue System**: Celery for async task processing (transcription, exports)

### Integration Points

- **OpenAI API**: Whisper for transcription, GPT for analysis
- **ElevenLabs**: Text-to-speech functionality
- **Multiple LLM Providers**: OpenAI, Anthropic, Google, Cohere, local models
- **Cloud Storage**: S3-compatible storage for media files
- **Email Services**: SMTP for notifications
- **Payment Processing**: Stripe integration for subscriptions

## Development Best Practices

### When Adding New Features

1. Create the core system module (e.g., `new_feature_system.py`)
2. Add API endpoints in `api/endpoints/new_feature.py`
3. Create Streamlit UI in `new_feature_ui.py`
4. Add React/Electron/React Native components as needed
5. Write comprehensive tests in `test_new_feature.py`
6. Update API documentation

### Testing Strategy

- Unit tests for all business logic
- Integration tests for API endpoints
- Mock external services (OpenAI, ElevenLabs, etc.)
- Use pytest fixtures for database setup
- Aim for >80% code coverage

### API Development

All new endpoints should:
- Use dependency injection for auth/database
- Include proper OpenAPI documentation
- Implement rate limiting
- Log audit events for sensitive operations
- Return consistent error responses

### Environment Configuration

Key environment variables:
- `OPENAI_API_KEY` - Required for transcription
- `JWT_SECRET_KEY` - For authentication
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection (optional in dev)
- `DISABLE_REDIS=true` - Run without Redis in development

## Project Status

The following major features have been implemented:
- Tasks 1-53: Core platform features
- Tasks 54-56: API platform, compliance, customer support
- Tasks 61-77: Advanced features (OCR, document analysis, etc.)
- Tasks 114-115: Multi-LLM support and optimization

Next pending tasks start from Task 59 (Internationalization).