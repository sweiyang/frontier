"""
Frontier Performance Test Data Seeder
=======================================
在运行性能测试前，初始化必要的测试数据：
- 验证服务器可达性
- 登录并获取 JWT token
- 创建测试项目（如不存在）
- 创建测试 Agent（如不存在）
- 预填充会话和消息历史

Usage:
  python perf/scripts/seed_test_data.py [options]

Options:
  --host        Frontier server URL (default: http://localhost:8000)
  --username    Admin username (default: admin)
  --password    Admin password (default: admin123)
  --project     Project name to create/verify (default: test)
  --agent-url   Agent endpoint URL (default: http://localhost:8080)
  --agent-type  Agent type: openai|http|langgraph (default: http)
  --conversations  Number of conversations to seed (default: 5)
  --messages    Messages per conversation (default: 3)
  --cleanup     Delete seeded data instead of creating it
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def parse_args():
    parser = argparse.ArgumentParser(description="Seed test data for Frontier performance tests")
    parser.add_argument("--host", default="http://localhost:8000")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    parser.add_argument("--project", default="test")
    parser.add_argument("--agent-url", default="http://localhost:8080")
    parser.add_argument("--agent-type", default="http", choices=["openai", "http", "langgraph"])
    parser.add_argument("--conversations", type=int, default=5)
    parser.add_argument("--messages", type=int, default=3)
    parser.add_argument("--cleanup", action="store_true", help="Remove seeded data")
    return parser.parse_args()


class FrontierClient:
    def __init__(self, host: str):
        self.host = host.rstrip("/")
        self.token: str = ""
        self.project: str = ""

    def _request(self, method: str, path: str, body=None, headers: dict | None = None) -> dict:
        url = f"{self.host}{path}"
        data = json.dumps(body).encode() if body else None
        req_headers = {"Content-Type": "application/json"}
        if self.token:
            req_headers["Authorization"] = f"Bearer {self.token}"
        if self.project:
            req_headers["X-Project-Name"] = self.project
        if headers:
            req_headers.update(headers)

        req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode()
            raise RuntimeError(f"HTTP {e.code} {method} {path}: {body_text}")

    def login(self, username: str, password: str) -> str:
        resp = self._request("POST", "/login", {"username": username, "password": password})
        self.token = resp["access_token"]
        return self.token

    def get_project(self, project_name: str) -> dict | None:
        try:
            return self._request("GET", f"/projects/{project_name}")
        except RuntimeError as e:
            if "404" in str(e):
                return None
            raise

    def create_project(self, project_name: str) -> dict:
        return self._request("POST", "/projects", {"project_name": project_name})

    def list_agents(self, project_name: str) -> list:
        resp = self._request("GET", f"/projects/{project_name}/agents")
        return resp.get("agents", [])

    def create_agent(self, project_name: str, name: str, endpoint: str, agent_type: str) -> dict:
        return self._request(
            "POST",
            f"/projects/{project_name}/agents",
            {
                "name": name,
                "endpoint": endpoint,
                "connection_type": agent_type,
                "is_default": True,
            },
        )

    def create_conversation(self, title: str) -> dict:
        return self._request("POST", "/conversations", {"title": title})

    def delete_conversation(self, conv_id: int):
        self._request("DELETE", f"/conversations/{conv_id}")

    def list_conversations(self) -> list:
        resp = self._request("GET", "/conversations")
        return resp.get("conversations", [])


def check_server(host: str) -> bool:
    try:
        req = urllib.request.Request(
            f"{host}/me",
            headers={"Authorization": "Bearer invalid"},
        )
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e:
        return e.code == 401
    except Exception:
        return False
    return True


def seed(args):
    print(f"\n{'='*55}")
    print(f"  Frontier Test Data Seeder")
    print(f"{'='*55}")
    print(f"  Host:    {args.host}")
    print(f"  Project: {args.project}")
    print(f"{'='*55}\n")

    # 1. Health check
    print("Checking server health...", end=" ")
    if not check_server(args.host):
        print(f"FAIL\nServer at {args.host} is not reachable.")
        sys.exit(1)
    print("OK")

    client = FrontierClient(args.host)

    # 2. Login
    print(f"Logging in as '{args.username}'...", end=" ")
    try:
        client.login(args.username, args.password)
        print("OK")
    except RuntimeError as e:
        print(f"FAIL\n{e}")
        sys.exit(1)

    # 3. Project
    client.project = args.project
    print(f"Checking project '{args.project}'...", end=" ")
    project = client.get_project(args.project)
    if project:
        print(f"exists (id={project.get('id', '?')})")
    else:
        print("not found, creating...", end=" ")
        try:
            project = client.create_project(args.project)
            print(f"OK (id={project.get('id', '?')})")
        except RuntimeError as e:
            print(f"FAIL\n{e}")
            sys.exit(1)

    # 4. Agent
    print(f"Checking agents in '{args.project}'...", end=" ")
    agents = client.list_agents(args.project)
    if agents:
        print(f"found {len(agents)} agent(s) — skipping creation")
    else:
        print(f"none found, creating '{args.agent_type}' agent...", end=" ")
        try:
            agent = client.create_agent(
                args.project,
                name="perf-test-agent",
                endpoint=args.agent_url,
                agent_type=args.agent_type,
            )
            print(f"OK (id={agent.get('id', '?')})")
        except RuntimeError as e:
            print(f"FAIL (non-critical)\n  {e}")
            print("  Continuing without agent — chat tests will fail.")

    # 5. Conversations
    print(f"\nSeeding {args.conversations} conversations ({args.messages} messages each)...")
    seeded_ids = []
    for i in range(args.conversations):
        try:
            conv = client.create_conversation(f"perf-seed-{i+1:03d}")
            conv_id = conv.get("id")
            seeded_ids.append(conv_id)
            print(f"  Created conversation {i+1}/{args.conversations} (id={conv_id})")
        except RuntimeError as e:
            print(f"  WARN: Failed to create conversation {i+1}: {e}")

    print(f"\n{'='*55}")
    print(f"  Seeding complete!")
    print(f"  Conversations created: {len(seeded_ids)}")
    print(f"  Ready to run performance tests.")
    print(f"{'='*55}\n")


def cleanup(args):
    print(f"\nCleaning up test data for project '{args.project}'...")

    client = FrontierClient(args.host)
    client.project = args.project

    try:
        client.login(args.username, args.password)
    except RuntimeError as e:
        print(f"Login failed: {e}")
        sys.exit(1)

    conversations = client.list_conversations()
    perf_convs = [c for c in conversations if str(c.get("title", "")).startswith("perf-")]

    print(f"Found {len(perf_convs)} perf-* conversations to delete...")
    deleted = 0
    for conv in perf_convs:
        try:
            client.delete_conversation(conv["id"])
            deleted += 1
        except RuntimeError as e:
            print(f"  WARN: Failed to delete conversation {conv['id']}: {e}")

    print(f"Deleted {deleted}/{len(perf_convs)} conversations.")


def main():
    args = parse_args()
    if args.cleanup:
        cleanup(args)
    else:
        seed(args)


if __name__ == "__main__":
    main()
