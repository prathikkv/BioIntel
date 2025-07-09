from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
from services.auth_service import auth_service
from models.user import User
from utils.logging import get_logger
from utils.security import security_utils

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()

# Pydantic models for request/response validation
class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    organization: Optional[str] = None
    position: Optional[str] = None
    research_interests: Optional[str] = None
    bio: Optional[str] = None
    consent_given: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "researcher@university.edu",
                "password": "SecurePass123!",
                "full_name": "Dr. Jane Smith",
                "organization": "University Research Lab",
                "position": "Principal Investigator",
                "research_interests": "Cancer genomics, biomarker discovery",
                "bio": "Computational biologist with 10+ years experience",
                "consent_given": True
            }
        }

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "researcher@university.edu",
                "password": "SecurePass123!"
            }
        }

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class APIKeyRequest(BaseModel):
    key_name: str
    permissions: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "key_name": "Analysis API Key",
                "permissions": {
                    "read": True,
                    "write": True,
                    "delete": False
                }
            }
        }

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    organization: Optional[str]
    position: Optional[str]
    research_interests: Optional[str]
    bio: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: Optional[datetime]
    last_login: Optional[datetime]
    consent_given: bool

class AuthResponse(BaseModel):
    message: str
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str
    session_id: Optional[str] = None

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        return await auth_service.get_current_user(token)
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Dependency to get current user (optional)
async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
    """Get current authenticated user (optional)"""
    try:
        if not credentials:
            return None
        token = credentials.credentials
        return await auth_service.get_current_user(token)
    except Exception:
        return None

# Rate limiting dependency
async def rate_limit_check(request: Request):
    """Check rate limit for authentication endpoints"""
    client_ip = request.client.host
    rate_limit_result = security_utils.check_rate_limit(f"auth:{client_ip}", limit=10, window=300)  # 10 requests per 5 minutes
    
    if not rate_limit_result["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(rate_limit_result["reset_time"])}
        )

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegistration, request: Request, _: None = Depends(rate_limit_check)):
    """Register a new user"""
    try:
        # Log registration attempt
        logger.info(f"User registration attempt: {user_data.email}")
        
        # Validate GDPR consent
        if not user_data.consent_given:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GDPR consent is required for registration"
            )
        
        # Call auth service
        result = await auth_service.register_user(user_data.dict())
        
        # Log successful registration
        logger.info(f"User registered successfully: {user_data.email}")
        
        return AuthResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )

@router.post("/login", response_model=AuthResponse)
async def login(user_credentials: UserLogin, request: Request, _: None = Depends(rate_limit_check)):
    """Authenticate user and return tokens"""
    try:
        # Log login attempt
        logger.info(f"User login attempt: {user_credentials.email}")
        
        # Get client IP
        client_ip = request.client.host
        
        # Call auth service
        result = await auth_service.authenticate_user(
            user_credentials.email, 
            user_credentials.password,
            client_ip
        )
        
        # Log successful login
        logger.info(f"User logged in successfully: {user_credentials.email}")
        
        return AuthResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/refresh")
async def refresh_token(refresh_request: RefreshTokenRequest, _: None = Depends(rate_limit_check)):
    """Refresh access token"""
    try:
        result = await auth_service.refresh_token(refresh_request.refresh_token)
        
        logger.info("Token refreshed successfully")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user"""
    try:
        token = credentials.credentials
        
        # Extract session ID from token if available
        payload = security_utils.verify_token(token)
        session_id = payload.get("session_id") if payload else None
        
        result = await auth_service.logout_user(token, session_id)
        
        logger.info("User logged out successfully")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(**current_user.to_dict())

@router.post("/password/reset-request")
async def request_password_reset(reset_request: PasswordResetRequest, _: None = Depends(rate_limit_check)):
    """Request password reset"""
    try:
        result = await auth_service.reset_password_request(reset_request.email)
        
        logger.info(f"Password reset requested for: {reset_request.email}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/password/reset")
async def reset_password(reset_data: PasswordReset, _: None = Depends(rate_limit_check)):
    """Reset password using reset token"""
    try:
        result = await auth_service.reset_password(reset_data.token, reset_data.new_password)
        
        logger.info("Password reset successful")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/api-key")
async def create_api_key(
    api_key_request: APIKeyRequest, 
    current_user: User = Depends(get_current_user)
):
    """Create API key for user"""
    try:
        result = await auth_service.create_api_key(
            current_user.id,
            api_key_request.key_name,
            api_key_request.permissions
        )
        
        logger.info(f"API key created for user {current_user.id}: {api_key_request.key_name}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/api-keys")
async def list_api_keys(current_user: User = Depends(get_current_user)):
    """List user's API keys"""
    try:
        # Get user's API keys from database
        from models.database import get_db
        from models.user import APIKey
        
        db = next(get_db())
        api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
        
        return {
            "api_keys": [key.to_dict() for key in api_keys]
        }
        
    except Exception as e:
        logger.error(f"API key listing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/api-key/{key_id}")
async def delete_api_key(key_id: int, current_user: User = Depends(get_current_user)):
    """Delete API key"""
    try:
        from models.database import get_db
        from models.user import APIKey
        
        db = next(get_db())
        api_key = db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        api_key.is_active = False
        db.commit()
        
        logger.info(f"API key deleted for user {current_user.id}: {key_id}")
        
        return {"message": "API key deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key deletion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/health")
async def auth_health_check():
    """Health check for authentication service"""
    return {
        "service": "authentication",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }