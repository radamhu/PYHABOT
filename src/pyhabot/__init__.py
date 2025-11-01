"""
PYHABOT - Async Python bot for monitoring HardverApró classified ads.

This package provides an async bot that monitors HardverApró search result pages,
scrapes ads, tracks new listings and price changes, and sends notifications
via Discord or terminal interface.
"""

__version__ = "0.1.0"
__author__ = "radamhu"
__email__ = "radamhu@example.com"
__description__ = "Async Python bot that monitors HardverApró (Hungarian classified ads site) search result pages"

# Import main components for easier access
try:
    from .app import Pyhabot
    from .config import Config
    from .logging import get_logger
    
    __all__ = [
        "Pyhabot",
        "Config", 
        "get_logger",
        "__version__",
    ]
except ImportError as e:
    # During development, some modules might not be fully implemented yet
    __all__ = ["__version__"]