"""
Auth & RBAC Performance Test — Frontier
=========================================
专项测试认证中间件和权限校验的性能开销：
- JWT Token 签发吞吐量 (POST /login)
- Token 验证延迟 (GET /me 高频调用)
- 无效 Token 拒绝速度 (401 响应延迟)
- 不同角色下相同端点的响应差异

Usage:
  locust -f perf/scenarios/auth_perf_test.py --headless -u 100 -r 10 -t 5m --host http://localhost:8000
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from locust import HttpUser, between, events, task

# Test credentials — configure via env vars
USERS = [
    {"username": os.getenv("PERF_USERNAME", "admin"), "password": os.getenv("PERF_PASSWORD", "admin123")},
    {"username": os.getenv("PERF_USERNAME2", "testuser"), "password": os.getenv("PERF_PASSWORD2", "test123")},
]
PROJECT = os.getenv("PERF_PROJECT", "test")

_token_cache: dict[str, str] = {}


def get_token(client, username: str, password: str) -> str:
    if username not in _token_cache:
        resp = client.post(
            "/login",
            json={"username": username, "password": password},
            name="/login [setup]",
        )
        if resp.status_code == 200:
            _token_cache[username] = resp.json()["access_token"]
        else:
            _token_cache[username] = ""
    return _token_cache[username]


# ---------------------------------------------------------------------------
# Scenario A: Login throughput — measures JWT issuance rate
# ---------------------------------------------------------------------------
class LoginThroughputUser(HttpUser):
    """
    Repeatedly logs in to measure JWT issuance throughput.
    Each task performs a fresh login (no caching).
    """

    weight = 1
    wait_time = between(0.5, 1.5)

    @task
    def login(self):
        cred = USERS[0]
        start = time.perf_counter()
        with self.client.post(
            "/login",
            json={"username": cred["username"], "password": cred["password"]},
            name="POST /login (throughput)",
            catch_response=True,
        ) as resp:
            elapsed = (time.perf_counter() - start) * 1000
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Login failed: {resp.status_code}")


# ---------------------------------------------------------------------------
# Scenario B: Token validation — measures /me latency under load
# ---------------------------------------------------------------------------
class TokenValidationUser(HttpUser):
    """
    Hammers GET /me with a valid token to measure JWT verification overhead.
    """

    weight = 3
    wait_time = between(0.1, 0.5)
    token: str = ""

    def on_start(self):
        cred = USERS[0]
        self.token = get_token(self.client, cred["username"], cred["password"])
        self.valid_headers = {"Authorization": f"Bearer {self.token}"}
        self.invalid_headers = {"Authorization": "Bearer invalid.token.here"}

    @task(8)
    def valid_token_check(self):
        """Valid token — should return 200 quickly."""
        self.client.get("/me", headers=self.valid_headers, name="GET /me (valid token)")

    @task(2)
    def invalid_token_check(self):
        """Invalid token — should return 401 quickly (no DB lookup needed)."""
        with self.client.get(
            "/me",
            headers=self.invalid_headers,
            name="GET /me (invalid token → 401)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 401:
                resp.success()  # 401 is the expected response
            else:
                resp.failure(f"Expected 401, got {resp.status_code}")

    @task(1)
    def missing_token_check(self):
        """No token — should return 401/403 immediately."""
        with self.client.get(
            "/me",
            name="GET /me (no token → 401)",
            catch_response=True,
        ) as resp:
            if resp.status_code in (401, 403):
                resp.success()
            else:
                resp.failure(f"Expected 401/403, got {resp.status_code}")


# ---------------------------------------------------------------------------
# Scenario C: RBAC overhead — same endpoint, different roles
# ---------------------------------------------------------------------------
class RBACOverheadUser(HttpUser):
    """
    Compares response times for the same endpoint accessed by different roles.
    Measures the overhead of RBAC membership checks.
    """

    weight = 2
    wait_time = between(0.5, 2)
    token: str = ""

    def on_start(self):
        cred = USERS[0]
        self.token = get_token(self.client, cred["username"], cred["password"])
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Project-Name": PROJECT,
        }

    @task(3)
    def get_project_as_member(self):
        """Project detail — triggers membership verification."""
        self.client.get(
            f"/projects/{PROJECT}",
            headers=self.headers,
            name="GET /projects/{name} (RBAC check)",
        )

    @task(3)
    def list_conversations_with_project(self):
        """Conversations — triggers project membership check."""
        self.client.get(
            "/conversations",
            headers=self.headers,
            name="GET /conversations (with project header)",
        )

    @task(2)
    def list_conversations_without_project(self):
        """Conversations without project header — no RBAC check."""
        self.client.get(
            "/conversations",
            headers={"Authorization": f"Bearer {self.token}"},
            name="GET /conversations (no project header)",
        )

    @task(1)
    def list_agents_rbac(self):
        """Agent list — triggers full project membership + role check."""
        self.client.get(
            f"/projects/{PROJECT}/agents",
            headers=self.headers,
            name="GET /agents (RBAC check)",
        )
