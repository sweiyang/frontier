# Worker-Scaling Volume Test

在不同 Gunicorn worker 数量下运行 volume test，找到每个配置的 threshold。

## 测试逻辑

对每个 worker 数量（默认 1, 2, 4, 8），执行与 `volume_payload_test.py` 相同的阶梯式 volume test：

- 每个 stage 发送 N 条大 payload 消息（写），再读回完整历史（读）
- 消息数从 `start_msgs` 按 `step_msgs` 递增，直到触发 threshold 或达到 `max_msgs`
- **Threshold 条件**：`success_rate < 90%` 或 `p95 > latency_threshold`（可选）

报告表格在原有列基础上**新增 Workers 列**，格式与 `volume_payload_test_report` 完全一致。

## 前置条件

```bash
pip install requests pyyaml
```

服务器需要已启动（或使用 `--no-restart` 手动控制）。

## 用法

### 模式 1：自动重启（推荐）

脚本自动修改 `config.yaml` 中的 `server.workers`，重启服务器，依次测试每个 worker 数量。

```bash
# 默认：测试 1, 2, 4, 8 workers
python perf/per-tst-workers/worker_volume_test.py

# 自定义 worker 数量
python perf/per-tst-workers/worker_volume_test.py --worker-counts 1 2 4

# 自定义 payload 和 volume 参数（与现有报告一致）
python perf/per-tst-workers/worker_volume_test.py \
    --worker-counts 1 2 4 8 \
    --start-msgs 100 --step-msgs 100 --max-msgs 1000 \
    --payload-size 20000 --concurrency 5
```

### 模式 2：手动控制（`--no-restart`）

手动启动不同 worker 数量的服务器，每次只测当前运行的实例。

```bash
# 终端 1：启动 4 workers
# 修改 config.yaml: server.workers: 4, server.reload: false
python project.py

# 终端 2：测试当前服务器
python perf/per-tst-workers/worker_volume_test.py --no-restart --workers 4
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--worker-counts` | `1 2 4 8` | 要测试的 worker 数量列表 |
| `--workers` | — | 单个 worker 数（配合 `--no-restart` 使用） |
| `--no-restart` | False | 跳过服务器重启，测试当前运行的服务器 |
| `--start-msgs` | 100 | 起始消息数 |
| `--step-msgs` | 100 | 每阶段消息数增量 |
| `--max-msgs` | 1000 | 最大消息数 |
| `--payload-size` | 20000 | 每条消息的字符数 |
| `--concurrency` | 5 | 并发写入线程数 |
| `--threshold` | 0.90 | 成功率低于此值时停止（90%） |
| `--latency-threshold` | 0 | p95 超过此秒数时停止（0=禁用） |
| `--url` | `http://localhost:8000` | 服务器地址 |
| `--project` | `test-project` | 项目名称 |
| `--username` | `admin` | 登录用户名 |
| `--password` | `admin123` | 登录密码 |
| `--config-yaml` | `config.yaml` | config.yaml 路径（自动重启模式使用） |

## 输出报告

报告保存在 `perf/per-tst-workers/` 目录：

- `worker_volume_report_<timestamp>.json` — 完整原始数据
- `worker_volume_report_<timestamp>.md` — Markdown 报告

### 报告表格示例

**Results 表**（新增 Workers 列）：

| Workers | Request (msgs) | Payload (chars) | Volume (total chars) | QPS | Concurrency | Memory | CPU Usage | Avg Latency (s) | P95 Latency (s) | Success Rate |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | 100 | 20,000 | 2,000,000 | 10.2 | 5 | 164MiB | 1.8% | 0.223 | 0.274 | 100.00% |
| 2 | 100 | 20,000 | 2,000,000 | 18.5 | 5 | 180MiB | 2.1% | 0.198 | 0.241 | 100.00% |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

**Threshold Summary 表**：

| Workers | Max Msgs Passed | Threshold Hit At | P95 at Threshold (s) | Success Rate at Threshold | Reason |
|:-:|:-:|:-:|:-:|:-:|:--|
| 1 | 800 | 900 msgs | 2.1s | 87.50% | success_rate=87.50% |
| 2 | 1000 (max) | Not reached | 0.8s | 100.00% | All stages passed |

## config.yaml 配置参考

```yaml
server:
  workers: 4        # Gunicorn worker 数量
  reload: false     # 生产模式必须为 false
  timeout: 120
  graceful_timeout: 30
```
