"""
Configuration for BioIntel.AI Streamlit Frontend
"""

import os
from typing import Dict, Any

class Config:
    """Frontend configuration settings"""
    
    # API Settings
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    
    # UI Settings
    PAGE_TITLE = "BioIntel.AI"
    PAGE_ICON = "🧬"
    LAYOUT = "wide"
    
    # File Upload Settings
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    ALLOWED_FILE_TYPES = {
        'csv': ['csv'],
        'excel': ['xlsx', 'xls'],
        'pdf': ['pdf'],
        'text': ['txt']
    }
    
    # Chart Settings
    CHART_THEME = "streamlit"
    CHART_HEIGHT = 400
    CHART_WIDTH = 600
    
    # Session Settings
    SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    
    # Feature Flags
    ENABLE_REGISTRATION = os.getenv("ENABLE_REGISTRATION", "True").lower() == "true"
    ENABLE_CHAT = os.getenv("ENABLE_CHAT", "True").lower() == "true"
    ENABLE_REPORTS = os.getenv("ENABLE_REPORTS", "True").lower() == "true"
    ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "True").lower() == "true"
    
    # Debug Settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def get_api_headers(cls, access_token: str = None) -> Dict[str, str]:
        """Get API headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        return headers
    
    @classmethod
    def get_file_upload_headers(cls, access_token: str = None) -> Dict[str, str]:
        """Get headers for file upload"""
        headers = {}
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        return headers

# Export configuration instance
config = Config()