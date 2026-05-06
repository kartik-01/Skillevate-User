"""HTTP routes for the user microservice."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status

logger = logging.getLogger(__name__)

from app.dependencies import get_user_service
from app.models.user import (
    Auth0Profile,
    SyncResult,
    UserPreferencesUpdate,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post(
    "/sync",
    response_model=UserResponse,
    summary="Upsert the authenticated user from their Auth0 profile",
    responses={
        200: {"description": "Existing user refreshed with the latest Auth0 claims"},
        201: {"description": "New user created from the Auth0 profile"},
    },
)
def sync_user(
    profile: Auth0Profile,
    response: Response,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Idempotent endpoint called by the frontend right after login.

    Auth0-sourced fields (name, email, picture, ...) are refreshed on every
    call, while user-set preferences are preserved. The HTTP status discloses
    whether a new document was inserted (201) or an existing one was updated
    (200).
    """

    logger.info("POST /api/users/sync (sub=%s)", profile.sub)
    result: SyncResult = service.sync_from_auth0(profile)
    response.status_code = (
        status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
    )
    return result.user


@router.get(
    "/{auth0_sub}",
    response_model=UserResponse,
    summary="Fetch a user profile by Auth0 subject",
)
def get_user(
    auth0_sub: str,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = service.get(auth0_sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.patch(
    "/{auth0_sub}/preferences",
    response_model=UserResponse,
    summary="Update a user's UI/UX preferences",
)
def update_preferences(
    auth0_sub: str,
    payload: UserPreferencesUpdate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = service.update_preferences(auth0_sub, payload)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.delete(
    "/{auth0_sub}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user account",
)
def delete_user(
    auth0_sub: str,
    service: UserService = Depends(get_user_service),
) -> Response:
    deleted = service.delete(auth0_sub)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
