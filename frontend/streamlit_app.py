import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from typing import Dict, Any, Optional
import base64
import io

# Configure page
st.set_page_config(
    page_title="BioIntel.AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #007bff;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
        padding: 1rem;
        background: #d4edda;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
        padding: 1rem;
        background: #f8d7da;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000/api"

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'datasets' not in st.session_state:
    st.session_state.datasets = []
if 'literature_summaries' not in st.session_state:
    st.session_state.literature_summaries = []

def make_api_request(endpoint: str, method: str = "GET", data: Any = None, files: Any = None, headers: Dict = None) -> Dict:
    """Make API request with authentication"""
    url = f"{API_BASE_URL}{endpoint}"
    
    # Add authentication header
    if st.session_state.access_token:
        if headers is None:
            headers = {}
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files, headers=headers)
            else:
                response = requests.post(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code == 200 or response.status_code == 201:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.json().get("detail", "Unknown error")}
    
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}

def login_page():
    """Login page"""
    st.markdown('<h1 class="main-header">🧬 BioIntel.AI</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI-powered bioinformatics platform</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Login")
        
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="your.email@example.com")
            password = st.text_input("🔒 Password", type="password")
            submit_button = st.form_submit_button("Login", use_container_width=True)
            
            if submit_button:
                if email and password:
                    # Make login request
                    result = make_api_request("/auth/login", "POST", {
                        "email": email,
                        "password": password
                    })
                    
                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.access_token = result["data"]["access_token"]
                        st.session_state.user_info = result["data"]["user"]
                        st.experimental_rerun()
                    else:
                        st.error(f"Login failed: {result['error']}")
                else:
                    st.error("Please enter both email and password")
        
        st.markdown("---")
        st.markdown("### 📝 New User?")
        if st.button("Create Account", use_container_width=True):
            st.session_state.show_register = True
            st.experimental_rerun()

def register_page():
    """Registration page"""
    st.markdown('<h1 class="main-header">🧬 BioIntel.AI</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Create your account</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 📝 Register")
        
        with st.form("register_form"):
            email = st.text_input("📧 Email", placeholder="your.email@example.com")
            password = st.text_input("🔒 Password", type="password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password")
            full_name = st.text_input("👤 Full Name", placeholder="Dr. Jane Smith")
            organization = st.text_input("🏢 Organization", placeholder="University Research Lab")
            consent = st.checkbox("I agree to the terms and conditions and privacy policy")
            
            submit_button = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit_button:
                if not consent:
                    st.error("Please accept the terms and conditions")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters")
                elif email and password and full_name:
                    # Make registration request
                    result = make_api_request("/auth/register", "POST", {
                        "email": email,
                        "password": password,
                        "full_name": full_name,
                        "organization": organization,
                        "consent_given": consent
                    })
                    
                    if result["success"]:
                        st.success("Account created successfully! Please login.")
                        st.session_state.show_register = False
                        st.experimental_rerun()
                    else:
                        st.error(f"Registration failed: {result['error']}")
                else:
                    st.error("Please fill in all required fields")
        
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.show_register = False
            st.experimental_rerun()

def main_dashboard():
    """Main dashboard"""
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.user_info.get('full_name', 'User')}!")
        st.markdown(f"**Organization:** {st.session_state.user_info.get('organization', 'N/A')}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.access_token = None
            st.session_state.user_info = None
            st.experimental_rerun()
        
        st.markdown("---")
        
        # Navigation
        page = st.selectbox(
            "🧭 Navigation",
            ["Dashboard", "Gene Expression Analysis", "Literature Analysis", "Reports", "Settings"]
        )
    
    # Main content based on selected page
    if page == "Dashboard":
        dashboard_page()
    elif page == "Gene Expression Analysis":
        gene_expression_page()
    elif page == "Literature Analysis":
        literature_page()
    elif page == "Reports":
        reports_page()
    elif page == "Settings":
        settings_page()

def dashboard_page():
    """Dashboard overview"""
    st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)
    
    # Fetch user statistics
    stats_result = make_api_request("/bio/analysis-jobs")
    literature_stats = make_api_request("/literature/stats")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📁 Datasets</h3>
            <h2>0</h2>
            <p>Total uploaded</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>🔬 Analyses</h3>
            <h2>0</h2>
            <p>Completed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📚 Literature</h3>
            <h2>0</h2>
            <p>Papers processed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Reports</h3>
            <h2>0</h2>
            <p>Generated</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h4>🔬 Analyze Gene Expression</h4>
            <p>Upload your dataset and perform PCA, clustering, and statistical analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-box">
            <h4>📚 Process Literature</h4>
            <p>Upload research papers or abstracts for AI-powered summarization</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-box">
            <h4>📊 Generate Reports</h4>
            <p>Create comprehensive reports combining your data and literature findings</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activity
    st.markdown("### 📈 Recent Activity")
    st.info("No recent activity to display. Upload a dataset or process literature to get started!")

def gene_expression_page():
    """Gene expression analysis page"""
    st.markdown('<h1 class="main-header">🔬 Gene Expression Analysis</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📥 Upload Data", "📊 Analysis", "📈 Results"])
    
    with tab1:
        st.markdown("### 📥 Upload Gene Expression Dataset")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=['csv', 'xlsx', 'xls'],
            help="Upload a gene expression dataset with genes as rows and samples as columns"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.info(f"File: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            # Metadata form
            with st.form("dataset_metadata"):
                col1, col2 = st.columns(2)
                
                with col1:
                    dataset_name = st.text_input("Dataset Name", value=uploaded_file.name.split('.')[0])
                    organism = st.text_input("Organism", placeholder="e.g., Homo sapiens")
                    tissue_type = st.text_input("Tissue Type", placeholder="e.g., Breast tissue")
                
                with col2:
                    description = st.text_area("Description", placeholder="Brief description of the dataset")
                    experiment_type = st.text_input("Experiment Type", placeholder="e.g., RNA-seq")
                
                submit_button = st.form_submit_button("Upload Dataset", use_container_width=True)
                
                if submit_button:
                    metadata = {
                        "name": dataset_name,
                        "description": description,
                        "organism": organism,
                        "tissue_type": tissue_type,
                        "experiment_type": experiment_type
                    }
                    
                    # Upload dataset
                    files = {"file": uploaded_file.getvalue()}
                    data = {"metadata": json.dumps(metadata)}
                    
                    result = make_api_request("/bio/upload", "POST", data=data, files=files)
                    
                    if result["success"]:
                        st.markdown('<div class="success-message">Dataset uploaded successfully!</div>', unsafe_allow_html=True)
                        st.json(result["data"])
                    else:
                        st.markdown(f'<div class="error-message">Upload failed: {result["error"]}</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 📊 Analysis Tools")
        
        # Get datasets
        datasets_result = make_api_request("/bio/datasets")
        
        if datasets_result["success"] and datasets_result["data"]["datasets"]:
            datasets = datasets_result["data"]["datasets"]
            
            # Dataset selection
            dataset_options = {f"{d['name']} (ID: {d['id']})": d['id'] for d in datasets}
            selected_dataset = st.selectbox("Select Dataset", options=list(dataset_options.keys()))
            
            if selected_dataset:
                dataset_id = dataset_options[selected_dataset]
                
                # Analysis options
                analysis_type = st.selectbox("Analysis Type", ["EDA", "PCA", "Clustering"])
                
                if analysis_type == "EDA":
                    if st.button("Perform Exploratory Data Analysis", use_container_width=True):
                        result = make_api_request(f"/bio/eda/{dataset_id}", "POST")
                        if result["success"]:
                            st.success("EDA completed successfully!")
                            st.json(result["data"])
                        else:
                            st.error(f"EDA failed: {result['error']}")
                
                elif analysis_type == "PCA":
                    n_components = st.slider("Number of Components", 2, 10, 2)
                    if st.button("Perform PCA", use_container_width=True):
                        result = make_api_request("/bio/pca", "POST", {
                            "dataset_id": dataset_id,
                            "n_components": n_components
                        })
                        if result["success"]:
                            st.success("PCA completed successfully!")
                            st.json(result["data"])
                        else:
                            st.error(f"PCA failed: {result['error']}")
                
                elif analysis_type == "Clustering":
                    col1, col2 = st.columns(2)
                    with col1:
                        method = st.selectbox("Method", ["kmeans", "hierarchical"])
                    with col2:
                        n_clusters = st.slider("Number of Clusters", 2, 10, 3)
                    
                    if st.button("Perform Clustering", use_container_width=True):
                        result = make_api_request("/bio/clustering", "POST", {
                            "dataset_id": dataset_id,
                            "method": method,
                            "n_clusters": n_clusters
                        })
                        if result["success"]:
                            st.success("Clustering completed successfully!")
                            st.json(result["data"])
                        else:
                            st.error(f"Clustering failed: {result['error']}")
        else:
            st.info("No datasets available. Please upload a dataset first.")
    
    with tab3:
        st.markdown("### 📈 Analysis Results")
        
        # Get analysis jobs
        jobs_result = make_api_request("/bio/analysis-jobs")
        
        if jobs_result["success"] and jobs_result["data"]["analysis_jobs"]:
            jobs = jobs_result["data"]["analysis_jobs"]
            
            for job in jobs:
                with st.expander(f"{job['job_name']} - {job['status'].title()}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Type:** {job['job_type']}")
                        st.write(f"**Status:** {job['status']}")
                        st.write(f"**Progress:** {job['progress']}%")
                    
                    with col2:
                        st.write(f"**Created:** {job['created_at']}")
                        if job['completed_at']:
                            st.write(f"**Completed:** {job['completed_at']}")
                    
                    if job['results']:
                        st.write("**Results:**")
                        st.json(job['results'])
        else:
            st.info("No analysis results available.")

def literature_page():
    """Literature analysis page"""
    st.markdown('<h1 class="main-header">📚 Literature Analysis</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📄 Process Literature", "💬 Chat with Papers", "📋 Summaries"])
    
    with tab1:
        st.markdown("### 📄 Process Research Literature")
        
        # Choose input type
        input_type = st.selectbox("Input Type", ["Abstract", "PDF Upload"])
        
        if input_type == "Abstract":
            with st.form("abstract_form"):
                title = st.text_input("Paper Title")
                authors = st.text_input("Authors")
                journal = st.text_input("Journal")
                abstract = st.text_area("Abstract", height=200, placeholder="Paste the research paper abstract here...")
                
                submit_button = st.form_submit_button("Process Abstract", use_container_width=True)
                
                if submit_button and abstract:
                    result = make_api_request("/literature/abstract", "POST", {
                        "abstract": abstract,
                        "title": title,
                        "authors": authors,
                        "journal": journal
                    })
                    
                    if result["success"]:
                        st.success("Abstract processed successfully!")
                        st.json(result["data"])
                    else:
                        st.error(f"Processing failed: {result['error']}")
        
        elif input_type == "PDF Upload":
            uploaded_pdf = st.file_uploader("Choose a PDF file", type=['pdf'])
            
            if uploaded_pdf is not None:
                with st.form("pdf_form"):
                    title = st.text_input("Paper Title")
                    authors = st.text_input("Authors")
                    journal = st.text_input("Journal")
                    
                    submit_button = st.form_submit_button("Process PDF", use_container_width=True)
                    
                    if submit_button:
                        metadata = {
                            "title": title,
                            "authors": authors,
                            "journal": journal
                        }
                        
                        files = {"file": uploaded_pdf.getvalue()}
                        data = {"metadata": json.dumps(metadata)}
                        
                        result = make_api_request("/literature/pdf", "POST", data=data, files=files)
                        
                        if result["success"]:
                            st.success("PDF processed successfully!")
                            st.json(result["data"])
                        else:
                            st.error(f"Processing failed: {result['error']}")
    
    with tab2:
        st.markdown("### 💬 Chat with Research Papers")
        
        # Get literature summaries
        summaries_result = make_api_request("/literature/summaries")
        
        if summaries_result["success"] and summaries_result["data"]["summaries"]:
            summaries = summaries_result["data"]["summaries"]
            
            # Select paper
            paper_options = {f"{s['title'][:50]}... (ID: {s['id']})": s['id'] for s in summaries}
            selected_paper = st.selectbox("Select Paper", options=list(paper_options.keys()))
            
            if selected_paper:
                paper_id = paper_options[selected_paper]
                
                # Chat interface
                question = st.text_input("Ask a question about the paper:", placeholder="What biomarkers were identified in this study?")
                
                if st.button("Ask Question", use_container_width=True) and question:
                    result = make_api_request(f"/literature/chat/{paper_id}", "POST", {
                        "question": question
                    })
                    
                    if result["success"]:
                        st.markdown("### 🤖 AI Response:")
                        st.write(result["data"]["response"])
                        
                        if result["data"]["citations"]:
                            st.markdown("### 📚 Citations:")
                            for citation in result["data"]["citations"]:
                                st.write(f"- {citation}")
                    else:
                        st.error(f"Chat failed: {result['error']}")
        else:
            st.info("No literature summaries available. Please process some papers first.")
    
    with tab3:
        st.markdown("### 📋 Literature Summaries")
        
        # Get summaries
        summaries_result = make_api_request("/literature/summaries")
        
        if summaries_result["success"] and summaries_result["data"]["summaries"]:
            summaries = summaries_result["data"]["summaries"]
            
            for summary in summaries:
                with st.expander(f"{summary['title']} ({summary['source_type']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Authors:** {summary['authors'] or 'N/A'}")
                        st.write(f"**Journal:** {summary['journal'] or 'N/A'}")
                        st.write(f"**Status:** {summary['processing_status']}")
                    
                    with col2:
                        st.write(f"**Created:** {summary['created_at']}")
                        if summary['confidence_score']:
                            st.write(f"**Confidence:** {summary['confidence_score']:.2%}")
                    
                    if summary['summary']:
                        st.write("**Summary:**")
                        st.write(summary['summary'])
                    
                    if summary['biomarkers']:
                        st.write("**Biomarkers:**")
                        st.write(", ".join(summary['biomarkers']))
        else:
            st.info("No literature summaries available.")

def reports_page():
    """Reports page"""
    st.markdown('<h1 class="main-header">📊 Reports</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 Generate Report", "📋 My Reports"])
    
    with tab1:
        st.markdown("### 📝 Generate New Report")
        
        with st.form("report_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Report Title", placeholder="My Analysis Report")
                report_type = st.selectbox("Report Type", ["analysis", "literature", "combined"])
                format_type = st.selectbox("Format", ["html", "pdf"])
            
            with col2:
                description = st.text_area("Description", placeholder="Brief description of the report")
                include_plots = st.checkbox("Include Plots", value=True)
                include_stats = st.checkbox("Include Statistics", value=True)
            
            submit_button = st.form_submit_button("Generate Report", use_container_width=True)
            
            if submit_button and title:
                result = make_api_request("/reports/generate", "POST", {
                    "title": title,
                    "description": description,
                    "report_type": report_type,
                    "format_type": format_type,
                    "include_plots": include_plots,
                    "include_statistics": include_stats
                })
                
                if result["success"]:
                    st.success("Report generated successfully!")
                    st.json(result["data"])
                else:
                    st.error(f"Report generation failed: {result['error']}")
    
    with tab2:
        st.markdown("### 📋 My Reports")
        
        # Get reports
        reports_result = make_api_request("/reports/")
        
        if reports_result["success"] and reports_result["data"]["reports"]:
            reports = reports_result["data"]["reports"]
            
            for report in reports:
                with st.expander(f"{report['title']} ({report['format_type'].upper()})"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Type:** {report['report_type']}")
                        st.write(f"**Format:** {report['format_type']}")
                        st.write(f"**Created:** {report['created_at']}")
                    
                    with col2:
                        if report['file_size']:
                            st.write(f"**Size:** {report['file_size']} bytes")
                        if report['generation_time']:
                            st.write(f"**Generation Time:** {report['generation_time']:.2f}s")
                    
                    with col3:
                        if st.button(f"Download {report['id']}", key=f"download_{report['id']}"):
                            st.info("Download functionality requires backend implementation")
        else:
            st.info("No reports available.")

def settings_page():
    """Settings page"""
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["👤 Profile", "🔧 Preferences"])
    
    with tab1:
        st.markdown("### 👤 User Profile")
        
        # Display current user info
        user_info = st.session_state.user_info
        
        with st.form("profile_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input("Full Name", value=user_info.get('full_name', ''))
                email = st.text_input("Email", value=user_info.get('email', ''), disabled=True)
            
            with col2:
                organization = st.text_input("Organization", value=user_info.get('organization', ''))
                position = st.text_input("Position", value=user_info.get('position', ''))
            
            bio = st.text_area("Bio", value=user_info.get('bio', ''))
            
            submit_button = st.form_submit_button("Update Profile", use_container_width=True)
            
            if submit_button:
                st.info("Profile update functionality requires backend implementation")
    
    with tab2:
        st.markdown("### 🔧 Preferences")
        
        # Theme
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
        
        # Notifications
        st.markdown("#### 🔔 Notifications")
        email_notifications = st.checkbox("Email Notifications", value=True)
        analysis_complete = st.checkbox("Analysis Completion", value=True)
        
        # Data Processing
        st.markdown("#### 📊 Data Processing")
        auto_save = st.checkbox("Auto-save results", value=True)
        max_file_size = st.slider("Max file size (MB)", 1, 100, 10)
        
        if st.button("Save Preferences", use_container_width=True):
            st.success("Preferences saved successfully!")

# Main app logic
def main():
    """Main application"""
    # Check if user wants to register
    if 'show_register' in st.session_state and st.session_state.show_register:
        register_page()
    elif not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()