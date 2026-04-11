# Frontier 后端性能测试计划（基于当前前端与标准启动方式）

> 版本: v2.1  
> 日期: 2026-04-09  
> 适用对象: 本地开发环境下的后端性能与稳定性验证  
> 运行环境: 本地 Docker Compose (localhost:8000)  
> 替代关系: 本文用于替代旧版 PERFORMANCE_TEST_PLAN.md 中与启动方式、接口热度、用户路径相关的内容  
> 设计原则: 本地测试不追求绝对吞吐量和长尾延迟阈值，侧重相对性能对比、并发正确性、资源泄漏检测、慢查询发现与回归检测

---

## 一、评估结论

现有的 PERFORMANCE_TEST_PLAN.md 受当前前端形态影响，已经不宜直接作为主测试计划使用，原因如下：

1. 启动假设已过时
   - 旧计划默认先起数据库，再直接执行 python project.py。
   - 当前已确认的标准启动方式是从仓库根目录执行 docker compose up -d --build，由 frontier-server 容器同时提供后端和已构建的前端。

2. 负载模型不再匹配真实页面流量
   - 当前首页是 Dashboard，而不是旧计划隐含的“登录后直接围绕项目列表/会话列表展开”。
   - 首页和应用启动阶段会稳定触发 /me、/me/agents、/me/stats、/admin/banners/active 等接口。
   - 项目设置页会并发触发 /projects/{project}/usage 与 /projects/{project}/dashboard/analytics。
   - Artefacts、Admin Panel、审批与权限配置现在都是前端可直接进入的有效路径。

3. 测试范围应从“全量 API 平铺”改为“前端驱动的关键用户旅程”
   - 旧计划按 52 个端点全量罗列，适合建立粗粒度基线。
   - 当前更需要围绕真实用户动作建模，识别高频读、关键写、流式聊天、管理突发和并发扇出场景。

4. 接口事实来源需要调整
   - 当前 openapi.json 与前端实际调用和后端现状存在偏差，不应再作为新版性能计划的唯一依据。
   - 新版计划以当前前端源码中的真实请求路径与后端 routers 为准。

结论：旧计划可以保留作为历史基线参考，但当前版本应以本文为执行主计划。

---

## 二、测试目标

### 本地测试侧重点说明

本地环境的 CPU、内存、Docker 虚拟化开销与生产环境差异巨大，因此绝对吞吐量（最大 RPS）、绝对长尾延迟阈值（P99 < Xms）在本地没有参考意义。本版计划围绕以下五个在本地环境下确实有价值的方向展开：

| # | 方向 | 为什么在本地有效 |
|---|---|---|
| 1 | **相对性能对比** | 同一台机器上，接口 A 比 B 慢 10 倍 → A 一定有优化空间，结论不依赖硬件 |
| 2 | **并发正确性** | 竞态条件、死锁、连接池耗尽、数据重复/丢失在本地即可复现 |
| 3 | **资源泄漏检测** | 内存持续增长、DB 连接不释放，本地跑 20-30 分钟就能看出趋势 |
| 4 | **慢查询与 N+1 识别** | 数据库层面的低效模式（缺索引、N+1、全表扫描）与硬件无关 |
| 5 | **回归检测** | 同机器上代码改动前后的基线对比，差异有统计意义 |

### 具体目标

1. 建立本地环境下各接口的响应时间基线，用于后续回归对比。
2. 发现明显偏慢的接口，定位到具体 SQL 或业务逻辑层。
3. 验证轻量并发下后端的正确性——无 5xx、无数据损坏、无连接泄漏。
4. 确认持续运行一段时间后无资源泄漏。
5. 为后续可能的远程/staging 环境压测提供可移植的测试脚本和场景结构。

---

## 三、测试范围

### 3.1 纳入范围的关键用户旅程

| 旅程 | 主要页面/动作 | 关键接口 |
|---|---|---|
| 启动与登录 | 打开应用、登录、完成首屏初始化 | POST /login, GET /config, GET /me, GET /me/agents, GET /me/stats, GET /admin/banners/active |
| Dashboard 浏览 | 首页查看全部 Agent、筛选后进入项目 | GET /me/agents, GET /me/stats, GET /projects/{project_name}, GET /projects/{project_name}/agents |
| Chat 主链路 | 创建会话、加载历史、发送消息、流式返回 | GET /conversations, POST /conversations, GET /conversations/{id}/messages, POST /chat |
| 项目与设置 | 创建项目、查看项目信息、成员/组/审批配置、Usage/Analytics | GET /projects/owned, POST /projects, GET /projects/{project_name}, PUT /projects/{project_name}, GET/POST/PUT/DELETE 成员与组接口, GET/PUT 审批接口, GET /projects/{project_name}/usage, GET /projects/{project_name}/dashboard/analytics |
| 反馈与 Artefacts | 提交反馈、查看 Artefacts | GET/POST /projects/{project_name}/feedback, GET /artefacts |
| 平台管理 | Workbench 权限、平台项目、Usage、Banner 管理 | GET/POST/DELETE /admin/workbench-access, GET/DELETE /admin/projects, GET /admin/usage, GET/POST/PUT/DELETE /admin/banners, PUT /admin/banners/reorder |

### 3.2 本版暂不作为主目标的范围

以下能力可以在第二阶段补充，不作为本版准入门槛：

1. Site Builder 作者态编辑相关性能。
2. Dashboard 文件上传与表单提交流量峰值。
3. 外部模型发现类接口的容量上限测试，如 /langgraph/assistants、/openai/models。

说明：这些接口仍可做补充压测，但不应挤占当前主业务链路的优先级。

---

## 四、流量画像与用户模型

### 4.1 角色配比

| 角色 | 占比 | 说明 |
|---|---|---|
| 普通登录用户 | 50% | 主要停留在 Dashboard、项目页、聊天页 |
| 聊天重度用户 | 25% | 高频创建会话、拉取历史、发送聊天消息 |
| 项目管理员/Owner | 15% | 会进入 Workbench、项目设置、审批、Usage |
| 平台管理员 | 10% | 访问 Admin Panel、Banner、平台项目与权限配置 |

### 4.2 行为权重

| 行为组 | 权重 | 说明 |

---

## 五、容量与阈值测试（Volume Testing）全新方案

### 5.1 历史方法缺陷分析
旧版容量测试方法存在明显缺陷：并未采用真正的“梯度施压”（Ramp-up）机制寻找转折点，指标也相对单一，无法准确找到 Frontier 系统的性能拐点（Threshold）。

### 5.2 改进方案：梯度递增容量测试
为了寻找 Frontier 系统的真正性能边界，新的容量测试将采取动态梯度递增模式，并在测试过程中严格监测多维指标，直到系统侧出现明显报错（Error Rate）或延迟剧增（High Latency）：
1. **递增并发率（Concurrency Rate / Ramp-up）**：并发度随时间逐步增加（如在每一轮持续周期内增加一定的 QPS 尝试）。
2. **QPS 与响应延迟特征**：观察系统吞吐量从线性增长变为平顶，判定当前硬件下的有效 QPS 阈值。
3. **系统突发应对能力（Burst 处理）**：并发的增加同样测试了系统对突发洪峰流量缓冲和连接池的排队抗爆能力。
4. **服务端 CPU 与资源观测**：联动 Docker 并发输出 CPU 与内存占用情况，判断应用层瓶颈还是硬件资源耗尽。

### 5.3 正确的前置全栈启动要求
执行本次及后续的容量测试前，**必须且只能使用**仓库根目录下的前端后端一体融合编排作为启动方式：
> **错误做法**：单独去启动某个前端模块页面，或仅仅只跑 `README.md` 中用于快速起后端的 `python project.py` 片段代码。
> **正确命令（必须且只需在 `frontier/` 目录下执行）**：
> ```bash
> docker compose up -d --build
> ```
此命令会在 `frontier-server` 容器内完成包括依赖前端静态构建、后端框架加载和配置注入的完整运行形态。

### 5.4 专项容量测试脚本（Volume Tester Script）
为此需求特别设计的 `volume_testing_script.py` 支持并发梯级攀爬，提供详细的每秒性能、错误及 Docker 后端实例的开销摘要，请在 `test2/performance/` 路径下执行该脚本验证。
|---|---|---|
| 启动与首屏初始化 | 20 | 登录后立即发生，且存在并发扇出 |
| Dashboard 浏览与进入项目 | 25 | 当前 UI 下的核心读流量 |
| Chat 主链路 | 30 | 最关键写路径，也是最敏感性能路径 |
| 项目设置/审批/Usage | 15 | 中频但查询较重 |
| 平台管理 | 10 | 低频但容易触发聚合查询与批量更新 |

### 4.3 需要重点模拟的并发扇出

1. 登录后并发初始化
   - 同一用户动作会短时间触发 /me、/me/agents、/me/stats、/admin/banners/active。

2. 进入项目设置页并发拉数
   - 同一页面会并发触发 /projects/{project}/usage 与 /projects/{project}/dashboard/analytics。

3. 聊天前置链路
   - 无会话时先 POST /conversations，再 POST /chat。
   - 恢复旧会话时通常先 GET /conversations/{id}/messages，再进入聊天发送。

---

## 五、关键测试接口优先级

### 5.1 P0：必须纳入主压测

| 类型 | 接口 |
|---|---|
| 认证与启动 | POST /login |
| 认证与启动 | GET /config |
| 认证与启动 | GET /me |
| Dashboard | GET /me/agents |
| Dashboard | GET /me/stats |
| 平台启动 Banner | GET /admin/banners/active |
| 项目进入 | GET /projects/{project_name} |
| 项目进入 | GET /projects/{project_name}/agents |
| 会话 | GET /conversations |
| 会话 | POST /conversations |
| 消息历史 | GET /conversations/{id}/messages |
| 聊天 | POST /chat |
| 项目统计 | GET /projects/{project_name}/usage |
| 项目统计 | GET /projects/{project_name}/dashboard/analytics |
| Artefacts | GET /artefacts |

### 5.2 P1：应纳入混合压测或专项压测

| 类型 | 接口 |
|---|---|
| 项目管理 | GET /projects/owned |
| 项目管理 | POST /projects |
| 项目管理 | PUT /projects/{project_name} |
| 反馈 | GET /projects/{project_name}/feedback |
| 反馈 | POST /projects/{project_name}/feedback |
| 审批 | GET /projects/{project_name}/approval-settings |
| 审批 | PUT /projects/{project_name}/approval-settings |
| 审批 | GET /projects/{project_name}/approvers |
| 审批 | POST /projects/{project_name}/approvers |
| 审批 | GET /projects/{project_name}/change-requests |
| 成员管理 | GET/POST/PUT/DELETE /projects/{project_name}/members |
| 组管理 | GET/POST/PUT/DELETE /projects/{project_name}/groups |

### 5.3 P2：管理面专项或补充测试

| 类型 | 接口 |
|---|---|
| 平台管理 | GET/POST/DELETE /admin/workbench-access |
| 平台管理 | GET/DELETE /admin/projects |
| 平台管理 | GET /admin/usage |
| Banner 管理 | GET/POST/PUT/DELETE /admin/banners |
| Banner 管理 | PUT /admin/banners/reorder |
| Agent 辅助配置 | POST /langgraph/assistants |
| Agent 辅助配置 | POST /openai/models |

---

## 六、测试指标（本地适用）

### 6.1 核心原则

本地测试**不设绝对延迟阈值和 RPS 目标**。所有延迟数据仅用于以下两个目的：

1. **纵向对比**：同接口在代码改动前后的基线差异，偏差超过 30% 视为回归信号。
2. **横向对比**：同类接口之间的相对快慢，用于识别异常慢的端点。

### 6.2 需要采集的指标

| 类别 | 指标 | 用途 |
|---|---|---|
| 响应时间 | 每接口 min / avg / P50 / P95 / max | 建立基线，识别异常慢接口 |
| 错误率 | 每接口 HTTP 状态码分布 | 发现并发下的逻辑 Bug |
| 5xx 明细 | 出错接口 + 错误日志 | 定位具体异常 |
| 慢查询 | 响应时间 > 该接口 P95 两倍的请求 | 触发慢查询分析 |
| DB 连接数 | 测试前/中/后的活跃连接数 | 检测连接泄漏 |
| 内存趋势 | frontier-server 容器 RSS，每 30 秒采样 | 检测内存泄漏 |
| 数据正确性 | 并发写入后的数据完整性校验 | 检测竞态条件 |

### 6.3 判定准则（本地可用）

| 判定项 | 通过条件 |
|---|---|
| 并发正确性 | 轻量并发下 5xx 为 0，无数据重复/丢失 |
| 资源泄漏 | 20 分钟持续运行后，内存增量 < 初始值 20%，DB 连接数无持续上升 |
| 回归检测 | 相同场景、相同数据下，改动后 P50 偏差不超过 30% |
| 慢接口 | 同类接口中，P50 超过均值 5 倍的视为需要优化 |
| 聊天链路 | /chat 首字节时间稳定输出，不因并发导致超时或 5xx |
---

## 七、测试环境与启动方式

### 7.1 标准环境

1. 从仓库根目录启动全栈：

```bash
docker compose up -d --build
```

2. 基本验收：
   - http://localhost:8000/config 返回 200
   - http://localhost:8000 可正常打开前端
   - LDAP 登录账号可用，例如 admin/admin123、testuser/test123

3. 不再将“本机直接执行 python project.py”作为主测试路径。

### 7.2 数据准备要求（本地规模）

本地测试不需要生产级数据量，但需要有足够数据让列表查询和聚合接口走到真实代码路径：

| 数据项 | 建议规模 | 说明 |
|---|---|---|
| 测试用户 | 5-10 | 使用 LDAP mock 用户即可 |
| 平台管理员 | 1-2 | admin/admin123 |
| 项目数 | 3-5 | 覆盖有/无 Agent、有/无审批 |
| 每项目 Agent 数 | 2-3 | 至少一个 HTTP、一个 LangGraph |
| 每项目会话数 | 5-15 | 保证列表查询有分页数据 |
| 每会话消息数 | 10-30 | 保证历史消息加载有内容 |
| Banner 数 | 3-5 | 至少有 active 和 inactive 各一条 |
| Artefact Agent 数 | 1-3 | 保证 /artefacts 有返回 |
| 待审批请求 | 每项目 2-5 | 覆盖审批流读取路径 |

### 7.3 测试控制要求

1. /chat 主压测优先使用稳定、可控的示例 Agent，避免把外部模型波动误判为 Frontier 回归。
2. 若需要测外部 Agent 影响，应将“Frontier 后端开销”和“端到端聊天耗时”分开统计。
3. 压测前固定 docker/config.yaml，避免临时改 schema、LDAP、Agent endpoint 造成结果不可比。

---

## 八、测试场景设计

### 场景 1：基线测试

目的：建立单接口和单旅程的无压基线。

覆盖内容：

1. 登录初始化旅程
   - POST /login
   - GET /me
   - GET /me/agents
   - GET /me/stats
   - GET /admin/banners/active

2. 进入项目旅程
   - GET /projects/{project_name}
   - GET /projects/{project_name}/agents

3. 聊天旅程
   - POST /conversations
   - GET /conversations/{id}/messages
   - POST /chat

4. 设置页旅程
   - GET /projects/{project_name}/usage
   - GET /projects/{project_name}/dashboard/analytics

建议工具：pytest-benchmark 或 httpx 自定义基准脚本。

### 场景 2：轻量并发正确性测试

目的：验证少量并发下后端是否出现 5xx、数据损坏或竞态问题。这是本地测试最核心的场景。

建议参数：

| 项目 | 建议值 |
|---|---|
| 并发用户 | 5-10 |
| 持续时间 | 5 分钟 |

用户行为按第四节权重分配。

**重点观察**：
1. 是否出现任何 5xx 响应
2. 并发创建会话/项目是否产生重复数据
3. 并发读写同一项目/会话是否产生脏数据
4. DB 连接数是否在并发结束后回落

### 场景 3：登录初始化并发扇出

目的：验证首页初始化的多接口并发扇出是否存在阻塞或报错。

重点接口（同一用户会近乎同时触发）：

1. POST /login
2. GET /me
3. GET /me/agents
4. GET /me/stats
5. GET /admin/banners/active

建议参数：5-10 个用户同时触发完整登录初始化序列。

**重点观察**：
1. 是否有接口因为其他接口阻塞而超时
2. 并发登录是否导致 Token 签发异常
3. /me/agents 和 /me/stats 的相对耗时差异（识别哪个更慢）

### 场景 4：聊天链路正确性测试

目的：验证聊天全链路在并发下的数据完整性和流式响应稳定性。

重点接口：

1. GET /conversations
2. POST /conversations
3. GET /conversations/{id}/messages
4. POST /chat

建议参数：

| 项目 | 建议值 |
|---|---|
| 并发聊天用户 | 3-5 |
| 每用户发送频率 | 30-60 秒/条 |
| 测试时长 | 5 分钟 |

**重点观察**：
1. 并发创建会话是否成功（无 5xx、无重复 ID）
2. /chat 流式响应是否能正常开始和结束（无中断、无挂起）
3. 消息历史加载是否与实际发送数据一致
4. 使用示例 Agent (http-example) 以隔离外部模型波动

### 场景 5：慢接口发现

目的：定位异常慢的接口，为后续优化提供方向。

做法：

1. 对所有 P0/P1 接口逐一执行 20 次串行调用
2. 记录每个接口的 min / avg / P50 / P95 / max
3. 按接口类别（读/写/聚合）分组对比
4. 标记 P50 超过同类均值 5 倍的接口为"慢接口"

**慢接口需进一步分析**：
1. 开启数据库慢查询日志，检查是否存在全表扫描或缺失索引
2. 检查是否存在 N+1 查询模式
3. 检查是否有不必要的嵌套序列化

### 场景 6：资源泄漏检测

目的：检测持续运行下的内存增长与连接泄漏。这是本地测试的第二核心场景。

建议参数：

| 项目 | 建议值 |
|---|---|
| 并发用户 | 3-5 |
| 运行时间 | 20-30 分钟 |
| 采样周期 | 30 秒 |

流量组成：采用"轻量并发"权重分配，将聊天比例降到 20%，避免示例 Agent 波动干扰。

**必须采集**：
1. frontier-server 容器 RSS 内存趋势（docker stats 或 cAdvisor）
2. Yugabyte 活跃连接数趋势
3. 运行前后的内存差值

**判定**：
1. 内存增量不超过初始值 20%
2. DB 连接数在测试结束后应回落到初始水平
3. 无逐步升高的响应时间趋势
---

## 九、执行步骤

### 第一步：启动环境

```bash
docker compose up -d --build
```

### 第二步：准备数据

1. 创建 3-5 个测试项目，每个项目配 2-3 个 Agent。
2. 每个项目创建若干会话和消息。
3. 创建少量 Banner、审批请求、成员与组。
4. 确认示例 Agent (http-example) 可正常响应。

### 第三步：预热

1. 手动执行一次完整登录 → Dashboard → 进入项目 → 发送聊天。
2. 清理明显异常日志。
3. 确认连接池已初始化。

### 第四步：执行测试

建议顺序：

1. 基线测试（场景 1）— 建立本次基准
2. 慢接口发现（场景 5）— 找到需要优化的端点
3. 轻量并发正确性（场景 2）— 核心验证
4. 登录初始化并发扇出（场景 3）
5. 聊天链路正确性（场景 4）
6. 资源泄漏检测（场景 6）— 最后运行，持续时间最长

### 第五步：采集与分析

必须采集：

1. 每接口 min / avg / P50 / P95 / max（用于回归对比）
2. 每接口 HTTP 状态码分布
3. 所有 5xx 的详细错误日志
4. frontier-server 容器内存趋势
5. Yugabyte 活跃连接数趋势
6. 标记出的"慢接口"清单及初步原因分析
7. /chat 首字节是否正常输出

---

## 十、报告输出要求

最终报告至少应包含：

1. 测试环境信息（本机配置、Docker 版本、镜像 hash）
2. 测试数据规模
3. 各场景参数与运行时长
4. 每接口响应时间统计表（用于后续回归对比基线）
5. 慢接口清单及初步原因（SQL 分析或 N+1 嫌疑）
6. 并发测试中的 5xx / 数据异常记录
7. 内存与连接数趋势截图或数据
8. 发现的 Bug 或需要优化的问题清单
9. 与上一次基线的回归对比（如适用）

---

## 十一、本地测试通过标准

| # | 判定项 | 通过条件 |
|---|---|---|
| 1 | 并发正确性 | 5-10 并发用户下，0 个 5xx，无数据重复/丢失/脏写 |
| 2 | 聊天链路 | /chat 流式响应能正常开始和结束，无挂起；并发创建会话无冲突 |
| 3 | 资源泄漏 | 20 分钟持续运行后，容器内存增量 < 初始值 20%，DB 连接数可回落 |
| 4 | 慢接口 | 无接口 P50 超过同类均值 10 倍（若有，记录为已知问题并给出原因） |
| 5 | 回归检测 | 若存在上次基线，相同场景下各 P0 接口 P50 偏差不超过 30% |

若第 1、2、3 项中任一不满足，应视为本版后端存在需要修复的问题。

第 4、5 项不满足时，不阻塞发布，但应作为优化 backlog 记录。

---

## 十二、本次本地测试脚本的侧重点

本次脚本落地时，侧重点不是追求“把本地机器压到极限”，而是让这套测试在开发机上稳定复现以下五类问题：

1. 相对性能差异
   - 同一台机器、同一份数据下，识别哪个接口明显慢于同类接口。
   - 用于代码改动前后的回归对比，而不是得出生产级吞吐结论。

2. 轻量并发正确性
   - 优先验证 5-10 并发下是否出现 5xx、脏写、重复创建、会话/消息不一致。
   - 这是本地环境最有价值的压测目标。

3. 流式聊天的首包时间与完成稳定性
   - 对 POST /chat 同时记录首字节时间和完整流结束时间。
   - 避免把“首包很快但中途挂起”和“完整响应很慢但稳定”混为一类问题。

4. 资源趋势而非瞬时峰值
   - 重点采集 frontier-server 容器内存趋势和 Yugabyte 活跃连接数趋势。
   - 目标是识别泄漏和不回收，而不是记录某一个时间点的峰值。

5. 前端真实旅程驱动
   - 脚本优先覆盖首页初始化、Dashboard 浏览、项目设置页扇出、聊天主链路、Artefacts、管理只读接口。
   - 不再按 OpenAPI 全量平铺执行，以免脱离当前前端的真实访问模式。

---

## 十三、计划合理性复核与修正建议

整体判断：这份计划作为“当前前端驱动的本地后端性能测试主计划”是合理的，方向基本正确，可以直接作为执行基线。

但落地执行时有 6 个地方需要修正或明确：

### 13.1 /config 应与“登录后初始化”拆开统计

当前计划把 POST /login、GET /config、GET /me、GET /me/agents、GET /me/stats、GET /admin/banners/active 放在同一启动旅程中，这在业务理解上可以接受，但在性能分析上不够精确。

原因：

1. GET /config 是匿名接口，属于应用启动/页面加载前置请求。
2. GET /me、GET /me/agents、GET /me/stats、GET /admin/banners/active 则属于拿到 token 之后的认证态初始化。

建议：

1. 将 GET /config 作为“匿名启动基线”单独统计。
2. 将登录后四个并发接口作为“认证后初始化扇出”单独统计。

### 13.2 默认混合压测不应直接包含破坏性管理写接口

计划中 P1/P2 包含项目创建、Banner 管理、Workbench Access 管理、成员和组增删改等接口。这些接口应保留在专项测试中，但不适合直接进入默认混合压测。

原因：

1. 这些接口会持续污染本地数据集，影响结果可比性。
2. 若不做资源隔离和清理，第二次运行的结果会被第一次运行残留数据扭曲。
3. 它们更适合“临时资源 + 自动清理”的专项场景，而不是常规基线场景。

建议：

1. 默认主脚本只覆盖只读管理接口和核心用户链路。
2. 破坏性管理写接口另做单独场景，并强制使用临时资源前缀和清理逻辑。

### 13.3 本地并发用户数应允许“凭证复用”回退模式

计划建议准备 5-10 个测试用户，这在理想情况下合理；但当前仓库内置 mock LDAP 默认只明确提供 admin/admin123 与 testuser/test123 两组账号。

这意味着如果不额外造数，严格要求“5-10 个不同账号”会让脚本无法开箱运行。

建议：

1. 脚本支持“多账号并发”与“单账号多会话并发”两种模式。
2. 当凭证数量不足时，允许复用账号，但在报告中显式标注这一点。
3. 若要测权限隔离或用户隔离，再单独补充更多 LDAP 用户。

### 13.4 /chat 必须拆分首包时间与完整流耗时

原计划已经提到“首字节时间稳定输出”，这个方向是对的，但执行脚本必须把该指标单独落地，否则最终仍然只会得到总耗时。

建议：

1. 记录 POST /chat 的 TTFB。
2. 同时记录完整流读取完成的总耗时。
3. 如果返回 200 但没有任何流内容，也应视为失败信号。

### 13.5 资源泄漏标准建议增加“趋势解释”

“20 分钟后内存增量 < 初始值 20%”可作为经验阈值，但不应机械化使用。

原因：

1. Python 进程、ORM、连接池、缓存和日志对象都可能在前几分钟出现一次性预热增长。
2. 只看起点和终点，可能把正常预热误判为泄漏。

建议：

1. 保留 20% 阈值作为警戒线。
2. 同时观察曲线是否持续单调上升、并在压测停止后不回落。
3. DB 连接数优先看“压测结束后是否回落”，而不是只看中途峰值。

### 13.6 需要补一条“前置数据可运行性”检查

目前计划写了建议数据规模，但没有把“至少要有一个可聊天的默认 Agent”明确成硬前置条件。

如果没有满足以下条件，P0 脚本会直接失败：

1. 目标项目存在。
2. 测试用户能访问该项目。
3. 目标项目下至少有一个可用 Agent，最好是 http-example。
4. 项目设置页 usage/analytics 可正常返回。

因此，执行前应先跑一轮 preflight，而不是直接进入压测。

---

## 十四、测试脚本落地方案

已新增两份文件：

1. scripts/perf/local_perf_runner.py
2. scripts/perf/perf_config.example.yaml

### 14.1 脚本设计目标

这套脚本默认服务于“本地、可重复、低侵入”的验证目标，因此设计上遵循以下原则：

1. 优先覆盖 P0 和高价值 P1 读链路。
2. 默认不执行破坏性管理写操作。
3. 同时支持单场景运行和 all 全量运行。
4. 输出结构化结果，便于后续回归对比。

### 14.2 已实现的场景

| 场景 | 脚本参数 | 用途 |
|---|---|---|
| 预检查 | --scenario preflight | 验证服务、登录、项目、Agent、资源采样是否可用 |
| 基线测试 | --scenario baseline | 建立单旅程顺序调用基线 |
| 慢接口扫描 | --scenario slow_endpoints | 对关键端点做串行重复调用，输出 P50/P95 |
| 登录扇出 | --scenario login_fanout | 模拟登录后 /me、/me/agents、/me/stats、/admin/banners/active 并发拉取 |
| 设置页扇出 | --scenario settings_fanout | 并发拉取 usage 与 analytics |
| 聊天正确性 | --scenario chat_correctness | 创建会话、拉历史、发起流式聊天，并校验消息历史增长 |
| 轻量混合压测 | --scenario mixed_light | 按权重混合首页、Dashboard、聊天、设置、Artefacts、管理只读 |
| 资源泄漏检测 | --scenario resource_leak | 在混合流量下后台采样容器内存与 DB 活跃连接 |
| 全量执行 | --scenario all | 依次执行上述所有默认场景 |

### 14.3 已覆盖的关键指标

脚本默认采集以下结果：

1. 每次请求的响应时间。
2. 每个端点的 min / avg / P50 / P95 / max。
3. 每个端点的状态码分布。
4. /chat 的首包时间 TTFB。
5. /chat 是否存在“200 但无流内容”的异常。
6. 聊天后消息历史是否增长。
7. frontier-server 容器内存采样。
8. Yugabyte 当前数据库活跃连接数采样。

### 14.4 脚本输出物

每次运行会在 artifacts/perf/时间戳 目录下生成：

1. raw_records.json：原始请求记录。
2. summary.json：聚合统计。
3. summary.csv：便于表格对比的汇总结果。
4. report.md：可直接查看的简要报告。
5. resource_samples.json：资源采样数据，仅 resource_leak 场景生成。

---

## 十五、建议运行方式

### 15.1 启动服务

```bash
docker compose up -d --build
```

### 15.2 准备并修改配置

复制并调整：

1. scripts/perf/perf_config.example.yaml
2. 至少确认 base_url、project_name、users、database 四项配置正确。
3. 推荐将 project_name 指向一个专门用于性能测试的项目，且其中有 http-example Agent。

### 15.3 先跑预检查

```bash
python scripts/perf/local_perf_runner.py --config scripts/perf/perf_config.example.yaml --scenario preflight
```

### 15.4 再跑核心场景

推荐顺序：

```bash
python scripts/perf/local_perf_runner.py --config scripts/perf/perf_config.example.yaml --scenario baseline
python scripts/perf/local_perf_runner.py --config scripts/perf/perf_config.example.yaml --scenario slow_endpoints
python scripts/perf/local_perf_runner.py --config scripts/perf/perf_config.example.yaml --scenario login_fanout
python scripts/perf/local_perf_runner.py --config scripts/perf/perf_config.example.yaml --scenario chat_correctness
python scripts/perf/local_perf_runner.py --config scripts/perf/perf_config.example.yaml --scenario resource_leak
```

若要一次执行默认全量场景：

```bash
python scripts/perf/local_perf_runner.py --config scripts/perf/perf_config.example.yaml --scenario all
```

---

## 十六、当前版本脚本的边界说明

为保证本地结果稳定且可重复，当前脚本有意没有把以下内容放进默认流量模型：

1. Banner 创建、更新、删除。
2. Workbench Access 增删。
3. 项目创建后再删除的循环。
4. 成员、组、审批人的增删改写压测。

这些接口仍然值得做专项测试，但应在“临时资源 + 自动清理”的隔离场景中单独执行，否则会破坏基线数据的一致性。
