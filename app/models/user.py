"""Pydantic schemas for the user microservice.

The `users` collection intentionally holds only generic, cross-cutting profile
data:

  * Identity claims sourced from Auth0 (name, email, picture URL, locale, ...).
  * UI/UX preferences that apply across the whole product (theme, language,
    notification opt-ins).

Anything domain-specific (skill targets, completed courses, analyses, journey
state, ...) lives in the corresponding domain collection and is keyed by the
same `auth0_sub` value.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


Theme = Literal["light", "dark", "system"]


class NotificationPreferences(BaseModel):
    """Per-channel notification opt-ins."""

    email: bool = True
    in_app: bool = True


class UserPreferences(BaseModel):
    """Cross-cutting, user-scoped UI/UX preferences."""

    theme: Theme = "system"
    language: str = Field(default="en", min_length=2, max_length=10)
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)


class UserPreferencesUpdate(BaseModel):
    """Partial-update payload for `UserPreferences`.

    Any field left unset is preserved server-side, so the frontend only needs
    to send the keys it actually wants to change.
    """

    model_config = ConfigDict(extra="forbid")

    theme: Optional[Theme] = None
    language: Optional[str] = Field(default=None, min_length=2, max_length=10)
    notifications: Optional[NotificationPreferences] = None


class Auth0Profile(BaseModel):
    """Subset of the Auth0 ID-token claims we mirror into our `users` collection.

    The frontend forwards these straight from `useAuth0().user` after a
    successful login. `sub` is Auth0's stable identifier for the user and is
    used as the MongoDB document `_id`, so we never store the same value twice.
    Unknown claims are ignored to stay forward-compatible with new Auth0 fields.
    """

    model_config = ConfigDict(extra="ignore")

    sub: str = Field(..., min_length=1, description="Stable Auth0 subject; becomes the MongoDB _id")
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    nickname: Optional[str] = None
    picture: Optional[str] = Field(
        default=None,
        description="Profile picture URL hosted by Auth0 / the upstream IDP",
    )
    locale: Optional[str] = None
    updated_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp from Auth0 indicating when the profile was last updated upstream",
    )


class UserResponse(BaseModel):
    """API representation of a user document.

    The MongoDB `_id` is the Auth0 subject; we expose it as `auth0_sub` here so
    consumers see the friendlier name without us duplicating the value on disk.
    """

    auth0_sub: str
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    nickname: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None
    auth0_updated_at: Optional[str] = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SyncResult(BaseModel):
    """Outcome of a `POST /api/users/sync` call."""

    created: bool
    user: UserResponse
