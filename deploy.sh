#!/bin/bash

# 🚀 TAPMAD ANTI-PIRACY PLATFORM - DEPLOYMENT SCRIPT
# This script will get your platform running in minutes!

echo "🚀 TAPMAD ANTI-PIRACY PLATFORM - DEPLOYMENT SCRIPT"
echo "=================================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Setup environment file
if [ ! -f .env ]; then
    if [ -f env.template ]; then
        cp env.template .env
        echo "✅ Created .env file from template"
        echo "⚠️  Please edit .env file with your API keys and configuration"
    else
        echo "⚠️  No env.template found. Creating basic .env file..."
        cat > .env << 'ENVEOF'
# Environment Configuration
ENV=development
API_KEY=your_strong_api_key_here

# Local AI Configuration (choose one)
LOCAL_AI_PROVIDER=ollama
LOCAL_AI_ENDPOINT=http://localhost:11434
LOCAL_AI_MODEL=llama2:7b

# External API Keys (optional)
YOUTUBE_API_KEY=your_youtube_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token_here
ENVEOF
        echo "✅ Created basic .env file"
        echo "⚠️  Please edit .env file with your actual API keys"
    fi
else
    echo "✅ .env file already exists"
fi

# Deploy platform
echo "🚀 Deploying Tapmad Anti-Piracy Platform..."

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up -d --build

echo "✅ Platform deployment initiated!"

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check if API is ready
if curl -s http://localhost:8000/health &> /dev/null; then
    echo "✅ API service is ready!"
else
    echo "⚠️  API service may still be starting. Check with: docker-compose logs api"
fi

echo ""
echo "🎉 TAPMAD ANTI-PIRACY PLATFORM IS READY!"
echo "========================================="
echo ""
echo "🌐 Dashboard: http://localhost:3000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "✅ Health Check: http://localhost:8000/health"
echo ""
echo "📋 Useful Commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop platform: docker-compose down"
echo "  - Restart platform: docker-compose restart"
echo "  - Check status: docker-compose ps"
echo ""
echo "�� Next Steps:"
echo "  1. Open the dashboard in your browser"
echo "  2. Explore the API documentation"
echo "  3. Configure your API keys in .env file"
echo "  4. Set up local AI models (see QUICK_START.md)"
echo ""
echo "✅ Deployment completed successfully!"
