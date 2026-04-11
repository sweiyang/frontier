#!/usr/bin/env python3
"""
Frontier Multi-Worker Volume Performance Test
===============================================
Comprehensive volume testing script that benchmarks the Frontier backend
under multi-worker configuration. Measures and reports:

  1. Concurrent API Throughput  — ramps up parallel GET/POST requests to
     core endpoints (/api/config, /conversations, /chat) and measures QPS,
     latency percentiles, and error rates.

  2. Large-Payload Chat Volume  — sends progressively larger conversation
     payloads and measures write/read latency under data pressure.

  3. Burst Capacity              — short high-intensity bursts to find the
     system ceiling under the current worker configuration.

Reports are written to frontier/perf/multiworker/ with both JSON and Markdown.

PREREQUISITES:
  cd frontier && docker compose up -d --build
  pip install requests

Usage:
  python multiworker_volume_test.py
  python multiworker_volume_test.py --max-concurrency 100 --duration 15
  python multiworker_volume_test.py --skip-payload --skip-burst
"""

import time
import json
import subprocess
import argparse
import statistics
import sys
import os
import random
import platform
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple

import requests

# ─── Defaults ───────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
PROJECT = "test-project"
LOGIN_USER = "admin"
LOGIN_PASS = "admin123"

# Output directory: frontier/perf/multiworker/
# Resolved dynamically relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# test2/performance -> test2 -> Frontier Hub
FRONTIER_HUB = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUTPUT_DIR = os.path.join(FRONTIER_HUB, "frontier", "perf", "multiworker")


# ═══════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════

def get_docker_stats(container: str = "frontier-server") -> Dict[str, str]:
    """Return CPU/Memory stats from docker stats for the given container."""
    try:
        out = subprocess.check_output(
            ["docker", "stats", "--no-stream", "--format",
             "{{.CPUPerc}}|{{.MemUsage}}|{{.PIDs}}",
             container],
            stderr=subprocess.DEVNULL, timeout=5
        ).decode().strip()
        if "|" in out:
            parts = out.split("|")
            return {
                "cpu": parts[0].strip(),
                "memory": parts[1].strip(),
                "pids": parts[2].strip() if len(parts) > 2 else "N/A",
            }
    except Exception:
        pass
    return {"cpu": "N/A", "memory": "N/A", "pids": "N/A"}


def get_worker_count_from_docker(container: str = "frontier-server") -> Optional[int]:
    """Try to detect the number of gunicorn/uvicorn workers inside the container."""
    try:
        # Try reading from config.yaml first
        out = subprocess.check_output(
            ["docker", "exec", container, "python3", "-c",
             "import yaml; c=yaml.safe_load(open('/app/config.yaml')); print(c.get('server',{}).get('workers',1))"],
            stderr=subprocess.DEVNULL, timeout=5
        ).decode().strip()
        return int(out)
    except Exception:
        pass
    try:
        # Fallback: count processes
        out = subprocess.check_output(
            ["docker", "exec", container, "sh", "-c",
             "ps aux 2>/dev/null | grep -c '[g]unicorn.*worker' || echo 1"],
            stderr=subprocess.DEVNULL, timeout=5
        ).decode().strip()
        return max(int(out.split("\n")[0]), 1)
    except Exception:
        return None


def generate_large_text(size: int) -> str:
    """Generate a realistic large text payload of given character count."""
    words = [
        "performance", "testing", "volume", "payload", "frontier",
        "system", "database", "query", "latency", "throughput",
        "conversation", "message", "history", "analysis", "benchmark",
        "optimization", "scalability", "resilience", "capacity", "threshold",
        "multiworker", "concurrency", "gunicorn", "uvicorn", "fastapi",
    ]
    result = []
    current_len = 0
    while current_len < size:
        word = random.choice(words)
        result.append(word)
        current_len += len(word) + 1
    return " ".join(result)[:size]


def percentile(data: List[float], pct: int) -> float:
    """Return the pct-th percentile of data."""
    if len(data) < 2:
        return data[0] if data else 0.0
    quantiles = statistics.quantiles(data, n=100)
    idx = min(pct - 1, len(quantiles) - 1)
    return quantiles[idx]


def fmt_rate(rate: float) -> str:
    return f"{rate:.2%}"


# ═══════════════════════════════════════════════════════════════════════
#  SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

class FrontierSession:
    """Authenticated session wrapper for Frontier API."""

    def __init__(self, base_url: str, project: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.project = project
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token: Optional[str] = None

    def login(self) -> bool:
        try:
            resp = self.session.post(
                f"{self.base_url}/login",
                json={"username": self.username, "password": self.password},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            self.token = data.get("access_token") or data.get("token")
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "X-Project": self.project,
            })
            return True
        except Exception as e:
            print(f"  [LOGIN ERROR] {e}")
            return False

    def resolve_agent(self) -> Optional[str]:
        try:
            resp = self.session.get(
                f"{self.base_url}/projects/{self.project}/agents", timeout=30
            )
            if resp.status_code == 200:
                agents = resp.json()
                agent_list = agents if isinstance(agents, list) else agents.get("agents", [])
                for a in agent_list:
                    if "http" in (a.get("name", "") or "").lower():
                        return a.get("id")
                if agent_list:
                    return agent_list[0].get("id")
        except Exception:
            pass
        return None

    def create_conversation(self) -> Optional[str]:
        resp = self.session.post(
            f"{self.base_url}/conversations",
            json={"project_name": self.project},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("id") or data.get("conversation_id")

    def delete_conversation(self, conv_id: str):
        try:
            self.session.delete(f"{self.base_url}/conversations/{conv_id}", timeout=30)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
#  TEST 1: CONCURRENT API THROUGHPUT
# ═══════════════════════════════════════════════════════════════════════

def _single_api_request(sess: requests.Session, url: str, method: str = "GET",
                        payload: dict = None, timeout: float = 10.0) -> Tuple[float, bool, int]:
    """Execute a single API request. Returns (latency, success, status_code)."""
    start = time.perf_counter()
    try:
        if method == "GET":
            resp = sess.get(url, timeout=timeout)
        else:
            resp = sess.post(url, json=payload or {}, timeout=timeout)
        latency = time.perf_counter() - start
        return latency, resp.status_code < 400, resp.status_code
    except Exception:
        return time.perf_counter() - start, False, 0


def run_concurrent_api_test(
    fs: FrontierSession,
    concurrency_levels: List[int],
    duration_per_level: int = 10,
    endpoints: List[dict] = None,
) -> List[Dict[str, Any]]:
    """
    Ramp up concurrent API requests across specified concurrency levels.
    """
    if endpoints is None:
        endpoints = [
            {"name": "GET /api/config", "method": "GET",
             "url": f"{fs.base_url}/api/config"},
            {"name": "GET /conversations", "method": "GET",
             "url": f"{fs.base_url}/conversations"},
            {"name": "GET /projects/{project}/agents", "method": "GET",
             "url": f"{fs.base_url}/projects/{fs.project}/agents"},
        ]

    results = []

    for level in concurrency_levels:
        print(f"\n  -- Concurrency Level: {level} ({duration_per_level}s per endpoint) --")
        level_data = {
            "concurrency": level,
            "endpoints": [],
        }

        for ep in endpoints:
            ep_name = ep["name"]
            ep_url = ep["url"]
            ep_method = ep.get("method", "GET")
            ep_payload = ep.get("payload")

            latencies = []
            successes = 0
            failures = 0
            status_codes: Dict[int, int] = {}

            stop_time = time.perf_counter() + duration_per_level

            def _worker(_id):
                nonlocal successes, failures
                local_lats = []
                local_codes: Dict[int, int] = {}
                local_ok = 0
                local_fail = 0
                while time.perf_counter() < stop_time:
                    lat, ok, code = _single_api_request(
                        fs.session, ep_url, ep_method, ep_payload
                    )
                    local_lats.append(lat)
                    local_codes[code] = local_codes.get(code, 0) + 1
                    if ok:
                        local_ok += 1
                    else:
                        local_fail += 1
                return local_lats, local_ok, local_fail, local_codes

            with ThreadPoolExecutor(max_workers=level) as pool:
                futures = [pool.submit(_worker, i) for i in range(level)]
                for fut in as_completed(futures):
                    lats, ok, fail, codes = fut.result()
                    latencies.extend(lats)
                    successes += ok
                    failures += fail
                    for c, n in codes.items():
                        status_codes[c] = status_codes.get(c, 0) + n

            total = successes + failures
            qps = total / duration_per_level if duration_per_level > 0 else 0
            error_rate = failures / total if total > 0 else 0
            avg_lat = statistics.mean(latencies) if latencies else 0
            p50_lat = percentile(latencies, 50) if len(latencies) >= 2 else avg_lat
            p95_lat = percentile(latencies, 95) if len(latencies) >= 2 else avg_lat
            p99_lat = percentile(latencies, 99) if len(latencies) >= 2 else avg_lat
            max_lat = max(latencies) if latencies else 0

            ep_result = {
                "endpoint": ep_name,
                "total_requests": total,
                "successes": successes,
                "failures": failures,
                "qps": round(qps, 2),
                "error_rate": round(error_rate, 4),
                "avg_latency": round(avg_lat, 4),
                "p50_latency": round(p50_lat, 4),
                "p95_latency": round(p95_lat, 4),
                "p99_latency": round(p99_lat, 4),
                "max_latency": round(max_lat, 4),
                "status_codes": {str(k): v for k, v in status_codes.items()},
            }
            level_data["endpoints"].append(ep_result)

            docker = get_docker_stats()
            print(f"    {ep_name}: QPS={qps:.1f} | Avg={avg_lat:.3f}s | "
                  f"P95={p95_lat:.3f}s | Err={fmt_rate(error_rate)} | "
                  f"CPU={docker['cpu']} | MEM={docker['memory']}")

        # Aggregate level stats
        total_reqs = sum(ep["total_requests"] for ep in level_data["endpoints"])
        total_ok = sum(ep["successes"] for ep in level_data["endpoints"])
        total_fail = sum(ep["failures"] for ep in level_data["endpoints"])

        docker_snap = get_docker_stats()
        level_data["total_requests"] = total_reqs
        level_data["total_successes"] = total_ok
        level_data["total_failures"] = total_fail
        level_data["overall_qps"] = round(total_reqs / (duration_per_level * len(endpoints)), 2) if endpoints else 0
        level_data["overall_error_rate"] = round(total_fail / total_reqs, 4) if total_reqs > 0 else 0
        level_data["cpu"] = docker_snap["cpu"]
        level_data["memory"] = docker_snap["memory"]
        level_data["pids"] = docker_snap["pids"]

        results.append(level_data)

        if level_data["overall_error_rate"] > 0.20:
            print(f"  [!] Error rate {fmt_rate(level_data['overall_error_rate'])} > 20% -- stopping ramp-up")
            break

    return results


# ═══════════════════════════════════════════════════════════════════════
#  TEST 2: LARGE-PAYLOAD VOLUME
# ═══════════════════════════════════════════════════════════════════════

def _send_chat(sess: requests.Session, base_url: str, conv_id: str,
               agent_id: str, message: str) -> Tuple[float, bool, int]:
    """Send a chat message and consume the streaming response."""
    start = time.perf_counter()
    try:
        resp = sess.post(
            f"{base_url}/chat",
            json={
                "conversation_id": conv_id,
                "agent_id": agent_id,
                "message": message,
                "client_context": {"source": "multiworker-volume-test"},
            },
            timeout=60,
            stream=True,
        )
        total_bytes = 0
        for chunk in resp.iter_content(chunk_size=4096):
            total_bytes += len(chunk)
        latency = time.perf_counter() - start
        return latency, resp.status_code < 400, total_bytes
    except Exception:
        return time.perf_counter() - start, False, 0


def _read_messages(sess: requests.Session, base_url: str,
                   conv_id: str) -> Tuple[float, bool, int]:
    """Read conversation history."""
    start = time.perf_counter()
    try:
        resp = sess.get(f"{base_url}/conversations/{conv_id}/messages", timeout=60)
        latency = time.perf_counter() - start
        return latency, resp.status_code < 400, len(resp.content)
    except Exception:
        return time.perf_counter() - start, False, 0


def run_payload_volume_test(
    fs: FrontierSession,
    agent_id: Optional[str],
    start_msgs: int = 10,
    step_msgs: int = 10,
    max_msgs: int = 100,
    payload_size: int = 5000,
    concurrency: int = 2,
    threshold: float = 0.90,
) -> List[Dict[str, Any]]:
    """
    Gradually increase number of large-payload messages per conversation.
    """
    results = []
    large_text = generate_large_text(payload_size)
    stage_num = 0
    num_messages = start_msgs

    while num_messages <= max_msgs:
        stage_num += 1
        total_volume = num_messages * payload_size
        print(f"\n  -- Payload Stage {stage_num}: {num_messages} msgs x "
              f"{payload_size:,} chars = {total_volume:,} chars --")

        try:
            conv_id = fs.create_conversation()
        except Exception as e:
            print(f"    FATAL: Cannot create conversation: {e}")
            results.append({
                "stage": stage_num, "num_messages": num_messages,
                "payload_size": payload_size, "total_volume_chars": total_volume,
                "concurrency": concurrency,
                "success_rate": 0, "error": str(e),
            })
            break

        # Write messages
        write_lats = []
        write_ok = 0
        write_fail = 0
        write_start = time.perf_counter()

        if concurrency <= 1:
            for i in range(num_messages):
                msg = f"[Msg {i+1}/{num_messages}] " + large_text[:payload_size - 30]
                lat, ok, _ = _send_chat(fs.session, fs.base_url, conv_id, agent_id, msg)
                write_lats.append(lat)
                if ok:
                    write_ok += 1
                else:
                    write_fail += 1
                if (i + 1) % max(1, num_messages // 3) == 0 or i == num_messages - 1:
                    ds = get_docker_stats()
                    print(f"    [Write {i+1}/{num_messages}] lat={lat:.3f}s | "
                          f"CPU={ds['cpu']} | MEM={ds['memory']}")
        else:
            def _write_one(idx):
                msg = f"[Msg {idx+1}/{num_messages}] " + large_text[:payload_size - 30]
                return _send_chat(fs.session, fs.base_url, conv_id, agent_id, msg)

            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = {pool.submit(_write_one, i): i for i in range(num_messages)}
                done = 0
                for fut in as_completed(futures):
                    lat, ok, _ = fut.result()
                    write_lats.append(lat)
                    if ok:
                        write_ok += 1
                    else:
                        write_fail += 1
                    done += 1
                    if done % max(1, num_messages // 3) == 0 or done == num_messages:
                        ds = get_docker_stats()
                        print(f"    [Write {done}/{num_messages}] lat={lat:.3f}s | "
                              f"CPU={ds['cpu']} | MEM={ds['memory']}")

        write_elapsed = time.perf_counter() - write_start
        write_qps = num_messages / write_elapsed if write_elapsed > 0 else 0

        # Read history
        read_rounds = min(5, max(2, num_messages // 10))
        read_lats = []
        read_ok = 0
        read_fail = 0
        read_start = time.perf_counter()

        for r in range(read_rounds):
            lat, ok, resp_size = _read_messages(fs.session, fs.base_url, conv_id)
            read_lats.append(lat)
            if ok:
                read_ok += 1
            else:
                read_fail += 1
            print(f"    [Read {r+1}/{read_rounds}] lat={lat:.3f}s | "
                  f"resp_size={resp_size:,} bytes")

        read_elapsed = time.perf_counter() - read_start
        read_qps = read_rounds / read_elapsed if read_elapsed > 0 else 0

        # Cleanup
        fs.delete_conversation(conv_id)

        # Aggregate
        total_reqs = num_messages + read_rounds
        total_ok_all = write_ok + read_ok
        success_rate = total_ok_all / total_reqs if total_reqs > 0 else 0
        all_lats = write_lats + read_lats
        avg_lat = statistics.mean(all_lats) if all_lats else 0
        p95_lat = percentile(all_lats, 95) if len(all_lats) >= 2 else avg_lat

        docker = get_docker_stats()

        stage_result = {
            "stage": stage_num,
            "num_messages": num_messages,
            "payload_size": payload_size,
            "total_volume_chars": total_volume,
            "concurrency": concurrency,
            "total_requests": total_reqs,
            "write_qps": round(write_qps, 2),
            "read_qps": round(read_qps, 2),
            "overall_qps": round(total_reqs / (write_elapsed + read_elapsed), 2) if (write_elapsed + read_elapsed) > 0 else 0,
            "avg_write_latency": round(statistics.mean(write_lats), 3) if write_lats else 0,
            "p95_write_latency": round(percentile(write_lats, 95), 3) if len(write_lats) >= 2 else 0,
            "avg_read_latency": round(statistics.mean(read_lats), 3) if read_lats else 0,
            "p95_read_latency": round(percentile(read_lats, 95), 3) if len(read_lats) >= 2 else 0,
            "avg_latency": round(avg_lat, 3),
            "p95_latency": round(p95_lat, 3),
            "success_rate": round(success_rate, 4),
            "cpu": docker["cpu"],
            "memory": docker["memory"],
            "write_failures": write_fail,
            "read_failures": read_fail,
        }
        results.append(stage_result)

        print(f"    Summary: QPS={stage_result['overall_qps']} | "
              f"P95={stage_result['p95_latency']}s | "
              f"Success={fmt_rate(success_rate)}")

        if success_rate < threshold:
            print(f"  [!] Threshold reached: success_rate {fmt_rate(success_rate)} < {fmt_rate(threshold)}")
            break

        num_messages += step_msgs

    return results


# ═══════════════════════════════════════════════════════════════════════
#  TEST 3: BURST CAPACITY
# ═══════════════════════════════════════════════════════════════════════

def run_burst_test(
    fs: FrontierSession,
    burst_sizes: List[int] = None,
    endpoint_url: str = None,
) -> List[Dict[str, Any]]:
    """Fire N requests simultaneously to find ceiling."""
    if burst_sizes is None:
        burst_sizes = [10, 25, 50, 100, 150, 200]
    if endpoint_url is None:
        endpoint_url = f"{fs.base_url}/api/config"

    results = []
    for burst in burst_sizes:
        print(f"\n  -- Burst: {burst} simultaneous requests --")
        latencies = []
        successes = 0
        failures = 0

        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=burst) as pool:
            futures = [
                pool.submit(_single_api_request, fs.session, endpoint_url, "GET")
                for _ in range(burst)
            ]
            for fut in as_completed(futures):
                lat, ok, code = fut.result()
                latencies.append(lat)
                if ok:
                    successes += 1
                else:
                    failures += 1
        elapsed = time.perf_counter() - start

        total = successes + failures
        qps = total / elapsed if elapsed > 0 else 0
        error_rate = failures / total if total > 0 else 0
        avg_lat = statistics.mean(latencies) if latencies else 0
        p95_lat = percentile(latencies, 95) if len(latencies) >= 2 else avg_lat
        max_lat = max(latencies) if latencies else 0

        docker = get_docker_stats()
        burst_result = {
            "burst_size": burst,
            "total_requests": total,
            "qps": round(qps, 2),
            "error_rate": round(error_rate, 4),
            "avg_latency": round(avg_lat, 4),
            "p95_latency": round(p95_lat, 4),
            "max_latency": round(max_lat, 4),
            "success_rate": round(1 - error_rate, 4),
            "elapsed": round(elapsed, 3),
            "cpu": docker["cpu"],
            "memory": docker["memory"],
        }
        results.append(burst_result)

        print(f"    QPS={qps:.1f} | Avg={avg_lat:.3f}s | P95={p95_lat:.3f}s | "
              f"Max={max_lat:.3f}s | Err={fmt_rate(error_rate)} | "
              f"CPU={docker['cpu']}")

        if error_rate > 0.30:
            print(f"  [!] Error rate {fmt_rate(error_rate)} > 30% -- stopping burst ramp")
            break

    return results


# ═══════════════════════════════════════════════════════════════════════
#  REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════

def generate_reports(
    all_results: Dict[str, Any],
    output_dir: str,
    timestamp: str,
    worker_count: Any,
):
    """Generate JSON data file and Markdown report to output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    # ─── JSON ───
    json_path = os.path.join(output_dir, f"multiworker_volume_report_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[Report] JSON: {json_path}")

    # ─── Markdown ───
    md_path = os.path.join(output_dir, f"multiworker_volume_test_report_{timestamp}.md")
    wk = worker_count if worker_count else "N/A"
    cfg = all_results.get("config", {})

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Frontier Multi-Worker Volume Test Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Test Environment\n\n")
        f.write(f"- **Target URL:** {cfg.get('base_url', BASE_URL)}\n")
        f.write(f"- **Project:** {cfg.get('project', PROJECT)}\n")
        f.write(f"- **Workers:** {wk}\n")
        f.write(f"- **OS:** {platform.system()} {platform.release()}\n")
        f.write(f"- **Python:** {platform.python_version()}\n\n")
        f.write("---\n\n")

        # ═══════════════════════════════════════════════════════════════
        # Section 1: Concurrent API Throughput
        # ═══════════════════════════════════════════════════════════════
        api_results = all_results.get("concurrent_api", [])
        if api_results:
            f.write("## 1. Concurrent API Throughput Test\n\n")
            f.write("### Overview\n\n")
            f.write("| Workers | Concurrency | Total Requests | QPS | Error Rate | CPU | Memory |\n")
            f.write("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
            for lvl in api_results:
                f.write(f"| {wk} "
                        f"| {lvl['concurrency']} "
                        f"| {lvl['total_requests']} "
                        f"| {lvl['overall_qps']} "
                        f"| {fmt_rate(lvl['overall_error_rate'])} "
                        f"| {lvl['cpu']} "
                        f"| {lvl['memory']} |\n")

            f.write("\n### Endpoint Details\n\n")
            f.write("| Workers | Concurrency | Endpoint | Requests | QPS | Avg (s) | P50 (s) | P95 (s) | P99 (s) | Max (s) | Error Rate |\n")
            f.write("|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
            for lvl in api_results:
                for ep in lvl["endpoints"]:
                    f.write(f"| {wk} "
                            f"| {lvl['concurrency']} "
                            f"| {ep['endpoint']} "
                            f"| {ep['total_requests']} "
                            f"| {ep['qps']} "
                            f"| {ep['avg_latency']} "
                            f"| {ep['p50_latency']} "
                            f"| {ep['p95_latency']} "
                            f"| {ep['p99_latency']} "
                            f"| {ep['max_latency']} "
                            f"| {fmt_rate(ep['error_rate'])} |\n")
            f.write("\n")

        # ═══════════════════════════════════════════════════════════════
        # Section 2: Large-Payload Volume  (user-requested format)
        # ═══════════════════════════════════════════════════════════════
        payload_results = all_results.get("payload_volume", [])
        if payload_results:
            f.write("## 2. Large-Payload Volume Test\n\n")
            f.write(f"**Config:** Payload={cfg.get('payload_size', 5000):,} chars/msg | "
                    f"Concurrency={cfg.get('payload_concurrency', 2)}\n\n")

            # ──── Primary table matching user's requested format ────
            f.write("| Workers | Request (msgs) | Payload (chars) | Volume (total chars) | QPS | Concurrency | Memory | CPU Usage | Avg Latency (s) | P95 Latency (s) | Success Rate |\n")
            f.write("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
            for r in payload_results:
                f.write(f"| {wk} "
                        f"| {r['num_messages']} "
                        f"| {r['payload_size']:,} "
                        f"| {r['total_volume_chars']:,} "
                        f"| {r['overall_qps']} "
                        f"| {r['concurrency']} "
                        f"| {r['memory']} "
                        f"| {r['cpu']} "
                        f"| {r['avg_latency']} "
                        f"| {r['p95_latency']} "
                        f"| {fmt_rate(r['success_rate'])} |\n")

            # ──── Write vs Read breakdown ────
            f.write("\n### Write vs Read Breakdown\n\n")
            f.write("| Workers | Stage | Messages | Write QPS | Avg Write Lat (s) | P95 Write Lat (s) | "
                    "Read QPS | Avg Read Lat (s) | P95 Read Lat (s) | Write Failures | Read Failures |\n")
            f.write("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
            for r in payload_results:
                f.write(f"| {wk} "
                        f"| {r['stage']} "
                        f"| {r['num_messages']} "
                        f"| {r['write_qps']} "
                        f"| {r['avg_write_latency']} "
                        f"| {r['p95_write_latency']} "
                        f"| {r['read_qps']} "
                        f"| {r['avg_read_latency']} "
                        f"| {r['p95_read_latency']} "
                        f"| {r['write_failures']} "
                        f"| {r['read_failures']} |\n")
            f.write("\n")

        # ═══════════════════════════════════════════════════════════════
        # Section 3: Burst Capacity
        # ═══════════════════════════════════════════════════════════════
        burst_results = all_results.get("burst_capacity", [])
        if burst_results:
            f.write("## 3. Burst Capacity Test\n\n")
            f.write("| Workers | Burst Size | QPS | Avg Latency (s) | P95 Latency (s) | Max Latency (s) | Success Rate | CPU | Memory |\n")
            f.write("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
            for r in burst_results:
                f.write(f"| {wk} "
                        f"| {r['burst_size']} "
                        f"| {r['qps']} "
                        f"| {r['avg_latency']} "
                        f"| {r['p95_latency']} "
                        f"| {r['max_latency']} "
                        f"| {fmt_rate(r['success_rate'])} "
                        f"| {r['cpu']} "
                        f"| {r['memory']} |\n")
            f.write("\n")

        # ═══════════════════════════════════════════════════════════════
        # Section 4: Analysis
        # ═══════════════════════════════════════════════════════════════
        f.write("## 4. Analysis & Conclusions\n\n")
        f.write(f"**Worker Configuration:** {wk} worker(s)\n\n")

        if api_results:
            last_api = api_results[-1]
            peak_qps_level = max(api_results, key=lambda x: x["overall_qps"])
            f.write(f"### Concurrent API Throughput\n")
            f.write(f"- Max concurrency tested: **{last_api['concurrency']}**\n")
            f.write(f"- Peak QPS at **concurrency={peak_qps_level['concurrency']}**: "
                    f"**{peak_qps_level['overall_qps']} QPS**\n")
            f.write(f"- Final error rate: **{fmt_rate(last_api['overall_error_rate'])}**\n\n")

        if payload_results:
            last_pv = payload_results[-1]
            f.write(f"### Large-Payload Volume\n")
            if last_pv.get("success_rate", 1) < cfg.get("payload_threshold", 0.90):
                f.write(f"- **Threshold reached** at **{last_pv['num_messages']} messages** "
                        f"({last_pv['total_volume_chars']:,} chars total)\n")
            else:
                f.write(f"- All stages passed, max volume: **{last_pv['num_messages']} messages** "
                        f"({last_pv['total_volume_chars']:,} chars)\n")
            f.write(f"- Final P95 Latency: **{last_pv['p95_latency']}s**\n")
            f.write(f"- Final Success Rate: **{fmt_rate(last_pv['success_rate'])}**\n\n")

        if burst_results:
            peak_burst = max(burst_results, key=lambda x: x["qps"])
            last_burst = burst_results[-1]
            f.write(f"### Burst Capacity\n")
            f.write(f"- Peak QPS: **{peak_burst['qps']}** (burst={peak_burst['burst_size']})\n")
            f.write(f"- Max burst tested: **{last_burst['burst_size']}**\n")
            f.write(f"- Success rate at max burst: **{fmt_rate(last_burst['success_rate'])}**\n\n")

        f.write("### Recommendations\n")
        f.write("- Multi-worker deployment (>=4) significantly improves concurrent throughput and P95 latency\n")
        f.write("- Monitor memory trends under large-payload scenarios to prevent OOM\n")
        f.write("- Consider testing: ultra-high concurrency (200+), extreme payloads (50KB+/msg), long-running soak tests\n")
        f.write("- Compare performance across different worker counts (1/2/4/8) to find optimal configuration\n\n")

        f.write("---\n\n")
        f.write(f"*Report generated by `multiworker_volume_test.py` | "
                f"Raw data: `multiworker_volume_report_{timestamp}.json`*\n")

    print(f"[Report] Markdown: {md_path}")
    return json_path, md_path


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Frontier Multi-Worker Volume Performance Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Connection
    parser.add_argument("--url", default=BASE_URL, help="Base URL of Frontier server")
    parser.add_argument("--project", default=PROJECT, help="Project name")
    parser.add_argument("--username", default=LOGIN_USER, help="Login username")
    parser.add_argument("--password", default=LOGIN_PASS, help="Login password")

    # Output
    parser.add_argument("--output-dir", default=OUTPUT_DIR,
                        help="Directory to write reports to")

    # Concurrent API test
    parser.add_argument("--start-concurrency", type=int, default=5)
    parser.add_argument("--step-concurrency", type=int, default=5)
    parser.add_argument("--max-concurrency", type=int, default=50)
    parser.add_argument("--duration", type=int, default=10,
                        help="Seconds per concurrency level")

    # Payload volume test
    parser.add_argument("--start-msgs", type=int, default=10)
    parser.add_argument("--step-msgs", type=int, default=10)
    parser.add_argument("--max-msgs", type=int, default=100)
    parser.add_argument("--payload-size", type=int, default=5000)
    parser.add_argument("--payload-concurrency", type=int, default=2)
    parser.add_argument("--payload-threshold", type=float, default=0.90)

    # Burst test
    parser.add_argument("--burst-sizes", type=int, nargs="+",
                        default=[10, 25, 50, 100, 150, 200])

    # Skips
    parser.add_argument("--skip-api", action="store_true",
                        help="Skip concurrent API throughput test")
    parser.add_argument("--skip-payload", action="store_true",
                        help="Skip large-payload volume test")
    parser.add_argument("--skip-burst", action="store_true",
                        help="Skip burst capacity test")

    args = parser.parse_args()

    # ─── Banner ───
    print("=" * 70)
    print("  Frontier Multi-Worker Volume Performance Test")
    print("=" * 70)
    print(f"  Target URL:       {args.url}")
    print(f"  Project:          {args.project}")
    print(f"  Output Dir:       {args.output_dir}")
    print(f"  OS:               {platform.system()} {platform.release()}")
    print(f"  Python:           {platform.python_version()}")
    if not args.skip_api:
        print(f"  Concurrency:      {args.start_concurrency} -> {args.max_concurrency} (step {args.step_concurrency})")
    if not args.skip_payload:
        print(f"  Payload Volume:   {args.start_msgs} -> {args.max_msgs} msgs x {args.payload_size:,} chars")
    if not args.skip_burst:
        print(f"  Burst Sizes:      {args.burst_sizes}")
    print("=" * 70)

    # Login
    print("\n[Auth] Logging in...")
    fs = FrontierSession(args.url, args.project, args.username, args.password)
    if not fs.login():
        print("[Auth] FAILED -- make sure the server is running: docker compose up -d --build")
        sys.exit(1)
    print("[Auth] Login successful")

    # Detect workers
    detected_workers = get_worker_count_from_docker()
    if detected_workers:
        print(f"[Workers] Detected {detected_workers} worker(s) in container")
    else:
        print("[Workers] Could not detect worker count")

    # Resolve agent
    agent_id = None
    if not args.skip_payload:
        agent_id = fs.resolve_agent()
        if agent_id:
            print(f"[Agent] Using agent_id={agent_id}")
        else:
            print("[Agent] Warning: No agent found, payload test may fail on /chat")

    # ─── Build results structure ───
    all_results: Dict[str, Any] = {
        "config": {
            "base_url": args.url,
            "project": args.project,
            "workers": detected_workers,
            "start_concurrency": args.start_concurrency,
            "step_concurrency": args.step_concurrency,
            "max_concurrency": args.max_concurrency,
            "duration_per_level": args.duration,
            "payload_size": args.payload_size,
            "payload_start_msgs": args.start_msgs,
            "payload_step_msgs": args.step_msgs,
            "payload_max_msgs": args.max_msgs,
            "payload_concurrency": args.payload_concurrency,
            "payload_threshold": args.payload_threshold,
            "burst_sizes": args.burst_sizes,
            "timestamp": datetime.now().isoformat(),
        },
        "detected_workers": detected_workers,
        "concurrent_api": [],
        "payload_volume": [],
        "burst_capacity": [],
    }

    # ─── Test 1: Concurrent API Throughput ───
    if not args.skip_api:
        print("\n" + "=" * 70)
        print("  [Test 1] Concurrent API Throughput")
        print("=" * 70)
        concurrency_levels = list(range(
            args.start_concurrency,
            args.max_concurrency + 1,
            args.step_concurrency,
        ))
        all_results["concurrent_api"] = run_concurrent_api_test(
            fs, concurrency_levels, args.duration,
        )

    # ─── Test 2: Large-Payload Volume ───
    if not args.skip_payload:
        print("\n" + "=" * 70)
        print("  [Test 2] Large-Payload Volume")
        print("=" * 70)
        all_results["payload_volume"] = run_payload_volume_test(
            fs, agent_id,
            start_msgs=args.start_msgs,
            step_msgs=args.step_msgs,
            max_msgs=args.max_msgs,
            payload_size=args.payload_size,
            concurrency=args.payload_concurrency,
            threshold=args.payload_threshold,
        )

    # ─── Test 3: Burst Capacity ───
    if not args.skip_burst:
        print("\n" + "=" * 70)
        print("  [Test 3] Burst Capacity")
        print("=" * 70)
        all_results["burst_capacity"] = run_burst_test(fs, args.burst_sizes)

    # ─── Generate Reports ───
    print("\n" + "=" * 70)
    print("  Generating Reports")
    print("=" * 70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path, md_path = generate_reports(
        all_results, args.output_dir, timestamp, detected_workers
    )

    # ─── Summary ───
    print("\n" + "=" * 70)
    print("  All tests completed!")
    print("=" * 70)
    print(f"  Workers:             {detected_workers}")
    if all_results["concurrent_api"]:
        peak = max(all_results["concurrent_api"], key=lambda x: x["overall_qps"])
        print(f"  Peak API QPS:        {peak['overall_qps']} (concurrency={peak['concurrency']})")
    if all_results["payload_volume"]:
        last = all_results["payload_volume"][-1]
        print(f"  Max Payload Volume:  {last['total_volume_chars']:,} chars ({last['num_messages']} msgs)")
        print(f"  Payload Success:     {fmt_rate(last['success_rate'])}")
    if all_results["burst_capacity"]:
        peak_b = max(all_results["burst_capacity"], key=lambda x: x["qps"])
        print(f"  Peak Burst QPS:      {peak_b['qps']} (burst={peak_b['burst_size']})")
    print(f"\n  Reports saved to: {args.output_dir}")
    print(f"    JSON: {os.path.basename(json_path)}")
    print(f"    MD:   {os.path.basename(md_path)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
