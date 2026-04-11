# Frontier Multi-Worker Volume Test Report

**Date:** 2026-04-10 15:30:27

## Test Environment

- **Target URL:** http://localhost:8000
- **Project:** test-project
- **Workers:** 4
- **OS:** Windows 11
- **Python:** 3.13.7

---

## 1. Concurrent API Throughput Test

### Overview

| Workers | Concurrency | Total Requests | QPS | Error Rate | CPU | Memory |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 4 | 10 | 15373 | 512.43 | 0.00% | 0.74% | 822.7MiB / 15.35GiB |
| 4 | 30 | 12053 | 401.77 | 0.00% | 0.71% | 824MiB / 15.35GiB |
| 4 | 50 | 11181 | 372.7 | 0.00% | 0.72% | 827.7MiB / 15.35GiB |
| 4 | 70 | 11656 | 388.53 | 0.00% | 0.72% | 831.8MiB / 15.35GiB |
| 4 | 90 | 11925 | 397.5 | 0.00% | 0.71% | 838.4MiB / 15.35GiB |
| 4 | 110 | 11563 | 385.43 | 0.00% | 0.75% | 843.2MiB / 15.35GiB |
| 4 | 130 | 10821 | 360.7 | 0.00% | 0.71% | 847.5MiB / 15.35GiB |
| 4 | 150 | 11714 | 390.47 | 0.00% | 0.70% | 851.8MiB / 15.35GiB |

### Endpoint Details

| Workers | Concurrency | Endpoint | Requests | QPS | Avg (s) | P50 (s) | P95 (s) | P99 (s) | Max (s) | Error Rate |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 4 | 10 | GET /api/config | 11411 | 1141.1 | 0.0088 | 0.0083 | 0.0143 | 0.0169 | 0.0255 | 0.00% |
| 4 | 10 | GET /conversations | 1997 | 199.7 | 0.0502 | 0.045 | 0.0636 | 0.1352 | 0.5864 | 0.00% |
| 4 | 10 | GET /projects/{project}/agents | 1965 | 196.5 | 0.0509 | 0.0486 | 0.0713 | 0.0866 | 0.1199 | 0.00% |
| 4 | 30 | GET /api/config | 8210 | 821.0 | 0.0365 | 0.0353 | 0.0565 | 0.0678 | 0.0965 | 0.00% |
| 4 | 30 | GET /conversations | 1910 | 191.0 | 0.1575 | 0.1565 | 0.2115 | 0.2414 | 0.5095 | 0.00% |
| 4 | 30 | GET /projects/{project}/agents | 1933 | 193.3 | 0.1554 | 0.1511 | 0.2102 | 0.2431 | 0.2826 | 0.00% |
| 4 | 50 | GET /api/config | 7827 | 782.7 | 0.0633 | 0.0615 | 0.0995 | 0.1209 | 0.1894 | 0.00% |
| 4 | 50 | GET /conversations | 1742 | 174.2 | 0.2888 | 0.2794 | 0.4286 | 0.5002 | 0.6973 | 0.00% |
| 4 | 50 | GET /projects/{project}/agents | 1612 | 161.2 | 0.3129 | 0.3343 | 0.5679 | 0.8334 | 1.0934 | 0.00% |
| 4 | 70 | GET /api/config | 8415 | 841.5 | 0.0815 | 0.0789 | 0.1315 | 0.1602 | 0.2322 | 0.00% |
| 4 | 70 | GET /conversations | 1616 | 161.6 | 0.4391 | 0.4172 | 0.6651 | 0.8906 | 1.1507 | 0.00% |
| 4 | 70 | GET /projects/{project}/agents | 1625 | 162.5 | 0.4355 | 0.4089 | 0.7054 | 0.9611 | 1.1635 | 0.00% |
| 4 | 90 | GET /api/config | 8934 | 893.4 | 0.0976 | 0.0936 | 0.1664 | 0.2021 | 0.3129 | 0.00% |
| 4 | 90 | GET /conversations | 1529 | 152.9 | 0.6037 | 0.5567 | 1.2493 | 1.5369 | 1.9113 | 0.00% |
| 4 | 90 | GET /projects/{project}/agents | 1462 | 146.2 | 0.6264 | 0.5604 | 1.2025 | 1.4277 | 1.7307 | 0.00% |
| 4 | 110 | GET /api/config | 8896 | 889.6 | 0.1186 | 0.1147 | 0.2034 | 0.251 | 0.352 | 0.00% |
| 4 | 110 | GET /conversations | 1338 | 133.8 | 0.8379 | 0.7327 | 1.7469 | 2.4046 | 2.7795 | 0.00% |
| 4 | 110 | GET /projects/{project}/agents | 1329 | 132.9 | 0.8462 | 0.6837 | 1.8074 | 2.2437 | 2.5885 | 0.00% |
| 4 | 130 | GET /api/config | 8153 | 815.3 | 0.1483 | 0.1447 | 0.2544 | 0.3111 | 0.548 | 0.00% |
| 4 | 130 | GET /conversations | 1397 | 139.7 | 0.951 | 0.8706 | 1.835 | 2.1454 | 2.5876 | 0.00% |
| 4 | 130 | GET /projects/{project}/agents | 1271 | 127.1 | 1.0509 | 0.8835 | 2.2909 | 2.6829 | 3.1832 | 0.00% |
| 4 | 150 | GET /api/config | 8849 | 884.9 | 0.1558 | 0.151 | 0.2812 | 0.3403 | 0.4876 | 0.00% |
| 4 | 150 | GET /conversations | 1454 | 145.4 | 1.0691 | 1.0334 | 1.8739 | 2.4109 | 2.6216 | 0.00% |
| 4 | 150 | GET /projects/{project}/agents | 1411 | 141.1 | 1.0945 | 1.0749 | 1.8787 | 2.2377 | 2.8896 | 0.00% |

## 2. Large-Payload Volume Test

**Config:** Payload=20,000 chars/msg | Concurrency=5

| Workers | Request (msgs) | Payload (chars) | Volume (total chars) | QPS | Concurrency | Memory | CPU Usage | Avg Latency (s) | P95 Latency (s) | Success Rate |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 4 | 50 | 20,000 | 1,000,000 | 6.62 | 5 | 850.5MiB / 15.35GiB | 0.71% | 0.112 | 0.182 | 100.00% |
| 4 | 100 | 20,000 | 2,000,000 | 11.54 | 5 | 848.1MiB / 15.35GiB | 0.67% | 0.101 | 0.181 | 100.00% |
| 4 | 150 | 20,000 | 3,000,000 | 21.83 | 5 | 791.9MiB / 15.35GiB | 0.64% | 0.083 | 0.11 | 100.00% |
| 4 | 200 | 20,000 | 4,000,000 | 22.52 | 5 | 792MiB / 15.35GiB | 0.68% | 0.08 | 0.115 | 100.00% |
| 4 | 250 | 20,000 | 5,000,000 | 27.95 | 5 | 789.4MiB / 15.35GiB | 0.80% | 0.085 | 0.116 | 100.00% |
| 4 | 300 | 20,000 | 6,000,000 | 42.97 | 5 | 789.7MiB / 15.35GiB | 0.70% | 0.093 | 0.109 | 100.00% |
| 4 | 350 | 20,000 | 7,000,000 | 36.19 | 5 | 790MiB / 15.35GiB | 1.07% | 0.093 | 0.111 | 100.00% |
| 4 | 400 | 20,000 | 8,000,000 | 36.25 | 5 | 789.5MiB / 15.35GiB | 0.80% | 0.09 | 0.12 | 100.00% |
| 4 | 450 | 20,000 | 9,000,000 | 38.85 | 5 | 789.7MiB / 15.35GiB | 0.74% | 0.115 | 0.138 | 100.00% |
| 4 | 500 | 20,000 | 10,000,000 | 32.82 | 5 | 789.7MiB / 15.35GiB | 0.89% | 0.117 | 0.144 | 100.00% |

### Write vs Read Breakdown

| Workers | Stage | Messages | Write QPS | Avg Write Lat (s) | P95 Write Lat (s) | Read QPS | Avg Read Lat (s) | P95 Read Lat (s) | Write Failures | Read Failures |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 4 | 1 | 50 | 6.38 | 0.113 | 0.183 | 10.75 | 0.093 | 0.2 | 0 | 0 |
| 4 | 2 | 100 | 11.19 | 0.104 | 0.182 | 30.21 | 0.033 | 0.053 | 0 | 0 |
| 4 | 3 | 150 | 21.59 | 0.084 | 0.111 | 32.7 | 0.031 | 0.034 | 0 | 0 |
| 4 | 4 | 200 | 22.32 | 0.081 | 0.115 | 35.15 | 0.028 | 0.035 | 0 | 0 |
| 4 | 5 | 250 | 27.89 | 0.086 | 0.116 | 31.48 | 0.032 | 0.033 | 0 | 0 |
| 4 | 6 | 300 | 43.01 | 0.094 | 0.109 | 40.57 | 0.025 | 0.026 | 0 | 0 |
| 4 | 7 | 350 | 36.22 | 0.094 | 0.111 | 33.94 | 0.029 | 0.034 | 0 | 0 |
| 4 | 8 | 400 | 36.24 | 0.091 | 0.12 | 37.07 | 0.027 | 0.034 | 0 | 0 |
| 4 | 9 | 450 | 38.85 | 0.116 | 0.138 | 38.95 | 0.026 | 0.031 | 0 | 0 |
| 4 | 10 | 500 | 32.76 | 0.118 | 0.144 | 40.3 | 0.025 | 0.029 | 0 | 0 |

## 3. Burst Capacity Test

| Workers | Burst Size | QPS | Avg Latency (s) | P95 Latency (s) | Max Latency (s) | Success Rate | CPU | Memory |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 4 | 50 | 722.27 | 0.0207 | 0.0328 | 0.0409 | 100.00% | 0.82% | 790.2MiB / 15.35GiB |
| 4 | 100 | 787.5 | 0.017 | 0.0336 | 0.042 | 100.00% | 0.66% | 790MiB / 15.35GiB |
| 4 | 200 | 895.29 | 0.03 | 0.0523 | 0.0821 | 100.00% | 0.69% | 790.6MiB / 15.35GiB |
| 4 | 300 | 1007.14 | 0.0289 | 0.0511 | 0.0632 | 100.00% | 0.77% | 790.6MiB / 15.35GiB |
| 4 | 400 | 990.26 | 0.0344 | 0.0623 | 0.1093 | 100.00% | 0.74% | 790.6MiB / 15.35GiB |
| 4 | 500 | 963.08 | 0.0417 | 0.0806 | 0.1115 | 100.00% | 0.74% | 791.3MiB / 15.35GiB |

## 4. Analysis & Conclusions

**Worker Configuration:** 4 worker(s)

### Concurrent API Throughput
- Max concurrency tested: **150**
- Peak QPS at **concurrency=10**: **512.43 QPS**
- Final error rate: **0.00%**

### Large-Payload Volume
- All stages passed, max volume: **500 messages** (10,000,000 chars)
- Final P95 Latency: **0.144s**
- Final Success Rate: **100.00%**

### Burst Capacity
- Peak QPS: **1007.14** (burst=300)
- Max burst tested: **500**
- Success rate at max burst: **100.00%**

### Recommendations
- Multi-worker deployment (>=4) significantly improves concurrent throughput and P95 latency
- Monitor memory trends under large-payload scenarios to prevent OOM
- Consider testing: ultra-high concurrency (200+), extreme payloads (50KB+/msg), long-running soak tests
- Compare performance across different worker counts (1/2/4/8) to find optimal configuration

---

*Report generated by `multiworker_volume_test.py` | Raw data: `multiworker_volume_report_20260410_153027.json`*
