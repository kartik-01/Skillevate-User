from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserCreate(BaseModel):
    auth0_sub: str = Field(..., min_length=1, description="Stable Auth0 user subject")
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    username: Optional[str] = None
    target_role: Optional[str] = None
    preferences: List[str] = Field(default_factory=list)
    onboarding_completed: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    username: Optional[str] = None
    target_role: Optional[str] = None
    preferences: Optional[List[str]] = None
    onboarding_completed: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    auth0_sub: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    username: Optional[str] = None
    target_role: Optional[str] = None
    preferences: List[str] = Field(default_factory=list)
    onboarding_completed: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
