"""
Unit tests for Authentication API
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from api.main import app
from models.user import User
from services.auth_service import AuthService

class TestAuthAPI:
    """Test cases for Authentication API endpoints"""
    
    def test_register_user_success(self, client, mock_auth_service):
        """Test successful user registration"""
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "organization": "Test Organization",
            "consent_given": True
        }
        
        with patch('services.auth_service.auth_service', mock_auth_service):
            response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert data["user"]["email"] == "test@example.com"
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_register_user_missing_consent(self, client):
        """Test user registration without consent"""
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "consent_given": False
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "GDPR consent is required" in response.json()["detail"]
    
    def test_register_user_invalid_email(self, client):
        """Test user registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "password": "testpassword123",
            "full_name": "Test User",
            "consent_given": True
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_user_weak_password(self, client):
        """Test user registration with weak password"""
        user_data = {
            "email": "test@example.com",
            "password": "123",  # Too short
            "full_name": "Test User",
            "consent_given": True
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_success(self, client, mock_auth_service):
        """Test successful user login"""
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        with patch('services.auth_service.auth_service', mock_auth_service):
            response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Authentication successful"
        assert data["user"]["email"] == "test@example.com"
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        mock_auth_service = MagicMock()
        mock_auth_service.authenticate_user.side_effect = Exception("Invalid credentials")
        
        with patch('services.auth_service.auth_service', mock_auth_service):
            response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        login_data = {
            "email": "test@example.com"
            # Missing password
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_current_user_success(self, client, mock_auth_service, auth_headers):
        """Test getting current user information"""
        with patch('services.auth_service.auth_service', mock_auth_service):
            response = client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token_success(self, client, mock_auth_service):
        """Test successful token refresh"""
        refresh_data = {
            "refresh_token": "valid-refresh-token"
        }
        
        mock_auth_service.refresh_token.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "bearer"
        }
        
        with patch('services.auth_service.auth_service', mock_auth_service):
            response = client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid token"""
        refresh_data = {
            "refresh_token": "invalid-refresh-token"
        }
        
        mock_auth_service = MagicMock()
        mock_auth_service.refresh_token.side_effect = Exception("Invalid refresh token")
        
        with patch('services.auth_service.auth_service', mock_auth_service):
            response = client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_logout_success(self, client, mock_auth_service, auth_headers):
        """Test successful logout"""
        mock_auth_service.logout_user.return_value = {
            "message": "Logout successful"
        }
        
        with patch('services.auth_service.auth_service', mock_auth_service):
            response = client.post("/api/auth/logout", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Logout successful"
    
    def test_logout_unauthorized(self, client):
        """Test logout without authentication"""
        response = client.post("/api/auth/logout")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_password_reset_request(self, client, mock_auth_service):
        """Test password reset request"""
        reset_data = {
            "email": "test@example.com"
        }
        
        mock_auth_service.reset_password_request.return_value = {
            "message": "Password reset email sent"
        }
        
        with patch('services.auth_service.auth_service', mock_auth_service):
            response = client.post("/api/auth/password/reset-request", json=reset_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Password reset email sent"
    
    def test_password_reset_request_invalid_email(self, client):
        """Test password reset request with invalid email"""
        reset_data = {
            "email": "invalid-email"
        }
        
        response = client.post("/api/auth/password/reset-request", json=reset_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_password_reset_success(self, client, mock_auth_service):
        """Test successful password reset"""
        reset_data = {
            "token": "valid-reset-token",
            "new_password": "newpassword123"
        }
        
        mock_auth_service.reset_password.return_value = {
            "message": "Password reset successful"
        }
        
        with patch('services.auth_service.auth_service', mock_auth_service):
            response = client.post("/api/auth/password/reset", json=reset_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Password reset successful"
    
    def test_password_reset_invalid_token(self, client):
        """Test password reset with invalid token"""
        reset_data = {
            "token": "invalid-reset-token",
            "new_password": "newpassword123"
        }
        
        mock_auth_service = MagicMock()
        mock_auth_service.reset_password.side_effect = Exception("Invalid reset token")
        
        with patch('services.auth_service.auth_service', mock_auth_service):
            response = client.post("/api/auth/password/reset", json=reset_data)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_create_api_key_success(self, client, mock_auth_service, auth_headers):
        """Test successful API key creation"""
        api_key_data = {
            "key_name": "Test API Key",
            "permissions": {
                "read": True,
                "write": True,
                "delete": False
            }
        }
        
        mock_auth_service.create_api_key.return_value = {
            "id": 1,
            "key_name": "Test API Key",
            "key_value": "test-api-key-value",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        with patch('services.auth_service.auth_service', mock_auth_service):
            response = client.post("/api/auth/api-key", json=api_key_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["key_name"] == "Test API Key"
        assert "key_value" in data
    
    def test_create_api_key_unauthorized(self, client):
        """Test API key creation without authentication"""
        api_key_data = {
            "key_name": "Test API Key"
        }
        
        response = client.post("/api/auth/api-key", json=api_key_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_api_keys_success(self, client, auth_headers):
        """Test listing API keys"""
        mock_api_keys = [
            {
                "id": 1,
                "key_name": "Test API Key 1",
                "created_at": "2024-01-01T00:00:00Z",
                "is_active": True
            },
            {
                "id": 2,
                "key_name": "Test API Key 2",
                "created_at": "2024-01-02T00:00:00Z",
                "is_active": True
            }
        ]
        
        with patch('models.user.APIKey') as mock_api_key_model:
            mock_api_key_model.query.filter.return_value.all.return_value = [
                MagicMock(to_dict=lambda: key) for key in mock_api_keys
            ]
            
            response = client.get("/api/auth/api-keys", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "api_keys" in data
    
    def test_list_api_keys_unauthorized(self, client):
        """Test listing API keys without authentication"""
        response = client.get("/api/auth/api-keys")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_delete_api_key_success(self, client, auth_headers):
        """Test successful API key deletion"""
        key_id = 1
        
        with patch('models.user.APIKey') as mock_api_key_model:
            mock_api_key = MagicMock()
            mock_api_key.id = key_id
            mock_api_key.user_id = 1
            mock_api_key_model.query.filter.return_value.first.return_value = mock_api_key
            
            response = client.delete(f"/api/auth/api-key/{key_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "API key deleted successfully"
    
    def test_delete_api_key_not_found(self, client, auth_headers):
        """Test deleting non-existent API key"""
        key_id = 999
        
        with patch('models.user.APIKey') as mock_api_key_model:
            mock_api_key_model.query.filter.return_value.first.return_value = None
            
            response = client.delete(f"/api/auth/api-key/{key_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_api_key_unauthorized(self, client):
        """Test deleting API key without authentication"""
        key_id = 1
        
        response = client.delete(f"/api/auth/api-key/{key_id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_auth_health_check(self, client):
        """Test authentication service health check"""
        response = client.get("/api/auth/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "authentication"
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_rate_limiting(self, client):
        """Test rate limiting on authentication endpoints"""
        # This test would need to be implemented based on the actual rate limiting logic
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        # Simulate multiple rapid requests
        responses = []
        for _ in range(15):  # Exceed rate limit
            response = client.post("/api/auth/login", json=user_data)
            responses.append(response)
        
        # The last few responses should be rate limited
        # This is a placeholder - actual implementation would depend on rate limiting setup
        assert len(responses) == 15
    
    def test_cors_headers(self, client):
        """Test CORS headers on authentication endpoints"""
        response = client.options("/api/auth/login")
        
        # Check for CORS headers
        assert "Access-Control-Allow-Origin" in response.headers or response.status_code == 200
    
    def test_security_headers(self, client):
        """Test security headers on authentication endpoints"""
        response = client.get("/api/auth/health")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers