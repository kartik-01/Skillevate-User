"""FastAPI dependency wiring.

Centralises construction of repositories and services so route handlers stay
declarative.
"""

from __future__ import annotations

from fastapi import Depends
from pymongo.database import Database

from app.db.client import get_database
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


def get_user_repository(db: Database = Depends(get_database)) -> UserRepository:
    return UserRepository(db)


def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)
