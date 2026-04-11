#!/usr/bin/env python3
"""
Volume-Concurrency Stress Test
================================
Holds volume constant at the discovered peak (300 msgs × 20K chars = 6M chars)
and gradually ramps up concurrency from 1 to 30 to find the write throughput
ceiling under realistic large-payload conditions.

Outputs: JSON data + Markdown report to frontier/perf/multiworker/

Usage:
  python volume_concurrency_stress_test.py
  python volume_concurrency_stress_test.py --concurrency-levels 1,3,5,10,15,20,25,30
"""

import time
import json
import subprocess
import argparse
import statistics
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

# Fixed volume: peak discovered in previous tests
FIXED_MSGS = 300
FIXED_PAYLOAD = 20000  # chars per message
FIXED_VOLUME = FIXED_MSGS * FIXED_PAYLOAD  # 6,000,000 chars

# Output directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTIER_HUB = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUTPUT_DIR = os.path.join(FRONTIER_HUB, "frontier", "perf", "multiworker")


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


def get_worker_count_from_docker(container: str = "frontier-server") -> Optional[int]:
    try:
        out = subprocess.check_output(
            ["docker", "exec", container, "python3", "-c",
             "import yaml; c=yaml.safe_load(open('/app/config.yaml')); print(c.get('server',{}).get('workers',1))"],
            stderr=subprocess.DEVNULL, timeout=5
        ).decode().strip()
        return int(out)
    except Exception:
        pass
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


def percentile(data: List[float], pct: int) -> float:
    if len(data) < 2:
        return data[0] if data else 0.0
    quantiles = statistics.quantiles(data, n=100)
    idx = min(pct - 1, len(quantiles) - 1)
    return quantiles[idx]


def fmt_rate(rate: float) -> str:
    return f"{rate:.2%}"


# ═══════════════════════════════════════════════════════════════════════
#  SESSION
# ═══════════════════════════════════════════════════════════════════════

class FrontierSession:
    def __init__(self, base_url, project, username, password):
        self.base_url = base_url.rstrip("/")
        self.project = project
        self.session = requests.Session()
        self.token = None
        self._login(username, password)

    def _login(self, username, password):
        resp = self.session.post(
            f"{self.base_url}/login",
            json={"username": username, "password": password},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data.get("access_token") or data.get("token")
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "X-Project": self.project,
        })

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

    def create_conversation(self) -> str:
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
#  CHAT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def send_chat(sess: requests.Session, base_url: str, conv_id: str,
              agent_id: str, message: str) -> Tuple[float, bool, int]:
    start = time.perf_counter()
    try:
        resp = sess.post(
            f"{base_url}/chat",
            json={
                "conversation_id": conv_id,
                "agent_id": agent_id,
                "message": message,
                "client_context": {"source": "volume-concurrency-stress-test"},
            },
            timeout=120,
            stream=True,
        )
        total_bytes = 0
        for chunk in resp.iter_content(chunk_size=4096):
            total_bytes += len(chunk)
        latency = time.perf_counter() - start
        return latency, resp.status_code < 400, total_bytes
    except Exception:
        return time.perf_counter() - start, False, 0


def read_messages(sess: requests.Session, base_url: str,
                  conv_id: str) -> Tuple[float, bool, int]:
    start = time.perf_counter()
    try:
        resp = sess.get(f"{base_url}/conversations/{conv_id}/messages", timeout=60)
        latency = time.perf_counter() - start
        return latency, resp.status_code < 400, len(resp.content)
    except Exception:
        return time.perf_counter() - start, False, 0


# ═══════════════════════════════════════════════════════════════════════
#  MAIN TEST: FIXED VOLUME + RAMPING CONCURRENCY
# ═══════════════════════════════════════════════════════════════════════

def run_volume_concurrency_test(
    fs: FrontierSession,
    agent_id: Optional[str],
    num_messages: int,
    payload_size: int,
    concurrency_levels: List[int],
) -> List[Dict[str, Any]]:
    """
    For each concurrency level:
      1. Create a fresh conversation
      2. Write `num_messages` messages of `payload_size` chars at `concurrency` parallelism
      3. Read back the history
      4. Record QPS, latency, success rate
      5. Delete the conversation
    """
    results = []
    large_text = generate_large_text(payload_size)
    total_volume = num_messages * payload_size

    for conc in concurrency_levels:
        print(f"\n{'='*70}")
        print(f"  CONCURRENCY={conc} | {num_messages} msgs x {payload_size:,} chars = {total_volume:,} chars")
        print(f"{'='*70}")

        # --- Create conversation ---
        try:
            conv_id = fs.create_conversation()
        except Exception as e:
            print(f"  FATAL: Cannot create conversation: {e}")
            results.append({
                "concurrency": conc, "num_messages": num_messages,
                "payload_size": payload_size, "total_volume_chars": total_volume,
                "error": str(e), "success_rate": 0,
            })
            continue

        # --- Write phase ---
        write_lats = []
        write_ok = 0
        write_fail = 0
        write_start = time.perf_counter()
        progress_step = max(1, num_messages // 5)

        if conc <= 1:
            for i in range(num_messages):
                msg = f"[Msg {i+1}/{num_messages}] " + large_text[:payload_size - 30]
                lat, ok, _ = send_chat(fs.session, fs.base_url, conv_id, agent_id, msg)
                write_lats.append(lat)
                if ok:
                    write_ok += 1
                else:
                    write_fail += 1
                if (i + 1) % progress_step == 0 or i == num_messages - 1:
                    ds = get_docker_stats()
                    elapsed = time.perf_counter() - write_start
                    cur_qps = (i + 1) / elapsed if elapsed > 0 else 0
                    print(f"    [Write {i+1}/{num_messages}] lat={lat:.3f}s | "
                          f"QPS={cur_qps:.1f} | CPU={ds['cpu']} | MEM={ds['memory']}")
        else:
            def _write_one(idx):
                msg = f"[Msg {idx+1}/{num_messages}] " + large_text[:payload_size - 30]
                return send_chat(fs.session, fs.base_url, conv_id, agent_id, msg)

            with ThreadPoolExecutor(max_workers=conc) as pool:
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
                    if done % progress_step == 0 or done == num_messages:
                        ds = get_docker_stats()
                        elapsed = time.perf_counter() - write_start
                        cur_qps = done / elapsed if elapsed > 0 else 0
                        print(f"    [Write {done}/{num_messages}] lat={lat:.3f}s | "
                              f"QPS={cur_qps:.1f} | CPU={ds['cpu']} | MEM={ds['memory']}")

        write_elapsed = time.perf_counter() - write_start
        write_qps = num_messages / write_elapsed if write_elapsed > 0 else 0

        # --- Read phase ---
        read_rounds = 5
        read_lats = []
        read_ok = 0
        read_fail = 0

        for r in range(read_rounds):
            lat, ok, resp_size = read_messages(fs.session, fs.base_url, conv_id)
            read_lats.append(lat)
            if ok:
                read_ok += 1
            else:
                read_fail += 1

        # --- Cleanup ---
        fs.delete_conversation(conv_id)

        # --- Stats ---
        docker = get_docker_stats()
        total_reqs = num_messages + read_rounds
        total_ok = write_ok + read_ok
        success_rate = total_ok / total_reqs if total_reqs > 0 else 0

        avg_write = statistics.mean(write_lats) if write_lats else 0
        p50_write = percentile(write_lats, 50) if len(write_lats) >= 2 else avg_write
        p95_write = percentile(write_lats, 95) if len(write_lats) >= 2 else avg_write
        p99_write = percentile(write_lats, 99) if len(write_lats) >= 2 else avg_write
        max_write = max(write_lats) if write_lats else 0

        avg_read = statistics.mean(read_lats) if read_lats else 0
        p95_read = percentile(read_lats, 95) if len(read_lats) >= 2 else avg_read
        read_qps = read_rounds / sum(read_lats) if sum(read_lats) > 0 else 0

        result = {
            "concurrency": conc,
            "num_messages": num_messages,
            "payload_size": payload_size,
            "total_volume_chars": total_volume,
            # Write metrics
            "write_qps": round(write_qps, 2),
            "write_elapsed": round(write_elapsed, 2),
            "avg_write_latency": round(avg_write, 4),
            "p50_write_latency": round(p50_write, 4),
            "p95_write_latency": round(p95_write, 4),
            "p99_write_latency": round(p99_write, 4),
            "max_write_latency": round(max_write, 4),
            "write_success": write_ok,
            "write_failure": write_fail,
            # Read metrics
            "read_qps": round(read_qps, 2),
            "avg_read_latency": round(avg_read, 4),
            "p95_read_latency": round(p95_read, 4),
            # Overall
            "success_rate": round(success_rate, 4),
            "cpu": docker["cpu"],
            "memory": docker["memory"],
        }
        results.append(result)

        print(f"\n  [OK] Summary C={conc}: Write QPS={write_qps:.2f} | "
              f"Avg Write={avg_write:.3f}s | P95 Write={p95_write:.3f}s | "
              f"Success={fmt_rate(success_rate)} | CPU={docker['cpu']} | MEM={docker['memory']}")

        # Stop if too many failures
        if success_rate < 0.80:
            print(f"  [!] Success rate {fmt_rate(success_rate)} < 80% -- stopping ramp-up")
            break

    return results


# ═══════════════════════════════════════════════════════════════════════
#  REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════

def generate_report(results: List[Dict], worker_count: Any, timestamp: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    wk = worker_count or "N/A"

    # — JSON —
    json_path = os.path.join(OUTPUT_DIR, f"volume_concurrency_stress_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"worker_count": wk, "fixed_volume": FIXED_VOLUME,
                    "fixed_msgs": FIXED_MSGS, "fixed_payload": FIXED_PAYLOAD,
                    "results": results}, f, indent=2, default=str)
    print(f"\n[Report] JSON: {json_path}")

    # — Markdown —
    md_path = os.path.join(OUTPUT_DIR, f"volume_concurrency_stress_report_{timestamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Volume-Concurrency Stress Test Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Test Design\n\n")
        f.write(f"- **Fixed Volume:** {FIXED_MSGS} msgs × {FIXED_PAYLOAD:,} chars = **{FIXED_VOLUME:,} chars (6M)**\n")
        f.write(f"- **Workers:** {wk}\n")
        f.write(f"- **Variable:** Concurrency (write parallelism)\n")
        f.write(f"- **Goal:** Find write QPS ceiling at peak volume under increasing concurrency\n\n")
        f.write("---\n\n")

        # Table 1: Main results
        f.write("## Results\n\n")
        f.write("| Workers | Concurrency | Msgs | Payload | Volume | Write QPS | "
                "Avg Write (s) | P50 Write (s) | P95 Write (s) | P99 Write (s) | "
                "Max Write (s) | Read QPS | Success Rate | CPU | Memory |\n")
        f.write("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
        for r in results:
            f.write(f"| {wk} "
                    f"| {r['concurrency']} "
                    f"| {r['num_messages']} "
                    f"| {r['payload_size']:,} "
                    f"| {r['total_volume_chars']:,} "
                    f"| {r['write_qps']} "
                    f"| {r['avg_write_latency']} "
                    f"| {r['p50_write_latency']} "
                    f"| {r['p95_write_latency']} "
                    f"| {r['p99_write_latency']} "
                    f"| {r['max_write_latency']} "
                    f"| {r['read_qps']} "
                    f"| {fmt_rate(r['success_rate'])} "
                    f"| {r['cpu']} "
                    f"| {r['memory']} |\n")

        # Analysis
        f.write("\n## Analysis\n\n")
        if results:
            peak = max(results, key=lambda x: x["write_qps"])
            last = results[-1]
            f.write(f"- **Peak Write QPS:** {peak['write_qps']} at concurrency={peak['concurrency']}\n")
            f.write(f"- **Peak Write QPS P95 Latency:** {peak['p95_write_latency']}s\n")
            f.write(f"- **Max Concurrency Tested:** {last['concurrency']}\n")
            f.write(f"- **Final Success Rate:** {fmt_rate(last['success_rate'])}\n\n")

            # Check for QPS plateau
            qps_values = [r["write_qps"] for r in results]
            if len(qps_values) >= 3:
                max_qps = max(qps_values)
                peak_idx = qps_values.index(max_qps)
                if peak_idx < len(qps_values) - 1:
                    decline = [(max_qps - q) / max_qps * 100 for q in qps_values[peak_idx+1:]]
                    if any(d > 10 for d in decline):
                        f.write(f"⚠️ QPS declined after concurrency={results[peak_idx]['concurrency']} "
                                f"— likely hitting DB connection pool or GIL contention\n\n")

        f.write("---\n\n")
        f.write(f"*Generated by `volume_concurrency_stress_test.py` | "
                f"Raw data: `volume_concurrency_stress_{timestamp}.json`*\n")

    print(f"[Report] Markdown: {md_path}")
    return json_path, md_path


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Volume-Concurrency Stress Test")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--project", default=PROJECT)
    parser.add_argument("--concurrency-levels", default="1,3,5,8,10,15,20,25,30",
                        help="Comma-separated concurrency levels to test")
    parser.add_argument("--msgs", type=int, default=FIXED_MSGS,
                        help=f"Number of messages per test (default: {FIXED_MSGS})")
    parser.add_argument("--payload", type=int, default=FIXED_PAYLOAD,
                        help=f"Chars per message (default: {FIXED_PAYLOAD})")
    args = parser.parse_args()

    concurrency_levels = [int(x.strip()) for x in args.concurrency_levels.split(",")]

    print("=" * 70)
    print("  Volume-Concurrency Stress Test")
    print(f"  Fixed: {args.msgs} msgs x {args.payload:,} chars = {args.msgs * args.payload:,} chars")
    print(f"  Variable: Concurrency {concurrency_levels}")
    print("=" * 70)

    # Login
    print("\n[1/3] Logging in...")
    fs = FrontierSession(args.base_url, args.project, LOGIN_USER, LOGIN_PASS)
    print("  [OK] Login OK")

    # Resolve agent
    print("\n[2/3] Resolving agent...")
    agent_id = fs.resolve_agent()
    print(f"  [OK] Agent: {agent_id or 'default'}")

    # Detect workers
    worker_count = get_worker_count_from_docker()
    print(f"  Workers: {worker_count or 'unknown'}")

    # Run test
    print(f"\n[3/3] Running volume-concurrency stress test...")
    results = run_volume_concurrency_test(
        fs, agent_id, args.msgs, args.payload, concurrency_levels
    )

    # Report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    generate_report(results, worker_count, timestamp)

    print("\n" + "=" * 70)
    print("  TEST COMPLETE")
    print("=" * 70)

    # Quick summary
    if results:
        peak = max(results, key=lambda x: x["write_qps"])
        print(f"\n  Peak Write QPS: {peak['write_qps']} @ concurrency={peak['concurrency']}")
        print(f"  P95 Latency at peak: {peak['p95_write_latency']}s")
        for r in results:
            status = "[OK]" if r["success_rate"] >= 0.99 else "[WARN]" if r["success_rate"] >= 0.90 else "[FAIL]"
            print(f"    C={r['concurrency']:3d}  QPS={r['write_qps']:7.2f}  "
                  f"P95={r['p95_write_latency']:.3f}s  "
                  f"Success={fmt_rate(r['success_rate'])}  {status}")


if __name__ == "__main__":
    main()
