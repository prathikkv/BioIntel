# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Instructions for Claude Code

**Development Approach:**
1. Use the TodoWrite tool to plan and track all tasks
2. Keep changes simple and focused - avoid massive refactors
3. Always test changes after implementation
4. Follow existing code patterns and architecture
5. Check for lint/type errors before completing tasks

**Key Commands to Remember:**
- Run tests: `pytest` or `pytest tests/test_specific.py`
- Run linting: Check if project has linting configured
- Run type checking: Check if project has type checking configured
- Database migrations: `alembic upgrade head` (if using Alembic)
- Start dev server: `uvicorn api.main:app --reload --port 8000`

## Project Overview

BioIntel.AI is a free AI-powered bioinformatics platform for gene expression analysis and literature summarization. It's built with FastAPI backend and optional Streamlit frontend, designed to provide researchers with powerful tools for analyzing gene expression data and processing scientific literature at zero cost.

## Common Development Commands

### Development Environment Setup
```bash
# Install dependencies (development - includes all ML libraries)
pip install -r requirements-full.txt

# Install dependencies (production - lightweight for Vercel)
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your database credentials and other settings
```

### Backend Development
```bash
# Start the main FastAPI application
uvicorn api.main:app --reload --port 8000

# Alternative: Start with main.py
uvicorn main:app --reload --port 8000

# For Vercel deployment testing
python api/index.py
```

### Database Management
```bash
# Database migrations (if Alembic is configured)
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Initialize database tables (manual)
python -c "from models.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_auth_api.py          # Authentication tests
pytest tests/test_bioinformatics_api.py # Bioinformatics API tests
pytest tests/test_literature_api.py    # Literature processing tests
pytest tests/test_integration_workflows.py # Integration tests

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run single test method
pytest tests/test_auth_api.py::test_register_user -v
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
# Deploy to Vercel
vercel --prod

# Set environment variables
vercel env add DATABASE_URL
vercel env add SECRET_KEY
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
- **Entry Point**: `api/index.py` (Vercel-compatible handler)
- **Routing**: `vercel.json` routes all requests to `api/index.py`
- **Requirements**: Ultra-minimal `requirements.txt` for 250MB limit
- **Environment**: Variables set in `vercel.json` and Vercel dashboard
- **Database**: Uses SQLite for serverless deployment
- **Timeout**: 30 seconds max duration for serverless functions

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

### Dual Entry Points
- **Development/Production**: `api/main.py` - Full FastAPI application with middleware
- **Vercel Deployment**: `api/index.py` - Vercel-compatible handler wrapping FastAPI

### Service Layer Pattern
- All business logic in `services/` directory
- Async service classes with initialization methods
- Service injection into API endpoints via dependency injection

### Configuration Management
- Environment-based configuration via `utils/config.py`
- Pydantic Settings for type-safe configuration
- Separate requirements files for different deployment scenarios

### Database Strategy
- **Development**: SQLite for simplicity
- **Production**: PostgreSQL with connection pooling
- **Vercel**: SQLite for serverless compatibility
- Models use SQLAlchemy with async support where needed