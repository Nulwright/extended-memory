#!/bin/bash

echo "🚀 Starting Extended Sienna Memory (ESM)..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before running again."
    exit 1
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
echo "🔍 Checking service health..."
docker-compose ps

# Show access URLs
echo ""
echo "✅ ESM is starting up!"
echo "🌐 Web Interface: http://localhost:3000"
echo "🔧 API Documentation: http://localhost:8000/docs"
echo "📊 API Health: http://localhost:8000/health"
echo ""
echo "📋 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"