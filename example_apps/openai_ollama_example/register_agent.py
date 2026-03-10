#!/usr/bin/env python3
"""
Register the Ollama agent with Conduit via the API.

Usage:
  export CONDUIT_URL=http://localhost:8000
  export PROJECT_NAME=your-project
  export TOKEN=your-jwt-token
  python register_agent.py

Or with optional overrides:
  python register_agent.py --url http://localhost:8000 --project myproject --model mistral
"""

import argparse
import json
import os
import sys

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Register Ollama as an OpenAI agent in Conduit")
    parser.add_argument("--url", default=os.environ.get("CONDUIT_URL", "http://localhost:8000"), help="Conduit API base URL")
    parser.add_argument("--project", default=os.environ.get("PROJECT_NAME"), required=not os.environ.get("PROJECT_NAME"), help="Project name")
    parser.add_argument("--token", default=os.environ.get("TOKEN"), help="JWT token (or set TOKEN)")
    parser.add_argument("--model", default="llama3.2", help="Ollama model name")
    parser.add_argument("--name", default=None, help="Agent display name (default: Ollama (<model>))")
    args = parser.parse_args()

    if not args.token:
        print("Set TOKEN or pass --token. Get a token by logging into Conduit.", file=sys.stderr)
        sys.exit(1)

    payload = {
        "name": args.name or f"Ollama ({args.model})",
        "endpoint": "http://localhost:11434",
        "connection_type": "openai",
        "is_default": True,
        "extras": {
            "model": args.model,
            "system_prompt": "You are a helpful assistant.",
        },
    }

    url = f"{args.url.rstrip('/')}/projects/{args.project}/agents"
    headers = {"Authorization": f"Bearer {args.token}", "Content-Type": "application/json"}

    with httpx.Client() as client:
        r = client.post(url, json=payload, headers=headers)
    if r.status_code in (200, 201):
        data = r.json()
        print(json.dumps(data, indent=2))
        print(f"\nAgent created. Use it in project '{args.project}'.")
    else:
        print(f"Error {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
