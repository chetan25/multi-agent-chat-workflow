"""
API routes for the chat application.
"""

from .thread_routes import router as thread_router
from .chat_routes import router as chat_router
from .upload_routes import router as upload_router
from .legacy_routes import router as legacy_router
from .async_routes import router as async_router
from .user_routes import router as user_router

__all__ = ["thread_router", "chat_router", "upload_router", "legacy_router", "async_router", "user_router"]
