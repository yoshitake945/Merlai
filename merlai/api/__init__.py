"""
API module for Merlai music generation service.
"""

from .main import app
from .routes import router

__all__ = ["app", "router"]
