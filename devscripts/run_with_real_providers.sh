#!/bin/bash
# Script to run the backend with real providers instead of mocks

# Export environment variables
export MOCK_PROVIDERS=false

# Change to project root directory
cd "$(dirname "$0")/.."

# Run the application with real providers
echo "Starting application with MOCK_PROVIDERS=false"
python -m backend.main