"""
Board Games API Router (v1)

This router handles all CRUD operations for board games.

Educational Note: What is CRUD?
-------------------------------
CRUD = Create, Read, Update, Delete
These are the four basic operations for any database-backed API:
- CREATE: POST /games (add new game)
- READ: GET /games (list all) and GET /games/{id} (get one)
- UPDATE: PATCH /games/{id} (modify existing)
- DELETE: DELETE /games/{id} (remove)
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.external.database import BoardGame, DatabaseSession

from .schemas import (
    BoardGameCreate,
    BoardGameUpdate,
    BoardGameResponse,
    BoardGameListResponse,
)


# Create the router
# - prefix: All routes in this file will start with /games
# - tags: Groups endpoints in the API documentation
router = APIRouter(prefix="/games", tags=["Board Games"])


# ============================================================================
# CREATE - Add a new board game
# ============================================================================

@router.post(
    "",
    response_model=BoardGameResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new board game",
    description="Add a new board game to the database"
)
async def create_game(
    game_data: BoardGameCreate,
    db: DatabaseSession,
) -> BoardGame:
    """
    Creates a new board game.
    
    How it works:
    1. game_data is automatically validated by Pydantic
    2. We create a SQLAlchemy BoardGame object from the validated data
    3. Add it to the session and commit to the database
    4. Return the created object (FastAPI converts it to BoardGameResponse)
    
    Educational Note: The async/await pattern here:
    - db.add() is synchronous (just adds to session)
    - db.commit() is async (actually writes to database)
    - db.refresh() is async (reloads the object with DB-generated values like id)
    """
    # Convert Pydantic model to SQLAlchemy model
    # .model_dump() converts Pydantic model to a dictionary
    db_game = BoardGame(**game_data.model_dump())
    
    # Add to session (doesn't write to DB yet)
    db.add(db_game)
    
    # Commit the transaction (writes to DB)
    await db.commit()
    
    # Refresh to get DB-generated fields (id, created_at, etc.)
    await db.refresh(db_game)
    
    return db_game


# ============================================================================
# READ - Get all board games (with optional pagination)
# ============================================================================

@router.get(
    "",
    response_model=BoardGameListResponse,
    summary="List all board games",
    description="Retrieve a list of all board games with optional pagination"
)
async def get_games(
    skip: int = 0,
    limit: int = 100,
    db: DatabaseSession = None,
) -> BoardGameListResponse:
    """
    Retrieves a paginated list of board games.
    
    Query Parameters:
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return
    
    Educational Note: SQLAlchemy 2.0 query style:
    - select(BoardGame): Creates a SELECT query
    - offset(skip): SQL OFFSET clause (skip N rows)
    - limit(limit): SQL LIMIT clause (return max N rows)
    - await db.execute(): Runs the query asynchronously
    - result.scalars().all(): Extracts the BoardGame objects
    """
    # Query for games with pagination
    query = select(BoardGame).offset(skip).limit(limit)
    result = await db.execute(query)
    games = result.scalars().all()
    
    # Query for total count
    count_query = select(func.count()).select_from(BoardGame)
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return BoardGameListResponse(games=games, total=total)


# ============================================================================
# READ - Get a single board game by ID
# ============================================================================

@router.get(
    "/{game_id}",
    response_model=BoardGameResponse,
    summary="Get a board game by ID",
    description="Retrieve detailed information about a specific board game"
)
async def get_game(
    game_id: int,
    db: DatabaseSession,
) -> BoardGame:
    """
    Retrieves a single board game by ID.
    
    Path Parameter:
    - game_id: The ID of the game to retrieve
    
    Educational Note: db.get()
    --------------------------
    This is a convenience method for getting by primary key:
        db.get(Model, primary_key_value)
    
    Equivalent to:
        result = await db.execute(select(BoardGame).where(BoardGame.id == game_id))
        game = result.scalar_one_or_none()
    """
    game = await db.get(BoardGame, game_id)
    
    if not game:
        # 404 Not Found - resource doesn't exist
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board game with ID {game_id} not found"
        )
    
    return game


# ============================================================================
# UPDATE - Modify an existing board game
# ============================================================================

@router.patch(
    "/{game_id}",
    response_model=BoardGameResponse,
    summary="Update a board game",
    description="Update specific fields of an existing board game"
)
async def update_game(
    game_id: int,
    game_updates: BoardGameUpdate,
    db: DatabaseSession,
) -> BoardGame:
    """
    Updates an existing board game.
    
    How it works:
    1. Find the game in the database
    2. Update only the fields that were provided (exclude_unset=True)
    3. Commit the changes
    4. Return the updated game
    
    Educational Note: exclude_unset=True
    ------------------------------------
    This only includes fields that were actually set in the request.
    Without it, all optional fields would be set to None!
    
    Example:
        PATCH /games/1 {"name": "New Name"}
        
        With exclude_unset=True:
            updates = {"name": "New Name"}  ✓ Only update name
        
        Without it:
            updates = {"name": "New Name", "description": None, ...}  ✗ Clears other fields!
    """
    # Find the game
    game = await db.get(BoardGame, game_id)
    
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board game with ID {game_id} not found"
        )
    
    # Update fields that were provided
    update_data = game_updates.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(game, field, value)
    
    # Commit changes
    await db.commit()
    await db.refresh(game)
    
    return game


# ============================================================================
# DELETE - Remove a board game
# ============================================================================

@router.delete(
    "/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a board game",
    description="Remove a board game from the database"
)
async def delete_game(
    game_id: int,
    db: DatabaseSession,
) -> None:
    """
    Deletes a board game.
    
    Educational Note: 204 No Content
    ---------------------------------
    Status code 204 means "success, but no response body"
    This is the standard for DELETE operations - the resource is gone,
    so there's nothing to return!
    
    FastAPI will automatically:
    - Return status 204
    - Send an empty response body
    """
    game = await db.get(BoardGame, game_id)
    
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board game with ID {game_id} not found"
        )
    
    await db.delete(game)
    await db.commit()
