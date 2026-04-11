#!/usr/bin/env python3
"""
Frontier Worker-Scaling Volume Test
=====================================
Measures how growing conversation history volume affects latency and throughput
at different Gunicorn worker counts. Finds the threshold (success_rate or p95)
for each worker configuration.

Design
------
- Each stage creates ONE conversation, sends N chat messages into it (concurrent),
  then reads back the full history multiple times to measure read degradation.
- Chat uses the real /chat SSE endpoint (echo agent) — same as production path.
- Concurrency is kept at 5 (matching existing reports) for comparability.
- Reports go to perf/ folder, format matches volume_payload_test_report exactly
  but with an added Workers column.

Usage
-----
  # Test current running server (no restart):
  python perf/per-tst-workers/worker_volume_test.py --no-restart --workers 1

  # Auto-restart with different worker counts (needs pyyaml):
  python perf/per-tst-workers/worker_volume_test.py --worker-counts 1 2 4

  # Match existing report parameters exactly:
  python perf/per-tst-workers/worker_volume_test.py --no-restart --workers 1 \\
      --start-msgs 100 --step-msgs 100 --max-msgs 1000 --payload-size 20000 --concurrency 5
"""

import argparse
import json
import os
import random
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests

# ── Defaults ──────────────────────────────────────────────────────────────────
BASE_URL    = "http://localhost:8000"
PROJECT     = "demo"
CONFIG_YAML = Path(__file__).resolve().parents[2] / "config.yaml"
PROJECT_PY  = Path(__file__).resolve().parents[2] / "project.py"

WORDS = [
    "performance", "testing", "volume", "payload", "frontier",
    "system", "database", "query", "latency", "throughput",
    "conversation", "message", "history", "analysis", "benchmark",
    "optimization", "scalability", "resilience", "capacity", "threshold",
    "worker", "gunicorn", "uvicorn", "concurrency", "parallel",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def gen_text(size: int) -> str:
    out, n = [], 0
    while n < size:
        w = random.choice(WORDS)
        out.append(w)
        n += len(w) + 1
    return " ".join(out)[:size]


def get_docker_stats(container="frontier-server"):
    try:
        out = subprocess.check_output(
            ["docker", "stats", "--no-stream", "--format",
             "{{.CPUPerc}}|{{.MemUsage}}", container],
            stderr=subprocess.DEVNULL, timeout=3,
        ).decode().strip()
        if "|" in out:
            p = out.split("|")
            return p[0].strip(), p[1].strip()
    except Exception:
        pass
    return "N/A", "N/A"


# ── Auth / session ─────────────────────────────────────────────────────────────

def login(base_url, username, password, project):
    sess = requests.Session()
    r = sess.post(f"{base_url}/login",
                  json={"username": username, "password": password}, timeout=15)
    r.raise_for_status()
    token = r.json().get("access_token") or r.json().get("token")
    sess.headers.update({"Authorization": f"Bearer {token}", "X-Project": project})
    return sess


def resolve_agent(sess, base_url, project):
    try:
        r = sess.get(f"{base_url}/projects/{project}/agents", timeout=10)
        if r.status_code == 200:
            lst = r.json() if isinstance(r.json(), list) else r.json().get("agents", [])
            if lst:
                return lst[0]["id"]
    except Exception:
        pass
    return None


# ── Per-request ops ────────────────────────────────────────────────────────────

def create_conv(sess, base_url, title="vol-test"):
    r = sess.post(f"{base_url}/conversations", json={"title": title}, timeout=15)
    r.raise_for_status()
    return r.json()["id"]


def send_chat(sess, base_url, conv_id, agent_id, msg):
    t0 = time.perf_counter()
    try:
        r = sess.post(
            f"{base_url}/chat",
            json={"conversation_id": conv_id, "agent_id": agent_id,
                  "message": msg, "client_context": {"source": "worker-vol-test"}},
            timeout=60, stream=True,
        )
        for _ in r.iter_content(chunk_size=4096):
            pass
        return time.perf_counter() - t0, r.status_code < 400
    except Exception:
        return time.perf_counter() - t0, False


def read_msgs(sess, base_url, conv_id):
    t0 = time.perf_counter()
    try:
        r = sess.get(f"{base_url}/conversations/{conv_id}/messages", timeout=30)
        return time.perf_counter() - t0, r.status_code < 400, len(r.content)
    except Exception:
        return time.perf_counter() - t0, False, 0


def del_conv(sess, base_url, conv_id):
    try:
        sess.delete(f"{base_url}/conversations/{conv_id}", timeout=10)
    except Exception:
        pass


# ── Stage runner ───────────────────────────────────────────────────────────────

def run_stage(stage_num, num_msgs, payload_size, concurrency,
              sess, agent_id, base_url, workers):
    total_vol = num_msgs * payload_size
    print(f"  [Stage {stage_num}] workers={workers} | msgs={num_msgs} | "
          f"payload={payload_size:,} | volume={total_vol:,} | conc={concurrency}")

    try:
        conv_id = create_conv(sess, base_url, f"vol-w{workers}-s{stage_num}")
    except Exception as e:
        return _empty(stage_num, num_msgs, payload_size, concurrency, workers, str(e))

    base_text = gen_text(payload_size)
    w_lats, w_ok, w_fail = [], 0, 0

    # ── Concurrent writes ──
    t_write_start = time.perf_counter()

    def _send(idx):
        msg = f"[W{workers}-S{stage_num}-M{idx+1}] " + base_text[:max(1, payload_size - 25)]
        return send_chat(sess, base_url, conv_id, agent_id, msg)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futs = {pool.submit(_send, i): i for i in range(num_msgs)}
        for fut in as_completed(futs):
            lat, ok = fut.result()
            w_lats.append(lat)
            if ok:
                w_ok += 1
            else:
                w_fail += 1

    write_elapsed = time.perf_counter() - t_write_start
    write_qps = num_msgs / write_elapsed if write_elapsed > 0 else 0

    # ── Read-back (scale rounds with volume) ──
    read_rounds = min(5, max(2, num_msgs // 100))
    r_lats, r_ok, r_fail = [], 0, 0
    t_read_start = time.perf_counter()
    for _ in range(read_rounds):
        lat, ok, _ = read_msgs(sess, base_url, conv_id)
        r_lats.append(lat)
        if ok:
            r_ok += 1
        else:
            r_fail += 1
    read_elapsed = time.perf_counter() - t_read_start
    read_qps = read_rounds / read_elapsed if read_elapsed > 0 else 0

    cpu, mem = get_docker_stats()
    del_conv(sess, base_url, conv_id)

    total_reqs = num_msgs + read_rounds
    success_rate = (w_ok + r_ok) / total_reqs if total_reqs > 0 else 0
    all_lats = w_lats + r_lats
    avg_lat = statistics.mean(all_lats) if all_lats else 0
    p95_lat = statistics.quantiles(all_lats, n=100)[94] if len(all_lats) >= 2 else avg_lat
    overall_qps = total_reqs / (write_elapsed + read_elapsed) if (write_elapsed + read_elapsed) > 0 else 0

    result = {
        "stage": stage_num, "workers": workers,
        "num_messages": num_msgs, "payload_size": payload_size,
        "total_volume_chars": total_vol, "concurrency": concurrency,
        "overall_qps": round(overall_qps, 2),
        "write_qps": round(write_qps, 2),
        "read_qps": round(read_qps, 2),
        "avg_write_latency": round(statistics.mean(w_lats), 3) if w_lats else 0,
        "p95_write_latency": round(statistics.quantiles(w_lats, n=100)[94], 3) if len(w_lats) >= 2 else 0,
        "avg_read_latency": round(statistics.mean(r_lats), 3) if r_lats else 0,
        "p95_read_latency": round(statistics.quantiles(r_lats, n=100)[94], 3) if len(r_lats) >= 2 else 0,
        "avg_latency": round(avg_lat, 3),
        "p95_latency": round(p95_lat, 3),
        "success_rate": round(success_rate, 4),
        "cpu": cpu, "memory": mem,
        "write_failures": w_fail, "read_failures": r_fail,
    }

    status = "✓" if success_rate >= 0.90 else "✗ THRESHOLD"
    print(f"    {status} QPS={result['overall_qps']} | p95={result['p95_latency']}s | "
          f"success={result['success_rate']:.2%} | CPU={cpu} | MEM={mem}")
    return result


def _empty(stage_num, num_msgs, payload_size, concurrency, workers, error):
    return {
        "stage": stage_num, "workers": workers,
        "num_messages": num_msgs, "payload_size": payload_size,
        "total_volume_chars": num_msgs * payload_size, "concurrency": concurrency,
        "overall_qps": 0, "write_qps": 0, "read_qps": 0,
        "avg_write_latency": 0, "p95_write_latency": 0,
        "avg_read_latency": 0, "p95_read_latency": 0,
        "avg_latency": 0, "p95_latency": 0,
        "success_rate": 0, "cpu": "N/A", "memory": "N/A",
        "write_failures": num_msgs, "read_failures": 0, "error": error,
    }


# ── Server lifecycle ───────────────────────────────────────────────────────────

_server_proc = None


def patch_config(n, config_path):
    try:
        import yaml
    except ImportError:
        print("  [WARN] pyyaml not installed — cannot patch config.yaml")
        return False
    data = {}
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
    if "server" not in data or not isinstance(data["server"], dict):
        data["server"] = {}
    data["server"]["workers"] = n
    data["server"]["reload"] = False
    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    print(f"  [Config] server.workers={n}")
    return True


def start_server(workers, config_path, project_py, base_url):
    global _server_proc
    stop_server()
    if not patch_config(workers, config_path):
        return False
    env = os.environ.copy()
    env["CONFIG_FILE"] = str(config_path)
    print(f"  [Server] Starting {workers} worker(s)...")
    _server_proc = subprocess.Popen(
        [sys.executable, str(project_py)], env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        time.sleep(1)
        try:
            if requests.get(f"{base_url}/config", timeout=2).status_code < 500:
                print(f"  [Server] Ready (pid={_server_proc.pid})")
                return True
        except Exception:
            pass
    print("  [Server] WARN: did not respond in 30s, continuing anyway")
    return True


def stop_server():
    global _server_proc
    if _server_proc and _server_proc.poll() is None:
        print(f"  [Server] Stopping pid={_server_proc.pid}...")
        _server_proc.terminate()
        try:
            _server_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _server_proc.kill()
        _server_proc = None
        time.sleep(2)


# ── Per-worker run ─────────────────────────────────────────────────────────────

def run_worker_config(workers, args, auto_restart):
    print(f"\n{'='*60}")
    print(f"  WORKER CONFIG: {workers} worker(s)")
    print(f"{'='*60}")

    if auto_restart:
        if not start_server(workers, CONFIG_YAML, PROJECT_PY, args.url):
            print(f"  [SKIP] Could not start server with {workers} workers.")
            return []
        time.sleep(1)

    try:
        sess = login(args.url, args.username, args.password, args.project)
        print("  [Auth] OK")
    except Exception as e:
        print(f"  [Auth] FAILED: {e}")
        return []

    agent_id = resolve_agent(sess, args.url, args.project)
    if not agent_id:
        print("  [WARN] No agent found — chat will fail")
    else:
        print(f"  [Agent] id={agent_id}")

    results, num_msgs = [], args.start_msgs
    stage = 0

    while num_msgs <= args.max_msgs:
        stage += 1
        r = run_stage(stage, num_msgs, args.payload_size,
                      args.concurrency, sess, agent_id, args.url, workers)
        results.append(r)

        hit_sr = r["success_rate"] < args.threshold
        hit_lat = args.latency_threshold > 0 and r["p95_latency"] > args.latency_threshold
        if hit_sr or hit_lat:
            reasons = []
            if hit_sr:
                reasons.append(f"success_rate={r['success_rate']:.2%} < {args.threshold:.0%}")
            if hit_lat:
                reasons.append(f"p95={r['p95_latency']}s > {args.latency_threshold}s")
            print(f"\n  *** THRESHOLD: {' | '.join(reasons)} at {num_msgs} msgs ***")
            break

        num_msgs += args.step_msgs

    if not results or results[-1]["success_rate"] >= args.threshold:
        print(f"\n  [OK] All stages passed for {workers} worker(s)")

    return results


# ── Report ─────────────────────────────────────────────────────────────────────

def write_report(all_results, args, timestamp):
    # Output to perf/ (parent of per-tst-workers/)
    out_dir = Path(__file__).parent.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = out_dir / f"worker_volume_report_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "config": vars(args) | {"timestamp": timestamp},
            "results_by_workers": {str(w): v for w, v in all_results.items()},
        }, f, indent=2, ensure_ascii=False)

    # Markdown
    md_path = out_dir / f"worker_volume_report_{timestamp}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        _write_md(f, all_results, args, timestamp)

    print(f"\nJSON   → {json_path}")
    print(f"Report → {md_path}")
    return md_path


def _write_md(f, all_results, args, timestamp):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write("# Frontier Worker-Scaling Volume Test Report\n\n")
    f.write(f"**Date:** {now}\n\n")
    f.write("**Test Configuration:**\n")
    f.write(f"- Worker Counts Tested: {sorted(all_results.keys())}\n")
    f.write(f"- Payload Size: {args.payload_size:,} chars per message\n")
    f.write(f"- Volume Ramp: {args.start_msgs} → {args.max_msgs} messages (step {args.step_msgs})\n")
    f.write(f"- Concurrency: {args.concurrency}\n")
    f.write(f"- Success Rate Threshold: < {args.threshold:.0%}\n")
    if args.latency_threshold > 0:
        f.write(f"- P95 Latency Threshold: > {args.latency_threshold}s\n")
    f.write("\n")

    # ── Main results table ──
    f.write("## Results\n\n")
    f.write("| Workers | Request (msgs) | Payload (chars) | Volume (total chars) | QPS | Concurrency | Memory | CPU Usage | Avg Latency (s) | P95 Latency (s) | Success Rate |\n")
    f.write("|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|\n")
    for w in sorted(all_results):
        for r in all_results[w]:
            f.write(
                f"| {r['workers']} "
                f"| {r['num_messages']} "
                f"| {r['payload_size']:,} "
                f"| {r['total_volume_chars']:,} "
                f"| {r['overall_qps']} "
                f"| {r['concurrency']} "
                f"| {r['memory']} "
                f"| {r['cpu']} "
                f"| {r['avg_latency']} "
                f"| {r['p95_latency']} "
                f"| {r['success_rate']:.2%} |\n"
            )

    # ── Write vs Read breakdown ──
    f.write("\n## Write vs Read Breakdown\n\n")
    f.write("| Workers | Stage | Messages | Write QPS | Avg Write Lat (s) | P95 Write Lat (s) | Read QPS | Avg Read Lat (s) | P95 Read Lat (s) | Write Failures | Read Failures |\n")
    f.write("|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|\n")
    for w in sorted(all_results):
        for r in all_results[w]:
            f.write(
                f"| {r['workers']} "
                f"| {r['stage']} "
                f"| {r['num_messages']} "
                f"| {r['write_qps']} "
                f"| {r['avg_write_latency']} "
                f"| {r['p95_write_latency']} "
                f"| {r['read_qps']} "
                f"| {r['avg_read_latency']} "
                f"| {r['p95_read_latency']} "
                f"| {r['write_failures']} "
                f"| {r['read_failures']} |\n"
            )

    # ── Threshold summary ──
    f.write("\n## Threshold Summary by Worker Count\n\n")
    f.write("| Workers | Max Msgs Passed | Threshold Hit At | P95 at Threshold (s) | Success Rate at Threshold | Reason |\n")
    f.write("|:-:|:-:|:-:|:-:|:-:|:--|\n")
    for w in sorted(all_results):
        stages = all_results[w]
        if not stages:
            f.write(f"| {w} | — | — | — | — | No data |\n")
            continue
        last = stages[-1]
        hit_sr = last["success_rate"] < args.threshold
        hit_lat = args.latency_threshold > 0 and last["p95_latency"] > args.latency_threshold
        if hit_sr or hit_lat:
            reasons = []
            if hit_sr:
                reasons.append(f"success_rate={last['success_rate']:.2%}")
            if hit_lat:
                reasons.append(f"p95={last['p95_latency']}s")
            prev = stages[-2]["num_messages"] if len(stages) >= 2 else "—"
            f.write(f"| {w} | {prev} | {last['num_messages']} msgs | {last['p95_latency']} | {last['success_rate']:.2%} | {', '.join(reasons)} |\n")
        else:
            f.write(f"| {w} | {last['num_messages']} (max) | Not reached | {last['p95_latency']} | {last['success_rate']:.2%} | All stages passed |\n")

    # ── Analysis ──
    f.write("\n## Analysis\n\n")
    for w in sorted(all_results):
        stages = all_results[w]
        f.write(f"### {w} Worker(s)\n\n")
        if not stages:
            f.write("No data collected.\n\n")
            continue
        last = stages[-1]
        hit = last["success_rate"] < args.threshold or (
            args.latency_threshold > 0 and last["p95_latency"] > args.latency_threshold)
        if hit:
            f.write(f"**Threshold reached** at **{last['num_messages']} messages** "
                    f"({last['total_volume_chars']:,} chars total).\n\n")
            f.write(f"- Final P95 Latency: **{last['p95_latency']}s**\n")
            f.write(f"- Final Success Rate: **{last['success_rate']:.2%}**\n")
            f.write(f"- CPU at breaking point: **{last['cpu']}**\n")
            f.write(f"- Memory at breaking point: **{last['memory']}**\n\n")
        else:
            f.write(f"All stages completed successfully up to **{last['num_messages']} messages** "
                    f"({last['total_volume_chars']:,} chars) without hitting the threshold.\n\n")
            f.write(f"- Final P95 Latency: **{last['p95_latency']}s**\n")
            f.write(f"- Final Success Rate: **{last['success_rate']:.2%}**\n\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Frontier Worker-Scaling Volume Test")
    p.add_argument("--worker-counts", type=int, nargs="+", default=[1, 2, 4, 8])
    p.add_argument("--workers", type=int, default=None,
                   help="Single worker count (use with --no-restart)")
    p.add_argument("--no-restart", action="store_true",
                   help="Skip server restart; test the currently running server")
    p.add_argument("--start-msgs", type=int, default=100)
    p.add_argument("--step-msgs",  type=int, default=100)
    p.add_argument("--max-msgs",   type=int, default=1000)
    p.add_argument("--payload-size", type=int, default=20000)
    p.add_argument("--concurrency",  type=int, default=5)
    p.add_argument("--threshold",    type=float, default=0.90)
    p.add_argument("--latency-threshold", type=float, default=0,
                   help="Max p95 latency in seconds (0=disabled)")
    p.add_argument("--url",      default=BASE_URL)
    p.add_argument("--project",  default=PROJECT)
    p.add_argument("--username", default="admin")
    p.add_argument("--password", default="admin123")
    p.add_argument("--config-yaml", default=str(CONFIG_YAML))
    return p.parse_args()


def main():
    args = parse_args()
    global CONFIG_YAML, PROJECT_PY
    CONFIG_YAML = Path(args.config_yaml)

    worker_counts = [args.workers] if args.workers is not None else args.worker_counts
    auto_restart  = not args.no_restart

    print("=" * 60)
    print("  Frontier Worker-Scaling Volume Test")
    print(f"  Host:        {args.url}")
    print(f"  Workers:     {worker_counts}")
    print(f"  Payload:     {args.payload_size:,} chars/msg")
    print(f"  Ramp:        {args.start_msgs}→{args.max_msgs} msgs (step {args.step_msgs})")
    print(f"  Concurrency: {args.concurrency}")
    print(f"  Threshold:   success_rate<{args.threshold:.0%}"
          + (f", p95>{args.latency_threshold}s" if args.latency_threshold else ""))
    print(f"  Auto-restart:{auto_restart}")
    print("=" * 60)

    all_results: dict[int, list] = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        for w in worker_counts:
            all_results[w] = run_worker_config(w, args, auto_restart)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        if auto_restart:
            stop_server()

    if not any(all_results.values()):
        print("No results. Exiting.")
        sys.exit(1)

    write_report(all_results, args, timestamp)


if __name__ == "__main__":
    main()
