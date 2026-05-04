import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_mongo_connection, connect_to_mongo, get_database
from app.routes.users import router as users_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Skillevate user identity, profile, and preference microservice",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    connect_to_mongo()
    logger.info("Connected to MongoDB")


@app.on_event("shutdown")
def shutdown() -> None:
    close_mongo_connection()
    logger.info("Closed MongoDB connection")


@app.get("/")
def root() -> dict:
    return {
        "service": settings.app_name,
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "users": "/api/users",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health_check() -> dict:
    db = get_database()
    db.command("ping")
    return {"status": "healthy", "database": "connected"}


app.include_router(users_router)

