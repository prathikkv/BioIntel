
# 🧠 Claude Prompt Sheet – BioIntel.AI
### Full-stack AI-powered Bioinformatics Assistant (RWE/GenAI/ML Project)

---

## ✅7 Claude rules

1. First think through the problem, read the codebase for relevant files, and write a plan to tasks/todo.md.
2. The plan should have a list of todo items that you can check off as you complete them
3. Before you begin working, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. Please every step of the way just give me a high level explanation of what changes you made
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
7. Finally, add a review section to the [todo.md](http://todo.md/) file with a summary of the changes you made and any other relevant information.

---

## 🧬 1. Gene Expression Upload + EDA

### 📥 Upload CSV + Return Stats
```
You're an expert Python developer. Build a Streamlit or FastAPI API endpoint where a user uploads a gene expression CSV (genes as rows, samples as columns). 
Return:
- number of genes
- number of samples
- top 10 most variable genes (by standard deviation)

Respond with JSON or render as a Streamlit table. Include comments and required libraries.
```

### 📊 PCA Plot + Heatmap
```
Extend the previous app to:
- Perform PCA on the expression matrix
- Render a PCA scatter plot (PC1 vs PC2)
- Show a heatmap of top 20 most variable genes using seaborn

Output: Plots in Streamlit or returned as base64 from API. Code only.
```

---

## 🧪 2. Clustering Analysis

### 🤖 K-Means Clustering (Gene/Sample)
```
Create a FastAPI endpoint that performs K-means clustering on a gene expression matrix uploaded by the user. Use k=3 by default. 
Return:
- cluster labels for each sample
- a PCA plot colored by cluster

Respond with JSON + base64 plot. Keep it modular and clean.
```

### 🔁 Hierarchical Clustering (Optional)
```
Add another clustering method option to your previous API: hierarchical clustering using SciPy. Let the user select between 'kmeans' and 'hierarchical'.
Return dendrogram plot and cluster assignments.
```

---

## 📚 3. Literature Summarization (Claude-Powered)

### 📄 PubMed Abstract Summarization
```
You are Claude, an expert biomedical assistant. Given a PubMed abstract, extract:
- A concise summary
- All genes, proteins, or biomarkers mentioned
- Disease names
- Study methods used
Return in clean bullet points.

Example abstract: [paste real abstract here]
```

### 📘 PDF Summarization (Full Paper)
```
Parse this biomedical research paper PDF (use PyMuPDF or pdfplumber). Extract full text, then summarize it using Claude. Return:
- Title + Summary
- Biomarkers or gene targets mentioned
- Methods and findings
- Any discussed clinical relevance
```

---

## 💬 4. Chat with Paper (RAG-style)

### 🧠 Chat on Research Paper (LLM QA)
```
You are an AI research assistant. Given the full text of a biomedical paper and a user query, answer using only the content of the paper. 
If unsure or not found, say: "Not found in this paper."
Also include relevant citation (e.g., "Figure 3", or "Section 2.2").

Input:
- [paste full text]
- Question: "What biomarkers were identified?"
```

---

## 📄 5. Generate Report

### 📝 HTML + PDF Report (Export)
```
Create a Python function that takes:
- summary text (string)
- base64 images (PCA plot, heatmap)
- clustering results (list or df)
and generates a styled HTML report (Markdown or template). Then export to PDF using WeasyPrint or pdfkit. Include sample inputs for testing.
```

---

## ⚙️ 6. Backend API System

### 🔗 FastAPI: Full API Suite
```
Write a complete FastAPI app with these POST endpoints:
1. /upload/eda – Accepts gene CSV, returns stats + PCA + heatmap
2. /analyze/clustering – Returns clusters from gene matrix
3. /summarize/literature – Accepts abstract or PDF text, returns Claude summary
4. /chat-with-paper – Accepts full paper + question, returns answer
5. /generate-report – Accepts text + plots, returns PDF

Add CORS support and structure with Pydantic models. Include requirements.txt.
```

---

## 🌐 7. Frontend API Calls (React or Streamlit)

### 🧾 React Upload + Display PCA Plot
```
Write a React component that:
- Uploads a CSV file to `/upload/eda` endpoint
- Displays the returned PCA plot and stats
- Uses Tailwind CSS for styling
- Handles loading and error states cleanly
```

### 🖥️ Streamlit Upload + Call API
```
Write a Streamlit UI that:
- Lets the user upload a CSV
- Calls FastAPI endpoint `/upload/eda`
- Displays JSON summary and images (heatmap + PCA)

Include request handling and clean display layout.
```

---

## 🔐 8. Claude/GPT Integration (Server-Side)

### 🔑 Claude API Call in Python
```
Write a Python function to call Claude (Anthropic API) using a prompt like:
"Summarize this biomedical paper and extract biomarkers."
Use `anthropic` Python SDK. Wrap this into an async FastAPI endpoint.

Include error handling and secret key usage from `.env`.
```

### 🧠 LangChain / LLM Retrieval (Optional)
```
Create a LangChain RAG pipeline that:
- Loads full-text biomedical paper
- Splits into chunks with metadata
- Answers user questions based only on document
- Uses Claude or OpenAI as LLM backend
```

---

## 📦 9. Deployment Ready

### 🚀 Vercel + Hugging Face Deployment
```
Give me:
1. A project structure with frontend (Next.js or Streamlit) and backend (FastAPI)
2. Instructions to deploy frontend on Vercel
3. Instructions to deploy backend on Hugging Face Spaces or Render
Include README.md with full steps and environment variable setup.
```

---

## 🧠 BONUS: Prompt Engineering Help

### 🎯 Biomedical Prompt Optimizer
```
You are a prompt engineer. Refine this Claude prompt to make it more precise and consistent when extracting biomarkers, diseases, and gene names from a biomedical abstract. 
Current prompt: 
"Summarize this biomedical paper and list all biomarkers, genes, and diseases mentioned."

Optimize for: clarity, consistency, and biomedical accuracy.
```

---

## 🔐 10. Authentication & Security

### 🛡️ JWT Authentication System
```
Build a secure JWT authentication system for FastAPI with:
- User registration with email verification
- Password hashing using bcrypt
- JWT token generation with refresh tokens
- Protected routes using dependency injection
- Password reset functionality
- Account lockout after failed attempts

Include proper error handling and security headers. Use SQLAlchemy for user storage.
```

### 🔒 API Security & Rate Limiting
```
Implement comprehensive API security:
- Rate limiting per user/IP (Redis-based)
- Input validation and sanitization
- CORS configuration
- API key management for external services
- SQL injection prevention
- XSS protection
- HTTPS enforcement

Create middleware for security headers and request validation.
```

### 🛡️ Data Encryption & Privacy
```
Implement data protection:
- Encrypt sensitive data at rest using AES-256
- Secure API key storage with environment variables
- Data anonymization for analytics
- PII detection and masking
- Secure file upload handling
- Data retention policies

Include examples of encrypting gene expression data and user information.
```

---

## ✅ 11. Data Validation & Error Handling

### 📊 Gene Expression Data Validation
```
Create robust data validation for bioinformatics inputs:
- CSV format validation (genes as rows, samples as columns)
- Gene identifier validation (HGNC, Ensembl, etc.)
- Expression value range validation
- Missing data detection and handling
- Duplicate gene/sample detection
- File size and format constraints

Return detailed error messages with suggestions for data correction.
```

### 🚨 Comprehensive Error Handling
```
Build a centralized error handling system:
- Custom exception classes for different error types
- Error logging with structured format
- User-friendly error messages
- Error recovery mechanisms
- Retry logic for external API calls
- Graceful degradation strategies

Include error codes and documentation for frontend integration.
```

### 🔍 Input Sanitization & Validation
```
Implement input validation for all endpoints:
- Pydantic models for request/response validation
- File upload validation (size, type, content)
- Parameter sanitization
- SQL injection prevention
- Path traversal protection
- Malicious file detection

Create reusable validation decorators and middleware.
```

---

## 🗄️ 12. Database Design & Management

### 📚 PostgreSQL Schema Design
```
Design a scalable database schema:
- User management (users, roles, permissions)
- Data processing audit logs
- Gene expression data storage
- Literature processing history
- Report generation tracking
- API usage analytics

Include proper indexing, foreign keys, and migration scripts.
```

### 🔄 Database Migrations & Backup
```
Implement database management:
- Alembic migration system
- Automated backup procedures
- Database connection pooling
- Query optimization
- Data archiving strategies
- Performance monitoring

Create migration scripts for schema updates and data transformations.
```

### 📊 Data Models & Relationships
```
Define comprehensive data models:
- User profiles and preferences
- Gene expression datasets
- Processing job status
- Literature analysis results
- Report metadata
- System configuration

Use SQLAlchemy ORM with proper relationships and constraints.
```

---

## 🧪 13. Testing Strategy & Quality Assurance

### 🔬 Unit & Integration Testing
```
Create comprehensive testing suite:
- Unit tests for all API endpoints
- Integration tests for database operations
- Mock external API calls (Claude, OpenAI)
- Gene expression data processing tests
- Authentication and security tests
- Performance and load testing

Use pytest with fixtures and proper test isolation.
```

### 🎯 End-to-End Testing
```
Implement E2E testing:
- Full user workflow testing
- File upload and processing
- Literature summarization pipeline
- Report generation and export
- Error scenario testing
- Cross-browser compatibility

Create automated test scenarios for critical user journeys.
```

### 📈 Performance Testing
```
Build performance testing framework:
- Load testing for API endpoints
- Database query optimization tests
- Memory usage monitoring
- Response time benchmarks
- Concurrent user testing
- Scalability testing

Include performance metrics and benchmarking tools.
```

---

## 📚 14. API Documentation & Developer Experience

### 📖 OpenAPI/Swagger Documentation
```
Generate comprehensive API documentation:
- Interactive Swagger UI
- Request/response examples
- Authentication instructions
- Error code documentation
- Rate limiting information
- SDK generation support

Include code examples in multiple programming languages.
```

### 🔧 Developer Tools & SDK
```
Create developer-friendly tools:
- Python SDK for API integration
- CLI tools for data upload
- Postman collections
- Code examples and tutorials
- Integration guides
- Troubleshooting documentation

Provide comprehensive onboarding materials for developers.
```

### 📝 API Versioning & Changelog
```
Implement API versioning strategy:
- Semantic versioning for API releases
- Backward compatibility maintenance
- Deprecation warnings and migration guides
- Changelog documentation
- Version negotiation headers
- Legacy API support

Create migration paths for API updates.
```

---

## ⚖️ 15. Legal Compliance & Privacy

### 🛡️ GDPR Compliance
```
Implement GDPR compliance:
- Data processing consent management
- Right to be forgotten implementation
- Data portability features
- Privacy by design principles
- Data processing audit logs
- Consent withdrawal mechanisms

Create GDPR-compliant data handling procedures.
```

### 🏥 HIPAA Compliance (Healthcare Data)
```
Ensure HIPAA compliance for healthcare data:
- PHI identification and protection
- Access controls and audit trails
- Data encryption requirements
- Business associate agreements
- Breach notification procedures
- Security risk assessments

Implement healthcare-specific security measures.
```

### 📋 Legal Documentation
```
Generate legal documentation:
- Privacy policy generator
- Terms of service template
- Cookie policy implementation
- Data processing agreements
- User consent forms
- Compliance reporting tools

Create automated legal document generation.
```

---

## 📊 16. Monitoring & Logging

### 📈 Application Monitoring
```
Implement comprehensive monitoring:
- Real-time performance metrics
- API endpoint monitoring
- Database performance tracking
- Error rate monitoring
- User behavior analytics
- Resource usage monitoring

Use structured logging with correlation IDs.
```

### 🚨 Alerting & Incident Response
```
Create alerting system:
- Performance threshold alerts
- Error rate monitoring
- Security incident detection
- Automated incident response
- Escalation procedures
- Recovery playbooks

Implement proactive monitoring and alerting.
```

### 📊 Analytics & Reporting
```
Build analytics dashboard:
- User engagement metrics
- API usage statistics
- Performance benchmarks
- Error analysis reports
- Business intelligence insights
- Cost optimization metrics

Create automated reporting and insights generation.
```

---

## 🚀 17. Performance & Scalability

### ⚡ Performance Optimization
```
Implement performance optimizations:
- Database query optimization
- Caching strategies (Redis)
- Async processing for large datasets
- CDN integration for static assets
- Image optimization and compression
- API response compression

Create performance monitoring and optimization tools.
```

### 📊 Scalability Architecture
```
Design scalable architecture:
- Microservices decomposition
- Load balancing strategies
- Database sharding
- Background job processing
- Auto-scaling configuration
- Resource optimization

Implement horizontal scaling capabilities.
```

### 🔄 Caching & Content Delivery
```
Implement caching strategies:
- Redis for session and API caching
- Database query result caching
- Static file CDN integration
- Cache invalidation strategies
- Edge caching for global users
- Cache warming procedures

Create intelligent caching mechanisms.
```

---

## 🔄 18. CI/CD Pipeline & DevOps

### 🚀 Continuous Integration
```
Setup CI/CD pipeline:
- GitHub Actions workflow
- Automated testing on PRs
- Code quality checks (linting, formatting)
- Security vulnerability scanning
- Dependency update automation
- Build and deployment automation

Create comprehensive CI/CD pipeline for Vercel deployment.
```

### 🛠️ Development Environment
```
Configure development environment:
- Docker containerization
- Local development setup
- Environment variable management
- Database seeding scripts
- Mock services for testing
- Development documentation

Create reproducible development environments.
```

### 🔧 Production Deployment
```
Implement production deployment:
- Vercel serverless deployment
- Environment-specific configurations
- Database migration automation
- Health check endpoints
- Rollback procedures
- Blue-green deployment strategy

Create automated deployment and monitoring systems.
```

---
