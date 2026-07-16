# AI课程选课冲突与候补调整系统：测试策略矩阵

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| 文档阶段 | ⑤ test-strategy |
| 版本 | v0.1 |
| 状态 | 测试策略初稿已完成；M3已验证，M1、M2及三模块集成待执行 |
| 上游输入 | `02_product-prd.md`、`03_design-options.md`、`04_dev-workflow.md`、`project/contracts/` |
| 当前环境 | Windows PowerShell；Python 3.14.6；pytest 8.4.2；Node.js 24.18.0；npm 11.16.0；Vitest 4.1.10 |
| 当前自动化基线 | M3后端14项通过、M3前端4项通过、前端生产构建通过；不代表M1/M2或全项目已通过 |
| 下游文档 | `06_qa-gates.md` |

## 2. 测试目标

本策略优先验证会破坏AI可信度、选课资格、公平递补和三模块集成的高风险事实，而不只验证接口能够返回数据：

1. 正常推荐至少真实调用一次MiMo，Stub或fallback不能替代主验收。
2. 模型只负责推荐和解释，重复、先修、冲突、容量与候补顺序必须由确定性代码决定。
3. 模型输出必须经过课程ID白名单和结构化Schema校验，目录外课程不得进入页面或状态。
4. `PASS/BLOCK`、`ENROLLED/WAITLISTED/REJECTED`和`WAITING/PROMOTED/SKIPPED`三类状态不得混用。
5. 满员是容量分流，不是资格失败；规则通过的学生应进入候补。
6. 候补重算必须保留申请顺序，第一名失效后继续检查下一名。
7. M1、M2、M3必须共享同一个Store和Trace事实来源，学生端、教师端和服务端状态一致。
8. 每个关键操作必须返回可查询的`trace_id`，模型、规则和状态事件按时间可追溯。
9. fallback必须明显标记“降级推荐”并保留失败原因，不得伪装为MiMo成功结果。
10. reset只能恢复内存状态，不得覆盖`ai-course-selection-data`种子JSON。
11. 实现必须服从冻结的`project/contracts`，不得通过修改共享契约来迁就单个模块。

## 3. 测试层次与执行方式

| 层次 | 目的 | 目标位置 | 主要方法 | 当前状态 |
|---|---|---|---|---|
| 单元测试 | 验证模型校验、确定性规则、状态转换、队列顺序 | `backend/tests/recommendation/`、`enrollment/`、`waitlist/` | 固定输入、手算预期、状态前后快照 | M3通过；M1/M2待执行 |
| 前端组件测试 | 验证两角色页面、来源标签、按钮行为和状态展示 | `frontend/tests/recommendation/`、`enrollment/`、`waitlist/` | Vue Test Utils、API Mock、事件与文案断言 | M3通过；M1/M2待执行 |
| 契约测试 | 验证请求、响应、枚举和错误包络符合冻结OpenAPI | `backend/tests/**/test_*contract*.py` | 用`project/contracts/openapi.yaml`校验真实响应 | M3成功/错误响应通过 |
| 模块API测试 | 验证8101、8102、8103独立纵向切片 | 各模块`demo.py`及API测试 | FastAPI TestClient、真实HTTP冒烟 | M3通过；M1/M2待执行 |
| 集成测试 | 验证M1→M2→M3共享Store、真实Ports和统一Trace | `backend/tests/integration/`、`frontend/tests/integration/` | 组合入口、固定场景、跨端状态对照 | 待执行 |
| 大模型验收 | 验证真实MiMo、结构化响应、重试和fallback | M1测试、调用记录、追溯响应 | 真实成功调用一次；故障注入单独验证 | 待执行 |
| 演示验收 | 验证V1—V4可reset并重复完成 | 学生页、教师页、`/docs` | 人工操作+服务端状态+Trace三方对照 | V4的M3独立切片通过；全链路待执行 |
| 回归测试 | 防止模块合并破坏已完成能力 | 全部前后端测试 | 每个模块Green及每次合并后全量执行 | 持续执行 |

统一验证命令：

```powershell
cd D:\xiaomi\Day5\project\backend
python -m pytest -q

cd D:\xiaomi\Day5\project\frontend
npm.cmd run test
npm.cmd run build

cd D:\xiaomi\Day5
git diff --exit-code -- project/contracts
```

最后一条命令必须无输出并返回0；若有差异，停止模块合并并先进行共享契约评审。

## 4. AC → TC 映射矩阵

“通过”表示已有直接自动化证据；“部分”表示只完成了独立模块证据，仍缺跨模块或双端断言；“待执行”表示已定义测试目标但对应成员尚未交付证据。24条AC均至少映射一条TC。

| AC | 测试用例TC | 测试文件/函数 | 类型 | 当前状态 | 证据或缺口 |
|---|---|---|---|---|---|
| AC-R1-1 | TC-R1-01 非空目标真实调用MiMo并返回目录内课程 | `tests/recommendation/test_mimo_adapter.py`（待新增）、V1调用记录 | 模型/集成 | 待执行 | 必须是真实MiMo成功调用，不能使用Stub |
| AC-R1-2 | TC-R1-02 正常响应包含课程ID、分数、理由、不确定性、`source=MODEL`和`trace_id` | `test_recommendation_service.py`（待新增） | 正常路径 | 待执行 | 同时校验OpenAPI响应 |
| AC-R1-3 | TC-R1-03 非法JSON或目录外课程最多重试一次，失败进入fallback | `test_mimo_validation.py`（待新增） | 对抗/降级 | 待执行 | 断言非法课程未进入结果和Store |
| AC-R1-4 | TC-R1-04 空目标在调用MiMo前被拒绝 | M1后端与前端测试（待新增） | 边界/拒收 | 待执行 | 需断言模型调用次数为0 |
| AC-R1-5 | TC-R1-05 超时、401、5xx和网络失败明确显示失败或fallback | M1故障注入测试（待新增） | 预期失败 | 待执行 | 页面必须显示“降级推荐”和失败原因 |
| AC-R2-1 | TC-R2-01 重复选课返回`BLOCK`和重复原因 | `tests/enrollment/test_rule_engine.py`（待新增） | 规则/拒收 | 待执行 | 状态不得被修改 |
| AC-R2-2 | TC-R2-02 缺少一个或多个先修课程返回`BLOCK`及缺失ID | 同上（待新增） | 规则/边界 | 待执行 | 多个缺失项也需覆盖 |
| AC-R2-3 | TC-R2-03 时间部分重叠返回`BLOCK`及冲突课程 | 同上（待新增） | 规则/边界 | 待执行 | 相邻但不重叠应允许 |
| AC-R2-4 | TC-R2-04 三项规则通过且有容量时返回`PASS` | 同上（待新增） | 正常路径 | 待执行 | 规则引擎本身不得写状态 |
| AC-R2-5 | TC-R2-05 满员时资格仍为`PASS`并交给容量分流 | `test_enrollment_service.py`（待新增） | 关键边界 | 待执行 | 禁止把满员返回为`BLOCK` |
| AC-R3-1 | TC-R3-01 `PASS`且有容量时返回`ENROLLED`并使人数加1 | M2 Service/API测试（待新增） | 状态转换 | 待执行 | M3 Store已有`save_enrolled`能力，尚缺M2闭环 |
| AC-R3-2 | TC-R3-02 `PASS`且满员时返回`WAITLISTED/WAITING`及排名 | M2与M3共享Store集成测试（待新增） | 状态/集成 | 待执行 | 教师端随后必须读到同一候补记录 |
| AC-R3-3 | TC-R3-03 `BLOCK`映射为`REJECTED`且不新增任何状态 | M2状态前后快照测试（待新增） | 拒收/保护 | 待执行 | 需同时检查已选与候补 |
| AC-R3-4 | TC-R3-04 重复候补返回原排名且不创建第二条记录 | M2 Service+M3 Store测试（待新增） | 幂等/边界 | 待执行 | `save_waitlisted`已有防重实现，尚缺跨模块证据 |
| AC-R3-5 | TC-R3-05 三种选课结果均返回可查询`trace_id` | M2 API/Trace测试（待新增） | 契约/追溯 | 待执行 | 需覆盖ENROLLED、WAITLISTED、REJECTED |
| AC-R4-1 | TC-R4-01 满员课程释放一个名额并完成一次重算 | `test_api.py::test_full_waitlist_flow_and_trace`、`test_waitlist_service.py::test_release_seat_increases_capacity_by_one` | API/集成 | 通过 | 容量30→31，可用名额0→1并进入重算 |
| AC-R4-2 | TC-R4-02 第一名资格失效后标记`SKIPPED`及冲突原因 | `test_waitlist_service.py::test_recompute_skips_first_candidate_and_promotes_second` | 状态/边界 | 通过 | S002因DB202冲突被跳过 |
| AC-R4-3 | TC-R4-03 第一名跳过后继续并补入第二名 | 同上、`test_api.py::test_full_waitlist_flow_and_trace` | 顺序/状态 | 通过 | S005变为`PROMOTED`，人数变31 |
| AC-R4-4 | TC-R4-04 没有空位时停止且队列不变 | `test_waitlist_service.py::test_recompute_without_a_seat_does_not_mutate_waitlist` | 边界/保护 | 通过 | checked为空，状态前后相等 |
| AC-R4-5 | TC-R4-05 教师与学生查询同一人数、候补和补入结果 | M3课程状态测试；M2学生状态集成测试（待新增） | 跨端集成 | 部分 | 教师/API状态通过；缺学生端与M2状态接口对照 |
| AC-R5-1 | TC-R5-01 一个`trace_id`串联学生输入、AI建议、规则和最终状态 | V1全链路Trace测试（待新增） | 端到端 | 待执行 | 三模块尚未组合 |
| AC-R5-2 | TC-R5-02 MiMo失败追溯含原因与`source=FALLBACK` | M1 fallback Trace测试（待新增） | 降级/追溯 | 待执行 | 不能用该场景替代V1 |
| AC-R5-3 | TC-R5-03 Trace包含资格重检、S002跳过原因和S005补入 | `test_waitlist_service.py::test_recompute_trace_contains_release_checks_skip_and_promotion` | 追溯/顺序 | 通过 | 6个事件按时间顺序可查 |
| AC-R5-4 | TC-R5-04 教师释放事件含角色、课程、操作前后状态和结果 | 同上、`test_shared_contract_conformance.py` | 追溯/契约 | 通过 | `actor=TEACHER`，容量30→31，响应符合OpenAPI |

### 当前AC覆盖结论

- AC总数：24。
- 至少有一个TC映射：24/24。
- 当前直接自动化证据充分：6。
- 当前部分覆盖：1（AC-R4-5）。
- 已定义但待M1/M2或集成执行：17。
- 当前结论只允许判定“M3独立模块通过”，不允许判定“整个项目通过”。

## 5. 当前18条M3自动化测试分布

| 模块 | 数量 | 覆盖重点 | 当前结果 |
|---|---:|---|---|
| Store与冻结Ports | 4 | 数据适配、候补顺序、三类Ports、reset不改种子、未知课程 | 4 passed |
| 候补Service | 4 | 释放名额、跳过后继续、无空位不变、完整追溯 | 4 passed |
| FastAPI接口 | 4 | 状态、完整重算、reset、错误包络 | 4 passed |
| 共享契约一致性 | 2 | 5个M3成功响应和错误响应符合冻结OpenAPI | 2 passed |
| Vue候补组件 | 3 | 容量/队列、API驱动释放、跳过与补入展示 | 3 passed |
| Vue追溯组件 | 1 | 事件按时间顺序展示 | 1 passed |
| 合计 | 18 | 当前仅为M3基线 | 18 passed；build通过 |

M1、M2完成后必须在本节增加实际测试数量和命令输出，不得预填通过数量。

## 6. AI发散：20条边界/异常候选

风险评分采用“影响1—5 × 出现频率1—5”，用于人工排序，不表示实现状态。

| ID | 候选用例 | 影响 | 频率 | 分数 | 当前覆盖 |
|---|---|---:|---:|---:|---|
| B01 | 学习目标为空或只有空白字符，仍错误调用MiMo | 5 | 4 | 20 | 待执行 |
| B02 | MiMo返回非法JSON或目录外课程ID | 5 | 4 | 20 | 待执行 |
| B03 | MiMo超时、401、429或5xx后重试超过一次 | 4 | 3 | 12 | 待执行 |
| B04 | API Key出现在响应、Trace、日志或前端构建产物 | 5 | 3 | 15 | 待执行 |
| B05 | fallback结果被标记成MODEL或页面未显示“降级推荐” | 5 | 3 | 15 | 待执行 |
| B06 | 模型对同一课程返回重复推荐或空推荐列表 | 3 | 3 | 9 | 待执行 |
| B07 | 学生重复选择同一门已选课程 | 5 | 4 | 20 | 待执行 |
| B08 | 两课程结束与开始时间相同，被误判为冲突 | 4 | 4 | 16 | 待执行 |
| B09 | 两课程只重叠一分钟，却未被判定冲突 | 5 | 3 | 15 | 待执行 |
| B10 | 学生同时缺多个先修课程，只返回一个或误判通过 | 4 | 3 | 12 | 待执行 |
| B11 | 课程满员被错误映射为`BLOCK/REJECTED` | 5 | 4 | 20 | 待执行 |
| B12 | 同一学生重复提交候补，生成两条记录或排名变化 | 5 | 3 | 15 | 实现具备防重，缺跨模块测试 |
| B13 | 无空位时执行重算，错误修改候补状态 | 5 | 3 | 15 | 已覆盖 |
| B14 | 多个空位时补入超过空位数或破坏原申请顺序 | 5 | 2 | 10 | 待补专门测试 |
| B15 | 第一名失效后算法停止，没有继续检查第二名 | 5 | 4 | 20 | 已覆盖 |
| B16 | 已`SKIPPED/PROMOTED`记录在下一次重算中被再次处理 | 4 | 2 | 8 | 实现跳过非WAITING，缺专门测试 |
| B17 | M2写入一个Store，M3或前端读取另一个Store实例 | 5 | 4 | 20 | 待集成测试 |
| B18 | reset覆盖种子JSON，或多次reset得到不同初始状态 | 5 | 3 | 15 | M3已覆盖只读与恢复；全场景待验证 |
| B19 | 请求包含额外字段、非法枚举或空ID时仍修改状态 | 5 | 3 | 15 | 严格Pydantic和响应契约已覆盖部分；请求保护待补 |
| B20 | Trace事件乱序、缺少actor/原因，或释放与重算使用不同事实链 | 5 | 3 | 15 | M3已覆盖；跨M1/M2待验证 |

## 7. 推荐收敛：20 → 8

以下8条按AI可信度、规则正确性、公平性、状态一致性和演示风险推荐进入P0边界集，尚待人工确认。

| 优先级 | ID | 推荐保留理由 | 对应路径 | 当前状态 |
|---:|---|---|---|---|
| 1 | B17 | 三模块若未共享Store，单模块都通过但合并后状态仍会互相不可见 | 集成/NFR-7 | 待执行 |
| 2 | B02 | 模型编造课程或非法结构会直接污染推荐和后续选课 | R1/模型边界 | 待执行 |
| 3 | B11 | 满员与资格失败混用会破坏R2/R3核心状态机 | R2/R3 | 待执行 |
| 4 | B15 | 第一名失效后停止会破坏候补公平和题目核心考点 | R4 | 自动化通过 |
| 5 | B04 | API Key泄露属于不可接受的安全问题 | R1/NFR-6 | 待执行 |
| 6 | B08/B09 | 时间边界错误会直接造成误拒或错选 | R2 | 待执行 |
| 7 | B19 | Schema漂移或无效请求写状态会破坏共享契约和一致性 | 契约/保护 | M3响应通过；请求保护待补 |
| 8 | B18 | 演示状态无法稳定恢复会导致V1—V4不可重复 | reset/演示 | M3通过；全场景待验证 |

暂未进入Top 8不表示不测试：B01、B03、B05、B07、B12—B14、B16和B20仍需按AC与模块门禁执行。

## 8. 正常、预期失败、拒收与降级案例

| 类别 | 代表TC | 预期行为 | 当前证据 |
|---|---|---|---|
| 正常路径 | TC-R1-01、TC-R2-04、TC-R3-01、TC-R4-01 | 真实MiMo推荐→规则PASS→选课/候补→状态可查 | M3候补切片通过；完整主链待执行 |
| 预期失败 | MiMo超时、401、非法JSON、未知课程、未知场景 | 返回契约错误或明确fallback，不静默成功 | M3未知课程/场景保护通过；M1待执行 |
| 拒收案例 | 空目标、重复选课、缺先修、时间冲突、非法Schema | 不调用不该调用的依赖，不写入已选或候补 | 待M1/M2执行 |
| 降级继续 | MiMo重试一次后使用fallback | 页面明显标记“降级推荐”，Trace保留失败原因 | 已批准策略，尚无实现证据 |
| 边界不变 | 无空位重算、已处理候补再次出现 | 不补入、不回滚、不改变其余顺序 | 无空位已通过；重复重算待补 |

## 9. 四个固定场景验收矩阵

每个场景都必须在reset后从固定数据开始，并同时保存页面、API响应和Trace证据。

| 场景 | 自动化路径 | 页面检查 | 服务端/Trace检查 | 当前状态 |
|---|---|---|---|---|
| V1 正常推荐并选课成功 | 真实MiMo→M1选择→M2 PASS→M3 Store ENROLLED | 显示“AI推荐 · MiMo”和`ENROLLED` | 推荐、规则、最终状态位于可查询Trace；真实模型调用成功 | 待执行 |
| V2 推荐课程发生时间冲突 | M1推荐→M2 TIME_CONFLICT | 显示`REJECTED`、冲突课程和原因 | Store没有新增已选/候补；Trace记录BLOCK | 待执行 |
| V3 满员后进入候补 | M1选择满员课→M2规则PASS→M3写候补 | 显示`WAITLISTED`、`WAITING`和排名 | 教师端立即读到相同候补记录 | 待执行 |
| V4 第一名失效、第二名补入 | M3释放名额→调用M2真实`EligibilityPort`→逐人重检 | S002已跳过且显示原因；S005已补入 | 人数31、空位0、6类事件顺序一致 | M3独立切片通过；真实M2注入与学生端对照待执行 |
| 额外故障场景 | MiMo超时→最多重试一次→fallback | 明显显示“降级推荐”和失败原因 | `source=FALLBACK`；不得作为V1证据 | 待执行 |

## 10. 共享契约与三模块集成门禁

### 10.1 冻结契约门禁

- `project/contracts/openapi.yaml`中的8个接口、领域Schema、枚举和前端事件是唯一共享契约。
- 模块不得私自新增字段、改枚举拼写或修改错误包络来迁就自己的实现。
- 若契约确实不足，必须先提出变更说明并由三人确认；不得在模块分支直接修改冻结文件。
- M3已有2项测试直接用冻结OpenAPI校验5个成功响应和错误响应。
- 每次合并前执行：

```powershell
git diff --exit-code -- project/contracts
```

### 10.2 真实组合门禁

- [ ] 生产`bootstrap.py`只创建一个`InMemoryStore`实例。
- [ ] M1通过`CatalogPort/TracePort`使用该Store。
- [ ] M2通过`StatePort/TracePort`使用该Store，并实现真实`EligibilityPort`。
- [ ] M3通过注入调用M2真实规则引擎，不在生产入口使用`FakeEligibilityPort`。
- [ ] 前端组合入口只组合组件和转发事件，不复制规则或直接改状态。
- [ ] M2写入的候补可由M3教师接口立即读取。
- [ ] M3补入的`ENROLLED`可由M2学生状态接口立即读取。
- [ ] 正式入口不读取`contracts/examples/`作为业务结果。

## 11. MiMo专项验收

| 检查项 | 测试方法 | 通过标准 | 当前状态 |
|---|---|---|---|
| 真实调用 | 使用测试账号和环境变量执行V1 | 至少1次MiMo成功响应，模型名和trace可核验 | 待执行 |
| 输出结构 | 合法、缺字段、非法JSON、额外字段 | 合法结果通过Pydantic；非法结果最多重试一次 | 待执行 |
| 课程白名单 | 返回`courses.json`外ID | 过滤或拒绝，绝不进入页面与Store | 待执行 |
| 超时与错误 | 注入超时、401、429、5xx | 失败可见；一次重试后进入明确fallback | 待执行 |
| fallback标识 | 检查API、页面和Trace | 三处均明确为`FALLBACK/降级推荐`并含原因 | 待执行 |
| 密钥保护 | 搜索仓库、响应、Trace和前端dist | 不出现真实API Key | 待执行 |
| AI/规则边界 | 让模型声称课程“可直接选” | 最终资格仍由M2确定性规则决定 | 待执行 |

## 12. 退出标准与剩余缺口

进入QA Gates前应满足：

- [x] 24条AC全部至少映射1条TC。
- [x] M3后端14项、前端4项测试和前端build通过。
- [x] M3成功响应与错误响应符合冻结OpenAPI。
- [x] M3种子JSON只读，reset可重复恢复固定状态。
- [ ] M1推荐后端、前端、真实MiMo和fallback测试全部通过。
- [ ] M2规则、选课状态和前端测试全部通过。
- [ ] M1、M2、M3均有独立Demo与真实命令输出。
- [ ] 三模块合并后共享同一个Store和Trace事实来源。
- [ ] V1—V4在reset后均可重复执行并保留证据。
- [ ] V1至少成功调用一次真实MiMo。
- [ ] fallback单独通过，且没有替代V1。
- [ ] 正常、预期失败、拒收和降级路径均有自动化证据。
- [ ] 前端全测、后端全测和生产build全部通过。
- [ ] `git diff --exit-code -- project/contracts`返回0。
- [ ] 仓库、响应、Trace和前端构建产物中没有真实API Key。
- [ ] Top 8边界用例已由人工确认。

## 13. 人工确认记录

| 确认项 | 结论 | 确认人 | 日期 | 备注 |
|---|---|---|---|---|
| AC→TC映射范围 | 待确认 | — | 2026-07-16 | 24/24 AC已有测试目标；当前6条直接通过、1条部分、17条待执行 |
| 20→8边界用例筛选 | 待确认 | — | 2026-07-16 | 优先保留Store共享、模型白名单、满员分流、公平递补、密钥、时间边界、契约和reset |
| 共享契约零漂移门禁 | 已确认 | 用户 | 2026-07-16 | 不允许通过改动`project/contracts`迁就模块实现 |
| 当前M3测试证据 | 通过 | AI执行记录 | 2026-07-16 | 后端14项、前端4项、build和8103 HTTP冒烟通过 |
| 是否进入QA Gates | 不批准 | — | 2026-07-16 | M1、M2、真实MiMo与三模块V1—V4尚未完成 |
