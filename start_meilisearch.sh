#!/bin/bash

echo "🔍 Starting MeiliSearch for Podcast Analyzer"
echo "==========================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if MeiliSearch is already running
if docker ps | grep -q meilisearch; then
    echo "✅ MeiliSearch is already running!"
    docker ps | grep meilisearch
    exit 0
fi

echo "🚀 Starting MeiliSearch container..."

# Create data directory if it doesn't exist
mkdir -p meili_data

# Start MeiliSearch
docker run -d \
  --name podcast-meilisearch \
  -p 7700:7700 \
  -v $(pwd)/meili_data:/meili_data \
  getmeili/meilisearch:latest

# Wait a moment for startup
echo "⏳ Waiting for MeiliSearch to start..."
sleep 3

# Check if it's running
if docker ps | grep -q meilisearch; then
    echo "✅ MeiliSearch started successfully!"
    echo ""
    echo "🌐 MeiliSearch is now available at:"
    echo "   http://localhost:7700"
    echo ""
    echo "🎯 You can now run:"
    echo "   python example.py          # Demo with sample data"
    echo "   python run.py api          # Start the API server"
    echo "   python run.py process URL  # Process real videos"
    echo ""
    echo "📊 To stop MeiliSearch later:"
    echo "   docker stop podcast-meilisearch"
else
    echo "❌ Failed to start MeiliSearch"
    echo "Check Docker logs: docker logs podcast-meilisearch"
    exit 1
fi