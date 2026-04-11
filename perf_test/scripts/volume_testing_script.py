#!/usr/bin/env python3
"""
Frontier Volume Testing Script
------------------------------
This script is designed to carry out a Volume Test (Capacity/Threshold) for the Frontier framework by
gradually ramping up the number of concurrent requests. It automatically adjusts concurrency and measures:
- QPS (Queries Per Second)
- Latency (Response times and distribution)
- Error Rate
- Concurrency and Burst handling
- CPU Usage of the `frontier-server` Docker container.

PREREQUISITE:
Run this script *only* after starting the full stack using Docker Compose:
  cd ../../frontier
  docker compose up -d --build

Requirements:
  pip install httpx aiohttp
"""

import asyncio
import httpx
import time
import subprocess
import argparse
import sys
import statistics
import traceback

# Configuration defaults
DEFAULT_URL = "http://localhost:8000/api/config"  # Or another endpoint representing application load
DEFAULT_START_CONCURRENCY = 10
DEFAULT_STEP_CONCURRENCY = 10
DEFAULT_STEP_DURATION = 10  # Seconds per step
DEFAULT_MAX_CONCURRENCY = 200
DEFAULT_MAX_ERROR_RATE = 0.05  # 5% error rate is threshold

def get_docker_stats():
    """Retrieve CPU and Memory stats of the frontier-server from docker."""
    try:
        out = subprocess.check_output(
            ["docker", "stats", "--no-stream", "--format", "CPU: {{.CPUPerc}} | MEM: {{.MemUsage}}", "frontier-server"],
            stderr=subprocess.DEVNULL,
            timeout=2
        ).decode().strip()
        if not out:
            return "N/A"
        return out
    except Exception:
        return "N/A (Docker not running or container 'frontier-server' not found)"

async def fetch(client, url):
    """Executes a single HTTP request and returns (latency_s, is_error)."""
    start = time.perf_counter()
    try:
        resp = await client.get(url, timeout=5.0)
        is_error = resp.status_code >= 400
    except Exception:
        is_error = True
    latency = time.perf_counter() - start
    return latency, is_error

async def worker(queue, client, url, results, stop_event):
    """Worker task that constantly consumes from the queue to form a continuous burst."""
    while not stop_event.is_set():
        try:
            # wait for task availability to manage rate
            _ = await asyncio.wait_for(queue.get(), timeout=1.0)
            latency, is_error = await fetch(client, url)
            results['latencies'].append(latency)
            if is_error:
                results['errors'] += 1
            results['successes'] += (not is_error)
            queue.task_done()
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            break

async def stage_runner(stage_num, concurrency, duration, url):
    """Run a specific testing stage with fixed concurrency."""
    print(f"\n[{time.strftime('%H:%M:%S')}] ==> Stage {stage_num}: Concurrency = {concurrency} | Duration = {duration}s")
    
    stop_event = asyncio.Event()
    queue = asyncio.Queue(maxsize=concurrency * 2)
    results = {'successes': 0, 'errors': 0, 'latencies': []}

    # Custom Limits matching concurrency profile
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    
    client = httpx.AsyncClient(limits=limits)
    try:
        # Start workers corresponding to the given concurrency
        workers = [asyncio.create_task(worker(queue, client, url, results, stop_event)) for _ in range(concurrency)]

        # Volume-based Producer: forces a certain number of requests per second (Target QPS)
        async def producer():
            target_qps_rate = concurrency * 2  # Set absolute volume target: start at 100 QPS, step 200, etc.
            interval = 1.0 / target_qps_rate if target_qps_rate > 0 else 0.01
            while not stop_event.is_set():
                if not queue.full():
                    await queue.put(1)
                await asyncio.sleep(interval) # Open model: strictly dictate the generation volume rate
        
        prod_task = asyncio.create_task(producer())

        # Wait for the stage duration
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < duration:
            await asyncio.sleep(1.0)  # Changed to 1 second to print more dynamically
            # Sample Docker stats during the run
            docker_info = get_docker_stats()
            print(f"  [Monitor - {concurrency} clients] {docker_info}")

        # Stop workers and producer
        stop_event.set()
        prod_task.cancel()
        for w in workers:
            w.cancel()
        
        # Wait for cancellation with a strict timeout to prevent Windows asyncio deadlocks
        try:
            await asyncio.wait_for(asyncio.gather(*workers, return_exceptions=True), timeout=2.0)
        except asyncio.TimeoutError:
            pass
    finally:
        try:
            await asyncio.wait_for(client.aclose(), timeout=2.0)
        except Exception:
            pass
    
    total_time = time.perf_counter() - start_time
    total_reqs = results['successes'] + results['errors']
    qps = total_reqs / total_time if total_time > 0 else 0
    error_rate = results['errors'] / total_reqs if total_reqs > 0 else 0
    
    lats = results['latencies']
    avg_latency = statistics.mean(lats) if lats else 0
    p95_latency = statistics.quantiles(lats, n=100)[94] if len(lats) >= 2 else avg_latency

    return {
        'concurrency': concurrency,
        'qps': round(qps, 2),
        'error_rate': error_rate,
        'avg_latency': round(avg_latency, 3),
        'p95_latency': round(p95_latency, 3),
        'total_reqs': total_reqs
    }

async def volume_test(args):
    print("=" * 60)
    print("🚀 Frontier Hub Volume Testing 🚀")
    print(f"Target URL:    {args.url}")
    print(f"Start Concv:   {args.start}")
    print(f"Step Concv:    {args.step}")
    print(f"Stage Timeout: {args.duration}s")
    print("=" * 60)
    
    # Quick health check
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(args.url)
            print(f"Health Check Passed! Target is REACHABLE (Status {resp.status_code})\n")
    except Exception as e:
        print(f"Failed to reach '{args.url}'. Make sure you ran 'docker compose up -d --build'.")
        print(f"Error: {e}")
        return

    report_data = []
    concurrency = args.start
    stage_num = 1

    try:
        while concurrency <= args.max:
            result = await stage_runner(stage_num, concurrency, args.duration, args.url)
            report_data.append(result)

            qps = result['qps']
            err_r = result['error_rate']
            
            print(f"--- Stage {stage_num} Summary ---")
            print(f"  Requests Total: {result['total_reqs']}")
            print(f"  QPS:            {qps}")
            print(f"  Error Rate:     {err_r:.2%}")
            print(f"  Avg Latency:    {result['avg_latency']}s")
            print(f"  P95 Latency:    {result['p95_latency']}s")
            print(f"-------------------------\n")

            if err_r > args.threshold:
                print(f"*** THRESHOLD REACHED ***")
                print(f"Error rate {err_r:.2%} exceeded limit {args.threshold:.2%} at concurrency level {concurrency}.")
                break
                
            concurrency += args.step
            stage_num += 1

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    finally:
        print("=" * 60)
        print("📊 VOLUME TEST FINAL REPORT 📊")
        print(f"{'Concurrency':<15} {'QPS':<10} {'Error Rate':<15} {'P95 Latency (s)'}")
        for r in report_data:
            print(f"{r['concurrency']:<15} {r['qps']:<10} {r['error_rate']:<15.2%} {r['p95_latency']}")
            
        import os
        import json
        from datetime import datetime
        
        # Save report to file
        report_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(report_dir, f'volume_test_report_{timestamp}.json')
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_config": {
                        "url": args.url,
                        "start_concurrency": args.start,
                        "step_concurrency": args.step,
                        "stage_duration": args.duration,
                        "max_concurrency": args.max,
                        "threshold": args.threshold,
                        "timestamp": timestamp
                    },
                    "stages": report_data
                }, f, indent=2)
            print(f"\nReport saved to: {report_path}")
            
            # also generate markdown report
            md_path = os.path.join(report_dir, f'volume_test_report_{timestamp}.md')
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# Frontier Volume Test Report\n\n")
                f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Target URL:** {args.url}\n")
                f.write(f"**Configuration:** Start={args.start}, Step={args.step}, Duration={args.duration}s\n\n")
                f.write("## Results\n\n")
                f.write("| Concurrency | QPS | Error Rate | Avg Latency (s) | P95 Latency (s) | Total Reqs |\n")
                f.write("|-------------|-----|------------|-----------------|-----------------|------------|\n")
                for r in report_data:
                    f.write(f"| {r['concurrency']} | {r['qps']} | {r['error_rate']:.2%} | {r['avg_latency']} | {r['p95_latency']} | {r['total_reqs']} |\n")
            print(f"Markdown report saved to: {md_path}")
        except Exception as e:
            print(f"Failed to save report: {e}")

def main():
    parser = argparse.ArgumentParser(description="Gradually ramp-up volume test for Frontier")
    parser.add_argument("--url", default=DEFAULT_URL, help="Target URL for testing. Example: http://localhost:8000/api/config")
    parser.add_argument("--start", type=int, default=DEFAULT_START_CONCURRENCY, help="Starting concurrent baseline")
    parser.add_argument("--step", type=int, default=DEFAULT_STEP_CONCURRENCY, help="Number of concurrent requests to add each stage")
    parser.add_argument("--duration", type=int, default=DEFAULT_STEP_DURATION, help="Duration in seconds for each specific load stage")
    parser.add_argument("--max", type=int, default=DEFAULT_MAX_CONCURRENCY, help="Absolute max concurrency limit to stop test if no threshold hit")
    parser.add_argument("--threshold", type=float, default=DEFAULT_MAX_ERROR_RATE, help="Maximum error rate ratio before test aborts (default=0.05)")

    args = parser.parse_args()
    asyncio.run(volume_test(args))

if __name__ == "__main__":
    main()