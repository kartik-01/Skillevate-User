#!/bin/bash

# Skillevate User Service - Startup Script
# This script sets up and starts the Skillevate User microservice

set -e

echo "🚀 Skillevate User Service - Startup"
echo "===================================="

# pydantic-core ships wheels for 3.10–3.13; 3.14 often falls back to Rust builds that fail.
resolve_python() {
    local cmd minor
    for cmd in python3.13 python3.12 python3.11 python3.10; do
        if command -v "$cmd" &>/dev/null; then
            echo "$cmd"
            return 0
        fi
    done
    if command -v python3 &>/dev/null; then
        minor=$(python3 -c 'import sys; print(sys.version_info[1])')
        if [ "${minor:-99}" -le 13 ]; then
            echo python3
            return 0
        fi
    fi
    return 1
}

PYTHON_CMD=""
if ! PYTHON_CMD=$(resolve_python); then
    echo "❌ Need Python 3.10–3.13. Python 3.14 fails: PyO3 (pydantic-core) supports at most 3.13."
    echo "   Install e.g. Homebrew: brew install python@3.12"
    echo "   Then: rm -rf .venv && ./start.sh"
    exit 1
fi

# Drop a stale venv (e.g. created with python3.14) so we recreate with PYTHON_CMD.
if [ -x ".venv/bin/python" ]; then
    existing_minor=$(.venv/bin/python -c 'import sys; print(sys.version_info[1])')
    if [ "${existing_minor:-99}" -ge 14 ]; then
        echo "♻️  Removing .venv (Python 3.${existing_minor}: pydantic-core cannot build on this interpreter)."
        rm -rf .venv
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment with $($PYTHON_CMD --version)..."
    "$PYTHON_CMD" -m venv .venv
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

# Reload only on changes to our app code. Uvicorn's watcher receives absolute
# paths from watchfiles, so a relative `--reload-exclude .venv` silently does
# nothing. Pin the watch roots to source files we actually edit.
APP_DIR="$(pwd)"
uvicorn main:app \
    --reload \
    --reload-dir "$APP_DIR/app" \
    --reload-include "main.py" \
    --reload-exclude "$APP_DIR/.venv" \
    --port 8001 \
    --host 0.0.0.0
