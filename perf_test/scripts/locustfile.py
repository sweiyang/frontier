"""
Frontier Performance Test Suite (Locust)
=========================================
Usage:
  # Install: pip install locust
  # Headless (CI):
  #   locust -f perf/locustfile.py --headless -u 50 -r 5 -t 60s --host http://localhost:8000
  # Web UI:
  #   locust -f perf/locustfile.py --host http://localhost:8000
  #   then open http://localhost:8089

Environment variables (override defaults):
  PERF_USERNAME   - login username  (default: admin)
  PERF_PASSWORD   - login password  (default: admin123)
  PERF_PROJECT    - project name    (default: test)
  PERF_AGENT_ID   - agent id        (default: 1)
"""

import os
import time
import uuid

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner

# ---------------------------------------------------------------------------
# Config (override via env vars)
# ---------------------------------------------------------------------------
USERNAME = os.getenv("PERF_USERNAME", "admin")
PASSWORD = os.getenv("PERF_PASSWORD", "admin123")
PROJECT = os.getenv("PERF_PROJECT", "test")
AGENT_ID = int(os.getenv("PERF_AGENT_ID", "1"))

# ---------------------------------------------------------------------------
# Shared token cache (one login per worker process)
# ---------------------------------------------------------------------------
_token_cache: dict[str, str] = {}


def get_token(client) -> str:
    """Login once and cache the JWT token for the worker process."""
    key = f"{USERNAME}@{PROJECT}"
    if key not in _token_cache:
        resp = client.post(
            "/login",
            json={"username": USERNAME, "password": PASSWORD},
            name="/login [setup]",
        )
        resp.raise_for_status()
        _token_cache[key] = resp.json()["access_token"]
    return _token_cache[key]


# ---------------------------------------------------------------------------
# Base user class
# ---------------------------------------------------------------------------
class FrontierUser(HttpUser):
    """Base class: authenticates on start and sets project header."""

    wait_time = between(1, 3)
    token: str = ""
    conversation_id: int | None = None

    def on_start(self):
        self.token = get_token(self.client)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Project-Name": PROJECT,
        }
        # Create a dedicated conversation for this virtual user
        self.conversation_id = self._create_conversation()

    def on_stop(self):
        if self.conversation_id:
            self._delete_conversation(self.conversation_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _create_conversation(self) -> int | None:
        resp = self.client.post(
            "/conversations",
            json={"title": f"perf-{uuid.uuid4().hex[:8]}"},
            headers=self.headers,
            name="/conversations [setup]",
        )
        if resp.status_code == 200:
            return resp.json().get("id")
        return None

    def _delete_conversation(self, conv_id: int):
        self.client.delete(
            f"/conversations/{conv_id}",
            headers=self.headers,
            name="/conversations/{id} [teardown]",
        )


# ---------------------------------------------------------------------------
# Scenario 1 — Read-heavy (lightweight, high concurrency)
# ---------------------------------------------------------------------------
class ReadHeavyUser(FrontierUser):
    """
    Simulates users browsing the platform:
    - Check session (/me)
    - List conversations
    - Get project details
    - List agents
    Weight: 60% of total users
    """

    weight = 3

    @task(4)
    def get_me(self):
        self.client.get("/me", headers=self.headers, name="GET /me")

    @task(3)
    def list_conversations(self):
        self.client.get("/conversations", headers=self.headers, name="GET /conversations")

    @task(2)
    def get_project(self):
        self.client.get(f"/projects/{PROJECT}", headers=self.headers, name="GET /projects/{name}")

    @task(1)
    def list_agents(self):
        self.client.get(
            f"/projects/{PROJECT}/agents",
            headers=self.headers,
            name="GET /projects/{name}/agents",
        )


# ---------------------------------------------------------------------------
# Scenario 2 — Chat-heavy (SSE streaming, most critical path)
# ---------------------------------------------------------------------------
class ChatUser(FrontierUser):
    """
    Simulates active chat users sending messages and consuming SSE streams.
    Weight: 30% of total users
    """

    weight = 2
    wait_time = between(3, 8)  # realistic think time between messages

    MESSAGES = [
        "Hello, can you help me?",
        "What can you do?",
        "Summarize the key points.",
        "Give me a brief overview.",
        "What are the next steps?",
    ]

    @task(5)
    def send_chat_message(self):
        if not self.conversation_id:
            self.conversation_id = self._create_conversation()
            if not self.conversation_id:
                return

        message = self.MESSAGES[int(time.time()) % len(self.MESSAGES)]
        start = time.perf_counter()
        first_byte_latency = None
        total_bytes = 0

        with self.client.post(
            "/chat",
            json={
                "message": message,
                "conversation_id": self.conversation_id,
                "agent_id": AGENT_ID,
            },
            headers=self.headers,
            name="POST /chat (stream)",
            stream=True,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Chat returned {resp.status_code}")
                return

            for chunk in resp.iter_content(chunk_size=None):
                if chunk:
                    if first_byte_latency is None:
                        first_byte_latency = time.perf_counter() - start
                    total_bytes += len(chunk)

            elapsed = time.perf_counter() - start
            resp.success()

        # Fire custom events for detailed metrics
        if first_byte_latency is not None:
            events.request.fire(
                request_type="SSE",
                name="chat/time_to_first_byte",
                response_time=first_byte_latency * 1000,
                response_length=0,
                exception=None,
                context={},
            )
        events.request.fire(
            request_type="SSE",
            name="chat/total_stream_time",
            response_time=elapsed * 1000,
            response_length=total_bytes,
            exception=None,
            context={},
        )

    @task(1)
    def get_conversation_messages(self):
        if not self.conversation_id:
            return
        self.client.get(
            f"/conversations/{self.conversation_id}/messages",
            headers=self.headers,
            name="GET /conversations/{id}/messages",
        )


# ---------------------------------------------------------------------------
# Scenario 3 — Write operations (conversation lifecycle)
# ---------------------------------------------------------------------------
class WriteUser(FrontierUser):
    """
    Simulates users creating and deleting conversations.
    Weight: 10% of total users
    """

    weight = 1
    wait_time = between(2, 5)

    @task(3)
    def conversation_lifecycle(self):
        """Create → rename → delete a conversation."""
        # Create
        resp = self.client.post(
            "/conversations",
            json={"title": f"perf-write-{uuid.uuid4().hex[:6]}"},
            headers=self.headers,
            name="POST /conversations",
        )
        if resp.status_code != 200:
            return
        conv_id = resp.json().get("id")
        if not conv_id:
            return

        # Rename
        self.client.patch(
            f"/conversations/{conv_id}",
            json={"title": "renamed-perf-conv"},
            headers=self.headers,
            name="PATCH /conversations/{id}",
        )

        # Delete
        self.client.delete(
            f"/conversations/{conv_id}",
            headers=self.headers,
            name="DELETE /conversations/{id}",
        )

    @task(1)
    def list_conversations(self):
        self.client.get("/conversations", headers=self.headers, name="GET /conversations")
