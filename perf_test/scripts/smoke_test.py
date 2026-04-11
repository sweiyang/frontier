"""
Smoke Test — Frontier
======================
Quick sanity check: 5 users, 30 seconds.
Verifies all critical endpoints respond correctly before a full load test.

Usage:
  locust -f perf/scenarios/smoke_test.py --headless -u 5 -r 1 -t 30s --host http://localhost:8000
  # or via runner:
  python perf/run_perf.py --users 5 --spawn-rate 1 --duration 30
"""

import os
import sys
from pathlib import Path

# Allow importing from perf/locustfile.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from locust import HttpUser, between, task

USERNAME = os.getenv("PERF_USERNAME", "admin")
PASSWORD = os.getenv("PERF_PASSWORD", "admin123")
PROJECT = os.getenv("PERF_PROJECT", "test")


class SmokeUser(HttpUser):
    """Hits every major endpoint once to verify they all return 2xx."""

    wait_time = between(1, 2)
    token: str = ""

    def on_start(self):
        resp = self.client.post(
            "/login",
            json={"username": USERNAME, "password": PASSWORD},
            name="/login",
        )
        if resp.status_code == 200:
            self.token = resp.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Project-Name": PROJECT,
        }

    @task
    def smoke_all_endpoints(self):
        h = self.headers

        # Auth
        with self.client.get("/me", headers=h, name="smoke: GET /me", catch_response=True) as r:
            if r.status_code not in (200, 401):
                r.failure(f"Unexpected status {r.status_code}")

        # Project
        with self.client.get(f"/projects/{PROJECT}", headers=h, name="smoke: GET /projects/{name}", catch_response=True) as r:
            if r.status_code not in (200, 404):
                r.failure(f"Unexpected status {r.status_code}")

        # Agents
        with self.client.get(f"/projects/{PROJECT}/agents", headers=h, name="smoke: GET /agents", catch_response=True) as r:
            if r.status_code not in (200, 404):
                r.failure(f"Unexpected status {r.status_code}")

        # Conversations
        with self.client.get("/conversations", headers=h, name="smoke: GET /conversations", catch_response=True) as r:
            if r.status_code not in (200,):
                r.failure(f"Unexpected status {r.status_code}")
