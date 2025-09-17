#!/bin/bash

# RoboGrammar Quick Start Script
# Builds Docker image and starts API server

set -e  # Exit on any error

echo "🤖 RoboGrammar Quick Start"
echo "========================="

# Stop and remove existing container if it exists
echo "🧹 Cleaning up existing containers..."
docker stop robogrammar_api 2>/dev/null || true
docker rm robogrammar_api 2>/dev/null || true

# Build Docker image
echo "🔨 Building Docker image..."
docker buildx build ./ -t robogrammar:latest

# Start API server using Docker Compose
echo "🚀 Starting API server..."
docker-compose up -d

# Wait for API to be ready
echo "⏳ Waiting for API to start..."
sleep 10

# Test API
echo "🔍 Testing API connection..."
if curl -f http://localhost:5555/ping 2>/dev/null; then
    echo "✅ API is running successfully!"
    echo "🌐 Access API at: http://localhost:5555"
    echo ""
    echo "📋 Useful commands:"
    echo "  View logs: docker-compose logs -f"
    echo "  Stop API:  docker-compose down"
    echo "  Restart:   docker-compose up -d --build"
else
    echo "❌ API failed to start. Check logs:"
    echo "  docker-compose logs"
fi