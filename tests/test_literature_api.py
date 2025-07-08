"""
Unit tests for Literature API
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from api.main import app
from models.literature import LiteratureSummary, ChatSession, ChatMessage

class TestLiteratureAPI:
    """Test cases for Literature API endpoints"""
    
    def test_process_abstract_success(self, client, mock_literature_service, auth_headers):
        """Test successful abstract processing"""
        abstract_data = {
            "abstract": "This is a test abstract about cancer research and biomarker discovery. We identified several genes associated with breast cancer progression.",
            "title": "Test Research Paper",
            "authors": "Smith, J., Johnson, M.",
            "journal": "Nature Biotechnology",
            "doi": "10.1038/nbt.test.2024"
        }
        
        with patch('services.literature_service.literature_service', mock_literature_service):
            response = client.post("/api/literature/abstract", json=abstract_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Abstract processed successfully"
        assert "literature_summary" in data
    
    def test_process_abstract_missing_abstract(self, client, auth_headers):
        """Test abstract processing without abstract text"""
        abstract_data = {
            "title": "Test Research Paper",
            "authors": "Smith, J., Johnson, M."
        }
        
        response = client.post("/api/literature/abstract", json=abstract_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_process_abstract_too_short(self, client, auth_headers):
        """Test abstract processing with too short abstract"""
        abstract_data = {
            "abstract": "Too short"  # Less than 100 characters
        }
        
        response = client.post("/api/literature/abstract", json=abstract_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_process_abstract_unauthorized(self, client):
        """Test abstract processing without authentication"""
        abstract_data = {
            "abstract": "This is a test abstract about cancer research and biomarker discovery. We identified several genes associated with breast cancer progression."
        }
        
        response = client.post("/api/literature/abstract", json=abstract_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_process_pdf_success(self, client, mock_literature_service, auth_headers, sample_pdf_data):
        """Test successful PDF processing"""
        files = {"file": ("test_paper.pdf", sample_pdf_data, "application/pdf")}
        metadata = {
            "title": "Test Research Paper",
            "authors": "Smith, J., Johnson, M.",
            "journal": "Nature Biotechnology"
        }
        data = {"metadata": json.dumps(metadata)}
        
        with patch('services.literature_service.literature_service', mock_literature_service):
            response = client.post("/api/literature/pdf", files=files, data=data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["message"] == "Abstract processed successfully"
        assert "literature_summary" in result
    
    def test_process_pdf_invalid_file_type(self, client, auth_headers):
        """Test PDF processing with invalid file type"""
        files = {"file": ("test_file.txt", b"Not a PDF", "text/plain")}
        metadata = {"title": "Test Paper"}
        data = {"metadata": json.dumps(metadata)}
        
        response = client.post("/api/literature/pdf", files=files, data=data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Only PDF files are supported" in response.json()["detail"]
    
    def test_process_pdf_invalid_metadata(self, client, auth_headers, sample_pdf_data):
        """Test PDF processing with invalid metadata"""
        files = {"file": ("test_paper.pdf", sample_pdf_data, "application/pdf")}
        data = {"metadata": "invalid-json"}
        
        response = client.post("/api/literature/pdf", files=files, data=data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid metadata format" in response.json()["detail"]
    
    def test_process_pdf_empty_file(self, client, auth_headers):
        """Test PDF processing with empty file"""
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        metadata = {"title": "Test Paper"}
        data = {"metadata": json.dumps(metadata)}
        
        response = client.post("/api/literature/pdf", files=files, data=data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Empty PDF file" in response.json()["detail"]
    
    def test_process_pdf_unauthorized(self, client, sample_pdf_data):
        """Test PDF processing without authentication"""
        files = {"file": ("test_paper.pdf", sample_pdf_data, "application/pdf")}
        metadata = {"title": "Test Paper"}
        data = {"metadata": json.dumps(metadata)}
        
        response = client.post("/api/literature/pdf", files=files, data=data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_literature_summaries_success(self, client, mock_literature_service, auth_headers):
        """Test successful literature summaries listing"""
        mock_summaries = [
            {
                "id": 1,
                "title": "Test Paper 1",
                "authors": "Smith, J.",
                "processing_status": "completed",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "title": "Test Paper 2",
                "authors": "Johnson, M.",
                "processing_status": "completed",
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
        
        mock_literature_service.list_literature_summaries.return_value = {
            "summaries": mock_summaries,
            "total": 2,
            "skip": 0,
            "limit": 20
        }
        
        with patch('services.literature_service.literature_service', mock_literature_service):
            response = client.get("/api/literature/summaries", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "summaries" in data
        assert len(data["summaries"]) == 2
        assert data["total"] == 2
    
    def test_list_literature_summaries_with_pagination(self, client, mock_literature_service, auth_headers):
        """Test literature summaries listing with pagination"""
        mock_literature_service.list_literature_summaries.return_value = {
            "summaries": [],
            "total": 0,
            "skip": 10,
            "limit": 5
        }
        
        with patch('services.literature_service.literature_service', mock_literature_service):
            response = client.get("/api/literature/summaries?skip=10&limit=5", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["skip"] == 10
        assert data["limit"] == 5
    
    def test_list_literature_summaries_unauthorized(self, client):
        """Test literature summaries listing without authentication"""
        response = client.get("/api/literature/summaries")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_literature_summary_success(self, client, auth_headers, test_literature_summary):
        """Test successful literature summary retrieval"""
        summary_id = test_literature_summary.id
        
        with patch('models.literature.LiteratureSummary') as mock_summary_model:
            mock_summary_model.query.filter.return_value.first.return_value = test_literature_summary
            
            response = client.get(f"/api/literature/summaries/{summary_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == summary_id
        assert data["title"] == test_literature_summary.title
    
    def test_get_literature_summary_not_found(self, client, auth_headers):
        """Test literature summary retrieval with non-existent ID"""
        summary_id = 999
        
        with patch('models.literature.LiteratureSummary') as mock_summary_model:
            mock_summary_model.query.filter.return_value.first.return_value = None
            
            response = client.get(f"/api/literature/summaries/{summary_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_literature_summary_unauthorized(self, client):
        """Test literature summary retrieval without authentication"""
        summary_id = 1
        
        response = client.get(f"/api/literature/summaries/{summary_id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_delete_literature_summary_success(self, client, auth_headers, test_literature_summary):
        """Test successful literature summary deletion"""
        summary_id = test_literature_summary.id
        
        with patch('models.literature.LiteratureSummary') as mock_summary_model:
            mock_summary_model.query.filter.return_value.first.return_value = test_literature_summary
            
            with patch('models.literature.ChatSession') as mock_session_model:
                mock_session_model.query.filter.return_value.all.return_value = []
                
                response = client.delete(f"/api/literature/summaries/{summary_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Literature summary deleted successfully"
    
    def test_delete_literature_summary_not_found(self, client, auth_headers):
        """Test literature summary deletion with non-existent ID"""
        summary_id = 999
        
        with patch('models.literature.LiteratureSummary') as mock_summary_model:
            mock_summary_model.query.filter.return_value.first.return_value = None
            
            response = client.delete(f"/api/literature/summaries/{summary_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_literature_summary_unauthorized(self, client):
        """Test literature summary deletion without authentication"""
        summary_id = 1
        
        response = client.delete(f"/api/literature/summaries/{summary_id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_chat_with_paper_success(self, client, mock_literature_service, auth_headers):
        """Test successful chat with paper"""
        literature_id = 1
        chat_request = {
            "question": "What biomarkers were identified in this study?"
        }
        
        with patch('services.literature_service.literature_service', mock_literature_service):
            response = client.post(f"/api/literature/chat/{literature_id}", json=chat_request, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["session_id"] == 1
        assert data["question"] == "Test question"
        assert data["response"] == "Test response"
        assert "citations" in data
        assert "confidence_score" in data
    
    def test_chat_with_paper_missing_question(self, client, auth_headers):
        """Test chat with paper without question"""
        literature_id = 1
        chat_request = {}
        
        response = client.post(f"/api/literature/chat/{literature_id}", json=chat_request, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_with_paper_too_short_question(self, client, auth_headers):
        """Test chat with paper with too short question"""
        literature_id = 1
        chat_request = {
            "question": "Hi"  # Less than 5 characters
        }
        
        response = client.post(f"/api/literature/chat/{literature_id}", json=chat_request, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_with_paper_unauthorized(self, client):
        """Test chat with paper without authentication"""
        literature_id = 1
        chat_request = {
            "question": "What biomarkers were identified?"
        }
        
        response = client.post(f"/api/literature/chat/{literature_id}", json=chat_request)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_chat_sessions_success(self, client, mock_literature_service, auth_headers):
        """Test successful chat sessions retrieval"""
        mock_sessions = [
            {
                "id": 1,
                "session_name": "Chat with Paper 1",
                "total_messages": 4,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "session_name": "Chat with Paper 2",
                "total_messages": 2,
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
        
        mock_literature_service.get_chat_sessions.return_value = {
            "sessions": mock_sessions
        }
        
        with patch('services.literature_service.literature_service', mock_literature_service):
            response = client.get("/api/literature/chat/sessions", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) == 2
    
    def test_get_chat_sessions_with_filter(self, client, mock_literature_service, auth_headers):
        """Test chat sessions retrieval with literature filter"""
        mock_literature_service.get_chat_sessions.return_value = {
            "sessions": []
        }
        
        with patch('services.literature_service.literature_service', mock_literature_service):
            response = client.get("/api/literature/chat/sessions?literature_id=1", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        mock_literature_service.get_chat_sessions.assert_called_once()
    
    def test_get_chat_sessions_unauthorized(self, client):
        """Test chat sessions retrieval without authentication"""
        response = client.get("/api/literature/chat/sessions")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_chat_messages_success(self, client, mock_literature_service, auth_headers):
        """Test successful chat messages retrieval"""
        session_id = 1
        
        mock_messages = [
            {
                "id": 1,
                "message_type": "user",
                "content": "What are the main findings?",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "message_type": "assistant",
                "content": "The main findings include...",
                "created_at": "2024-01-01T00:01:00Z"
            }
        ]
        
        mock_literature_service.get_chat_messages.return_value = {
            "session": {"id": session_id, "session_name": "Test Session"},
            "messages": mock_messages
        }
        
        with patch('services.literature_service.literature_service', mock_literature_service):
            response = client.get(f"/api/literature/chat/sessions/{session_id}/messages", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session" in data
        assert "messages" in data
        assert len(data["messages"]) == 2
    
    def test_get_chat_messages_unauthorized(self, client):
        """Test chat messages retrieval without authentication"""
        session_id = 1
        
        response = client.get(f"/api/literature/chat/sessions/{session_id}/messages")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_delete_chat_session_success(self, client, auth_headers):
        """Test successful chat session deletion"""
        session_id = 1
        
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.user_id = 1
        
        with patch('models.literature.ChatSession') as mock_session_model:
            mock_session_model.query.filter.return_value.first.return_value = mock_session
            
            with patch('models.literature.ChatMessage') as mock_message_model:
                mock_message_model.query.filter.return_value.delete.return_value = None
                
                response = client.delete(f"/api/literature/chat/sessions/{session_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Chat session deleted successfully"
    
    def test_delete_chat_session_not_found(self, client, auth_headers):
        """Test chat session deletion with non-existent ID"""
        session_id = 999
        
        with patch('models.literature.ChatSession') as mock_session_model:
            mock_session_model.query.filter.return_value.first.return_value = None
            
            response = client.delete(f"/api/literature/chat/sessions/{session_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_chat_session_unauthorized(self, client):
        """Test chat session deletion without authentication"""
        session_id = 1
        
        response = client.delete(f"/api/literature/chat/sessions/{session_id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_search_literature_success(self, client, auth_headers):
        """Test successful literature search"""
        search_query = "cancer biomarkers"
        
        mock_results = [
            {
                "id": 1,
                "title": "Cancer Biomarkers in Breast Cancer",
                "authors": "Smith, J.",
                "summary": "This study identifies novel biomarkers...",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        with patch('models.literature.LiteratureSummary') as mock_summary_model:
            mock_query = MagicMock()
            mock_query.offset.return_value.limit.return_value.all.return_value = [
                MagicMock(to_dict=lambda: result) for result in mock_results
            ]
            mock_query.count.return_value = 1
            mock_summary_model.query.filter.return_value = mock_query
            
            response = client.get(f"/api/literature/search?query={search_query}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert data["total"] == 1
        assert data["query"] == search_query
    
    def test_search_literature_with_type_filter(self, client, auth_headers):
        """Test literature search with type filter"""
        search_query = "cancer"
        literature_type = "abstract"
        
        with patch('models.literature.LiteratureSummary') as mock_summary_model:
            mock_query = MagicMock()
            mock_query.offset.return_value.limit.return_value.all.return_value = []
            mock_query.count.return_value = 0
            mock_summary_model.query.filter.return_value = mock_query
            
            response = client.get(f"/api/literature/search?query={search_query}&literature_type={literature_type}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert data["total"] == 0
    
    def test_search_literature_unauthorized(self, client):
        """Test literature search without authentication"""
        search_query = "cancer"
        
        response = client.get(f"/api/literature/search?query={search_query}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_literature_stats_success(self, client, auth_headers):
        """Test successful literature statistics retrieval"""
        with patch('models.literature.LiteratureSummary') as mock_summary_model:
            mock_summary_model.query.filter.return_value.count.return_value = 5
            
            with patch('models.literature.ChatSession') as mock_session_model:
                mock_session_model.query.filter.return_value.count.return_value = 3
                
                with patch('models.literature.ChatMessage') as mock_message_model:
                    mock_message_model.query.join.return_value.filter.return_value.count.return_value = 12
                    
                    mock_summary_model.query.filter.return_value.group_by.return_value.all.return_value = [
                        ("completed", 4),
                        ("processing", 1)
                    ]
                    
                    response = client.get("/api/literature/stats", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_summaries"] == 5
        assert data["total_chat_sessions"] == 3
        assert data["total_chat_messages"] == 12
        assert "status_breakdown" in data
        assert "source_breakdown" in data
    
    def test_get_literature_stats_unauthorized(self, client):
        """Test literature statistics retrieval without authentication"""
        response = client.get("/api/literature/stats")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_literature_health_check(self, client):
        """Test literature service health check"""
        response = client.get("/api/literature/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "literature"
        assert data["status"] == "healthy"
        assert "timestamp" in data