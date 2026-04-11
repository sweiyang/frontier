# Frontier Volume Test Report

**Date:** 2026-04-10 09:44:44
**Target URL:** http://localhost:8000/api/config
**Configuration:** Start=10, Step=10, Duration=5s

## Results

| Concurrency | QPS | Error Rate | Avg Latency (s) | P95 Latency (s) | Total Reqs |
|-------------|-----|------------|-----------------|-----------------|------------|
| 10 | 114.74 | 0.00% | 0.073 | 0.058 | 814 |
| 20 | 227.57 | 0.00% | 0.067 | 0.067 | 1498 |
| 30 | 315.2 | 0.00% | 0.078 | 0.076 | 1938 |
