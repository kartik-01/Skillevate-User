"""Entry point for the Skillevate user microservice."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.client import close as close_db
from app.db.client import connect as connect_db
from app.db.client import get_database
from app.routes.users import router as users_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    connect_db()
    logger.info("Skillevate user service ready")
    try:
        yield
    finally:
        close_db()


app = FastAPI(
    title=settings.app_name,
    description=(
        "Skillevate user identity and preference microservice. Stores only "
        "generic, cross-cutting profile data sourced from Auth0; domain-"
        "specific data lives in its own collection."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "service": settings.app_name,
        "version": "0.2.0",
        "endpoints": {
            "health": "GET /health",
            "sync_user": "POST /api/users/sync",
            "get_user": "GET /api/users/{auth0_sub}",
            "update_preferences": "PATCH /api/users/{auth0_sub}/preferences",
            "delete_user": "DELETE /api/users/{auth0_sub}",
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["meta"])
def health_check() -> dict:
    db = get_database()
    db.command("ping")
    return {"status": "healthy", "database": "connected"}


app.include_router(users_router)
