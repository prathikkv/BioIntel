"""
Utility functions for BioIntel.AI Streamlit Frontend
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import base64
import io
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from config import config

def make_api_request(endpoint: str, method: str = "GET", data: Any = None, 
                    files: Any = None, timeout: int = None) -> Dict[str, Any]:
    """
    Make API request with authentication and error handling
    
    Args:
        endpoint: API endpoint (e.g., "/auth/login")
        method: HTTP method (GET, POST, DELETE, etc.)
        data: Request data (JSON or form data)
        files: Files to upload
        timeout: Request timeout in seconds
        
    Returns:
        Dict with success status and data/error
    """
    url = f"{config.API_BASE_URL}{endpoint}"
    timeout = timeout or config.API_TIMEOUT
    
    # Prepare headers
    if files:
        headers = config.get_file_upload_headers(st.session_state.get('access_token'))
    else:
        headers = config.get_api_headers(st.session_state.get('access_token'))
    
    try:
        # Make request based on method
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=timeout)
        else:
            return {"success": False, "error": f"Unsupported HTTP method: {method}"}
        
        # Handle response
        if response.status_code in [200, 201]:
            try:
                return {"success": True, "data": response.json()}
            except json.JSONDecodeError:
                return {"success": True, "data": {"message": "Success"}}
        else:
            try:
                error_data = response.json()
                error_message = error_data.get("detail", f"HTTP {response.status_code}")
            except json.JSONDecodeError:
                error_message = f"HTTP {response.status_code}: {response.text}"
            
            return {"success": False, "error": error_message}
    
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to API. Please check if the backend is running."}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out. Please try again."}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Request error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def validate_file_upload(uploaded_file, allowed_types: List[str], max_size_mb: int = None) -> Dict[str, Any]:
    """
    Validate uploaded file
    
    Args:
        uploaded_file: Streamlit uploaded file object
        allowed_types: List of allowed file extensions
        max_size_mb: Maximum file size in MB
        
    Returns:
        Dict with validation result
    """
    if not uploaded_file:
        return {"valid": False, "error": "No file uploaded"}
    
    # Check file extension
    file_ext = uploaded_file.name.split('.')[-1].lower()
    if file_ext not in allowed_types:
        return {"valid": False, "error": f"File type .{file_ext} not allowed. Allowed types: {', '.join(allowed_types)}"}
    
    # Check file size
    max_size_mb = max_size_mb or config.MAX_FILE_SIZE_MB
    if uploaded_file.size > max_size_mb * 1024 * 1024:
        return {"valid": False, "error": f"File size ({uploaded_file.size / 1024 / 1024:.1f} MB) exceeds maximum allowed size ({max_size_mb} MB)"}
    
    return {"valid": True}

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_datetime(datetime_str: str) -> str:
    """Format datetime string for display"""
    if not datetime_str:
        return "N/A"
    
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return datetime_str

def create_download_link(data: Any, filename: str, mime_type: str = "application/octet-stream") -> str:
    """
    Create download link for data
    
    Args:
        data: Data to download (string, bytes, or pandas DataFrame)
        filename: Name of the file
        mime_type: MIME type of the file
        
    Returns:
        HTML download link
    """
    if isinstance(data, pd.DataFrame):
        data = data.to_csv(index=False)
        mime_type = "text/csv"
    elif isinstance(data, str):
        data = data.encode('utf-8')
    
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

def show_success_message(message: str):
    """Show success message with custom styling"""
    st.markdown(
        f'<div class="success-message">{message}</div>',
        unsafe_allow_html=True
    )

def show_error_message(message: str):
    """Show error message with custom styling"""
    st.markdown(
        f'<div class="error-message">{message}</div>',
        unsafe_allow_html=True
    )

def show_info_message(message: str):
    """Show info message with custom styling"""
    st.markdown(
        f'<div class="info-message">{message}</div>',
        unsafe_allow_html=True
    )

def create_metric_card(title: str, value: str, description: str = "", color: str = "#007bff") -> str:
    """
    Create HTML for a metric card
    
    Args:
        title: Card title
        value: Main value to display
        description: Additional description
        color: Card color
        
    Returns:
        HTML string for the metric card
    """
    return f"""
    <div class="metric-card" style="border-left-color: {color};">
        <h3 style="color: {color};">{title}</h3>
        <h2>{value}</h2>
        {f"<p>{description}</p>" if description else ""}
    </div>
    """

def create_feature_box(title: str, description: str, icon: str = "🔬") -> str:
    """
    Create HTML for a feature box
    
    Args:
        title: Feature title
        description: Feature description
        icon: Feature icon
        
    Returns:
        HTML string for the feature box
    """
    return f"""
    <div class="feature-box">
        <h4>{icon} {title}</h4>
        <p>{description}</p>
    </div>
    """

def create_plotly_chart(data: pd.DataFrame, chart_type: str, **kwargs) -> go.Figure:
    """
    Create Plotly chart based on data and type
    
    Args:
        data: DataFrame with data
        chart_type: Type of chart (scatter, bar, line, etc.)
        **kwargs: Additional chart parameters
        
    Returns:
        Plotly figure
    """
    if chart_type == "scatter":
        return px.scatter(data, **kwargs)
    elif chart_type == "bar":
        return px.bar(data, **kwargs)
    elif chart_type == "line":
        return px.line(data, **kwargs)
    elif chart_type == "histogram":
        return px.histogram(data, **kwargs)
    elif chart_type == "box":
        return px.box(data, **kwargs)
    else:
        return px.scatter(data, **kwargs)

def paginate_data(data: List[Any], page_size: int = 10, page_number: int = 1) -> Dict[str, Any]:
    """
    Paginate data for display
    
    Args:
        data: List of data items
        page_size: Number of items per page
        page_number: Current page number (1-based)
        
    Returns:
        Dict with paginated data and pagination info
    """
    total_items = len(data)
    total_pages = (total_items + page_size - 1) // page_size
    
    start_idx = (page_number - 1) * page_size
    end_idx = start_idx + page_size
    
    page_data = data[start_idx:end_idx]
    
    return {
        "data": page_data,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page_number,
        "page_size": page_size,
        "has_next": page_number < total_pages,
        "has_previous": page_number > 1
    }

def check_authentication() -> bool:
    """
    Check if user is authenticated
    
    Returns:
        True if authenticated, False otherwise
    """
    return st.session_state.get('authenticated', False) and st.session_state.get('access_token')

def logout_user():
    """Logout user by clearing session state"""
    keys_to_clear = [
        'authenticated', 'access_token', 'user_info', 'datasets', 
        'literature_summaries', 'analysis_jobs', 'reports'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def refresh_user_data():
    """Refresh user data from API"""
    if not check_authentication():
        return
    
    # Refresh datasets
    datasets_result = make_api_request("/bio/datasets")
    if datasets_result["success"]:
        st.session_state.datasets = datasets_result["data"]["datasets"]
    
    # Refresh literature summaries
    literature_result = make_api_request("/literature/summaries")
    if literature_result["success"]:
        st.session_state.literature_summaries = literature_result["data"]["summaries"]
    
    # Refresh analysis jobs
    jobs_result = make_api_request("/bio/analysis-jobs")
    if jobs_result["success"]:
        st.session_state.analysis_jobs = jobs_result["data"]["analysis_jobs"]

def get_user_stats() -> Dict[str, int]:
    """
    Get user statistics
    
    Returns:
        Dict with user statistics
    """
    if not check_authentication():
        return {"datasets": 0, "analyses": 0, "literature": 0, "reports": 0}
    
    stats = {
        "datasets": len(st.session_state.get('datasets', [])),
        "analyses": len(st.session_state.get('analysis_jobs', [])),
        "literature": len(st.session_state.get('literature_summaries', [])),
        "reports": 0  # Will be updated when reports are implemented
    }
    
    return stats

def init_session_state():
    """Initialize session state variables"""
    default_values = {
        'authenticated': False,
        'access_token': None,
        'user_info': None,
        'datasets': [],
        'literature_summaries': [],
        'analysis_jobs': [],
        'reports': [],
        'show_register': False,
        'current_page': 'Dashboard'
    }
    
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value