"""
API runner script for PYHABOT.

This script provides a way to run the FastAPI server
for development and testing.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyhabot.api.main import app

def main():
    """Run the FastAPI application."""
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    print(f"🚀 Starting PYHABOT API server...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"📚 Documentation: http://{host}:{port}/docs")
    print(f"📖 Alternative docs: http://{host}:{port}/redoc")
    print(f"🔄 Reload: {reload}")
    print()
    
    # Run the server
    uvicorn.run(
        "pyhabot.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()