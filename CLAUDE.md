# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BioIntel.AI is a free AI-powered bioinformatics platform for gene expression analysis and literature summarization. It's built with FastAPI backend and optional Streamlit frontend, designed to provide researchers with powerful tools for analyzing gene expression data and processing scientific literature at zero cost.

## Common Development Commands

### Backend Development
```bash
# Install dependencies (development - includes all ML libraries)
pip install -r requirements-full.txt

# Install dependencies (production - lightweight for Vercel)
pip install -r requirements.txt

# Start the main FastAPI application
uvicorn api.main:app --reload --port 8000

# Run database migrations
alembic upgrade head

# Run all tests
pytest

# Run specific test categories
pytest tests/test_auth_api.py          # Authentication tests
pytest tests/test_bioinformatics_api.py # Bioinformatics API tests
pytest tests/test_literature_api.py    # Literature processing tests
pytest tests/test_integration_workflows.py # Integration tests

# Run tests with coverage
pytest --cov=. --cov-report=html
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
- Uses SQLAlchemy with PostgreSQL for production, SQLite for development
- Alembic for database migrations
- Models follow domain-driven design principles
- Supports both local and cloud database deployments

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
- **Vercel**: Serverless deployment with automatic scaling
- **Docker**: Containerized deployment with docker-compose
- **Local**: Direct Python execution with virtual environment

## Testing Strategy

### Test Structure
- **Unit Tests**: Individual service and utility testing
- **Integration Tests**: End-to-end API testing
- **Test Fixtures**: Comprehensive test data setup in `tests/conftest.py`
- **Mocking**: External API and AI service mocking for reliable tests

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
- Create new Alembic migration for schema changes: `alembic revision --autogenerate -m "description"`
- Apply migrations: `alembic upgrade head`
- Test migrations on sample data

### Adding New Features
- Create service class in `services/` for business logic
- Add API endpoints in appropriate `api/` module
- Create database models in `models/` if needed
- Add comprehensive tests in `tests/`
- Update frontend components in `frontend/` if needed

### External API Integration
- All external APIs are free and don't require authentication
- Use httpx for async HTTP calls
- Implement proper error handling and retry logic
- Cache responses when appropriate

## Deployment Notes

### Vercel Configuration
- Configured for serverless Python deployment
- Uses `vercel.json` for routing configuration
- Optimized requirements.txt for 250MB limit
- Environment variables managed through Vercel dashboard

### Docker Configuration
- Multi-stage builds for production optimization
- Separate containers for backend and frontend
- PostgreSQL and Redis as service dependencies
- Health checks for service monitoring

### Performance Considerations
- Database connection pooling for production
- Redis caching for frequently accessed data
- Async request handling for better concurrency
- Optimized AI model loading and caching