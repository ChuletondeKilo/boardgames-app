"""
Board Games API - Main Application

This is the entry point for the FastAPI application.

Educational Note: Application Lifecycle
----------------------------------------
1. Application starts → lifespan events run
2. Database tables are created (if they don't exist)
3. Application is ready to receive requests
4. Each request gets its own database session via dependency injection
5. Session closes automatically after request completes
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.external.database import init_db
from app.routers import v1_router


# ============================================================================
# Lifespan Event Handler
# ============================================================================
# This runs once when the app starts up and once when it shuts down
# Perfect for initializing database connections, creating tables, etc.

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Startup:
    - Initialize database tables
    
    Shutdown:
    - Clean up resources (if needed)
    
    Educational Note: Why use lifespan?
    ------------------------------------
    FastAPI needs to know when to run startup/shutdown code.
    The @asynccontextmanager pattern allows:
    - Code before 'yield' runs at startup
    - Code after 'yield' runs at shutdown
    - Proper async/await support
    """
    # Startup: Create database tables
    print("🚀 Starting up...")
    print("📊 Initializing database...")
    await init_db()
    print("✅ Database initialized!")
    
    yield  # Application runs here
    
    # Shutdown: Cleanup (if needed)
    print("👋 Shutting down...")


# ============================================================================
# Create FastAPI Application
# ============================================================================

app = FastAPI(
    title="Board Games API",
    description="A RESTful API for managing board games",
    version="1.0.0",
    lifespan=lifespan,  # Attach the lifespan handler
)


# ============================================================================
# CORS Middleware
# ============================================================================
# Allow frontend applications to call this API from different domains

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React/Vite dev servers
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# ============================================================================
# Include Routers
# ============================================================================
# All v1 routes will be prefixed with /api/v1

app.include_router(
    v1_router,
    prefix="/api/v1",
    tags=["v1"],
)


# ============================================================================
# Health Check Endpoint
# ============================================================================
# Simple endpoint to verify the API is running

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns simple status to verify the API is running.
    Useful for:
    - Docker health checks
    - Load balancer health checks
    - Monitoring services
    """
    return {"status": "healthy", "message": "Board Games API is running!"}
