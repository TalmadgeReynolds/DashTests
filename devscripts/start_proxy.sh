#!/bin/bash
# Start the proxy server

# Change to project root directory
cd "$(dirname "$0")/.."

echo "Starting proxy server on port 3001..."
node proxy-server.js