"""
API Version 1 Router

This module aggregates all v1 API endpoints into a single router.

Educational Note: API Versioning
---------------------------------
Why version your API?
- Allows making breaking changes without affecting existing clients
- Clients can migrate to new versions at their own pace
- You can run v1 and v2 simultaneously

Example URL structure:
- /api/v1/games  (version 1)
- /api/v2/games  (version 2, maybe with different response format)
"""

from fastapi import APIRouter

from .boardgames import router as boardgames_router

# Create the main v1 router
# All routes from sub-routers will be prefixed with whatever is set in main.py
v1_router = APIRouter()

# Include all v1 routers
v1_router.include_router(boardgames_router)

# As you add more features, include them here:
# v1_router.include_router(users_router)
# v1_router.include_router(reviews_router)
# v1_router.include_router(auth_router)
