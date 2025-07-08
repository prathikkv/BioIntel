#!/bin/bash

# BioIntel.AI Streamlit Frontend Launch Script

echo "🧬 Starting BioIntel.AI Streamlit Frontend"
echo "========================================"

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit is not installed. Installing now..."
    pip install -r requirements.txt
fi

# Check if backend is running
echo "🔍 Checking backend availability..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running"
else
    echo "⚠️  Backend is not running. Please start the backend server first:"
    echo "   cd .. && uvicorn api.main:app --reload --port 8000"
    echo ""
    echo "Continue anyway? (y/N)"
    read -r response
    if [[ ! $response =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."

# Launch Streamlit
echo "🚀 Starting Streamlit application..."
echo "📱 Frontend will be available at: http://localhost:8501"
echo "🔧 Backend API should be running at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the application"
echo "=================================="

streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0