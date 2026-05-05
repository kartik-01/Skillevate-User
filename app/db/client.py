"""MongoDB connection lifecycle for the user service.

A single `MongoClient` is created on app startup and shared across requests.
The client and its database handle are kept as module-level singletons so
FastAPI dependencies can grab them cheaply without re-establishing TCP/TLS
connections per request.
"""

from __future__ import annotations

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None
_database: Optional[Database] = None


def connect() -> Database:
    """Open the singleton MongoDB connection and ensure required indexes exist."""

    global _client, _database

    settings = get_settings()
    if not settings.mongodb_uri:
        raise RuntimeError("MONGODB_URI is not configured")

    _client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    _database = _client[settings.mongodb_database]
    _client.admin.command("ping")
    logger.info("Connected to MongoDB database '%s'", settings.mongodb_database)

    # Imported lazily to keep this module free of circular imports during
    # application bootstrap.
    from app.db.indexes import ensure_indexes

    ensure_indexes(_database)
    return _database


def close() -> None:
    """Tear down the MongoDB connection on app shutdown."""

    global _client, _database

    if _client is not None:
        _client.close()
        logger.info("Closed MongoDB connection")
    _client = None
    _database = None


def get_database() -> Database:
    """FastAPI dependency that returns the active database handle."""

    if _database is None:
        raise RuntimeError("MongoDB is not connected")
    return _database
