from .user_router import user_router
from .kb_router import kb_router, DOWNLOAD_FOLDER
from .assistant_router import assistant_router
from .dashboard_router import dashboard_router

__all__ = [
    "user_router",
    "kb_router",
    "assistant_router",
    "dashboard_router",
    DOWNLOAD_FOLDER,
]
