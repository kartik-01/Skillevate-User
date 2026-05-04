#!/usr/bin/env python3
"""
Skillevate User Service - API Test Script

This script tests all API endpoints and demonstrates proper usage.
Run this after starting the service with: uvicorn main:app --reload --port 8001
"""

import httpx
import json
from datetime import datetime
from typing import Dict, Any

BASE_URL = "http://localhost:8001"
TIMEOUT = 10.0


class UserServiceTester:
    """Test client for Skillevate User Service API"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(timeout=TIMEOUT)
        self.test_users = []

    def print_section(self, title: str) -> None:
        """Print a formatted section header"""
        print(f"\n{'=' * 70}")
        print(f"  {title}")
        print(f"{'=' * 70}\n")

    def print_request(self, method: str, path: str, data: Dict[str, Any] | None = None) -> None:
        """Print formatted request info"""
        print(f"📤 Request: {method} {path}")
        if data:
            print(f"   Body: {json.dumps(data, indent=2)}")

    def print_response(self, status_code: int, data: Any) -> None:
        """Print formatted response info"""
        status_emoji = "✅" if 200 <= status_code < 300 else "❌"
        print(f"{status_emoji} Response: {status_code}")
        if isinstance(data, dict):
            print(f"   {json.dumps(data, indent=2, default=str)}")
        else:
            print(f"   {data}")

    def test_health_check(self) -> bool:
        """Test 1: Health Check"""
        self.print_section("TEST 1: Health Check")

        self.print_request("GET", "/health")
        response = self.client.get(f"{self.base_url}/health")
        self.print_response(response.status_code, response.json())

        return response.status_code == 200

    def test_root_endpoint(self) -> bool:
        """Test 2: Root Endpoint"""
        self.print_section("TEST 2: Root Endpoint")

        self.print_request("GET", "/")
        response = self.client.get(f"{self.base_url}/")
        self.print_response(response.status_code, response.json())

        return response.status_code == 200

    def test_create_user(self, auth0_sub: str) -> bool:
        """Test 3: Create New User"""
        self.print_section(f"TEST 3: Create New User - {auth0_sub}")

        user_data = {
            "auth0_sub": auth0_sub,
            "email": f"{auth0_sub.split('|')[1]}@example.com",
            "name": "John Doe",
            "picture": "https://example.com/avatar.jpg",
            "given_name": "John",
            "family_name": "Doe",
            "username": "johndoe",
            "target_role": "Senior Frontend Engineer",
            "preferences": ["React", "TypeScript", "GraphQL"],
            "onboarding_completed": False,
        }

        self.print_request("POST", "/api/users", user_data)
        response = self.client.post(f"{self.base_url}/api/users", json=user_data)
        self.print_response(response.status_code, response.json())

        if response.status_code == 201:
            self.test_users.append(response.json())
            return True
        return False

    def test_get_user(self, auth0_sub: str) -> bool:
        """Test 4: Get Existing User"""
        self.print_section(f"TEST 4: Get User - {auth0_sub}")

        self.print_request("GET", f"/api/users/{auth0_sub}")
        response = self.client.get(f"{self.base_url}/api/users/{auth0_sub}")
        self.print_response(response.status_code, response.json())

        return response.status_code == 200

    def test_get_nonexistent_user(self, auth0_sub: str) -> bool:
        """Test 5: Get Non-existent User"""
        self.print_section(f"TEST 5: Get Non-existent User - {auth0_sub}")

        self.print_request("GET", f"/api/users/{auth0_sub}")
        response = self.client.get(f"{self.base_url}/api/users/{auth0_sub}")
        self.print_response(response.status_code, response.json())

        return response.status_code == 404

    def test_update_user(self, auth0_sub: str) -> bool:
        """Test 6: Update User Profile"""
        self.print_section(f"TEST 6: Update User - {auth0_sub}")

        update_data = {
            "target_role": "Staff Frontend Engineer",
            "preferences": ["React", "TypeScript", "GraphQL", "Tailwind CSS", "Next.js"],
            "onboarding_completed": True,
            "metadata": {"theme_preference": "dark", "notifications_enabled": True},
        }

        self.print_request("PUT", f"/api/users/{auth0_sub}", update_data)
        response = self.client.put(f"{self.base_url}/api/users/{auth0_sub}", json=update_data)
        self.print_response(response.status_code, response.json())

        return response.status_code == 200

    def test_partial_update(self, auth0_sub: str) -> bool:
        """Test 7: Partial Update (only some fields)"""
        self.print_section(f"TEST 7: Partial Update - {auth0_sub}")

        partial_data = {
            "metadata": {"login_count": 5, "last_login": datetime.now().isoformat()},
        }

        self.print_request("PUT", f"/api/users/{auth0_sub}", partial_data)
        response = self.client.put(f"{self.base_url}/api/users/{auth0_sub}", json=partial_data)
        self.print_response(response.status_code, response.json())

        return response.status_code == 200

    def test_delete_user(self, auth0_sub: str) -> bool:
        """Test 8: Delete User"""
        self.print_section(f"TEST 8: Delete User - {auth0_sub}")

        self.print_request("DELETE", f"/api/users/{auth0_sub}")
        response = self.client.delete(f"{self.base_url}/api/users/{auth0_sub}")
        self.print_response(response.status_code, "No content" if response.status_code == 204 else response.json())

        return response.status_code == 204

    def test_upsert_behavior(self, auth0_sub: str) -> bool:
        """Test 9: Upsert Behavior (Update or Create)"""
        self.print_section(f"TEST 9: Upsert Behavior - {auth0_sub}")

        new_user_data = {
            "target_role": "Backend Engineer",
            "preferences": ["Python", "FastAPI", "PostgreSQL"],
            "metadata": {"source": "manual_creation"},
        }

        self.print_request("PUT", f"/api/users/{auth0_sub}", new_user_data)
        response = self.client.put(f"{self.base_url}/api/users/{auth0_sub}", json=new_user_data)
        self.print_response(response.status_code, response.json())

        return response.status_code == 200

    def test_duplicate_user_creation(self, auth0_sub: str) -> bool:
        """Test 10: Duplicate User Creation (should return existing user)"""
        self.print_section(f"TEST 10: Duplicate Creation - {auth0_sub}")

        user_data = {
            "auth0_sub": auth0_sub,
            "email": f"{auth0_sub.split('|')[1]}@example.com",
            "name": "Jane Smith",  # Different name
            "target_role": "QA Engineer",  # Different role
            "preferences": ["Testing", "Automation"],
            "onboarding_completed": False,
        }

        self.print_request("POST", "/api/users", user_data)
        response = self.client.post(f"{self.base_url}/api/users", json=user_data)
        self.print_response(response.status_code, response.json())

        return response.status_code == 201

    def run_all_tests(self) -> None:
        """Run all tests"""
        print("\n" + "=" * 70)
        print("  SKILLEVATE USER SERVICE - COMPREHENSIVE API TEST SUITE")
        print("=" * 70)

        results = []

        # Core functionality tests
        results.append(("Health Check", self.test_health_check()))
        results.append(("Root Endpoint", self.test_root_endpoint()))

        # User operations
        test_user_1 = "auth0|test_user_001"
        test_user_2 = "auth0|test_user_002"
        test_user_3 = "auth0|test_user_003"

        results.append((f"Create User 1 ({test_user_1})", self.test_create_user(test_user_1)))
        results.append((f"Get User 1 ({test_user_1})", self.test_get_user(test_user_1)))
        results.append((f"Get Non-existent User", self.test_get_nonexistent_user("auth0|nonexistent")))
        results.append((f"Update User 1 ({test_user_1})", self.test_update_user(test_user_1)))
        results.append((f"Partial Update User 1", self.test_partial_update(test_user_1)))
        results.append((f"Upsert User 2 ({test_user_2})", self.test_upsert_behavior(test_user_2)))
        results.append((f"Create User 3 ({test_user_3})", self.test_create_user(test_user_3)))
        results.append(
            (f"Duplicate Creation (should return existing)", self.test_duplicate_user_creation(test_user_1))
        )
        results.append((f"Delete User 1 ({test_user_1})", self.test_delete_user(test_user_1)))

        # Print summary
        self.print_section("TEST SUMMARY")
        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            emoji = "✅" if result else "❌"
            print(f"{emoji} {test_name}")

        print(f"\n{'=' * 70}")
        print(f"  {passed}/{total} tests passed")
        print(f"{'=' * 70}\n")

        # Cleanup: Delete remaining test users
        print("🧹 Cleaning up test data...")
        for user_data in self.test_users:
            try:
                self.client.delete(f"{self.base_url}/api/users/{user_data['auth0_sub']}")
            except Exception as e:
                print(f"   Note: Could not delete {user_data['auth0_sub']}: {e}")

        self.client.close()

        return passed == total


if __name__ == "__main__":
    import sys

    tester = UserServiceTester()

    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
