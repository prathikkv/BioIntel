"""
Pytest configuration and fixtures for BioIntel.AI testing
"""

import pytest
import asyncio
import tempfile
import os
from typing import Generator, Dict, Any
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import application components
from api.main import app
from models.database import Base, get_db
from models.user import User
from models.bioinformatics import Dataset, AnalysisJob
from models.literature import LiteratureSummary
from services.auth_service import AuthService
from services.bioinformatics_service import BioinformaticsService
from services.literature_service import LiteratureService
from services.reports_service import ReportsService
from utils.config import Settings

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def test_settings():
    """Test configuration settings"""
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=True,
        DATABASE_URL=TEST_DATABASE_URL,
        SECRET_KEY="test-secret-key",
        JWT_SECRET_KEY="test-jwt-secret",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        ANTHROPIC_API_KEY="test-anthropic-key",
        OPENAI_API_KEY="test-openai-key",
        REDIS_URL="redis://localhost:6379",
        MAX_FILE_SIZE=10 * 1024 * 1024,  # 10MB
        MAX_GENES=50000,
        MAX_SAMPLES=10000,
        MAX_PAPER_LENGTH=100000,
        REPORTS_DIR="/tmp/test_reports"
    )

@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_db):
    """Create database session for tests"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(test_db, test_settings):
    """Create test client"""
    def override_get_db():
        session = test_db()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_here",
        full_name="Test User",
        is_active=True,
        is_verified=True,
        organization="Test Organization",
        position="Researcher",
        consent_given=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Create authentication headers for test user"""
    # Mock JWT token
    access_token = "test-jwt-token"
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def test_dataset(db_session, test_user):
    """Create test dataset"""
    dataset = Dataset(
        user_id=test_user.id,
        name="Test Dataset",
        description="Test gene expression dataset",
        file_name="test_data.csv",
        file_size=1024,
        file_type="csv",
        num_genes=100,
        num_samples=10,
        organism="Homo sapiens",
        tissue_type="Breast tissue",
        experiment_type="RNA-seq",
        data_quality_score=85.5,
        processing_status="completed"
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset

@pytest.fixture(scope="function")
def test_analysis_job(db_session, test_user, test_dataset):
    """Create test analysis job"""
    analysis_job = AnalysisJob(
        user_id=test_user.id,
        dataset_id=test_dataset.id,
        job_type="pca",
        job_name="Test PCA Analysis",
        parameters={"n_components": 2},
        status="completed",
        progress=100.0,
        results={
            "explained_variance": [0.6, 0.3],
            "pca_scores": {"PC1": [1, 2, 3], "PC2": [4, 5, 6]}
        }
    )
    db_session.add(analysis_job)
    db_session.commit()
    db_session.refresh(analysis_job)
    return analysis_job

@pytest.fixture(scope="function")
def test_literature_summary(db_session, test_user):
    """Create test literature summary"""
    literature_summary = LiteratureSummary(
        user_id=test_user.id,
        title="Test Research Paper",
        authors="Smith, J., Johnson, M.",
        journal="Nature Biotechnology",
        abstract="This is a test abstract for testing purposes.",
        source_type="abstract",
        summary="Test summary of the research paper",
        key_findings=["Finding 1", "Finding 2"],
        biomarkers=["Biomarker A", "Biomarker B"],
        genes=["GENE1", "GENE2"],
        diseases=["Cancer", "Diabetes"],
        methods=["RNA-seq", "Western blot"],
        confidence_score=0.85,
        processing_status="completed"
    )
    db_session.add(literature_summary)
    db_session.commit()
    db_session.refresh(literature_summary)
    return literature_summary

@pytest.fixture(scope="function")
def sample_gene_expression_data():
    """Sample gene expression data for testing"""
    return {
        "genes": ["GENE1", "GENE2", "GENE3", "GENE4", "GENE5"],
        "samples": ["Sample1", "Sample2", "Sample3", "Sample4"],
        "expression_matrix": [
            [1.5, 2.3, 1.8, 2.1],  # GENE1
            [0.8, 1.2, 0.9, 1.1],  # GENE2
            [3.2, 3.8, 3.1, 3.5],  # GENE3
            [2.1, 1.9, 2.3, 2.0],  # GENE4
            [1.1, 1.3, 1.0, 1.2]   # GENE5
        ]
    }

@pytest.fixture(scope="function")
def sample_csv_data():
    """Sample CSV data for testing file uploads"""
    csv_content = """Gene,Sample1,Sample2,Sample3,Sample4
GENE1,1.5,2.3,1.8,2.1
GENE2,0.8,1.2,0.9,1.1
GENE3,3.2,3.8,3.1,3.5
GENE4,2.1,1.9,2.3,2.0
GENE5,1.1,1.3,1.0,1.2
"""
    return csv_content.encode('utf-8')

@pytest.fixture(scope="function")
def sample_pdf_data():
    """Sample PDF data for testing"""
    # Mock PDF content
    return b"Mock PDF content for testing"

@pytest.fixture(scope="function")
def mock_anthropic_client():
    """Mock Anthropic API client"""
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"summary": "Test summary", "biomarkers": ["Test biomarker"], "genes": ["TEST_GENE"], "diseases": ["Test disease"], "methods": ["Test method"], "confidence_score": 0.8}')]
    mock_client.messages.create.return_value = mock_message
    return mock_client

@pytest.fixture(scope="function")
def mock_openai_client():
    """Mock OpenAI API client"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"summary": "Test summary", "biomarkers": ["Test biomarker"], "genes": ["TEST_GENE"], "diseases": ["Test disease"], "methods": ["Test method"], "confidence_score": 0.8}'))]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

@pytest.fixture(scope="function")
def temp_reports_dir():
    """Create temporary directory for reports"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir

@pytest.fixture(scope="function")
def mock_auth_service():
    """Mock authentication service"""
    mock_service = AsyncMock()
    mock_service.register_user = AsyncMock(return_value={
        "message": "User registered successfully",
        "user": {"id": 1, "email": "test@example.com", "full_name": "Test User"},
        "access_token": "test-token",
        "refresh_token": "test-refresh-token",
        "token_type": "bearer"
    })
    mock_service.authenticate_user = AsyncMock(return_value={
        "message": "Authentication successful",
        "user": {"id": 1, "email": "test@example.com", "full_name": "Test User"},
        "access_token": "test-token",
        "refresh_token": "test-refresh-token",
        "token_type": "bearer"
    })
    mock_service.get_current_user = AsyncMock(return_value=User(
        id=1,
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_verified=True
    ))
    return mock_service

@pytest.fixture(scope="function")
def mock_bioinformatics_service():
    """Mock bioinformatics service"""
    mock_service = AsyncMock()
    mock_service.upload_dataset = AsyncMock(return_value={
        "message": "Dataset uploaded successfully",
        "dataset": {"id": 1, "name": "Test Dataset", "num_genes": 100, "num_samples": 10}
    })
    mock_service.perform_eda = AsyncMock(return_value={
        "dataset_id": 1,
        "statistics": {"num_genes": 100, "num_samples": 10},
        "plots": {"distribution": "base64_plot_data"}
    })
    mock_service.perform_pca = AsyncMock(return_value={
        "analysis_job_id": 1,
        "pca_scores": {"PC1": [1, 2, 3], "PC2": [4, 5, 6]},
        "explained_variance": [0.6, 0.3]
    })
    return mock_service

@pytest.fixture(scope="function")
def mock_literature_service():
    """Mock literature service"""
    mock_service = AsyncMock()
    mock_service.process_abstract = AsyncMock(return_value={
        "message": "Abstract processed successfully",
        "literature_summary": {"id": 1, "title": "Test Paper", "summary": "Test summary"}
    })
    mock_service.chat_with_paper = AsyncMock(return_value={
        "session_id": 1,
        "question": "Test question",
        "response": "Test response",
        "citations": ["Reference 1"],
        "confidence_score": 0.8
    })
    return mock_service

@pytest.fixture(scope="function")
def mock_reports_service():
    """Mock reports service"""
    mock_service = AsyncMock()
    mock_service.generate_report = AsyncMock(return_value={
        "id": 1,
        "title": "Test Report",
        "format_type": "html",
        "created_at": "2024-01-01T00:00:00Z"
    })
    return mock_service

# Helper functions for tests
def create_test_user_data():
    """Create test user registration data"""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "organization": "Test Organization",
        "position": "Researcher",
        "consent_given": True
    }

def create_test_dataset_metadata():
    """Create test dataset metadata"""
    return {
        "name": "Test Dataset",
        "description": "Test gene expression dataset",
        "organism": "Homo sapiens",
        "tissue_type": "Breast tissue",
        "experiment_type": "RNA-seq"
    }

def create_test_literature_data():
    """Create test literature data"""
    return {
        "title": "Test Research Paper",
        "authors": "Smith, J., Johnson, M.",
        "journal": "Nature Biotechnology",
        "abstract": "This is a test abstract for testing purposes. It contains information about gene expression analysis and biomarker discovery in cancer research."
    }

# Async test utilities
@pytest.fixture(scope="function")
async def async_client(client):
    """Async test client wrapper"""
    return client

# Mock external dependencies
@pytest.fixture(autouse=True)
def mock_external_apis(monkeypatch):
    """Mock external API calls"""
    # Mock Redis
    mock_redis = MagicMock()
    monkeypatch.setattr("redis.Redis", lambda **kwargs: mock_redis)
    
    # Mock file operations
    mock_os = MagicMock()
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("os.makedirs", lambda path, exist_ok=True: None)
    
    return {"redis": mock_redis, "os": mock_os}