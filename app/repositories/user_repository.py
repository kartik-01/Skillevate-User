"""Data-access layer for the `users` collection.

Routes and services interact with this repository instead of touching PyMongo
directly. The repository is responsible for:

  * Translating between Mongo's `_id` and the API-friendly `auth0_sub` name.
  * Stripping legacy fields from previous schemas so Pydantic gets a clean
    document to validate.
  * Enforcing the rule that Auth0-sourced fields never overwrite user-set
    preferences during a re-sync.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Tuple

from pymongo import ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database

from app.models.user import Auth0Profile, UserPreferences, UserPreferencesUpdate

# Fields written by older revisions of this service that no longer belong in
# the users collection. Domain-specific data lives in its own collection now.
# `auth0_sub` was duplicated alongside `_id`; it is removed in `_to_response_dict`
# *before* this list is applied via `out.pop("_id")`, so we don't include it here.
_LEGACY_FIELDS = ("target_role", "metadata", "username", "onboarding_completed")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _strip_none(values: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


class UserRepository:
    def __init__(self, db: Database) -> None:
        self._collection: Collection = db["users"]

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_response_dict(document: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Normalise a Mongo document into the shape `UserResponse` expects."""

        if document is None:
            return None

        out = dict(document)
        out["auth0_sub"] = out.pop("_id")

        prefs = out.get("preferences")
        if not isinstance(prefs, dict):
            # Older revisions stored preferences as `List[str]` for skill
            # affinities; that data has migrated to the recommendation service,
            # so fall back to defaults here.
            out["preferences"] = {}

        _drop_keys(out, _LEGACY_FIELDS)
        return out

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def find_by_sub(self, auth0_sub: str) -> Optional[Dict[str, Any]]:
        return self._to_response_dict(self._collection.find_one({"_id": auth0_sub}))

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def upsert_from_auth0(self, profile: Auth0Profile) -> Tuple[Dict[str, Any], bool]:
        """Insert or refresh a user from an Auth0 profile.

        Only Auth0-sourced fields are `$set` on each call. `preferences` and
        `created_at` are written via `$setOnInsert`, so user-modified
        preferences survive subsequent logins.
        """

        now = _utcnow()
        auth0_fields = _strip_none(
            {
                "email": profile.email,
                "email_verified": profile.email_verified,
                "name": profile.name,
                "given_name": profile.given_name,
                "family_name": profile.family_name,
                "nickname": profile.nickname,
                "picture": profile.picture,
                "locale": profile.locale,
                "auth0_updated_at": profile.updated_at,
            }
        )

        existing = self._collection.find_one({"_id": profile.sub}, {"_id": 1})
        created = existing is None

        update: Dict[str, Any] = {
            "$set": {**auth0_fields, "last_login_at": now, "updated_at": now},
            "$setOnInsert": {
                "preferences": UserPreferences().model_dump(),
                "created_at": now,
            },
        }

        self._collection.update_one({"_id": profile.sub}, update, upsert=True)
        document = self._collection.find_one({"_id": profile.sub})
        if document is None:
            raise RuntimeError("User upsert succeeded but document could not be re-read")

        return self._to_response_dict(document), created  # type: ignore[return-value]

    def update_preferences(
        self,
        auth0_sub: str,
        update: UserPreferencesUpdate,
    ) -> Optional[Dict[str, Any]]:
        """Patch the nested `preferences` subdocument."""

        deltas = update.model_dump(exclude_unset=True)
        if not deltas:
            return self.find_by_sub(auth0_sub)

        set_doc: Dict[str, Any] = {"updated_at": _utcnow()}
        for key, value in deltas.items():
            # `notifications` is itself a nested document; replace it as a
            # whole so callers can safely opt out of channels without
            # round-tripping the entire payload.
            set_doc[f"preferences.{key}"] = value

        document = self._collection.find_one_and_update(
            {"_id": auth0_sub},
            {"$set": set_doc},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_response_dict(document)

    def delete_user(self, auth0_sub: str) -> bool:
        result = self._collection.delete_one({"_id": auth0_sub})
        return result.deleted_count == 1


def _drop_keys(document: Dict[str, Any], keys: Iterable[str]) -> None:
    for key in keys:
        document.pop(key, None)
