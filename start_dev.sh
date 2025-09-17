#!/bin/bash

# Tapmad Anti-Piracy Development Server Startup Script
echo "🚀 Starting Tapmad Anti-Piracy Development Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dependencies not installed. Installing..."
    pip install -r requirements-dev.txt
fi

# Start the development server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
