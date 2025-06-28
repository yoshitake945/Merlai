#!/bin/bash

# Optimized Docker build script for Merlai
set -e

echo "🐳 Building optimized Docker images for Merlai..."

# Build optimized CPU image
echo "📦 Building optimized CPU image..."
docker build \
    --file docker/Dockerfile.optimized \
    --target production \
    --tag merlai:optimized-cpu \
    --tag ghcr.io/yoshitake945/merlai:optimized-cpu \
    .

# Build lightweight image (no AI models)
echo "⚡ Building lightweight image..."
docker build \
    --file docker/Dockerfile.lightweight \
    --target production \
    --tag merlai:lightweight \
    --tag ghcr.io/yoshitake945/merlai:lightweight \
    .

# Build development image
echo "🔧 Building development image..."
docker build \
    --file docker/Dockerfile.optimized \
    --target development \
    --tag merlai:optimized-dev \
    --tag ghcr.io/yoshitake945/merlai:optimized-dev \
    .

echo "✅ All optimized images built successfully!"

# Show image sizes
echo ""
echo "📊 Image sizes:"
docker images | grep merlai

echo ""
echo "🚀 To run the optimized CPU image:"
echo "docker run -p 8000:8000 merlai:optimized-cpu"
echo ""
echo "⚡ To run the lightweight image:"
echo "docker run -p 8000:8000 merlai:lightweight" 