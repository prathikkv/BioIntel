from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import hmac
import secrets
import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from email_validator import validate_email, EmailNotValidError
import re
import redis
from utils.config import get_settings
from utils.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

class SecurityUtils:
    """Security utilities for authentication, encryption, and validation"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.redis_client = redis.from_url(settings.REDIS_URL)
        
        # Initialize encryption
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key"""
        try:
            # Try to get existing key from environment or generate new one
            key = settings.SECRET_KEY.encode()[:32]  # Use first 32 bytes
            return Fernet.generate_key()  # Generate a proper Fernet key
        except Exception:
            return Fernet.generate_key()
    
    # Password utilities
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "strength": self._calculate_password_strength(password)
        }
    
    def _calculate_password_strength(self, password: str) -> str:
        """Calculate password strength score"""
        score = 0
        
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if re.search(r"[A-Z]", password):
            score += 1
        if re.search(r"[a-z]", password):
            score += 1
        if re.search(r"\d", password):
            score += 1
        if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            score += 1
        
        if score <= 2:
            return "weak"
        elif score <= 4:
            return "medium"
        else:
            return "strong"
    
    # JWT utilities
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.JWTError:
            logger.warning("Invalid token")
            return None
    
    def revoke_token(self, token: str):
        """Revoke a token by adding it to blacklist"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            exp = payload.get("exp")
            
            if exp:
                # Add token to blacklist with expiration
                self.redis_client.setex(
                    f"blacklist:{token}",
                    int(exp - datetime.utcnow().timestamp()),
                    "revoked"
                )
        except jwt.JWTError:
            pass
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        return bool(self.redis_client.get(f"blacklist:{token}"))
    
    # Data encryption utilities
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def hash_data(self, data: str) -> str:
        """Create SHA-256 hash of data"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def create_hmac(self, data: str, secret: str = None) -> str:
        """Create HMAC signature"""
        secret = secret or settings.SECRET_KEY
        return hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
    
    def verify_hmac(self, data: str, signature: str, secret: str = None) -> bool:
        """Verify HMAC signature"""
        secret = secret or settings.SECRET_KEY
        expected_signature = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    
    # Input validation utilities
    def validate_email(self, email: str) -> Dict[str, Any]:
        """Validate email address"""
        try:
            valid = validate_email(email)
            return {
                "is_valid": True,
                "email": valid.email,
                "normalized": valid.email.lower()
            }
        except EmailNotValidError as e:
            return {
                "is_valid": False,
                "error": str(e)
            }
    
    def sanitize_input(self, input_string: str) -> str:
        """Sanitize user input to prevent XSS"""
        # Remove or escape potentially dangerous characters
        dangerous_chars = ["<", ">", "&", "\"", "'", "/"]
        sanitized = input_string
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        return sanitized.strip()
    
    def validate_file_type(self, filename: str) -> bool:
        """Validate file type against allowed types"""
        if not filename:
            return False
        
        extension = filename.split(".")[-1].lower()
        return extension in settings.ALLOWED_FILE_TYPES
    
    def validate_file_size(self, file_size: int) -> bool:
        """Validate file size"""
        return file_size <= settings.MAX_FILE_SIZE
    
    # Rate limiting utilities
    def check_rate_limit(self, identifier: str, limit: int = None, window: int = None) -> Dict[str, Any]:
        """Check rate limit for identifier (IP, user, etc.)"""
        limit = limit or settings.RATE_LIMIT_REQUESTS
        window = window or settings.RATE_LIMIT_WINDOW
        
        key = f"rate_limit:{identifier}"
        current = self.redis_client.get(key)
        
        if current is None:
            # First request
            self.redis_client.setex(key, window, 1)
            return {
                "allowed": True,
                "remaining": limit - 1,
                "reset_time": datetime.utcnow() + timedelta(seconds=window)
            }
        
        current_count = int(current)
        
        if current_count >= limit:
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": datetime.utcnow() + timedelta(seconds=self.redis_client.ttl(key))
            }
        
        # Increment counter
        self.redis_client.incr(key)
        
        return {
            "allowed": True,
            "remaining": limit - current_count - 1,
            "reset_time": datetime.utcnow() + timedelta(seconds=self.redis_client.ttl(key))
        }
    
    # Session utilities
    def generate_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_hex(32)
    
    def verify_csrf_token(self, token: str, session_token: str) -> bool:
        """Verify CSRF token"""
        return hmac.compare_digest(token, session_token)
    
    # Account security utilities
    def track_failed_login(self, identifier: str):
        """Track failed login attempts"""
        key = f"failed_login:{identifier}"
        current = self.redis_client.get(key)
        
        if current is None:
            self.redis_client.setex(key, 3600, 1)  # 1 hour window
        else:
            self.redis_client.incr(key)
    
    def is_account_locked(self, identifier: str) -> bool:
        """Check if account is locked due to failed attempts"""
        key = f"failed_login:{identifier}"
        current = self.redis_client.get(key)
        
        if current is None:
            return False
        
        return int(current) >= 5  # Lock after 5 failed attempts
    
    def unlock_account(self, identifier: str):
        """Unlock account"""
        key = f"failed_login:{identifier}"
        self.redis_client.delete(key)
    
    def clear_failed_logins(self, identifier: str):
        """Clear failed login attempts"""
        key = f"failed_login:{identifier}"
        self.redis_client.delete(key)

# Global security utils instance
security_utils = SecurityUtils()