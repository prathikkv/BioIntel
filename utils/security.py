from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import hmac
import secrets
import re
import json
import base64
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from utils.config import get_settings
from utils.logging import get_logger

# Conditional imports for heavy dependencies
try:
    from jose import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("⚠️  python-jose not available - using lightweight JWT implementation")

try:
    from passlib.context import CryptContext
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False
    print("⚠️  passlib not available - using built-in password hashing")

try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False
    print("⚠️  cryptography not available - using basic encryption")

try:
    from email_validator import validate_email, EmailNotValidError
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False
    print("⚠️  email-validator not available - using basic email validation")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  redis not available - using in-memory caching")

settings = get_settings()
logger = get_logger(__name__)

class SecurityUtils:
    """Security utilities for authentication, encryption, and validation"""
    
    def __init__(self):
        # Initialize password context
        if PASSLIB_AVAILABLE:
            self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        else:
            self.pwd_context = None
        
        # Initialize Redis client and memory cache
        self._memory_cache = {}  # Always initialize memory cache
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
            except Exception:
                self.redis_client = None
        else:
            self.redis_client = None
        
        # Initialize encryption
        if FERNET_AVAILABLE:
            self.encryption_key = self._get_or_create_encryption_key()
            self.cipher_suite = Fernet(self.encryption_key)
        else:
            self.cipher_suite = None
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key"""
        if not FERNET_AVAILABLE:
            return b""
        try:
            # Try to get existing key from environment or generate new one
            key = settings.SECRET_KEY.encode()[:32]  # Use first 32 bytes
            return Fernet.generate_key()  # Generate a proper Fernet key
        except Exception:
            return Fernet.generate_key()
    
    # Password utilities
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt or fallback"""
        if PASSLIB_AVAILABLE and self.pwd_context:
            return self.pwd_context.hash(password)
        else:
            # Fallback to basic hashing with salt
            salt = secrets.token_hex(16)
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        if PASSLIB_AVAILABLE and self.pwd_context:
            return self.pwd_context.verify(plain_password, hashed_password)
        else:
            # Fallback verification
            try:
                salt, stored_hash = hashed_password.split(':')
                password_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000)
                return password_hash.hex() == stored_hash
            except Exception:
                return False
    
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
        
        if JWT_AVAILABLE:
            return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        else:
            # Lightweight JWT-like implementation
            return self._create_simple_token(to_encode)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        if JWT_AVAILABLE:
            return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        else:
            # Lightweight JWT-like implementation
            return self._create_simple_token(to_encode)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            if JWT_AVAILABLE:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                return payload
            else:
                # Lightweight token verification
                return self._verify_simple_token(token)
        except Exception as e:
            logger.warning(f"Token verification failed: {str(e)}")
            return None
    
    def revoke_token(self, token: str):
        """Revoke a token by adding it to blacklist"""
        if not self.redis_client:
            # Use memory cache
            self._memory_cache[f"blacklist:{token}"] = "revoked"
            return
            
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
        except Exception:
            # Fallback to memory cache
            self._memory_cache[f"blacklist:{token}"] = "revoked"
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        if not self.redis_client:
            # Use memory cache
            return f"blacklist:{token}" in self._memory_cache
            
        try:
            return bool(self.redis_client.get(f"blacklist:{token}"))
        except Exception:
            # Fallback to memory cache
            return f"blacklist:{token}" in self._memory_cache
    
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
        
        # If Redis is not available, always allow (for development)
        if not self.redis_client:
            return {
                "allowed": True,
                "remaining": limit - 1,
                "reset_time": datetime.utcnow() + timedelta(seconds=window)
            }
        
        try:
            key = f"rate_limit:{identifier}"
            current = self.redis_client.get(key)
        except Exception:
            # If Redis connection fails, allow request
            return {
                "allowed": True,
                "remaining": limit - 1,
                "reset_time": datetime.utcnow() + timedelta(seconds=window)
            }
        
        try:
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
        except Exception:
            # If any Redis operation fails, allow the request
            return {
                "allowed": True,
                "remaining": limit - 1,
                "reset_time": datetime.utcnow() + timedelta(seconds=window)
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
        if not self.redis_client:
            # If Redis not available, use in-memory cache
            key = f"failed_login:{identifier}"
            current = self._memory_cache.get(key, 0)
            self._memory_cache[key] = current + 1
            return
            
        try:
            key = f"failed_login:{identifier}"
            current = self.redis_client.get(key)
            
            if current is None:
                self.redis_client.setex(key, 3600, 1)  # 1 hour window
            else:
                self.redis_client.incr(key)
        except Exception:
            # Fallback to memory cache
            key = f"failed_login:{identifier}"
            current = self._memory_cache.get(key, 0)
            self._memory_cache[key] = current + 1
    
    def is_account_locked(self, identifier: str) -> bool:
        """Check if account is locked due to failed attempts"""
        key = f"failed_login:{identifier}"
        
        if not self.redis_client:
            # Use memory cache
            current = self._memory_cache.get(key, 0)
            return current >= 5  # Lock after 5 failed attempts
            
        try:
            current = self.redis_client.get(key)
            
            if current is None:
                return False
            
            return int(current) >= 5  # Lock after 5 failed attempts
        except Exception:
            # Fallback to memory cache
            current = self._memory_cache.get(key, 0)
            return current >= 5
    
    def unlock_account(self, identifier: str):
        """Unlock account"""
        key = f"failed_login:{identifier}"
        
        if not self.redis_client:
            # Use memory cache
            self._memory_cache.pop(key, None)
            return
            
        try:
            self.redis_client.delete(key)
        except Exception:
            # Fallback to memory cache
            self._memory_cache.pop(key, None)
    
    def clear_failed_logins(self, identifier: str):
        """Clear failed login attempts"""
        key = f"failed_login:{identifier}"
        
        if not self.redis_client:
            # Use memory cache
            self._memory_cache.pop(key, None)
            return
            
        try:
            self.redis_client.delete(key)
        except Exception:
            # Fallback to memory cache
            self._memory_cache.pop(key, None)
    
    # Lightweight JWT-like implementation for when jose is not available
    def _create_simple_token(self, data: Dict[str, Any]) -> str:
        """Create a simple signed token without external dependencies"""
        # Convert datetime objects to timestamps
        payload = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                payload[key] = value.timestamp()
            else:
                payload[key] = value
        
        # Create token: base64(payload).signature
        payload_json = json.dumps(payload, sort_keys=True)
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip('=')
        
        # Create signature using HMAC
        signature = hmac.new(
            settings.JWT_SECRET_KEY.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()[:16]  # Truncate for shorter tokens
        
        return f"{payload_b64}.{signature}"
    
    def _verify_simple_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a simple signed token"""
        try:
            payload_b64, signature = token.split('.')
            
            # Verify signature
            expected_signature = hmac.new(
                settings.JWT_SECRET_KEY.encode(),
                payload_b64.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            # Decode payload
            # Add padding if needed
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64).decode()
            payload = json.loads(payload_json)
            
            # Convert timestamps back to datetime objects
            if 'exp' in payload:
                exp_timestamp = payload['exp']
                if exp_timestamp < datetime.utcnow().timestamp():
                    return None  # Token expired
            
            return payload
            
        except Exception:
            return None

# Global security utils instance
security_utils = SecurityUtils()