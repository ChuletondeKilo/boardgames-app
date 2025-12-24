"""
Pydantic Schemas (DTOs - Data Transfer Objects)

These are the request/response models for your API endpoints.

Educational Note: Why separate from SQLAlchemy models?
------------------------------------------------------
1. Security: You can hide internal fields (like passwords, internal IDs)
2. Validation: Pydantic validates incoming data automatically
3. Documentation: FastAPI auto-generates API docs from these
4. Flexibility: API schema can differ from database schema

Example: Your database might have 50 columns, but your API
only exposes 10 of them. Or you might combine multiple database
tables into one API response.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Base Schema - Shared Fields
# ============================================================================

class BoardGameBase(BaseModel):
    """
    Base schema with fields common to all BoardGame schemas.
    
    This is reused by Create, Update, and Response schemas
    to avoid repetition (DRY principle).
    """
    name: str = Field(
        ...,  # ... means required
        min_length=1,
        max_length=200,
        description="Name of the board game"
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed description of the game"
    )
    min_players: int = Field(
        ...,
        ge=1,  # Greater than or equal to 1
        le=100,
        description="Minimum number of players"
    )
    max_players: int = Field(
        ...,
        ge=1,
        le=100,
        description="Maximum number of players"
    )
    min_playtime: Optional[int] = Field(
        default=None,
        ge=1,
        description="Minimum playtime in minutes"
    )
    max_playtime: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum playtime in minutes"
    )
    year_published: Optional[int] = Field(
        default=None,
        ge=1900,
        le=2100,
        description="Year the game was published"
    )
    rating: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="Average rating (0-10)"
    )


# ============================================================================
# Create Schema - For POST requests
# ============================================================================

class BoardGameCreate(BoardGameBase):
    """
    Schema for creating a new board game.
    
    Inherits all fields from BoardGameBase.
    No additional fields needed - just the game data, no ID or timestamps.
    
    Usage in endpoint:
        @router.post("/games")
        async def create_game(game: BoardGameCreate, db: DatabaseSession):
            ...
    """
    pass


# ============================================================================
# Update Schema - For PUT/PATCH requests
# ============================================================================

class BoardGameUpdate(BaseModel):
    """
    Schema for updating an existing board game.
    
    All fields are optional - you can update just one field if you want!
    This is different from Create where some fields are required.
    
    Usage in endpoint:
        @router.patch("/games/{game_id}")
        async def update_game(
            game_id: int,
            updates: BoardGameUpdate,
            db: DatabaseSession
        ):
            ...
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    min_players: Optional[int] = Field(default=None, ge=1, le=100)
    max_players: Optional[int] = Field(default=None, ge=1, le=100)
    min_playtime: Optional[int] = Field(default=None, ge=1)
    max_playtime: Optional[int] = Field(default=None, ge=1)
    year_published: Optional[int] = Field(default=None, ge=1900, le=2100)
    rating: Optional[float] = Field(default=None, ge=0.0, le=10.0)


# ============================================================================
# Response Schema - For GET requests
# ============================================================================

class BoardGameResponse(BoardGameBase):
    """
    Schema for board game responses (what the API returns).
    
    This includes all the data from the database, including:
    - id: Auto-generated primary key
    - created_at: When the record was created
    - updated_at: When the record was last modified
    
    The magic: model_config with from_attributes=True
    -----------------------------------------------
    This allows Pydantic to read data from SQLAlchemy ORM objects!
    
    Without it:
        game = BoardGame(name="Catan")  # SQLAlchemy model
        response = BoardGameResponse(**game)  # ERROR!
    
    With it:
        game = BoardGame(name="Catan")  # SQLAlchemy model
        response = BoardGameResponse.model_validate(game)  # Works!
    
    FastAPI does this conversion automatically.
    """
    
    # Additional fields that come from the database
    id: int = Field(description="Unique identifier")
    created_at: datetime = Field(description="When the game was added")
    updated_at: datetime = Field(description="When the game was last updated")
    
    # Configuration for Pydantic v2
    # from_attributes=True allows creating from SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# List Response - For paginated results
# ============================================================================

class BoardGameListResponse(BaseModel):
    """
    Response schema for listing multiple games.
    
    This is useful for pagination and metadata.
    Instead of just returning a list of games, we can include:
    - Total count
    - Current page
    - Has more results?
    """
    games: list[BoardGameResponse] = Field(description="List of board games")
    total: int = Field(description="Total number of games in database")
    
    model_config = ConfigDict(from_attributes=True)
