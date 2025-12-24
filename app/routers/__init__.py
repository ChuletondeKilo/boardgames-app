"""
API Routers

This module exports all API routers for the application.

Educational Note: Router Organization
--------------------------------------
Organizing routers by version allows you to:
1. Keep related endpoints together
2. Version your API properly
3. Easily add new features without cluttering main.py
"""

from .v1 import v1_router

__all__ = ["v1_router"]
