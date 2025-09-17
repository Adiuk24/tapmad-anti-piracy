#!/bin/bash

# Tapmad Anti-Piracy Platform Setup Script
# This script sets up the development environment for your team

set -e  # Exit on any error

echo "🚀 Setting up Tapmad Anti-Piracy Platform..."
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    echo "   macOS: brew install python@3.13"
    echo "   Ubuntu: sudo apt install python3.13"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements-dev.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file..."
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "⚠️  Please edit .env file with your API keys for full functionality"
else
    echo "✅ .env file already exists"
fi

# Test installation
echo "🧪 Testing installation..."
python -c "from src.api.app import app; print('✅ FastAPI app imported successfully!')"

echo ""
echo "🎉 Setup complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start the development server: ./start_dev.sh"
echo "3. Open http://localhost:8000/docs for API documentation"
echo "4. Edit .env file with your API keys (optional for development)"
echo ""
echo "Happy coding! 🚀"
