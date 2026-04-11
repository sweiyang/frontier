# Volume-Concurrency Stress Test 更新总结

## 完成时间
2026-04-10 17:13

## 执行的测试
运行了 `volume_concurrency_stress_test.py` 脚本，测试配置：
- **固定容量**: 300 条消息 × 20,000 字符 = 6,000,000 字符 (6M)
- **变量**: 并发度从 1 → 3 → 5 → 8 → 10 → 15 → 20 → 25 → 30
- **Workers**: 4
- **目标**: 在峰值容量下找到写入 QPS 上限

## 测试结果摘要

### 关键发现
- **峰值写入 QPS**: 29.97 @ 并发度=10
- **QPS 平台期**: 在 C=10-15 达到峰值后保持稳定
- **延迟增长**: P95 延迟从 0.14s (C=10) → 0.60s (C=30)
- **成功率**: 所有并发级别均为 100%
- **内存稳定**: 从 C=1 到 C=30 仅增长 1.3 MiB
- **CPU 使用率**: 即使在最高并发度下也保持在 1.3% 以下

### 性能瓶颈分析
- QPS 平台期 + 低 CPU 使用率 → 可能是 Python GIL 竞争或数据库连接池限制
- 最佳并发度: **C=10** (吞吐量 30 QPS，P95 延迟 0.14s 的最佳平衡)

## 报告更新内容

### 1. 新增 SECTION 4: Volume-Concurrency Stress Test
在 HTML 报告中添加了完整的新章节，包括：
- 测试设计说明
- 两个交互式图表 (Chart 9 & 10):
  - Write QPS vs Concurrency
  - Write Latency Percentiles vs Concurrency
- 完整的测试结果表格（9 个并发级别）
- 关键发现和分析

### 2. 更新 KPI 卡片
添加了新的 KPI 指标：
- **Peak Write QPS (6M chars)**: 29.97 @ C=10, 20K/msg

### 3. 更新 Header
- 副标题更新为包含 "Volume-Concurrency Stress Test"
- 时间戳更新为 2026-04-10 17:13

### 4. 更新 Threshold Summary (SECTION 5)
在软阈值部分添加：
- **Write QPS ceiling (large payload)**: ~30 QPS @ C=10
- 更新了阈值总结表格，包含新的写入 QPS 上限发现

### 5. JavaScript 图表代码
添加了两个新图表的完整实现：
- **Chart 9**: 线形图展示写入 QPS 随并发度变化
- **Chart 10**: 多线图展示 Avg/P50/P95/P99 延迟随并发度变化

## 生成的文件
1. **JSON 数据**: `perf/multiworker/volume_concurrency_stress_20260410_171336.json`
2. **Markdown 报告**: `perf/multiworker/volume_concurrency_stress_report_20260410_171336.md`
3. **更新的 HTML 报告**: `perf_cc/multiworker_volume_test.html`

## 实际意义

这个测试揭示了在真实大负载条件下（20K 字符/消息）的**写入吞吐量上限**：

1. **吞吐量上限**: 对于 20K 字符的消息，系统在 ~30 写入 QPS 达到上限
2. **过度并行化的代价**: 在 C=30 时，平均延迟是 C=10 的 4 倍（0.40s vs 0.11s），但 QPS 没有提升
3. **实用建议**: 对于大负载写入（15-20K 字符），将客户端并发限制在 ~10 以避免不必要的延迟膨胀

## 下一步建议

1. 考虑测试不同 worker 数量（8W, 16W）下的 Volume-Concurrency 性能
2. 分析数据库连接池配置，可能需要调整以支持更高的写入并发
3. 考虑实施写入队列或批处理机制来提高大负载场景下的吞吐量
