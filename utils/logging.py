import logging
import sys
from datetime import datetime
from typing import Any, Dict
import json
from utils.config import get_settings

# Conditional import for structlog
try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    print("⚠️  structlog not available - using basic logging")

settings = get_settings()

def setup_logging():
    """Configure structured logging for the application"""
    
    if STRUCTLOG_AVAILABLE:
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    else:
        # Fallback to basic logging
        print("Using basic logging configuration")
    
    # Configure standard logging
    logging.basicConfig(
        format=getattr(settings, 'LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        stream=sys.stdout
    )
    
    # Set up logger for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

class APILogger:
    """Custom logger for API operations"""
    
    def __init__(self, name: str):
        if STRUCTLOG_AVAILABLE:
            self.logger = structlog.get_logger(name)
        else:
            self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self.logger.debug(message, **kwargs)
    
    def log_request(self, method: str, path: str, user_id: str = None, **kwargs):
        """Log API request"""
        self.logger.info(
            "API Request",
            method=method,
            path=path,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    def log_response(self, status_code: int, response_time: float, **kwargs):
        """Log API response"""
        self.logger.info(
            "API Response",
            status_code=status_code,
            response_time=response_time,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        self.logger.error(
            "Error occurred",
            error=str(error),
            error_type=type(error).__name__,
            context=context or {},
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_security_event(self, event_type: str, user_id: str = None, ip_address: str = None, **kwargs):
        """Log security-related events"""
        self.logger.warning(
            "Security Event",
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    def log_data_processing(self, operation: str, file_name: str, record_count: int, **kwargs):
        """Log data processing operations"""
        self.logger.info(
            "Data Processing",
            operation=operation,
            file_name=file_name,
            record_count=record_count,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )

class AuditLogger:
    """Logger for audit trail and compliance"""
    
    def __init__(self):
        self.logger = structlog.get_logger("audit")
    
    def log_user_action(self, user_id: str, action: str, resource: str, **kwargs):
        """Log user actions for audit trail"""
        self.logger.info(
            "User Action",
            user_id=user_id,
            action=action,
            resource=resource,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    def log_data_access(self, user_id: str, data_type: str, operation: str, **kwargs):
        """Log data access for compliance"""
        self.logger.info(
            "Data Access",
            user_id=user_id,
            data_type=data_type,
            operation=operation,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    def log_consent_change(self, user_id: str, consent_type: str, granted: bool, **kwargs):
        """Log consent changes for GDPR compliance"""
        self.logger.info(
            "Consent Change",
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )

class SecurityLogger:
    """Logger for security events"""
    
    def __init__(self):
        self.logger = structlog.get_logger("security")
    
    def log_auth_attempt(self, username: str, success: bool, ip_address: str, **kwargs):
        """Log authentication attempts"""
        self.logger.info(
            "Authentication Attempt",
            username=username,
            success=success,
            ip_address=ip_address,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    def log_rate_limit_exceeded(self, ip_address: str, endpoint: str, **kwargs):
        """Log rate limit violations"""
        self.logger.warning(
            "Rate Limit Exceeded",
            ip_address=ip_address,
            endpoint=endpoint,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )
    
    def log_suspicious_activity(self, user_id: str, activity: str, risk_score: float, **kwargs):
        """Log suspicious activities"""
        self.logger.warning(
            "Suspicious Activity",
            user_id=user_id,
            activity=activity,
            risk_score=risk_score,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs
        )

# Global logger instances
api_logger = APILogger("api")
audit_logger = AuditLogger()
security_logger = SecurityLogger()

def get_logger(name: str) -> APILogger:
    """Get a logger instance for a specific module"""
    return APILogger(name)