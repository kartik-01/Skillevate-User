from __future__ import annotations

from pymongo import ASCENDING, MongoClient
from pymongo.database import Database

from app.config import get_settings


client: MongoClient | None = None
database: Database | None = None


def connect_to_mongo() -> None:
    global client, database

    settings = get_settings()
    if not settings.mongodb_uri:
        raise RuntimeError("MONGODB_URI is not configured")

    client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    database = client[settings.mongodb_database]
    client.admin.command("ping")
    create_indexes(database)


def close_mongo_connection() -> None:
    global client, database

    if client is not None:
        client.close()
    client = None
    database = None


def get_database() -> Database:
    if database is None:
        raise RuntimeError("MongoDB is not connected")
    return database


def create_indexes(db: Database) -> None:
    db.users.create_index([("auth0_sub", ASCENDING)], unique=True)
    db.users.create_index([("email", ASCENDING)], sparse=True)
    db.users.create_index([("updated_at", ASCENDING)])
