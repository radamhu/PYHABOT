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
    
    print("=" * 60)
    print(f"🚀 Starting PYHABOT API server...")
    print("=" * 60)
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"📚 Documentation: http://{host}:{port}/docs")
    print(f"📖 Alternative docs: http://{host}:{port}/redoc")
    print(f"💚 Health check: http://{host}:{port}/health")
    print(f"🔄 Reload: {reload}")
    print(f"🌍 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"📦 Data path: {os.getenv('PERSISTENT_DATA_PATH', './persistent_data')}")
    print("=" * 60)
    print()
    
    # Run the server
    try:
        uvicorn.run(
            "pyhabot.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()