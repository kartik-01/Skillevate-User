"""Business logic for the user microservice.

The service layer is intentionally thin; it orchestrates the repository and
converts raw documents into Pydantic models. Keeping it separate from the
routes makes the logic easy to unit-test without spinning up FastAPI.
"""

from __future__ import annotations

from typing import Optional

from app.models.user import (
    Auth0Profile,
    SyncResult,
    UserPreferencesUpdate,
    UserResponse,
)
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def sync_from_auth0(self, profile: Auth0Profile) -> SyncResult:
        document, created = self._repository.upsert_from_auth0(profile)
        return SyncResult(created=created, user=UserResponse.model_validate(document))

    def get(self, auth0_sub: str) -> Optional[UserResponse]:
        document = self._repository.find_by_sub(auth0_sub)
        return UserResponse.model_validate(document) if document else None

    def update_preferences(
        self,
        auth0_sub: str,
        update: UserPreferencesUpdate,
    ) -> Optional[UserResponse]:
        document = self._repository.update_preferences(auth0_sub, update)
        return UserResponse.model_validate(document) if document else None

    def delete(self, auth0_sub: str) -> bool:
        return self._repository.delete_user(auth0_sub)
