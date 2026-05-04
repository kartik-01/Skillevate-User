#!/bin/bash

# Skillevate User Service - Startup Script
# This script sets up and starts the Skillevate User microservice

set -e

echo "🚀 Skillevate User Service - Startup"
echo "===================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚙️  Creating .env file from .env.example..."
        cp .env.example .env
        echo "   ⚠️  WARNING: Please update .env with your actual MongoDB URI"
    else
        echo "❌ .env.example not found"
        exit 1
    fi
fi

# Start the service
echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting Skillevate User Service..."
echo "   - Local: http://localhost:8001"
echo "   - API Docs: http://localhost:8001/docs"
echo "   - Health: http://localhost:8001/health"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

uvicorn main:app --reload --port 8001 --host 0.0.0.0
