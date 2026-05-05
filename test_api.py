#!/usr/bin/env python3
"""Smoke tests for the Skillevate User Service API.

Run the service first, then execute this script:

    uvicorn main:app --reload --port 8001
    python test_api.py
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional

import httpx

BASE_URL = "http://localhost:8001"
TIMEOUT = 10.0


def _print_section(title: str) -> None:
    print(f"\n{'=' * 70}\n  {title}\n{'=' * 70}\n")


def _print_request(method: str, path: str, data: Optional[Dict[str, Any]] = None) -> None:
    print(f"📤 {method} {path}")
    if data is not None:
        print(f"   Body: {json.dumps(data, indent=2)}")


def _print_response(status_code: int, payload: Any) -> None:
    emoji = "✅" if 200 <= status_code < 300 else "❌"
    print(f"{emoji} {status_code}")
    if isinstance(payload, (dict, list)):
        print(f"   {json.dumps(payload, indent=2, default=str)}")
    else:
        print(f"   {payload}")


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text


def _build_profile(sub: str) -> Dict[str, Any]:
    """Mirror the shape we receive from `useAuth0().user` on the frontend."""

    handle = sub.split("|")[-1]
    return {
        "sub": sub,
        "email": f"{handle}@example.com",
        "email_verified": True,
        "name": "Jane Doe",
        "given_name": "Jane",
        "family_name": "Doe",
        "nickname": handle,
        "picture": f"https://s.gravatar.com/avatar/{handle}.png",
        "locale": "en",
        "updated_at": "2026-05-05T12:34:56.000Z",
    }


def main() -> int:
    client = httpx.Client(timeout=TIMEOUT, base_url=BASE_URL)
    sub = "auth0|test_user_001"
    failures = 0

    _print_section("Health")
    _print_request("GET", "/health")
    response = client.get("/health")
    _print_response(response.status_code, _safe_json(response))
    failures += 0 if response.status_code == 200 else 1

    _print_section("First sync (expect 201)")
    profile = _build_profile(sub)
    _print_request("POST", "/api/users/sync", profile)
    response = client.post("/api/users/sync", json=profile)
    _print_response(response.status_code, _safe_json(response))
    failures += 0 if response.status_code == 201 else 1

    _print_section("Re-sync same user (expect 200)")
    _print_request("POST", "/api/users/sync", profile)
    response = client.post("/api/users/sync", json=profile)
    _print_response(response.status_code, _safe_json(response))
    failures += 0 if response.status_code == 200 else 1

    _print_section("Get user")
    _print_request("GET", f"/api/users/{sub}")
    response = client.get(f"/api/users/{sub}")
    _print_response(response.status_code, _safe_json(response))
    failures += 0 if response.status_code == 200 else 1

    _print_section("Patch theme preference to dark")
    payload = {"theme": "dark"}
    _print_request("PATCH", f"/api/users/{sub}/preferences", payload)
    response = client.patch(f"/api/users/{sub}/preferences", json=payload)
    _print_response(response.status_code, _safe_json(response))
    failures += 0 if response.status_code == 200 else 1

    _print_section("Patch notifications channel")
    payload = {"notifications": {"email": False, "in_app": True}}
    _print_request("PATCH", f"/api/users/{sub}/preferences", payload)
    response = client.patch(f"/api/users/{sub}/preferences", json=payload)
    _print_response(response.status_code, _safe_json(response))
    failures += 0 if response.status_code == 200 else 1

    _print_section("Get unknown user (expect 404)")
    _print_request("GET", "/api/users/auth0|does_not_exist")
    response = client.get("/api/users/auth0|does_not_exist")
    _print_response(response.status_code, _safe_json(response))
    failures += 0 if response.status_code == 404 else 1

    _print_section("Delete user (expect 204)")
    _print_request("DELETE", f"/api/users/{sub}")
    response = client.delete(f"/api/users/{sub}")
    _print_response(
        response.status_code,
        "No content" if response.status_code == 204 else _safe_json(response),
    )
    failures += 0 if response.status_code == 204 else 1

    print()
    if failures:
        print(f"❌ {failures} test(s) failed")
    else:
        print("✅ All smoke tests passed")
    client.close()
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except httpx.HTTPError as exc:
        print(f"\n❌ HTTP error: {exc}")
        sys.exit(1)
