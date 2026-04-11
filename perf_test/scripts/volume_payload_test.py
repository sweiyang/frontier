#!/usr/bin/env python3
"""
Frontier Large-Payload Volume Test
-----------------------------------
Gradually increases the volume of large-payload chat messages sent to the system,
measuring how it handles bloated conversation history under growing data pressure.

Each "stage" sends N large messages (payload_size chars each) into conversations,
then reads back the full bloated message history. The stage volume increases
incrementally until the system hits a threshold (high error rate or extreme latency).

Metrics per stage:
  - request count, payload size, total volume (chars sent), QPS,
    concurrency, memory, CPU usage, avg latency, success rate

PREREQUISITE:
  cd frontier && docker compose up -d --build

Usage:
  python volume_payload_test.py
  python volume_payload_test.py --start-msgs 10 --step-msgs 10 --max-msgs 200 --payload-size 5000
"""

import time
import json
import subprocess
import argparse
import statistics
import sys
import os
import string
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE_URL = "http://localhost:8000"
PROJECT = "test-project"


# ─── Helpers ────────────────────────────────────────────────────────────

def get_docker_stats():
    """Return (cpu_str, mem_str) from docker stats for frontier-server."""
    try:
        out = subprocess.check_output(
            ["docker", "stats", "--no-stream", "--format",
             "{{.CPUPerc}}|{{.MemUsage}}",
             "frontier-server"],
            stderr=subprocess.DEVNULL, timeout=3
        ).decode().strip()
        if "|" in out:
            parts = out.split("|")
            return parts[0].strip(), parts[1].strip()
    except Exception:
        pass
    return "N/A", "N/A"


def generate_large_text(size: int) -> str:
    """Generate a realistic large text payload of given character count."""
    words = [
        "performance", "testing", "volume", "payload", "frontier",
        "system", "database", "query", "latency", "throughput",
        "conversation", "message", "history", "analysis", "benchmark",
        "optimization", "scalability", "resilience", "capacity", "threshold",
    ]
    result = []
    current_len = 0
    while current_len < size:
        word = random.choice(words)
        result.append(word)
        current_len += len(word) + 1
    return " ".join(result)[:size]


def login(username="admin", password="admin123"):
    """Login and return (token, session) or raise."""
    sess = requests.Session()
    resp = sess.post(f"{BASE_URL}/login",
                     json={"username": username, "password": password},
                     timeout=30)
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token") or data.get("token")
    sess.headers.update({
        "Authorization": f"Bearer {token}",
        "X-Project": PROJECT,
    })
    return token, sess


def resolve_agent(sess):
    """Get an agent ID from the project."""
    resp = sess.get(f"{BASE_URL}/projects/{PROJECT}/agents", timeout=30)
    if resp.status_code == 200:
        agents = resp.json()
        agent_list = agents if isinstance(agents, list) else agents.get("agents", [])
        for a in agent_list:
            if "http" in (a.get("name", "") or "").lower():
                return a.get("id")
        if agent_list:
            return agent_list[0].get("id")
    return None


def create_conversation(sess):
    """Create a new conversation and return its ID."""
    resp = sess.post(f"{BASE_URL}/conversations",
                     json={"project_name": PROJECT}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("id") or data.get("conversation_id")


def send_chat_message(sess, conv_id, agent_id, message):
    """Send a chat message and consume the streaming response. Returns (latency, success, response_size)."""
    start = time.perf_counter()
    try:
        resp = sess.post(
            f"{BASE_URL}/chat",
            json={
                "conversation_id": conv_id,
                "agent_id": agent_id,
                "message": message,
                "client_context": {"source": "volume-payload-test"},
            },
            timeout=60,
            stream=True,
        )
        # Consume the full streaming response
        total_bytes = 0
        for chunk in resp.iter_content(chunk_size=4096):
            total_bytes += len(chunk)
        latency = time.perf_counter() - start
        success = resp.status_code < 400
        return latency, success, total_bytes
    except Exception:
        latency = time.perf_counter() - start
        return latency, False, 0


def read_messages(sess, conv_id):
    """Read conversation history. Returns (latency, success, response_size)."""
    start = time.perf_counter()
    try:
        resp = sess.get(f"{BASE_URL}/conversations/{conv_id}/messages", timeout=60)
        latency = time.perf_counter() - start
        return latency, resp.status_code < 400, len(resp.content)
    except Exception:
        latency = time.perf_counter() - start
        return latency, False, 0


def delete_conversation(sess, conv_id):
    """Clean up conversation."""
    try:
        sess.delete(f"{BASE_URL}/conversations/{conv_id}", timeout=30)
    except Exception:
        pass


# ─── Single Stage Runner ────────────────────────────────────────────────

def run_stage(stage_num, num_messages, payload_size, concurrency, sess, agent_id):
    """
    Run a single volume stage:
      1. Create conversation
      2. Send num_messages large messages (payload_size chars each)
      3. Read back full bloated history
      4. Delete conversation
    Returns dict of metrics.
    """
    total_volume_chars = num_messages * payload_size
    print(f"\n{'='*60}")
    print(f"[Stage {stage_num}] Messages={num_messages} | Payload={payload_size} chars | "
          f"Total Volume={total_volume_chars:,} chars | Concurrency={concurrency}")
    print(f"{'='*60}")

    # Docker stats snapshot BEFORE
    cpu_before, mem_before = get_docker_stats()

    # 1. Create conversation
    try:
        conv_id = create_conversation(sess)
    except Exception as e:
        print(f"  FATAL: Cannot create conversation: {e}")
        return {
            "stage": stage_num, "num_messages": num_messages,
            "payload_size": payload_size, "total_volume_chars": total_volume_chars,
            "concurrency": concurrency,
            "write_qps": 0, "read_qps": 0,
            "avg_write_latency": 0, "avg_read_latency": 0,
            "cpu": "N/A", "memory": "N/A",
            "success_rate": 0, "error": str(e),
        }

    # 2. Send messages (with optional concurrency)
    write_latencies = []
    write_successes = 0
    write_failures = 0
    large_text = generate_large_text(payload_size)  # Reuse for consistency

    stage_start = time.perf_counter()

    if concurrency <= 1:
        for i in range(num_messages):
            msg = f"[Msg {i+1}/{num_messages}] " + large_text[:payload_size - 30]
            lat, ok, _ = send_chat_message(sess, conv_id, agent_id, msg)
            write_latencies.append(lat)
            if ok:
                write_successes += 1
            else:
                write_failures += 1
            # Brief progress
            if (i + 1) % max(1, num_messages // 5) == 0 or i == num_messages - 1:
                cpu_now, mem_now = get_docker_stats()
                print(f"  [Write {i+1}/{num_messages}] lat={lat:.3f}s | CPU={cpu_now} | MEM={mem_now}")
    else:
        # Concurrent writes
        def _write_one(idx):
            msg = f"[Msg {idx+1}/{num_messages}] " + large_text[:payload_size - 30]
            return send_chat_message(sess, conv_id, agent_id, msg)

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {pool.submit(_write_one, i): i for i in range(num_messages)}
            done_count = 0
            for fut in as_completed(futures):
                lat, ok, _ = fut.result()
                write_latencies.append(lat)
                if ok:
                    write_successes += 1
                else:
                    write_failures += 1
                done_count += 1
                if done_count % max(1, num_messages // 5) == 0 or done_count == num_messages:
                    cpu_now, mem_now = get_docker_stats()
                    print(f"  [Write {done_count}/{num_messages}] lat={lat:.3f}s | CPU={cpu_now} | MEM={mem_now}")

    write_elapsed = time.perf_counter() - stage_start
    write_qps = num_messages / write_elapsed if write_elapsed > 0 else 0

    # 3. Read back bloated history multiple times to measure read perf
    read_latencies = []
    read_successes = 0
    read_failures = 0
    read_rounds = min(5, max(2, num_messages // 10))  # Scale read rounds with volume

    read_start = time.perf_counter()
    for r in range(read_rounds):
        lat, ok, resp_size = read_messages(sess, conv_id)
        read_latencies.append(lat)
        if ok:
            read_successes += 1
        else:
            read_failures += 1
        print(f"  [Read {r+1}/{read_rounds}] lat={lat:.3f}s | resp_size={resp_size:,} bytes | ok={ok}")

    read_elapsed = time.perf_counter() - read_start
    read_qps = read_rounds / read_elapsed if read_elapsed > 0 else 0

    # Docker stats snapshot AFTER
    cpu_after, mem_after = get_docker_stats()

    # 4. Cleanup
    delete_conversation(sess, conv_id)

    # Aggregate
    total_requests = num_messages + read_rounds
    total_successes = write_successes + read_successes
    total_failures = write_failures + read_failures
    success_rate = total_successes / total_requests if total_requests > 0 else 0

    all_latencies = write_latencies + read_latencies
    avg_latency = statistics.mean(all_latencies) if all_latencies else 0
    p95_latency = statistics.quantiles(all_latencies, n=100)[94] if len(all_latencies) >= 2 else avg_latency

    overall_qps = total_requests / (write_elapsed + read_elapsed) if (write_elapsed + read_elapsed) > 0 else 0

    result = {
        "stage": stage_num,
        "num_messages": num_messages,
        "payload_size": payload_size,
        "total_volume_chars": total_volume_chars,
        "concurrency": concurrency,
        "total_requests": total_requests,
        "write_qps": round(write_qps, 2),
        "read_qps": round(read_qps, 2),
        "overall_qps": round(overall_qps, 2),
        "avg_write_latency": round(statistics.mean(write_latencies), 3) if write_latencies else 0,
        "p95_write_latency": round(statistics.quantiles(write_latencies, n=100)[94], 3) if len(write_latencies) >= 2 else 0,
        "avg_read_latency": round(statistics.mean(read_latencies), 3) if read_latencies else 0,
        "p95_read_latency": round(statistics.quantiles(read_latencies, n=100)[94], 3) if len(read_latencies) >= 2 else 0,
        "avg_latency": round(avg_latency, 3),
        "p95_latency": round(p95_latency, 3),
        "success_rate": round(success_rate, 4),
        "cpu": cpu_after,
        "memory": mem_after,
        "write_failures": write_failures,
        "read_failures": read_failures,
    }

    print(f"\n  --- Stage {stage_num} Summary ---")
    print(f"  Total Requests: {total_requests} (Write: {num_messages}, Read: {read_rounds})")
    print(f"  Write QPS: {result['write_qps']} | Read QPS: {result['read_qps']}")
    print(f"  Avg Write Latency: {result['avg_write_latency']}s | Avg Read Latency: {result['avg_read_latency']}s")
    print(f"  P95 Latency: {result['p95_latency']}s")
    print(f"  Success Rate: {result['success_rate']:.2%}")
    print(f"  CPU: {result['cpu']} | Memory: {result['memory']}")
    print(f"  -------------------------")

    return result


# ─── Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Large-Payload Volume Test for Frontier")
    parser.add_argument("--start-msgs", type=int, default=10,
                        help="Starting number of messages per conversation stage")
    parser.add_argument("--step-msgs", type=int, default=10,
                        help="Increment in messages per stage")
    parser.add_argument("--max-msgs", type=int, default=200,
                        help="Max messages per conversation before stopping")
    parser.add_argument("--payload-size", type=int, default=5000,
                        help="Size of each message payload in characters")
    parser.add_argument("--concurrency", type=int, default=1,
                        help="Concurrent writers per stage")
    parser.add_argument("--threshold", type=float, default=0.90,
                        help="Minimum success rate before aborting (default 0.90 = 90%%)")
    parser.add_argument("--url", default=BASE_URL, help="Base URL")
    parser.add_argument("--project", default=PROJECT, help="Project name")
    args = parser.parse_args()

    _base_url = args.url
    _project = args.project

    # Patch module-level vars so all helpers pick them up
    import volume_payload_test as _self
    _self.BASE_URL = _base_url
    _self.PROJECT = _project

    print("=" * 70)
    print("  Frontier Large-Payload Volume Test")
    print(f"  Target: {_base_url}")
    print(f"  Payload Size: {args.payload_size:,} chars per message")
    print(f"  Volume Ramp: {args.start_msgs} -> {args.max_msgs} msgs (step {args.step_msgs})")
    print(f"  Concurrency: {args.concurrency}")
    print(f"  Threshold: success_rate < {args.threshold:.0%}")
    print("=" * 70)

    # Login
    print("\n[Auth] Logging in...")
    try:
        token, sess = login()
        print("[Auth] Login successful.")
    except Exception as e:
        print(f"[Auth] FAILED: {e}")
        print("Make sure the server is running: docker compose up -d --build")
        sys.exit(1)

    # Resolve agent
    agent_id = resolve_agent(sess)
    if not agent_id:
        print("[WARN] No agent found. Chat messages may fail.")
    else:
        print(f"[Agent] Using agent_id={agent_id}")

    # Run stages
    results = []
    stage_num = 0
    num_messages = args.start_msgs

    while num_messages <= args.max_msgs:
        stage_num += 1
        result = run_stage(stage_num, num_messages, args.payload_size,
                           args.concurrency, sess, agent_id)
        results.append(result)

        # Check threshold
        if result["success_rate"] < args.threshold:
            print(f"\n*** THRESHOLD REACHED ***")
            print(f"Success rate {result['success_rate']:.2%} dropped below {args.threshold:.0%} "
                  f"at {num_messages} messages ({num_messages * args.payload_size:,} chars total volume)")
            break

        num_messages += args.step_msgs

    # ─── Generate Reports ────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.dirname(os.path.abspath(__file__))
    test2_dir = os.path.dirname(report_dir)

    # JSON report
    json_path = os.path.join(report_dir, f"volume_payload_report_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "config": {
                "payload_size": args.payload_size,
                "start_msgs": args.start_msgs,
                "step_msgs": args.step_msgs,
                "max_msgs": args.max_msgs,
                "concurrency": args.concurrency,
                "threshold": args.threshold,
                "timestamp": timestamp,
            },
            "stages": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nJSON report: {json_path}")

    # Markdown report -> test2/
    md_path = os.path.join(test2_dir, f"volume_payload_test_report_{timestamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Frontier Large-Payload Volume Test Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Test Configuration:**\n")
        f.write(f"- Payload Size: {args.payload_size:,} chars per message\n")
        f.write(f"- Volume Ramp: {args.start_msgs} -> {args.max_msgs} messages (step {args.step_msgs})\n")
        f.write(f"- Concurrency: {args.concurrency}\n")
        f.write(f"- Threshold: success_rate < {args.threshold:.0%}\n\n")

        f.write("## Results\n\n")
        f.write("| Request (msgs) | Payload (chars) | Volume (total chars) | QPS | Concurrency | Memory | CPU Usage | Avg Latency (s) | P95 Latency (s) | Success Rate |\n")
        f.write("|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|\n")
        for r in results:
            f.write(f"| {r['num_messages']} "
                    f"| {r['payload_size']:,} "
                    f"| {r['total_volume_chars']:,} "
                    f"| {r['overall_qps']} "
                    f"| {r['concurrency']} "
                    f"| {r['memory']} "
                    f"| {r['cpu']} "
                    f"| {r['avg_latency']} "
                    f"| {r['p95_latency']} "
                    f"| {r['success_rate']:.2%} |\n")

        # Write/Read breakdown
        f.write("\n## Write vs Read Breakdown\n\n")
        f.write("| Stage | Messages | Write QPS | Avg Write Lat (s) | P95 Write Lat (s) | Read QPS | Avg Read Lat (s) | P95 Read Lat (s) | Write Failures | Read Failures |\n")
        f.write("|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|\n")
        for r in results:
            f.write(f"| {r['stage']} "
                    f"| {r['num_messages']} "
                    f"| {r['write_qps']} "
                    f"| {r['avg_write_latency']} "
                    f"| {r['p95_write_latency']} "
                    f"| {r['read_qps']} "
                    f"| {r['avg_read_latency']} "
                    f"| {r['p95_read_latency']} "
                    f"| {r['write_failures']} "
                    f"| {r['read_failures']} |\n")

        # Analysis
        f.write("\n## Analysis\n\n")
        if results:
            last = results[-1]
            if last["success_rate"] < args.threshold:
                f.write(f"**Threshold Reached** at **{last['num_messages']} messages** "
                        f"({last['total_volume_chars']:,} chars total volume).\n\n")
                f.write(f"- Success rate dropped to **{last['success_rate']:.2%}**\n")
                f.write(f"- P95 Latency at breaking point: **{last['p95_latency']}s**\n")
                f.write(f"- CPU at breaking point: **{last['cpu']}**\n")
                f.write(f"- Memory at breaking point: **{last['memory']}**\n")
            else:
                f.write(f"All stages completed successfully up to **{last['num_messages']} messages** "
                        f"({last['total_volume_chars']:,} chars) without hitting the threshold.\n\n")
                f.write(f"- Final P95 Latency: **{last['p95_latency']}s**\n")
                f.write(f"- Final Success Rate: **{last['success_rate']:.2%}**\n")

    print(f"Markdown report: {md_path}")
    print("\nDone.")


if __name__ == "__main__":
    main()
