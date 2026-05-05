"""Index management for the `users` collection.

Because `_id` *is* the Auth0 subject we get a unique primary index for free.
We only need secondary indexes for the lookups the service actually performs,
plus a one-time cleanup of the legacy `auth0_sub_1` index from the previous
schema where the subject was duplicated as its own field.
"""

from __future__ import annotations

import logging
from typing import Iterable

from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database

logger = logging.getLogger(__name__)

_LEGACY_INDEXES = ("auth0_sub_1",)


def ensure_indexes(db: Database) -> None:
    users = db["users"]

    _drop_indexes_if_exist(users, _LEGACY_INDEXES)

    users.create_index([("email", ASCENDING)], name="email_1", sparse=True)
    users.create_index([("updated_at", ASCENDING)], name="updated_at_1")
    users.create_index([("last_login_at", ASCENDING)], name="last_login_at_1", sparse=True)


def _drop_indexes_if_exist(collection: Collection, names: Iterable[str]) -> None:
    try:
        existing = {idx["name"] for idx in collection.list_indexes()}
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Unable to enumerate indexes for cleanup: %s", exc)
        return

    for name in names:
        if name in existing:
            try:
                collection.drop_index(name)
                logger.info("Dropped legacy index '%s'", name)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to drop legacy index '%s': %s", name, exc)
