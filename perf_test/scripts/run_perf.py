"""
Frontier Performance Test Runner
==================================
A standalone script that runs Locust programmatically and generates
a Markdown report. No web UI required.

Usage:
  python perf/run_perf.py [options]

Options:
  --host        Base URL of the Frontier server (default: http://localhost:8000)
  --users       Peak number of concurrent users (default: 50)
  --spawn-rate  Users spawned per second (default: 5)
  --duration    Test duration in seconds (default: 60)
  --username    Login username (default: admin)
  --password    Login password (default: admin123)
  --project     Project name (default: test)
  --agent-id    Agent ID to use for chat (default: 1)
  --output-dir  Directory for reports (default: perf/reports)

Examples:
  # Quick smoke test (10 users, 30s)
  python perf/run_perf.py --users 10 --duration 30

  # Load test (100 users, 2 min)
  python perf/run_perf.py --users 100 --spawn-rate 10 --duration 120

  # Stress test (200 users, 5 min)
  python perf/run_perf.py --users 200 --spawn-rate 20 --duration 300
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Frontier Performance Test Runner")
    parser.add_argument("--host", default="http://localhost:8000", help="Target host URL")
    parser.add_argument("--users", type=int, default=50, help="Peak concurrent users")
    parser.add_argument("--spawn-rate", type=int, default=5, help="Users spawned per second")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--username", default="admin", help="Login username")
    parser.add_argument("--password", default="admin123", help="Login password")
    parser.add_argument("--project", default="test", help="Project name")
    parser.add_argument("--agent-id", type=int, default=1, help="Agent ID for chat tests")
    parser.add_argument("--output-dir", default="perf/reports", help="Report output directory")
    return parser.parse_args()


def check_locust_installed():
    try:
        import locust  # noqa: F401
        return True
    except ImportError:
        return False


def check_server_health(host: str) -> bool:
    """Verify the server is reachable before starting the test."""
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request(f"{host}/me", headers={"Authorization": "Bearer invalid"})
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as e:
        # 401 means server is up but token is invalid — that's fine
        return e.code == 401
    except Exception:
        return False
    return True


def run_locust(args, output_dir: Path) -> tuple[int, Path, Path]:
    """Run Locust as a subprocess and return (exit_code, csv_prefix, html_report)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_prefix = output_dir / f"frontier_perf_{timestamp}"
    html_report = output_dir / f"frontier_perf_{timestamp}.html"

    env = os.environ.copy()
    env["PERF_USERNAME"] = args.username
    env["PERF_PASSWORD"] = args.password
    env["PERF_PROJECT"] = args.project
    env["PERF_AGENT_ID"] = str(args.agent_id)

    locustfile = Path(__file__).parent / "locustfile.py"

    cmd = [
        sys.executable, "-m", "locust",
        "-f", str(locustfile),
        "--headless",
        "--host", args.host,
        "-u", str(args.users),
        "-r", str(args.spawn_rate),
        "-t", f"{args.duration}s",
        "--csv", str(csv_prefix),
        "--html", str(html_report),
        "--csv-full-history",
        "--only-summary",
    ]

    print(f"\n{'='*60}")
    print(f"  Frontier Performance Test")
    print(f"{'='*60}")
    print(f"  Host:        {args.host}")
    print(f"  Users:       {args.users} (spawn rate: {args.spawn_rate}/s)")
    print(f"  Duration:    {args.duration}s")
    print(f"  Project:     {args.project}")
    print(f"  Agent ID:    {args.agent_id}")
    print(f"  Reports:     {output_dir}")
    print(f"{'='*60}\n")

    start = time.time()
    result = subprocess.run(cmd, env=env)
    elapsed = time.time() - start

    print(f"\nTest completed in {elapsed:.1f}s (exit code: {result.returncode})")
    return result.returncode, csv_prefix, html_report


def parse_csv_stats(csv_prefix: Path) -> list[dict]:
    """Parse Locust CSV stats file into a list of dicts."""
    stats_file = Path(f"{csv_prefix}_stats.csv")
    if not stats_file.exists():
        return []

    import csv
    rows = []
    with open(stats_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def generate_markdown_report(args, csv_prefix: Path, html_report: Path, exit_code: int) -> Path:
    """Generate a Markdown summary report from Locust CSV output."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(f"{csv_prefix}_report.md")

    stats = parse_csv_stats(csv_prefix)

    # Determine pass/fail based on thresholds
    thresholds = {
        "p95_ms": 2000,    # 95th percentile response time < 2s
        "failure_pct": 1,  # failure rate < 1%
    }

    failures = []
    for row in stats:
        if row.get("Name") == "Aggregated":
            continue
        try:
            p95 = float(row.get("95%", 0))
            fail_pct = float(row.get("Failure Count", 0)) / max(float(row.get("Request Count", 1)), 1) * 100
            if p95 > thresholds["p95_ms"]:
                failures.append(f"  - `{row['Name']}`: p95={p95:.0f}ms > {thresholds['p95_ms']}ms threshold")
            if fail_pct > thresholds["failure_pct"]:
                failures.append(f"  - `{row['Name']}`: failure rate={fail_pct:.1f}% > {thresholds['failure_pct']}% threshold")
        except (ValueError, ZeroDivisionError):
            pass

    overall_status = "✅ PASS" if not failures and exit_code == 0 else "❌ FAIL"

    lines = [
        f"# Frontier Performance Test Report",
        f"",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Status**: {overall_status}  ",
        f"**Host**: `{args.host}`  ",
        f"**Users**: {args.users} (spawn rate: {args.spawn_rate}/s)  ",
        f"**Duration**: {args.duration}s  ",
        f"**Project**: `{args.project}`  ",
        f"",
        f"## Thresholds",
        f"",
        f"| Metric | Threshold |",
        f"|--------|-----------|",
        f"| p95 response time | < {thresholds['p95_ms']}ms |",
        f"| Failure rate | < {thresholds['failure_pct']}% |",
        f"",
    ]

    if failures:
        lines += [
            f"## ⚠️ Threshold Violations",
            f"",
        ] + failures + [""]

    if stats:
        lines += [
            f"## Request Statistics",
            f"",
            f"| Endpoint | Requests | Failures | Median (ms) | p95 (ms) | p99 (ms) | RPS |",
            f"|----------|----------|----------|-------------|----------|----------|-----|",
        ]
        for row in stats:
            name = row.get("Name", "")
            req_count = row.get("Request Count", "0")
            fail_count = row.get("Failure Count", "0")
            median = row.get("50%", "-")
            p95 = row.get("95%", "-")
            p99 = row.get("99%", "-")
            rps = row.get("Requests/s", "-")
            lines.append(f"| `{name}` | {req_count} | {fail_count} | {median} | {p95} | {p99} | {rps} |")
        lines.append("")

    lines += [
        f"## Reports",
        f"",
        f"- HTML report: `{html_report.name}`",
        f"- CSV stats:   `{csv_prefix.name}_stats.csv`",
        f"- CSV history: `{csv_prefix.name}_stats_history.csv`",
        f"",
        f"---",
        f"*Generated by `perf/run_perf.py`*",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    args = parse_args()

    if not check_locust_installed():
        print("ERROR: locust is not installed.")
        print("Install it with:  pip install locust")
        sys.exit(1)

    print(f"Checking server health at {args.host}...")
    if not check_server_health(args.host):
        print(f"WARNING: Server at {args.host} may not be reachable. Proceeding anyway...")
    else:
        print("Server is reachable.")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    exit_code, csv_prefix, html_report = run_locust(args, output_dir)

    report_path = generate_markdown_report(args, csv_prefix, html_report, exit_code)
    print(f"\nMarkdown report: {report_path}")
    print(f"HTML report:     {html_report}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
