from .user_router import user_router
from .kb_router import kb_router
from .assistant_router import assistant_router
from .dashboard_router import dashboard_router
from .tool_router import tool_router
from .admin_router import admin_router

__all__ = [
    "user_router",
    "kb_router",
    "assistant_router",
    "dashboard_router",
    "tool_router",
    "admin_router",
]
