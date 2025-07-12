# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical Development Patterns

**Dependency Management:**
- The project uses dual requirements files: `requirements.txt` (minimal for Vercel) and `requirements-full-backup.txt` (full development)
- Security utilities in `utils/security.py` use conditional imports with fallbacks for missing dependencies
- Always test imports work in both environments before deploying

**Vercel Deployment Architecture:**
- `api/index.py` is the Vercel entry point with custom ASGI-to-HTTP handler
- Uses BaseHTTPRequestHandler wrapper for serverless compatibility
- Heavy ML dependencies (transformers, torch) are conditionally loaded and skipped in production
- Environment variable `ENVIRONMENT=production` controls feature loading

**Database Strategy:**
- SQLite for development/Vercel, PostgreSQL for full production
- Alembic migrations available but database models can be initialized manually
- `models/database.py` handles connection management with environment-based switching

## Project Overview

BioIntel.AI is a free AI-powered bioinformatics platform for gene expression analysis and literature summarization. It's built with FastAPI backend and optional Streamlit frontend, designed to provide researchers with powerful tools for analyzing gene expression data and processing scientific literature at zero cost.

## Common Development Commands

### Environment Setup
```bash
# Full development environment (includes ML libraries)
pip install -r requirements-full-backup.txt

# Minimal environment (for testing Vercel compatibility)
pip install -r requirements.txt

# Environment configuration already exists (.env file is committed)
# Key settings: ENVIRONMENT=development, USE_FREE_AI=true, ENABLE_RATE_LIMITING=False
```

### Development Server
```bash
# Main development server (full features)
uvicorn api.main:app --reload --port 8000

# Test Vercel compatibility locally
python api/index.py

# Alternative: Direct FastAPI app testing
python -c "from api.index import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"
```

### Database Management
```bash
# Alembic is configured - apply migrations
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Manual database initialization (if migrations fail)
python -c "from models.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Test database connectivity
python -c "from models.database import get_db; db = next(get_db()); print('Database connected'); db.close()"
```

### Testing and Debugging
```bash
# Test import compatibility between environments
python -c "from api.index import app, FASTAPI_AVAILABLE; print(f'Vercel-safe imports: {FASTAPI_AVAILABLE}')"

# Test authentication system components
python -c "from utils.security import security_utils; token = security_utils.create_access_token({'sub': '1'}); print('Auth system working')"

# Test database initialization
python -c "from models.database import get_db; db = next(get_db()); print('DB connected'); db.close()"

# Run pytest tests (if available)
pytest tests/test_auth_api.py -v
pytest tests/test_bioinformatics_api.py -v
pytest tests/test_literature_api.py -v
pytest tests/test_integration_workflows.py -v

# Test Vercel handler locally
python api/index.py
```

### Linting and Type Checking
```bash
# Note: Check if project has these configured
# Common Python linting tools:
# flake8 .
# black .
# mypy .
# ruff check .
```

### Frontend Development
```bash
# Start Streamlit frontend
cd frontend && ./run_frontend.sh

# Or manually:
cd frontend && streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild containers
docker-compose up -d --build
```

### Vercel Deployment
```bash
# Deploy to Vercel (uses current requirements.txt - minimal)
vercel --prod

# Check function logs for debugging
vercel logs

# Test deployment endpoints
curl https://your-app.vercel.app/health
curl -X POST https://your-app.vercel.app/api/auth/register -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'

# Environment variables are pre-configured in vercel.json
# Critical: ENVIRONMENT=production, USE_FREE_AI=true, ENABLE_RATE_LIMITING=False
```

## Code Architecture

### Backend Structure
- **`api/`** - FastAPI route handlers organized by domain
  - `main.py` - Main application entry point with middleware and router configuration
  - `auth.py` - Authentication endpoints (login, register, JWT management)
  - `bioinformatics.py` - Gene expression analysis endpoints
  - `literature.py` - Literature processing and AI summarization endpoints
  - `reports.py` - Report generation endpoints
  - `enterprise.py` - Enterprise features and team management
  - `workflows.py` - Research workflow automation endpoints

- **`services/`** - Business logic layer with async service classes
  - `auth_service.py` - User authentication and JWT management
  - `bioinformatics_service.py` - Gene expression analysis algorithms
  - `literature_service.py` - Literature processing and AI integration
  - `free_ai_service.py` - Free AI model integration (Hugging Face)
  - `bio_apis_service.py` - External bioinformatics API integration
  - `reports_service.py` - Report generation and templating
  - `enterprise_service.py` - Team collaboration features

- **`models/`** - SQLAlchemy database models
  - `database.py` - Database connection and session management
  - `user.py` - User authentication and profile models
  - `bioinformatics.py` - Dataset and analysis job models
  - `literature.py` - Literature summary and chat session models
  - `enterprise.py` - Team and workspace models

- **`utils/`** - Shared utilities
  - `config.py` - Configuration management with Pydantic settings
  - `security.py` - Security utilities and validation
  - `logging.py` - Structured logging configuration

### Database Design
- **SQLAlchemy ORM** with PostgreSQL for production, SQLite for development
- Database migrations handled via Alembic (check if configured)
- Models organized by domain: `user.py`, `bioinformatics.py`, `literature.py`, `enterprise.py`
- Supports both local and cloud database deployments
- Connection management in `models/database.py`

### AI Integration
- **Free AI Models**: Uses Hugging Face Transformers for zero-cost AI processing
- **Literature Processing**: Rule-based entity extraction + AI summarization
- **Gene Expression Analysis**: scikit-learn for PCA, clustering, and statistical analysis
- **External APIs**: Integrates with PubMed, UniProt, Ensembl, STRING, and KEGG APIs

### Frontend Architecture
- **Streamlit**: Interactive web interface for data upload and analysis
- **Plotly**: Interactive visualizations for gene expression data
- **Multi-page Structure**: Dashboard, analysis, literature, reports, and settings
- **Authentication**: JWT-based authentication with the backend API

## Configuration

### Environment Variables
Key environment variables are defined in `.env` file:
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - Application secret key
- `JWT_SECRET_KEY` - JWT token signing key
- `USE_FREE_AI=true` - Enable free AI models (no API keys required)
- `REDIS_URL` - Redis connection for caching
- External API base URLs (all free, no keys required)

### Database Configuration
- **Development**: SQLite with file-based storage
- **Production**: PostgreSQL with connection pooling
- **Testing**: In-memory SQLite database

### Deployment Environments
- **Vercel**: Serverless deployment via `api/index.py` (Vercel handler)
- **Docker**: Containerized deployment with `docker-compose.yml`
- **Local**: Direct Python execution with virtual environment
- **Production**: Uses `api/main.py` as main application entry point

## Testing Strategy

### Test Structure
- **Unit Tests**: Individual service and utility testing
- **Integration Tests**: End-to-end API testing
- **Test Fixtures**: Comprehensive test data setup in `tests/conftest.py`
- **Mocking**: External API and AI service mocking for reliable tests
- **Test Database**: Uses separate SQLite database for testing
- **Test Client**: FastAPI TestClient for API endpoint testing

### Test Database
- Uses separate SQLite database for testing
- Automatic setup and teardown of test data
- Isolated test sessions to prevent data contamination

### Running Tests
- All tests use pytest framework
- Test configuration in `tests/conftest.py`
- Mock external dependencies for faster, reliable testing
- Coverage reporting available

## Security Considerations

### Authentication & Authorization
- JWT-based authentication with refresh tokens
- Password hashing using bcrypt
- Input validation using Pydantic models
- Rate limiting on API endpoints

### Data Protection
- SQL injection prevention through SQLAlchemy ORM
- File upload validation and size limits
- CORS configuration for frontend integration
- Security headers middleware

### Free AI Models
- Uses local Hugging Face models to avoid API key requirements
- No external AI service dependencies in free tier
- Cached models for faster inference

## Development Workflow

### Code Style
- Follow existing patterns in the codebase
- Use async/await for database and external API calls
- Comprehensive error handling with structured logging
- Type hints for better code documentation

### Database Changes
- **If Alembic is configured:** Create migration with `alembic revision --autogenerate -m "description"`
- **If Alembic is configured:** Apply migrations with `alembic upgrade head`
- **Manual approach:** Modify models and recreate tables (development only)
- Always test migrations on sample data
- Database initialization via `models/database.py`

### Adding New Features
1. **Service Layer**: Create service class in `services/` for business logic
2. **API Endpoints**: Add endpoints in appropriate `api/` module
3. **Database Models**: Create models in `models/` if needed
4. **Testing**: Add comprehensive tests in `tests/`
5. **Frontend**: Update Streamlit components in `frontend/` if needed
6. **Dependencies**: Update requirements files if new packages needed

### External API Integration
- **Free APIs**: All external APIs are free and don't require authentication
- **HTTP Client**: Use httpx for async HTTP calls
- **Error Handling**: Implement proper error handling and retry logic
- **Caching**: Cache responses when appropriate
- **Available APIs**: PubMed, UniProt, Ensembl, STRING, KEGG (configured in environment)

## Deployment Notes

### Vercel Configuration
- **Entry Point**: `api/index.py` uses custom BaseHTTPRequestHandler with ASGI delegation to FastAPI
- **Routing**: `vercel.json` routes all traffic to `api/index.py`, which handles both FastAPI and fallback routing
- **Dependencies**: `requirements.txt` contains only essential packages (FastAPI, Pydantic, python-dotenv)
- **Environment**: Production variables defined in `vercel.json`, including `ENVIRONMENT=production`
- **Database**: SQLite file-based storage for serverless compatibility
- **Function Timeout**: 30 seconds maximum, configured in `vercel.json`
- **Error Handling**: Comprehensive fallback routing with helpful error messages for wrong HTTP methods

### Docker Configuration
- **Multi-service Setup**: `docker-compose.yml` with API, database, Redis, frontend, and Nginx
- **Services**: API (FastAPI), PostgreSQL, Redis, Streamlit frontend, Nginx reverse proxy
- **Health Checks**: Configured for all services
- **Volumes**: Persistent data for database and Redis
- **Development**: Use `docker-compose up -d` for full stack

### Performance Considerations
- Database connection pooling for production
- Redis caching for frequently accessed data (configured in docker-compose)
- Async request handling for better concurrency
- Optimized AI model loading and caching
- Free AI models via Hugging Face (no API keys required)
- Vercel deployment optimized with minimal requirements.txt

## Key Architecture Points

### Conditional Dependency Loading
- **Security Utils**: `utils/security.py` implements graceful fallbacks for missing packages (jose→custom JWT, passlib→builtin hashing, redis→memory cache)
- **ML Dependencies**: Heavy packages (transformers, torch) are conditionally imported and skipped in production
- **Environment-Based Features**: `ENVIRONMENT=production` disables ML routers to prevent import failures

### Dual Entry Points with Different Capabilities
- **Development**: `api/main.py` loads all routers including ML-heavy bioinformatics and literature services
- **Vercel**: `api/index.py` loads only lightweight routers (auth, reports) and provides fallback endpoints for missing services
- **Routing Strategy**: Custom ASGI-to-HTTP bridge in Vercel handler with comprehensive error handling

### Authentication Architecture
- JWT-based with both lightweight (itsdangerous) and full (jose) implementations
- Rate limiting optional (disabled in development via `ENABLE_RATE_LIMITING=False`)
- Memory cache fallbacks when Redis unavailable
- Account lockout tracking with configurable thresholds

### Database Model Relationships
- Foreign key relationships temporarily disabled in some models to prevent SQLAlchemy conflicts
- Enterprise models exist but have commented-out back_populates to avoid circular imports
- Manual relationship management in service layer when needed