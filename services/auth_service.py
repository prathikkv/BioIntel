from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.user import User, UserSession, APIKey
from models.database import get_db
from utils.security import security_utils
from utils.logging import get_logger
from utils.config import get_settings
import secrets
import hashlib

settings = get_settings()
logger = get_logger(__name__)

class AuthService:
    """Authentication service for user management and JWT operations"""
    
    def __init__(self):
        self.db = next(get_db())
        
    @staticmethod
    async def initialize():
        """Initialize authentication service"""
        logger.info("Authentication service initialized")
    
    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Validate email
            email_validation = security_utils.validate_email(user_data["email"])
            if not email_validation["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid email: {email_validation['error']}"
                )
            
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                User.email == email_validation["normalized"]
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # Validate password strength
            password_validation = security_utils.validate_password_strength(user_data["password"])
            if not password_validation["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Password validation failed: {', '.join(password_validation['errors'])}"
                )
            
            # Hash password
            hashed_password = security_utils.hash_password(user_data["password"])
            
            # Create new user
            new_user = User(
                email=email_validation["normalized"],
                hashed_password=hashed_password,
                full_name=user_data.get("full_name"),
                organization=user_data.get("organization"),
                position=user_data.get("position"),
                research_interests=user_data.get("research_interests"),
                bio=user_data.get("bio"),
                consent_given=user_data.get("consent_given", False),
                consent_date=datetime.utcnow() if user_data.get("consent_given") else None,
                email_verification_token=secrets.token_urlsafe(32)
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            # Create access and refresh tokens
            access_token = security_utils.create_access_token(
                data={"sub": str(new_user.id), "email": new_user.email}
            )
            refresh_token = security_utils.create_refresh_token(
                data={"sub": str(new_user.id), "email": new_user.email}
            )
            
            logger.info(f"User registered successfully: {new_user.email}")
            
            return {
                "message": "User registered successfully",
                "user": new_user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during registration"
            )
    
    async def authenticate_user(self, email: str, password: str, ip_address: str = None) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        try:
            # Validate email format
            email_validation = security_utils.validate_email(email)
            if not email_validation["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email format"
                )
            
            normalized_email = email_validation["normalized"]
            
            # Check if account is locked
            if security_utils.is_account_locked(normalized_email):
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account is temporarily locked due to failed login attempts"
                )
            
            # Get user from database
            user = self.db.query(User).filter(User.email == normalized_email).first()
            
            if not user:
                security_utils.track_failed_login(normalized_email)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Verify password
            if not security_utils.verify_password(password, user.hashed_password):
                security_utils.track_failed_login(normalized_email)
                user.failed_login_attempts += 1
                self.db.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is deactivated"
                )
            
            # Clear failed login attempts
            security_utils.clear_failed_logins(normalized_email)
            user.failed_login_attempts = 0
            user.last_login = datetime.utcnow()
            self.db.commit()
            
            # Create tokens
            access_token = security_utils.create_access_token(
                data={"sub": str(user.id), "email": user.email}
            )
            refresh_token = security_utils.create_refresh_token(
                data={"sub": str(user.id), "email": user.email}
            )
            
            # Create session
            session = UserSession(
                user_id=user.id,
                session_id=security_utils.generate_session_id(),
                ip_address=ip_address,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            
            self.db.add(session)
            self.db.commit()
            
            logger.info(f"User authenticated successfully: {user.email}")
            
            return {
                "message": "Authentication successful",
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "session_id": session.session_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during authentication"
            )
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = security_utils.verify_token(refresh_token)
            
            if not payload or payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Check if token is blacklisted
            if security_utils.is_token_blacklisted(refresh_token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            # Get user
            user_id = payload.get("sub")
            user = self.db.query(User).filter(User.id == int(user_id)).first()
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create new access token
            access_token = security_utils.create_access_token(
                data={"sub": str(user.id), "email": user.email}
            )
            
            logger.info(f"Token refreshed for user: {user.email}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during token refresh"
            )
    
    async def logout_user(self, token: str, session_id: str = None) -> Dict[str, Any]:
        """Logout user by revoking token and session"""
        try:
            # Revoke token
            security_utils.revoke_token(token)
            
            # Deactivate session if provided
            if session_id:
                session = self.db.query(UserSession).filter(
                    UserSession.session_id == session_id
                ).first()
                
                if session:
                    session.is_active = False
                    self.db.commit()
            
            logger.info("User logged out successfully")
            
            return {"message": "Logout successful"}
            
        except Exception as e:
            logger.error(f"Error logging out user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during logout"
            )
    
    async def get_current_user(self, token: str) -> User:
        """Get current user from token"""
        try:
            # Verify token
            payload = security_utils.verify_token(token)
            
            if not payload or payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid access token"
                )
            
            # Check if token is blacklisted
            if security_utils.is_token_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            # Get user
            user_id = payload.get("sub")
            user = self.db.query(User).filter(User.id == int(user_id)).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is deactivated"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def reset_password_request(self, email: str) -> Dict[str, Any]:
        """Request password reset"""
        try:
            # Validate email
            email_validation = security_utils.validate_email(email)
            if not email_validation["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email format"
                )
            
            # Get user
            user = self.db.query(User).filter(
                User.email == email_validation["normalized"]
            ).first()
            
            if not user:
                # Don't reveal if user exists
                return {"message": "If the email exists, a reset link will be sent"}
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            user.password_reset_token = reset_token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            
            self.db.commit()
            
            # TODO: Send email with reset link
            logger.info(f"Password reset requested for user: {user.email}")
            
            return {"message": "If the email exists, a reset link will be sent"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error requesting password reset: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """Reset password using reset token"""
        try:
            # Validate password strength
            password_validation = security_utils.validate_password_strength(new_password)
            if not password_validation["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Password validation failed: {', '.join(password_validation['errors'])}"
                )
            
            # Find user with reset token
            user = self.db.query(User).filter(
                User.password_reset_token == token
            ).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )
            
            # Check if token is expired
            if user.password_reset_expires < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reset token has expired"
                )
            
            # Update password
            user.hashed_password = security_utils.hash_password(new_password)
            user.password_reset_token = None
            user.password_reset_expires = None
            user.failed_login_attempts = 0
            
            self.db.commit()
            
            logger.info(f"Password reset successful for user: {user.email}")
            
            return {"message": "Password reset successful"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def create_api_key(self, user_id: int, key_name: str, permissions: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create API key for user"""
        try:
            # Generate API key
            api_key = f"bai_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Create API key record
            new_api_key = APIKey(
                user_id=user_id,
                key_name=key_name,
                key_hash=key_hash,
                permissions=permissions or {},
                rate_limit=settings.RATE_LIMIT_REQUESTS
            )
            
            self.db.add(new_api_key)
            self.db.commit()
            self.db.refresh(new_api_key)
            
            logger.info(f"API key created for user {user_id}: {key_name}")
            
            return {
                "message": "API key created successfully",
                "api_key": api_key,  # Only return this once
                "key_info": new_api_key.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error creating API key: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def verify_api_key(self, api_key: str) -> User:
        """Verify API key and return user"""
        try:
            if not api_key.startswith("bai_"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key format"
                )
            
            # Hash the provided key
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Find API key record
            api_key_record = self.db.query(APIKey).filter(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            ).first()
            
            if not api_key_record:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or inactive API key"
                )
            
            # Check if API key has expired
            if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired"
                )
            
            # Get user
            user = self.db.query(User).filter(User.id == api_key_record.user_id).first()
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Update usage statistics
            api_key_record.usage_count += 1
            api_key_record.last_used = datetime.utcnow()
            self.db.commit()
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying API key: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

# Global auth service instance
auth_service = AuthService()