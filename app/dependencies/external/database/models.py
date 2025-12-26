"""
Database ORM Models

This module contains all SQLAlchemy ORM models (database tables).

Educational Note: SQLAlchemy ORM
--------------------------------
ORM = Object-Relational Mapping
- You define Python classes that represent database tables
- SQLAlchemy handles all the SQL for you
- You work with Python objects instead of writing raw SQL

Example: Instead of writing:
    SELECT * FROM boardgames WHERE id = 1

You write:
    game = await db.get(BoardGame, 1)
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class BoardGame(Base):
    """
    BoardGame model representing the 'boardgames' table.
    
    This demonstrates the modern SQLAlchemy 2.0 style using:
    - Mapped[type]: Type hints that SQLAlchemy uses to determine column types
    - mapped_column(): Creates database columns with constraints
    
    Table Structure:
    ----------------
    CREATE TABLE boardgames (
        id SERIAL PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        min_players INTEGER NOT NULL,
        max_players INTEGER NOT NULL,
        min_playtime INTEGER,
        max_playtime INTEGER,
        year_published INTEGER,
        rating NUMERIC(3, 1),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    __tablename__ = "boardgames"
    
    # Primary Key
    # - auto-increment by default
    # - required for all tables
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Required text fields
    # - String(200): VARCHAR(200) in the database
    # - nullable=False means NOT NULL constraint
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    
    # Optional text field
    # - Text: Unlimited length text field
    # - Optional[] means this can be None (nullable=True is automatic)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Player count
    # - Integer: Standard integer column
    # - Both are required (no Optional[])
    min_players: Mapped[int] = mapped_column(Integer, nullable=False)
    max_players: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Playtime in minutes
    # - Optional: These can be None if not specified
    min_playtime: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_playtime: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Publication year
    year_published: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Rating (e.g., 7.5 out of 10)
    # - NUMERIC(3, 1) allows values like 7.5 (3 digits total, 1 after decimal)
    rating: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    users_games: Mapped["UsersGames"] = relationship(back_populates="boardgame_id")
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<BoardGame(id={self.id}, name='{self.name}')>"


# Add more models as your application grows:
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    surname: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    users_games: Mapped["UsersGames"] = relationship(back_populates="user_id")
  

class UsersGames(Base):
    __tablename__ = "users_games"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    boardgame_id: Mapped[int] = mapped_column(ForeignKey("boardgames.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    boardgame_map: Mapped["BoardGame"] = relationship(back_populates="users_games")
    user_map: Mapped["User"] = relationship(back_populates="users_games")

