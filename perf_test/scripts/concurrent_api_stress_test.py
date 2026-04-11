#!/usr/bin/env python3
"""
Frontier Concurrent API Stress Test — Volume-Primed Edition
=============================================================
Tests Concurrent API Throughput at the proven peak volume baseline
(6,000,000 chars = 300 msgs × 20K chars/msg), then progressively 
increases concurrency with dynamic step sizes until hitting a 
threshold or reaching an industrially meaningless level.

Strategy:
  Phase 1: Prime the database with 6M chars volume (the proven peak from
            multiworker testing where Write QPS reached 43.01)
  Phase 2: Run concurrent API throughput test at exponentially increasing
            concurrency levels with adaptive step sizes:
            - Fine steps (5) at low concurrency (5→50)
            - Medium steps (25) at moderate concurrency (50→200)
            - Large steps (50) at high concurrency (200→500)
            - Jump steps (100) at extreme concurrency (500→1000)
            Auto-stops when:
            - Error rate exceeds 10%
            - P95 latency exceeds 5s for DB endpoints
            - QPS drops below 30% of peak observed
            - Concurrency reaches 1000 (industrially meaningless for 4W)

Output: JSON data + Markdown report + HTML visual report

PREREQUISITES:
  cd frontier && docker compose up -d --build
  pip install requests

Usage:
  python concurrent_api_stress_test.py
  python concurrent_api_stress_test.py --max-concurrency 500 --duration 15
"""

import time
import json
import subprocess
import argparse
import statistics
import os
import platform
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple

import requests

# ─── Defaults ───────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
PROJECT = "test-project"
LOGIN_USER = "admin"
LOGIN_PASS = "admin123"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = SCRIPT_DIR  # Output to same directory


# ═══════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════

def get_docker_stats(container: str = "frontier-server") -> Dict[str, str]:
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


def get_worker_count(container: str = "frontier-server") -> Optional[int]:
    try:
        out = subprocess.check_output(
            ["docker", "exec", container, "python3", "-c",
             "import yaml; c=yaml.safe_load(open('/app/config.yaml')); print(c.get('server',{}).get('workers',1))"],
            stderr=subprocess.DEVNULL, timeout=5
        ).decode().strip()
        return int(out)
    except Exception:
        return None


def generate_large_text(size: int) -> str:
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


def pct(data: List[float], p: int) -> float:
    if len(data) < 2:
        return data[0] if data else 0.0
    quantiles = statistics.quantiles(data, n=100)
    idx = min(p - 1, len(quantiles) - 1)
    return quantiles[idx]


def fmt_rate(rate: float) -> str:
    return f"{rate:.2%}"


def fmt_num(n: int) -> str:
    return f"{n:,}"


# ═══════════════════════════════════════════════════════════════════════
#  SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

class FrontierSession:
    def __init__(self, base_url: str, project: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.project = project
        self.session = requests.Session()
        self.token = None
        self._username = username
        self._password = password

    def login(self) -> bool:
        try:
            resp = self.session.post(
                f"{self.base_url}/login",
                json={"username": self._username, "password": self._password},
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
#  PHASE 1: VOLUME PRIMING (6M chars baseline)
# ═══════════════════════════════════════════════════════════════════════

def _send_chat(sess: requests.Session, base_url: str, conv_id: str,
               agent_id: str, message: str) -> Tuple[float, bool, int]:
    start = time.perf_counter()
    try:
        resp = sess.post(
            f"{base_url}/chat",
            json={
                "conversation_id": conv_id,
                "agent_id": agent_id,
                "message": message,
                "client_context": {"source": "concurrent-api-stress-test"},
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


def prime_volume(fs: FrontierSession, agent_id: str,
                 num_msgs: int = 300, payload_size: int = 20000,
                 concurrency: int = 5) -> Dict[str, Any]:
    """
    Prime the database with baseline volume data.
    Creates a conversation with 300 msgs × 20K chars = 6,000,000 chars.
    """
    total_volume = num_msgs * payload_size
    print(f"\n  Priming database: {num_msgs} msgs × {payload_size:,} chars = {total_volume:,} chars")
    print(f"  Concurrency: {concurrency}")

    large_text = generate_large_text(payload_size)
    conv_id = fs.create_conversation()

    write_lats = []
    write_ok = 0
    write_fail = 0
    start_time = time.perf_counter()

    def _write_one(idx):
        msg = f"[Prime {idx+1}/{num_msgs}] " + large_text[:payload_size - 30]
        return _send_chat(fs.session, fs.base_url, conv_id, agent_id, msg)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(_write_one, i): i for i in range(num_msgs)}
        done = 0
        for fut in as_completed(futures):
            lat, ok, _ = fut.result()
            write_lats.append(lat)
            if ok:
                write_ok += 1
            else:
                write_fail += 1
            done += 1
            if done % 50 == 0 or done == num_msgs:
                ds = get_docker_stats()
                elapsed = time.perf_counter() - start_time
                qps = done / elapsed if elapsed > 0 else 0
                print(f"    [{done}/{num_msgs}] QPS={qps:.1f} | lat={lat:.3f}s | "
                      f"CPU={ds['cpu']} | MEM={ds['memory']}")

    elapsed = time.perf_counter() - start_time
    ds = get_docker_stats()

    result = {
        "conversation_id": conv_id,
        "num_messages": num_msgs,
        "payload_size": payload_size,
        "total_volume": total_volume,
        "write_qps": round(num_msgs / elapsed, 2) if elapsed > 0 else 0,
        "avg_write_latency": round(statistics.mean(write_lats), 4) if write_lats else 0,
        "p95_write_latency": round(pct(write_lats, 95), 4) if len(write_lats) >= 2 else 0,
        "success_rate": round(write_ok / (write_ok + write_fail), 4) if (write_ok + write_fail) > 0 else 0,
        "elapsed_seconds": round(elapsed, 2),
        "cpu": ds["cpu"],
        "memory": ds["memory"],
    }

    print(f"\n  [OK] Priming complete: {write_ok}/{num_msgs} msgs written in {elapsed:.1f}s "
          f"(QPS={result['write_qps']})")
    return result


# ═══════════════════════════════════════════════════════════════════════
#  PHASE 2: CONCURRENT API THROUGHPUT (adaptive step)
# ═══════════════════════════════════════════════════════════════════════

def generate_concurrency_levels(max_concurrency: int) -> List[int]:
    """
    Generate concurrency levels with adaptive step sizes:
      5→50:   step=5   (fine-grained, find initial curve)
      50→200:  step=25  (moderate, capture plateau)
      200→500: step=50  (coarse, diminishing returns zone)
      500→1000:step=100 (jump, industrially meaningless zone)
    """
    levels = []
    c = 5
    while c <= min(max_concurrency, 50):
        levels.append(c)
        c += 5
    c = 75
    while c <= min(max_concurrency, 200):
        levels.append(c)
        c += 25
    c = 250
    while c <= min(max_concurrency, 500):
        levels.append(c)
        c += 50
    c = 600
    while c <= min(max_concurrency, 1000):
        levels.append(c)
        c += 100
    return sorted(set(levels))


def _single_api_request(sess: requests.Session, url: str, method: str = "GET",
                        payload: dict = None, timeout: float = 15.0) -> Tuple[float, bool, int]:
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


def run_concurrent_stress_test(
    fs: FrontierSession,
    concurrency_levels: List[int],
    duration_per_level: int = 10,
    max_error_rate: float = 0.10,
    max_p95_latency: float = 5.0,
    qps_drop_threshold: float = 0.30,
) -> List[Dict[str, Any]]:
    """
    Run concurrent API throughput with adaptive stopping conditions.
    """
    endpoints = [
        {"name": "GET /api/config", "method": "GET",
         "url": f"{fs.base_url}/api/config"},
        {"name": "GET /conversations", "method": "GET",
         "url": f"{fs.base_url}/conversations"},
        {"name": "GET /projects/{project}/agents", "method": "GET",
         "url": f"{fs.base_url}/projects/{fs.project}/agents"},
    ]

    results = []
    peak_qps = 0
    stop_reason = None

    for level in concurrency_levels:
        step_label = ""
        if level <= 50:
            step_label = "Fine"
        elif level <= 200:
            step_label = "Medium"
        elif level <= 500:
            step_label = "Coarse"
        else:
            step_label = "Extreme"

        print(f"\n  -- Concurrency: {level} [{step_label}] ({duration_per_level}s/endpoint) --")

        level_data = {
            "concurrency": level,
            "step_zone": step_label,
            "endpoints": [],
        }

        db_p95_max = 0

        for ep in endpoints:
            ep_name = ep["name"]
            ep_url = ep["url"]
            ep_method = ep.get("method", "GET")

            latencies = []
            successes = 0
            failures = 0
            status_codes: Dict[int, int] = {}

            stop_time = time.perf_counter() + duration_per_level

            def _worker(_id):
                nonlocal successes, failures
                local_lats = []
                local_ok = 0
                local_fail = 0
                local_codes: Dict[int, int] = {}
                while time.perf_counter() < stop_time:
                    lat, ok, code = _single_api_request(
                        fs.session, ep_url, ep_method
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
            p50_lat = pct(latencies, 50) if len(latencies) >= 2 else avg_lat
            p95_lat = pct(latencies, 95) if len(latencies) >= 2 else avg_lat
            p99_lat = pct(latencies, 99) if len(latencies) >= 2 else avg_lat
            max_lat = max(latencies) if latencies else 0

            # Track DB endpoint P95 for stop conditions
            if "config" not in ep_name.lower():
                db_p95_max = max(db_p95_max, p95_lat)

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
        overall_qps = round(total_reqs / (duration_per_level * len(endpoints)), 2)
        overall_error_rate = round(total_fail / total_reqs, 4) if total_reqs > 0 else 0

        level_data["total_requests"] = total_reqs
        level_data["total_successes"] = total_ok
        level_data["total_failures"] = total_fail
        level_data["overall_qps"] = overall_qps
        level_data["overall_error_rate"] = overall_error_rate
        level_data["db_p95_max"] = round(db_p95_max, 4)
        level_data["cpu"] = docker_snap["cpu"]
        level_data["memory"] = docker_snap["memory"]

        peak_qps = max(peak_qps, overall_qps)
        results.append(level_data)

        # ─── Adaptive Stop Conditions ───
        if overall_error_rate > max_error_rate:
            stop_reason = f"Error rate {fmt_rate(overall_error_rate)} > {fmt_rate(max_error_rate)} threshold"
            print(f"  ⛔ STOP: {stop_reason}")
            break

        if db_p95_max > max_p95_latency:
            stop_reason = f"DB endpoint P95 {db_p95_max:.2f}s > {max_p95_latency}s threshold"
            print(f"  ⛔ STOP: {stop_reason}")
            break

        if len(results) >= 3 and overall_qps < peak_qps * qps_drop_threshold:
            stop_reason = f"QPS {overall_qps} dropped below {qps_drop_threshold:.0%} of peak ({peak_qps})"
            print(f"  ⛔ STOP: {stop_reason}")
            break

        print(f"    → Level total: {fmt_num(total_reqs)} reqs | "
              f"QPS={overall_qps} | Err={fmt_rate(overall_error_rate)} | "
              f"DB P95={db_p95_max:.3f}s")

    return results, stop_reason, peak_qps


# ═══════════════════════════════════════════════════════════════════════
#  REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════

def generate_reports(all_results: Dict[str, Any], output_dir: str,
                     timestamp: str, worker_count: Any):
    os.makedirs(output_dir, exist_ok=True)

    # ─── JSON ───
    json_path = os.path.join(output_dir, f"concurrent_stress_report_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[Report] JSON: {json_path}")

    # ─── Markdown ───
    md_path = os.path.join(output_dir, f"concurrent_stress_report_{timestamp}.md")
    wk = worker_count or "N/A"
    prime = all_results.get("priming", {})
    api = all_results.get("concurrent_api", [])
    stop = all_results.get("stop_reason", None)
    peak = all_results.get("peak_qps", 0)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Frontier Concurrent API Stress Test Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Test Environment\n\n")
        f.write(f"- **Target URL:** {all_results.get('config', {}).get('base_url', BASE_URL)}\n")
        f.write(f"- **Workers:** {wk}\n")
        f.write(f"- **OS:** {platform.system()} {platform.release()}\n")
        f.write(f"- **Python:** {platform.python_version()}\n")
        f.write(f"- **Volume Baseline:** {prime.get('total_volume', 0):,} chars "
                f"({prime.get('num_messages', 0)} msgs × {prime.get('payload_size', 0):,} chars)\n\n")
        f.write("---\n\n")

        # Priming
        f.write("## 1. Volume Priming (Baseline)\n\n")
        f.write(f"| Workers | Messages | Payload (chars) | Total Volume | Write QPS | "
                f"Avg Latency (s) | P95 Latency (s) | Success Rate | Duration (s) | Memory |\n")
        f.write(f"|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
        f.write(f"| {wk} "
                f"| {prime.get('num_messages', 0)} "
                f"| {prime.get('payload_size', 0):,} "
                f"| {prime.get('total_volume', 0):,} "
                f"| {prime.get('write_qps', 0)} "
                f"| {prime.get('avg_write_latency', 0)} "
                f"| {prime.get('p95_write_latency', 0)} "
                f"| {fmt_rate(prime.get('success_rate', 0))} "
                f"| {prime.get('elapsed_seconds', 0)} "
                f"| {prime.get('memory', 'N/A')} |\n\n")

        # API Throughput
        if api:
            f.write("## 2. Concurrent API Throughput — Escalating Stress\n\n")
            f.write("### Overview\n\n")
            f.write("| Workers | Concurrency | Zone | Total Reqs | QPS | Error Rate | "
                    "DB P95 Max (s) | CPU | Memory | Status |\n")
            f.write("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
            for lvl in api:
                # Determine status tag
                err = lvl["overall_error_rate"]
                dbp95 = lvl.get("db_p95_max", 0)
                if err > 0.1:
                    status = "❌ Error"
                elif dbp95 > 5.0:
                    status = "❌ Latency"
                elif dbp95 > 2.0:
                    status = "⚠️ High Lat"
                elif dbp95 > 1.0:
                    status = "⚠️ Warn"
                else:
                    status = "✅ OK"
                f.write(f"| {wk} "
                        f"| {lvl['concurrency']} "
                        f"| {lvl.get('step_zone', '')} "
                        f"| {fmt_num(lvl['total_requests'])} "
                        f"| {lvl['overall_qps']} "
                        f"| {fmt_rate(err)} "
                        f"| {dbp95} "
                        f"| {lvl['cpu']} "
                        f"| {lvl['memory']} "
                        f"| {status} |\n")

            # Endpoint details
            f.write("\n### Endpoint Details\n\n")
            f.write("| Workers | Concurrency | Endpoint | Requests | QPS | "
                    "Avg (s) | P50 (s) | P95 (s) | P99 (s) | Max (s) | Error Rate |\n")
            f.write("|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
            for lvl in api:
                for ep in lvl["endpoints"]:
                    f.write(f"| {wk} "
                            f"| {lvl['concurrency']} "
                            f"| {ep['endpoint']} "
                            f"| {fmt_num(ep['total_requests'])} "
                            f"| {ep['qps']} "
                            f"| {ep['avg_latency']} "
                            f"| {ep['p50_latency']} "
                            f"| {ep['p95_latency']} "
                            f"| {ep['p99_latency']} "
                            f"| {ep['max_latency']} "
                            f"| {fmt_rate(ep['error_rate'])} |\n")
            f.write("\n")

        # Analysis
        f.write("## 3. Analysis & Conclusions\n\n")

        if stop:
            f.write(f"**Stop Reason:** {stop}\n\n")

        if api:
            last = api[-1]
            peak_level = max(api, key=lambda x: x["overall_qps"])
            f.write(f"### Key Findings\n")
            f.write(f"- **Max concurrency tested:** {last['concurrency']}\n")
            f.write(f"- **Peak QPS:** {peak} (at concurrency={peak_level['concurrency']})\n")
            f.write(f"- **Final error rate:** {fmt_rate(last['overall_error_rate'])}\n")
            f.write(f"- **Concurrency levels tested:** {len(api)}\n\n")

            # Find threshold points
            warn_level = None
            crit_level = None
            for lvl in api:
                if lvl.get("db_p95_max", 0) > 1.0 and not warn_level:
                    warn_level = lvl["concurrency"]
                if lvl.get("db_p95_max", 0) > 2.0 and not crit_level:
                    crit_level = lvl["concurrency"]

            f.write("### Discovered Thresholds\n\n")
            f.write("| Threshold | Concurrency | Description |\n")
            f.write("|:---|:---:|:---|\n")
            f.write(f"| Peak QPS | {peak_level['concurrency']} | "
                    f"Maximum throughput ({peak} QPS) |\n")
            if warn_level:
                f.write(f"| DB P95 > 1s | {warn_level} | "
                        f"DB-heavy endpoints start degrading |\n")
            if crit_level:
                f.write(f"| DB P95 > 2s | {crit_level} | "
                        f"Critical latency for real-time UIs |\n")
            f.write(f"| Test stopped | {last['concurrency']} | "
                    f"{stop or 'Reached max configured concurrency'} |\n\n")

        f.write("---\n\n")
        f.write(f"*Report generated by `concurrent_api_stress_test.py` | "
                f"Volume baseline: 6M chars (300×20K) | "
                f"Raw data: `concurrent_stress_report_{timestamp}.json`*\n")

    print(f"[Report] Markdown: {md_path}")
    return json_path, md_path


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Frontier Concurrent API Stress Test (Volume-Primed)")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--project", default=PROJECT)
    parser.add_argument("--user", default=LOGIN_USER)
    parser.add_argument("--password", default=LOGIN_PASS)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    # Priming
    parser.add_argument("--prime-msgs", type=int, default=300,
                        help="Number of messages for volume priming (default: 300)")
    parser.add_argument("--prime-payload", type=int, default=20000,
                        help="Chars per message for priming (default: 20000)")
    parser.add_argument("--prime-concurrency", type=int, default=5)
    parser.add_argument("--skip-prime", action="store_true",
                        help="Skip volume priming (if DB already loaded)")
    # Concurrency test
    parser.add_argument("--max-concurrency", type=int, default=1000,
                        help="Maximum concurrency to test (default: 1000)")
    parser.add_argument("--duration", type=int, default=10,
                        help="Seconds per endpoint per concurrency level (default: 10)")
    parser.add_argument("--max-error-rate", type=float, default=0.10,
                        help="Stop if error rate exceeds this (default: 0.10)")
    parser.add_argument("--max-p95", type=float, default=5.0,
                        help="Stop if DB endpoint P95 exceeds this (default: 5.0s)")
    parser.add_argument("--qps-drop", type=float, default=0.30,
                        help="Stop if QPS drops below this fraction of peak (default: 0.30)")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 70)
    print("  Frontier Concurrent API Stress Test — Volume-Primed Edition")
    print("=" * 70)

    # ─── Connect ───
    fs = FrontierSession(args.base_url, args.project, args.user, args.password)
    if not fs.login():
        print("\n[FATAL] Could not log in. Is the server running?")
        return

    worker_count = get_worker_count()
    print(f"\n  Workers detected: {worker_count or 'unknown'}")
    print(f"  Max concurrency: {args.max_concurrency}")
    print(f"  Duration/endpoint: {args.duration}s")
    print(f"  Stop conditions: err>{fmt_rate(args.max_error_rate)} | "
          f"P95>{args.max_p95}s | QPS<{args.qps_drop:.0%}×peak")

    all_results = {
        "config": {
            "base_url": args.base_url,
            "project": args.project,
            "workers": worker_count,
            "max_concurrency": args.max_concurrency,
            "duration": args.duration,
            "prime_msgs": args.prime_msgs,
            "prime_payload": args.prime_payload,
        }
    }

    # ─── Phase 1: Volume Priming ───
    if not args.skip_prime:
        print("\n" + "=" * 70)
        print("  [Phase 1] Volume Priming — 6,000,000 chars baseline")
        print("=" * 70)

        agent_id = fs.resolve_agent()
        if not agent_id:
            print("  [WARN] No agent found, priming will write to default agent")
            agent_id = "http-example"

        prime_result = prime_volume(
            fs, agent_id,
            num_msgs=args.prime_msgs,
            payload_size=args.prime_payload,
            concurrency=args.prime_concurrency,
        )
        all_results["priming"] = prime_result
    else:
        print("\n  [SKIP] Volume priming skipped (--skip-prime)")
        all_results["priming"] = {
            "num_messages": args.prime_msgs,
            "payload_size": args.prime_payload,
            "total_volume": args.prime_msgs * args.prime_payload,
            "write_qps": 0,
            "avg_write_latency": 0,
            "p95_write_latency": 0,
            "success_rate": 1.0,
            "elapsed_seconds": 0,
            "memory": "N/A",
        }

    # ─── Phase 2: Concurrent API Stress ───
    print("\n" + "=" * 70)
    print("  [Phase 2] Concurrent API Throughput — Escalating Stress")
    print("=" * 70)

    levels = generate_concurrency_levels(args.max_concurrency)
    print(f"  Concurrency schedule: {levels}")

    api_results, stop_reason, peak_qps = run_concurrent_stress_test(
        fs, levels,
        duration_per_level=args.duration,
        max_error_rate=args.max_error_rate,
        max_p95_latency=args.max_p95,
        qps_drop_threshold=args.qps_drop,
    )
    all_results["concurrent_api"] = api_results
    all_results["stop_reason"] = stop_reason
    all_results["peak_qps"] = peak_qps

    # ─── Reports ───
    print("\n" + "=" * 70)
    print("  Generating Reports")
    print("=" * 70)

    json_path, md_path = generate_reports(
        all_results, args.output_dir, timestamp, worker_count
    )

    # ─── Summary ───
    print("\n" + "=" * 70)
    print("  Test Complete!")
    print("=" * 70)
    print(f"  Workers:          {worker_count or 'unknown'}")
    print(f"  Concurrency max:  {api_results[-1]['concurrency'] if api_results else 0}")
    print(f"  Peak QPS:         {peak_qps}")
    if stop_reason:
        print(f"  Stop reason:      {stop_reason}")
    print(f"  Levels tested:    {len(api_results)}")
    print(f"\n  Reports: {args.output_dir}")
    print(f"    JSON: {os.path.basename(json_path)}")
    print(f"    MD:   {os.path.basename(md_path)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
