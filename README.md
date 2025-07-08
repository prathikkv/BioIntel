# 🧬 BioIntel.AI

**AI-powered bioinformatics platform for gene expression analysis and literature summarization**

BioIntel.AI is a comprehensive platform that combines advanced bioinformatics analysis with AI-powered literature mining to provide researchers with powerful tools for gene expression analysis, biomarker discovery, and scientific literature summarization.

## ✨ Features

### 🔬 Gene Expression Analysis
- **Data Upload & Validation**: Support for CSV, Excel, and other common formats
- **Quality Assessment**: Comprehensive data quality metrics and validation
- **Exploratory Data Analysis**: Statistical summaries and visualizations
- **Principal Component Analysis (PCA)**: Dimensionality reduction and visualization
- **Clustering Analysis**: K-means and hierarchical clustering
- **Interactive Visualizations**: PCA plots, heatmaps, and correlation matrices

### 📚 Literature Analysis
- **Abstract Processing**: AI-powered summarization of research abstracts
- **PDF Processing**: Full-text extraction and analysis from research papers
- **Entity Extraction**: Automatic identification of genes, biomarkers, diseases, and methods
- **Chat with Papers**: Interactive Q&A with research papers using RAG
- **Literature Search**: Comprehensive search across processed literature

### 📊 Report Generation
- **HTML Reports**: Interactive web-based reports
- **PDF Export**: Professional PDF reports for sharing
- **Custom Templates**: Customizable report templates
- **Combined Analysis**: Integrated data and literature reports

### 🔐 Security & Authentication
- **JWT Authentication**: Secure user authentication
- **Role-based Access**: User permissions and access control
- **Rate Limiting**: API protection and usage limits
- **Data Encryption**: Secure data storage and transmission

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- Redis (for caching)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/biointel-ai/biointel.git
   cd biointel
   ```

2. **Run the installation script**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the services**
   ```bash
   # Start PostgreSQL and Redis
   brew services start postgresql  # macOS
   brew services start redis       # macOS
   
   # Activate virtual environment
   source venv/bin/activate
   
   # Start the application
   uvicorn api.main:app --reload --port 8000
   ```

### Manual Installation

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start the application**
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

## 🔧 Configuration

### Required Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/biointel

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# AI APIs
ANTHROPIC_API_KEY=your-anthropic-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Redis
REDIS_URL=redis://localhost:6379
```

See `.env.example` for complete configuration options.

## 📖 API Documentation

Once the application is running, you can access:

- **Interactive API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Specification**: http://localhost:8000/openapi.json

## 🧪 Usage Examples

### Data Analysis Workflow

1. **Upload Dataset**
   ```bash
   curl -X POST "http://localhost:8000/api/bio/upload" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@your_dataset.csv" \
     -F "metadata={\"name\":\"My Dataset\",\"description\":\"Test dataset\"}"
   ```

2. **Perform PCA Analysis**
   ```bash
   curl -X POST "http://localhost:8000/api/bio/pca" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"dataset_id": 1, "n_components": 2}'
   ```

3. **Generate Report**
   ```bash
   curl -X POST "http://localhost:8000/api/reports/generate" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"report_type": "analysis", "title": "My Analysis Report", "dataset_ids": [1]}'
   ```

### Literature Analysis

1. **Process Abstract**
   ```bash
   curl -X POST "http://localhost:8000/api/literature/abstract" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"abstract": "Your research abstract here...", "title": "Paper Title"}'
   ```

2. **Chat with Paper**
   ```bash
   curl -X POST "http://localhost:8000/api/literature/chat/1" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"question": "What biomarkers were identified?"}'
   ```

## 🏗️ Architecture

```
BioIntel.AI/
├── api/                    # FastAPI routes
│   ├── auth.py            # Authentication endpoints
│   ├── bioinformatics.py  # Data analysis endpoints
│   ├── literature.py      # Literature processing endpoints
│   ├── reports.py         # Report generation endpoints
│   └── main.py            # Main application
├── models/                # SQLAlchemy models
├── services/              # Business logic
├── utils/                 # Utilities and helpers
├── templates/             # Report templates
└── tests/                 # Test suite
```

## 🧪 Testing

```bash
# Run all tests
./run_tests.sh

# Run specific test types
./run_tests.sh -t unit        # Unit tests
./run_tests.sh -t integration # Integration tests
./run_tests.sh -t api         # API tests

# Run with coverage
./run_tests.sh -c

# Run specific test file
./run_tests.sh -f test_bioinformatics.py

# Verbose output
./run_tests.sh -v
```

## 🚀 Deployment

### Quick Docker Deployment

```bash
# Deploy with Docker Compose
./docker-deploy.sh

# Deploy in production mode
./docker-deploy.sh -e production --rebuild

# Scale services
./docker-deploy.sh --scale-api 3 --scale-frontend 2
```

### Vercel Deployment

```bash
# Deploy to Vercel
./deploy.sh -p vercel -e production

# Set environment variables
vercel env add DATABASE_URL
vercel env add SECRET_KEY
vercel env add ANTHROPIC_API_KEY
vercel env add OPENAI_API_KEY
```

### Heroku Deployment

```bash
# Deploy to Heroku
./deploy.sh -p heroku -e production
```

### Manual Docker Commands

```bash
# Build image
docker build -t biointel-ai .

# Run container
docker run -p 8000:8000 biointel-ai

# Using Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### Manual Deployment

1. Set up production environment variables
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `alembic upgrade head`
4. Start with production server: `gunicorn api.main:app -k uvicorn.workers.UvicornWorker`

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 **Documentation**: https://docs.biointel.ai
- 🐛 **Issues**: https://github.com/biointel-ai/biointel/issues
- 💬 **Discussions**: https://github.com/biointel-ai/biointel/discussions
- 📧 **Email**: support@biointel.ai

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- AI powered by [Anthropic Claude](https://www.anthropic.com/) and [OpenAI](https://openai.com/)
- Bioinformatics analysis with [scikit-learn](https://scikit-learn.org/) and [pandas](https://pandas.pydata.org/)
- Visualizations with [Plotly](https://plotly.com/) and [Matplotlib](https://matplotlib.org/)

---

**Made with ❤️ by the BioIntel.AI Team**

