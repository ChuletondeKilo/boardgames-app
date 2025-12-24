"""
Database Engine and Session Management

This module sets up the async SQLAlchemy engine and provides:
1. Database engine configured for async operations
2. Session factory for creating database sessions
3. Declarative base for ORM models
4. Dependency injection function for FastAPI routes

Educational Note: Why Async?
----------------------------
- Async SQLAlchemy allows your FastAPI app to handle multiple requests concurrently
- While one request waits for a database query, other requests can be processed
- This is similar to the async httpx example you saw earlier!
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .settings import settings


# ============================================================================
# PART 1: Create the Async Engine
# ============================================================================
# The engine is the core interface to the database
# - create_async_engine: Creates an async-compatible engine
# - str(settings.url): Converts the PostgresDsn to a string
# - echo: If True, logs all SQL queries (useful for learning!)
# - pool_pre_ping: Tests connections before using them (prevents stale connections)

engine = create_async_engine(
    str(settings.url),
    echo=settings.echo,  # Set to True in .env to see SQL queries
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_pre_ping=True,  # Verify connections are alive before using
)


# ============================================================================
# PART 2: Create the Session Factory
# ============================================================================
# Sessions are how you interact with the database
# - async_sessionmaker: Factory that creates async sessions
# - expire_on_commit=False: Keeps objects accessible after commit
# - class_=AsyncSession: Specifies we want async sessions

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Allows accessing objects after session closes
    autocommit=False,  # We'll explicitly commit transactions
    autoflush=False,  # We'll explicitly flush when needed
)


# ============================================================================
# PART 3: Declarative Base for ORM Models
# ============================================================================
# All database models will inherit from this base class
# This is how SQLAlchemy knows which classes represent database tables

class Base(DeclarativeBase):
    """
    Base class for all ORM models.
    
    Any class that inherits from this will:
    1. Be mapped to a database table
    2. Have automatic type mapping (Python types → SQL types)
    3. Support SQLAlchemy queries
    
    Example usage:
        class User(Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(100))
    """
    pass


# ============================================================================
# PART 4: Dependency Injection for FastAPI
# ============================================================================
# This is a FastAPI "dependency" - a reusable function that provides resources
# to your route handlers

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a database session to FastAPI route handlers.
    
    How it works:
    1. Creates a new session using the session factory
    2. Yields it to the route handler (via FastAPI's Depends)
    3. Automatically closes the session when the request completes
    
    The 'async with' ensures:
    - Session is properly closed even if an exception occurs
    - Resources are cleaned up automatically
    
    Usage in routes:
        @router.get("/games")
        async def get_games(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Game))
            return result.scalars().all()
    
    Educational Note: This is the "Dependency Injection" pattern!
    - FastAPI automatically calls this function for each request
    - The session is injected into your route handler
    - You don't manually create/close sessions - it's automatic!
    """
    async with async_session_maker() as session:
        try:
            yield session  # This is where the route handler runs
        finally:
            await session.close()  # Always cleanup, even on errors


# ============================================================================
# Type Alias for Cleaner Code
# ============================================================================
# This creates a type hint that means "database session from dependency injection"
# Makes your route signatures cleaner and more readable

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]

# Now you can use it like this in your routes:
# async def get_games(db: DatabaseSession):
#     # db is automatically injected!
#     pass


# ============================================================================
# Database Initialization Function
# ============================================================================

async def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This function:
    1. Connects to the database using the async engine
    2. Creates all tables defined by models inheriting from Base
    3. Should be called on application startup
    
    Note: In production, you'd use Alembic for migrations instead!
    """
    async with engine.begin() as conn:
        # Create all tables defined by Base subclasses
        # This is equivalent to running CREATE TABLE for each model
        await conn.run_sync(Base.metadata.create_all)
