#!/bin/bash
# Startup script for FastAPI service

set -e

# Change to project root
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run with uvicorn
python -m services.api
