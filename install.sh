#!/bin/bash

# BioIntel.AI Installation Script
# This script sets up the BioIntel.AI platform for development

echo "🧬 BioIntel.AI Installation Script"
echo "=================================="

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p /tmp/biointel_reports
mkdir -p logs
mkdir -p uploads

# Copy environment template
echo "⚙️ Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Environment file created. Please edit .env with your API keys and configuration."
else
    echo "⚠️ Environment file already exists. Skipping .env creation."
fi

# Check for additional system dependencies
echo "🔍 Checking system dependencies..."

# Check for PostgreSQL
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL is installed"
else
    echo "⚠️ PostgreSQL is not installed. Please install PostgreSQL for database functionality."
    echo "   macOS: brew install postgresql"
    echo "   Ubuntu: sudo apt-get install postgresql postgresql-contrib"
fi

# Check for Redis
if command -v redis-server &> /dev/null; then
    echo "✅ Redis is installed"
else
    echo "⚠️ Redis is not installed. Please install Redis for caching."
    echo "   macOS: brew install redis"
    echo "   Ubuntu: sudo apt-get install redis-server"
fi

# Run database migrations (if database is available)
echo "🗄️ Setting up database..."
if command -v alembic &> /dev/null; then
    alembic upgrade head
    echo "✅ Database migrations completed"
else
    echo "⚠️ Alembic not found. Database migrations skipped."
fi

# Install development tools
echo "🛠️ Installing development tools..."
pip install -e ".[dev]"

# Set up pre-commit hooks
echo "🔗 Setting up pre-commit hooks..."
pre-commit install

echo ""
echo "🎉 Installation completed!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file with your API keys and configuration"
echo "2. Start PostgreSQL and Redis services"
echo "3. Run the application with: uvicorn api.main:app --reload"
echo ""
echo "🚀 To start the development server:"
echo "   source venv/bin/activate"
echo "   uvicorn api.main:app --reload --port 8000"
echo ""
echo "📖 Documentation: https://docs.biointel.ai"
echo "🐛 Issues: https://github.com/biointel-ai/biointel/issues"
echo ""
echo "Happy analyzing! 🧬✨"