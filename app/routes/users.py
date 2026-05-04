from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import ReturnDocument
from pymongo.database import Database

from app.database import get_database
from app.models import UserCreate, UserResponse, UserUpdate


router = APIRouter(prefix="/api/users", tags=["users"])


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def serialize_user(document: Dict[str, Any]) -> UserResponse:
    document["_id"] = str(document["_id"])
    return UserResponse.model_validate(document)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_or_get_user(payload: UserCreate, db: Database = Depends(get_database)) -> UserResponse:
    existing = db.users.find_one({"auth0_sub": payload.auth0_sub})
    if existing:
        return serialize_user(existing)

    timestamp = now_utc()
    document = payload.model_dump()
    document["_id"] = payload.auth0_sub
    document["created_at"] = timestamp
    document["updated_at"] = timestamp

    db.users.insert_one(document)
    return serialize_user(document)


@router.get("/{auth0_sub}", response_model=UserResponse)
def get_user(auth0_sub: str, db: Database = Depends(get_database)) -> UserResponse:
    document = db.users.find_one({"auth0_sub": auth0_sub})
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return serialize_user(document)


@router.put("/{auth0_sub}", response_model=UserResponse)
def update_user(auth0_sub: str, payload: UserUpdate, db: Database = Depends(get_database)) -> UserResponse:
    update_data = payload.model_dump(exclude_unset=True)
    update_data["updated_at"] = now_utc()

    document = db.users.find_one_and_update(
        {"auth0_sub": auth0_sub},
        {"$set": update_data, "$setOnInsert": {"_id": auth0_sub, "auth0_sub": auth0_sub, "created_at": now_utc()}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return serialize_user(document)


@router.delete("/{auth0_sub}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(auth0_sub: str, db: Database = Depends(get_database)) -> None:
    db.users.delete_one({"auth0_sub": auth0_sub})

