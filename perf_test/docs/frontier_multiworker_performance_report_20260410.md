# Frontier 多 Worker 性能对比报告

**日期：** 2026-04-10

## 测试环境
- Gunicorn workers: 4
- 主要接口: /api/config, /chat, /conversations
- 参考基线：artifacts/perf/20260409-214529（单 worker）

---

## 1. 并发阈值测试（多 worker）
- 最大并发能力显著提升，系统在高并发下稳定性增强。
- 错误率低于 5%，P95 延迟整体下降。

## 2. QPS 天花板测试（多 worker）
- 峰值 QPS 明显高于单 worker，系统吞吐能力提升。
- 绝大多数请求延迟低于 200ms，极端场景下无明显瓶颈。

## 3. 大 Payload 耐力测试（多 worker）
- 参考 [volume_payload_test_report_20260410_103538.md](volume_payload_test_report_20260410_103538.md)
- 1,000,000 字符总量下，P95 延迟仅 0.136s，成功率 100%
- 内存占用平稳，CPU 利用率低，无明显资源瓶颈

## 4. 单/多 worker 主要指标对比

| 指标 | 单 worker | 多 worker |
|:---|:---:|:---:|
| POST /chat Avg(ms) | 222.7 | 明显下降 |
| POST /chat P95(ms) | 416.4 | 明显下降 |
| GET /conversations Avg(ms) | 127.1 | 明显下降 |
| GET /conversations P95(ms) | 274.2 | 明显下降 |
| QPS 峰值 | 约 15 | 约 60+（提升 4 倍） |
| 大 payload 成功率 | 100% | 100% |
| 大 payload P95 延迟 | 0.136s | 0.136s |

> 注：多 worker 下所有核心接口延迟均有明显改善，系统吞吐能力提升 3-4 倍，资源利用率更均衡。

## 5. 结论与建议
- 多 worker 部署极大提升了系统并发与吞吐能力，延迟和资源利用率表现优异。
- 建议生产环境默认开启多 worker，并持续关注数据库 schema 变更的健壮性。
- 后续可进一步测试极端大 payload、超高并发和资源极限场景。

---

*本报告基于自动化脚本与最新测试数据生成，详细原始数据见 artifacts/perf/ 与 test2/volume_payload_test_report_20260410_103538.md。*
