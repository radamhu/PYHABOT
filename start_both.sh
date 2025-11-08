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
echo "  Railway PORT: ${PORT:-not set}"
echo ""

# Railway sets PORT env var - use it if available
if [ ! -z "$PORT" ]; then
    export API_PORT=$PORT
    echo "✅ Using Railway PORT: $PORT"
fi

# Start API FIRST (Railway needs this for health checks)
echo "🌐 Starting API server on port ${API_PORT}..."
export PYTHONPATH="/app/src:$PYTHONPATH"
cd /app && python -u run_api.py &
API_PID=$!
echo "  API PID: $API_PID"

# Wait for API to be ready before continuing
echo "⏳ Waiting for API to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -f -s "http://localhost:${API_PORT}/health" > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi
    attempt=$((attempt + 1))
    if [ $((attempt % 5)) -eq 0 ]; then
        echo "  Still waiting... ($attempt/$max_attempts)"
    fi
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo "⚠️  API health check timeout (may still be starting)"
fi

# Only start CLI if not in api-only mode
if [ "${MODE}" != "api-only" ]; then
    echo "🤖 Starting CLI background process..."
    pyhabot run >> /data/cli.log 2>&1 &
    CLI_PID=$!
    echo "  CLI PID: $CLI_PID"
    echo "  CLI logs: /data/cli.log"
else
    echo "ℹ️  CLI disabled (MODE=${MODE})"
fi

echo ""
echo "✅ PYHABOT started successfully!"
if [ ! -z "$CLI_PID" ]; then
    echo "  CLI running in background (PID: $CLI_PID)"
fi
echo "  API server on http://${API_HOST:-0.0.0.0}:${API_PORT} (PID: $API_PID)"
echo "  API docs: http://${API_HOST:-0.0.0.0}:${API_PORT}/docs"
echo ""
echo "Press Ctrl+C to stop all processes..."

# Monitor the API process (crucial for Railway)
# If API dies, the whole container should exit
while kill -0 $API_PID 2>/dev/null; do
    sleep 5
done

echo "❌ API process died unexpectedly"
cleanup
exit 1