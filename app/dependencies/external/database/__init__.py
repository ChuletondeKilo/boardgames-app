"""
Database package exports

This makes it easy to import database components from anywhere in the app:

    from app.external.database import DatabaseSession, Base, BoardGame
    
Instead of:

    from app.external.database.database import DatabaseSession, Base
    from app.external.database.models import BoardGame
"""

from .database import Base, DatabaseSession, get_db, init_db
from .models import BoardGame
from .settings import settings

__all__ = [
    # Database infrastructure
    "Base",
    "DatabaseSession",
    "get_db",
    "init_db",
    "settings",
    # Models
    "BoardGame",
]
