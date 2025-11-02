#!/bin/bash

echo "🚀 Starting PYHABOT with both CLI and API..."

# Function to handle graceful shutdown
cleanup() {
    echo "🛑 Shutting down PYHABOT..."
    
    # Kill background processes
    if [ ! -z "$CLI_PID" ]; then
        echo "Stopping CLI process (PID: $CLI_PID)..."
        kill $CLI_PID 2>/dev/null
    fi
    
    if [ ! -z "$API_PID" ]; then
        echo "Stopping API process (PID: $API_PID)..."
        kill $API_PID 2>/dev/null
    fi
    
    # Wait for processes to exit
    wait $CLI_PID 2>/dev/null
    wait $API_PID 2>/dev/null
    
    echo "✅ PYHABOT shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "📊 Environment Configuration:"
echo "  Mode: ${MODE:-api}"
echo "  API Host: ${API_HOST:-0.0.0.0}"
echo "  API Port: ${API_PORT:-8000}"
echo "  Data Path: ${PERSISTENT_DATA_PATH:-/data}"
echo ""

# Start CLI background process
echo "🤖 Starting CLI background process..."
pyhabot run &
CLI_PID=$!
echo "  CLI PID: $CLI_PID"

# Give CLI a moment to start
sleep 2

# Start API process
echo "🌐 Starting API server..."
# Set PYTHONPATH to use installed packages
export PYTHONPATH="/app/src:$PYTHONPATH"
# Use python directly since poetry already installed dependencies
cd /app && python run_api.py &
API_PID=$!
echo "  API PID: $API_PID"

echo ""
echo "✅ PYHABOT started successfully!"
echo "  CLI running in background (PID: $CLI_PID)"
echo "  API server on http://${API_HOST:-0.0.0.0}:${API_PORT:-8000}"
echo "  API docs: http://${API_HOST:-0.0.0.0}:${API_PORT:-8000}/docs"
echo ""
echo "Press Ctrl+C to stop both processes..."

# Wait for any process to exit
wait $CLI_PID $API_PID