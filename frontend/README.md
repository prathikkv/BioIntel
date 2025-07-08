# 🧬 BioIntel.AI Streamlit Frontend

A modern, user-friendly web interface for the BioIntel.AI bioinformatics platform built with Streamlit.

## ✨ Features

- **🔐 Authentication**: Secure login and registration
- **📊 Dashboard**: Overview of user data and quick actions
- **🔬 Gene Expression Analysis**: Upload datasets, perform PCA, clustering, and EDA
- **📚 Literature Processing**: Upload PDFs/abstracts and chat with papers
- **📊 Report Generation**: Create comprehensive analysis reports
- **⚙️ Settings**: User profile and preferences management

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- BioIntel.AI backend running on `http://localhost:8000`

### Installation

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the application**
   ```bash
   ./run_frontend.sh
   ```

   Or manually:
   ```bash
   streamlit run streamlit_app.py --server.port=8501
   ```

4. **Open in browser**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000

## 📁 Project Structure

```
frontend/
├── streamlit_app.py     # Main Streamlit application
├── config.py           # Configuration settings
├── utils.py            # Utility functions
├── requirements.txt    # Python dependencies
├── run_frontend.sh     # Launch script
└── README.md          # This file
```

## 🎯 Usage

### Authentication
1. Register a new account or login with existing credentials
2. The system uses JWT tokens for secure authentication
3. Sessions are maintained until logout

### Gene Expression Analysis
1. **Upload Dataset**: Support for CSV and Excel files
2. **Perform Analysis**: Choose from EDA, PCA, or clustering
3. **View Results**: Interactive visualizations and detailed results

### Literature Processing
1. **Upload Papers**: Process abstracts or PDF files
2. **AI Analysis**: Extract biomarkers, genes, and key findings
3. **Chat Interface**: Ask questions about processed papers

### Report Generation
1. **Create Reports**: Combine analysis and literature data
2. **Multiple Formats**: Export as HTML or PDF
3. **Custom Templates**: Professional report layouts

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
# API Configuration
API_BASE_URL=http://localhost:8000/api
API_TIMEOUT=30

# UI Settings
MAX_FILE_SIZE_MB=10
SESSION_TIMEOUT_HOURS=24

# Feature Flags
ENABLE_REGISTRATION=True
ENABLE_CHAT=True
ENABLE_REPORTS=True
ENABLE_ANALYTICS=True

# Debug
DEBUG=False
```

### Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[server]
port = 8501
address = "0.0.0.0"

[theme]
base = "light"
primaryColor = "#007bff"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
textColor = "#262730"

[browser]
gatherUsageStats = false
```

## 🎨 Customization

### Themes and Styling

The application uses custom CSS defined in `streamlit_app.py`. Key style classes:

- `.main-header`: Page headers
- `.feature-box`: Feature highlight boxes
- `.metric-card`: Dashboard metric cards
- `.success-message`: Success notifications
- `.error-message`: Error notifications

### Adding New Pages

1. Create a new function in `streamlit_app.py`
2. Add the page to the sidebar navigation
3. Update the main routing logic

Example:
```python
def new_page():
    st.markdown('<h1 class="main-header">🔬 New Feature</h1>', unsafe_allow_html=True)
    st.write("Your content here...")

# Add to sidebar
page = st.selectbox("Navigation", ["Dashboard", "Gene Expression", "Literature", "Reports", "New Feature"])

# Add to routing
if page == "New Feature":
    new_page()
```

## 🔧 Development

### Running in Development Mode

```bash
# Enable debug mode
export DEBUG=True

# Run with auto-reload
streamlit run streamlit_app.py --server.runOnSave=true
```

### Adding New Features

1. Update `utils.py` with new utility functions
2. Add API endpoints to the routing
3. Create UI components in the main app
4. Update configuration if needed

### Testing

```bash
# Install test dependencies
pip install pytest streamlit-testing

# Run tests
pytest tests/
```

## 📱 Mobile Responsiveness

The application is designed to work on both desktop and mobile devices:

- Responsive layout using Streamlit columns
- Mobile-friendly navigation
- Touch-friendly interface elements
- Optimized for various screen sizes

## 🔒 Security

### Authentication
- JWT token-based authentication
- Secure session management
- Automatic token refresh

### Data Protection
- File upload validation
- XSS prevention
- CSRF protection through API design

### Privacy
- No local data storage
- Secure API communication
- User consent management

## 🚀 Deployment

### Local Development
```bash
streamlit run streamlit_app.py
```

### Production Deployment

1. **Using Docker**
   ```bash
   docker build -t biointel-frontend .
   docker run -p 8501:8501 biointel-frontend
   ```

2. **Using Streamlit Cloud**
   - Push to GitHub repository
   - Connect to Streamlit Cloud
   - Deploy with automatic builds

3. **Using Heroku**
   ```bash
   heroku create biointel-frontend
   git push heroku main
   ```

## 📊 Analytics

The frontend includes optional analytics features:

- User interaction tracking
- Performance monitoring
- Error reporting
- Usage statistics

Enable in configuration:
```env
ENABLE_ANALYTICS=True
```

## 🐛 Troubleshooting

### Common Issues

1. **Backend Connection Error**
   - Ensure backend is running on port 8000
   - Check firewall settings
   - Verify API_BASE_URL configuration

2. **File Upload Issues**
   - Check file size limits
   - Verify file format support
   - Ensure proper permissions

3. **Authentication Problems**
   - Clear browser cache
   - Check token expiration
   - Verify API credentials

### Debug Mode

Enable debug mode for detailed error messages:
```bash
export DEBUG=True
streamlit run streamlit_app.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- 📖 Documentation: https://docs.biointel.ai
- 🐛 Issues: https://github.com/biointel-ai/biointel/issues
- 💬 Discussions: https://github.com/biointel-ai/biointel/discussions

---

**Made with ❤️ using Streamlit**