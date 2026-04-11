# Frontier 后端性能测试计划

> **版本**: v1.0  
> **日期**: 2026-04-09  
> **测试范围**: Frontier FastAPI 后端全量 API (52 个端点)  
> **运行环境**: 本地开发环境 (localhost:8000)

---

## 一、测试目的

| # | 目的 | 说明 |
|---|------|------|
| 1 | **基线建立** | 测量各 API 端点在无压力和标准负载下的响应时间，建立性能基线数据 |
| 2 | **瓶颈发现** | 识别高延迟端点、数据库慢查询、内存泄漏等性能瓶颈 |
| 3 | **并发能力验证** | 验证系统在多用户并发访问下是否能保持可接受的响应时间和稳定性 |
| 4 | **吞吐量评估** | 评估系统能承受的最大请求量 (RPS)，确定容量上限 |
| 5 | **稳定性验证** | 通过持续负载测试确认系统在长时间运行后是否存在性能退化 |
| 6 | **回归基准** | 为后续开发迭代提供可复现的性能回归基准 |

---

## 二、测试工具

| 工具 | 用途 | 安装方式 |
|------|------|----------|
| **Locust** (主力) | 负载测试 & 并发模拟 | `pip install locust` |
| **pytest-benchmark** | 单端点微基准测试 | `pip install pytest-benchmark httpx` |
| **psutil** | 系统资源监控 (CPU/内存) | `pip install psutil` |
| **Docker Compose** | 启动 PostgreSQL 数据库 | 已有 `docker-compose.yml` |

### 为什么选择 Locust

- Python 原生，与 Frontier 技术栈一致
- 支持 Web UI 实时监控
- 支持分布式负载生成
- 场景用 Python 编写，可复用项目已有代码和配置
- 支持 CSV/HTML 报告导出

---

## 三、测试指标

### 3.1 响应时间指标

| 指标 | 定义 | 目标值 |
|------|------|--------|
| **Avg Latency** | 平均响应时间 | REST API < 200ms |
| **P50 Latency** | 第 50 百分位响应时间 | REST API < 150ms |
| **P90 Latency** | 第 90 百分位响应时间 | REST API < 500ms |
| **P95 Latency** | 第 95 百分位响应时间 | REST API < 1s，SSE 流式 < 2s |
| **P99 Latency** | 第 99 百分位响应时间 | REST API < 2s |
| **Max Latency** | 最大响应时间 | REST API < 5s |

### 3.2 吞吐量指标

| 指标 | 定义 | 目标值 |
|------|------|--------|
| **RPS** | 每秒请求数 (Requests Per Second) | ≥ 100 RPS (50 并发用户) |
| **Successful RPS** | 每秒成功请求数 | ≥ 95% of total RPS |
| **Concurrent Users** | 系统可承受的最大并发用户数 | ≥ 50 用户无错误 |

### 3.3 错误率指标

| 指标 | 定义 | 目标值 |
|------|------|--------|
| **Error Rate** | 请求失败比例 (非 2xx/3xx) | < 1% |
| **Timeout Rate** | 请求超时比例 (> 10s) | < 0.1% |
| **5xx Rate** | 服务器内部错误比例 | 0% |

### 3.4 系统资源指标

| 指标 | 定义 | 目标值 |
|------|------|--------|
| **CPU Usage** | 后端进程 CPU 使用率 | < 80% (常态负载) |
| **Memory Usage** | 后端进程内存占用 | 无持续增长 (无泄漏) |
| **DB Connections** | 数据库活跃连接数 | 不超过连接池上限 |

---

## 四、测试场景

### 场景 1：单端点基准测试 (Baseline)

**目的**: 无并发压力下，测量每个端点的原始响应时间  
**工具**: pytest-benchmark  
**脚本位置**: `scripts/test_baseline_bench.py`

覆盖端点：

| 分类 | 端点 | 方法 |
|------|------|------|
| 认证 | `/login` | POST |
| 认证 | `/me` | GET |
| 项目 | `/projects` | POST |
| 项目 | `/projects/{name}` | GET |
| 项目 | `/projects/owned` | GET |
| Agent | `/projects/{name}/agents` | GET |
| Agent | `/projects/{name}/agents` | POST |
| 会话 | `/conversations` | GET |
| 会话 | `/conversations` | POST |
| 消息 | `/conversations/{id}/messages` | GET |
| 聊天 | `/chat` | POST (SSE) |
| 仪表板 | `/projects/{name}/dashboard` | GET |
| 成员 | `/projects/{name}/members` | GET |
| 用量 | `/projects/{name}/usage` | GET |
| 监控 | `/metrics` | GET |
| 配置 | `/config` | GET |

### 场景 2：标准负载测试 (Load Test)

**目的**: 模拟正常使用场景下的混合负载  
**工具**: Locust  
**脚本位置**: `scenarios/load_test.py`  
**参数**:
- 并发用户: 20 → 50 (5 分钟线性增长)
- 持续时间: 10 分钟
- 用户行为权重:

| 行为 | 权重 | 说明 |
|------|------|------|
| 登录获取 Token | 启动时 1 次 | `on_start` |
| 浏览项目列表 | 5 | 高频读操作 |
| 查看项目详情 | 3 | |
| 列出 Agent | 3 | |
| 获取会话列表 | 4 | 高频读操作 |
| 获取消息历史 | 4 | |
| 发送聊天消息 | 2 | 写操作 + SSE 流 |
| 创建会话 | 1 | 低频写操作 |
| 查看仪表板 | 2 | |
| 查看使用量 | 1 | |
| 获取配置 | 1 | |

### 场景 3：压力测试 (Stress Test)

**目的**: 找到系统的极限并发能力和崩溃临界点  
**工具**: Locust  
**脚本位置**: `scenarios/stress_test.py`  
**参数**:
- 并发用户: 10 → 200 (阶梯式增长，每 2 分钟 +30 用户)
- 持续时间: 20 分钟
- 观察点: 错误率开始上升的拐点，P95 延迟超过 2s 的临界用户数

### 场景 4：耐久测试 (Endurance/Soak Test)

**目的**: 长时间运行检测内存泄漏和性能退化  
**工具**: Locust + psutil  
**脚本位置**: `scenarios/soak_test.py`  
**参数**:
- 并发用户: 30 (恒定)
- 持续时间: 30 分钟
- 每 60 秒采集一次 CPU/内存数据
- 判定标准: 内存增长不超过初始值的 20%

### 场景 5：认证 & RBAC 专项测试

**目的**: 验证认证中间件和权限校验的性能开销  
**工具**: Locust  
**脚本位置**: `scenarios/auth_perf_test.py`  
**测试内容**:
- JWT Token 签发吞吐量 (`POST /login`)
- Token 验证延迟 (`GET /me` 高频调用)
- 无效 Token 拒绝速度 (401 响应延迟)
- 不同角色 (owner/admin/member) 下相同端点的响应差异

---

## 五、完整测试步骤

### 第一阶段：环境准备

```
步骤 1.1  启动数据库
         $ docker-compose up -d
         验证: 确认 PostgreSQL 容器运行正常

步骤 1.2  启动后端服务
         $ python project.py
         验证: 访问 http://localhost:8000/config 返回 200

步骤 1.3  准备测试数据
         - 创建测试用户 (通过 admin 账户 或 LDAP)
         - 创建 2-3 个测试项目
         - 每个项目配置 1-2 个 Agent
         - 每个项目创建 5-10 条会话和消息
         脚本: scripts/seed_test_data.py

步骤 1.4  安装测试工具
         $ pip install locust pytest-benchmark httpx psutil
```

### 第二阶段：基准测试

```
步骤 2.1  运行单端点基准测试
         $ pytest scripts/test_baseline_bench.py --benchmark-only --benchmark-json=reports/baseline.json
         输出: reports/baseline.json

步骤 2.2  记录基准结果
         将各端点的 min/avg/max/stddev 记录到 reports/ 下
```

### 第三阶段：负载测试

```
步骤 3.1  运行标准负载测试
         $ locust -f scenarios/load_test.py --headless \
             -u 50 -r 5 --run-time 10m \
             --csv=reports/load_test --html=reports/load_test.html
         输出: reports/load_test.html, reports/load_test_stats.csv

步骤 3.2  运行压力测试
         $ locust -f scenarios/stress_test.py --headless \
             -u 200 -r 15 --run-time 20m \
             --csv=reports/stress_test --html=reports/stress_test.html
         输出: reports/stress_test.html

步骤 3.3  运行认证专项测试
         $ locust -f scenarios/auth_perf_test.py --headless \
             -u 100 -r 10 --run-time 5m \
             --csv=reports/auth_test --html=reports/auth_test.html
```

### 第四阶段：耐久测试

```
步骤 4.1  运行耐久测试
         $ locust -f scenarios/soak_test.py --headless \
             -u 30 -r 5 --run-time 30m \
             --csv=reports/soak_test --html=reports/soak_test.html
         输出: reports/soak_test.html + reports/soak_resource_usage.csv

步骤 4.2  分析资源趋势
         检查 CPU/内存是否有持续增长趋势
```

### 第五阶段：结果分析 & 报告

```
步骤 5.1  汇总所有报告
         收集以下文件:
         - reports/baseline.json          (基准数据)
         - reports/load_test.html         (负载测试)
         - reports/stress_test.html       (压力测试)
         - reports/auth_test.html         (认证专项)
         - reports/soak_test.html         (耐久测试)
         - reports/soak_resource_usage.csv (资源趋势)

步骤 5.2  对比目标值
         将实际指标与第三节的目标值逐项对比

步骤 5.3  识别瓶颈
         - P95 > 1s 的端点
         - 错误率 > 1% 的端点
         - 压力测试中的拐点并发数
         - 耐久测试中的内存增长率

步骤 5.4  输出最终报告
         生成 reports/PERFORMANCE_REPORT.md 包含:
         - 测试环境信息
         - 各场景测试结果
         - 指标达标/未达标清单
         - 瓶颈分析与优化建议
```

---

## 六、目录结构

```
tests/performance/
├── PERFORMANCE_TEST_PLAN.md          ← 本文件 (测试计划)
├── scenarios/                         ← Locust 场景文件
│   ├── load_test.py                  ← 标准负载测试
│   ├── stress_test.py                ← 压力测试
│   ├── soak_test.py                  ← 耐久测试
│   └── auth_perf_test.py            ← 认证专项测试
├── scripts/                           ← 辅助脚本
│   ├── seed_test_data.py             ← 测试数据初始化
│   └── test_baseline_bench.py        ← pytest-benchmark 基准测试
└── reports/                           ← 测试报告输出目录
    ├── baseline.json
    ├── load_test.html
    ├── stress_test.html
    ├── auth_test.html
    ├── soak_test.html
    ├── soak_resource_usage.csv
    └── PERFORMANCE_REPORT.md         ← 最终汇总报告
```

---

## 七、前置条件与注意事项

1. **数据库**: 必须使用 PostgreSQL/YugabyteDB，SQLite 不受支持
2. **测试隔离**: 使用专属测试项目和用户，避免污染生产数据
3. **网络**: 本地测试时后端和 Locust 运行在同一机器上，网络延迟可忽略
4. **冷启动**: 每个场景执行前先运行 1 分钟预热避免冷启动偏差
5. **Agent 流式**: `/chat` 端点使用 SSE 流式响应，Locust 需配置 `catch_response=True` 手动处理
6. **报告保留**: 每次测试的报告按日期归档，便于纵向对比
