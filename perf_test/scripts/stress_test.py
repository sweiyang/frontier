"""
Stress Test — Frontier
=======================
Ramps users up aggressively to find the breaking point.
Uses StepLoadShape to increase load in steps and observe degradation.

Usage:
  locust -f perf/scenarios/stress_test.py --headless --host http://localhost:8000
  # (StepLoadShape controls users/duration automatically)
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from locust import HttpUser, LoadTestShape, between, task

USERNAME = os.getenv("PERF_USERNAME", "admin")
PASSWORD = os.getenv("PERF_PASSWORD", "admin123")
PROJECT = os.getenv("PERF_PROJECT", "test")
AGENT_ID = int(os.getenv("PERF_AGENT_ID", "1"))

_token_cache: dict = {}


def get_token(client) -> str:
    if "token" not in _token_cache:
        resp = client.post("/login", json={"username": USERNAME, "password": PASSWORD}, name="/login [setup]")
        if resp.status_code == 200:
            _token_cache["token"] = resp.json()["access_token"]
        else:
            _token_cache["token"] = ""
    return _token_cache["token"]


class StressUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.token = get_token(self.client)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Project-Name": PROJECT,
        }

    @task(5)
    def get_me(self):
        self.client.get("/me", headers=self.headers, name="GET /me")

    @task(3)
    def list_conversations(self):
        self.client.get("/conversations", headers=self.headers, name="GET /conversations")

    @task(2)
    def get_project(self):
        self.client.get(f"/projects/{PROJECT}", headers=self.headers, name="GET /projects/{name}")


class StepLoadShape(LoadTestShape):
    """
    Step-up load shape:
      Step 1:  10 users  for 30s
      Step 2:  25 users  for 30s
      Step 3:  50 users  for 30s
      Step 4: 100 users  for 30s
      Step 5: 150 users  for 30s  ← likely stress zone
      Step 6: 200 users  for 30s  ← potential breaking point
    Total: ~3 minutes
    """

    steps = [
        {"users": 10,  "spawn_rate": 5,  "duration": 30},
        {"users": 25,  "spawn_rate": 5,  "duration": 60},
        {"users": 50,  "spawn_rate": 10, "duration": 90},
        {"users": 100, "spawn_rate": 10, "duration": 120},
        {"users": 150, "spawn_rate": 20, "duration": 150},
        {"users": 200, "spawn_rate": 20, "duration": 180},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for step in self.steps:
            if run_time < step["duration"]:
                return step["users"], step["spawn_rate"]
        return None  # stop test
