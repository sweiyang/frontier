"""
Soak Test — Frontier
=====================
Sustained load at moderate concurrency for an extended period.
Detects memory leaks, connection pool exhaustion, and gradual degradation.

Usage:
  locust -f perf/scenarios/soak_test.py --headless -u 30 -r 3 -t 30m --host http://localhost:8000
"""

import os
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from locust import HttpUser, between, events, task

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


class SoakUser(HttpUser):
    """
    Realistic mixed workload held for a long duration.
    Rotates through conversations to simulate real usage patterns.
    """

    wait_time = between(2, 6)
    MAX_CONVERSATIONS = 3  # keep a small pool per user

    def on_start(self):
        self.token = get_token(self.client)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Project-Name": PROJECT,
        }
        self.conversation_pool: list[int] = []
        # Pre-create a few conversations
        for _ in range(self.MAX_CONVERSATIONS):
            conv_id = self._create_conversation()
            if conv_id:
                self.conversation_pool.append(conv_id)

    def on_stop(self):
        for conv_id in self.conversation_pool:
            self.client.delete(
                f"/conversations/{conv_id}",
                headers=self.headers,
                name="/conversations/{id} [teardown]",
            )

    def _create_conversation(self) -> int | None:
        resp = self.client.post(
            "/conversations",
            json={"title": f"soak-{uuid.uuid4().hex[:6]}"},
            headers=self.headers,
            name="POST /conversations [setup]",
        )
        if resp.status_code == 200:
            return resp.json().get("id")
        return None

    def _get_conversation(self) -> int | None:
        if not self.conversation_pool:
            conv_id = self._create_conversation()
            if conv_id:
                self.conversation_pool.append(conv_id)
        return self.conversation_pool[int(time.time()) % len(self.conversation_pool)] if self.conversation_pool else None

    @task(4)
    def get_me(self):
        self.client.get("/me", headers=self.headers, name="GET /me")

    @task(3)
    def list_conversations(self):
        self.client.get("/conversations", headers=self.headers, name="GET /conversations")

    @task(2)
    def get_project(self):
        self.client.get(f"/projects/{PROJECT}", headers=self.headers, name="GET /projects/{name}")

    @task(2)
    def get_messages(self):
        conv_id = self._get_conversation()
        if conv_id:
            self.client.get(
                f"/conversations/{conv_id}/messages",
                headers=self.headers,
                name="GET /conversations/{id}/messages",
            )

    @task(1)
    def rotate_conversation(self):
        """Periodically create a new conversation and drop the oldest."""
        new_id = self._create_conversation()
        if new_id:
            if len(self.conversation_pool) >= self.MAX_CONVERSATIONS:
                old_id = self.conversation_pool.pop(0)
                self.client.delete(
                    f"/conversations/{old_id}",
                    headers=self.headers,
                    name="DELETE /conversations/{id}",
                )
            self.conversation_pool.append(new_id)
