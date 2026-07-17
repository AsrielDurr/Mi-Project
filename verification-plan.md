# AI课程选课冲突与候补调整系统：验证计划与测试记录

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| 文档阶段 | ⑦ verification-plan |
| 版本 | v0.1 |
| 状态 | 测试用例已定义，实际执行记录待补充 |
| 目的 | 定义验证样例、边界测试、风险说明，作为"证据链可信"考点的支撑 |

---

## 2. 验证策略

| 层级 | 范围 | 工具 | 通过标准 |
|---|---|---|---|
| 单元测试 | 规则引擎、模型校验、候补逻辑、状态转换 | pytest | 所有测试用例通过 |
| 组件测试 | 前端组件渲染、事件触发、状态展示 | Vitest | 组件行为符合契约 |
| API集成测试 | 推荐→选课→候补→重算完整流程 | pytest + httpx | 端到端流程通过 |
| 手动验收 | 四个固定场景、fallback场景 | 人工操作 | 结果与预期一致 |
| 证据收集 | 测试输出、截图、trace_id记录 | 文件/截图 | 可追溯、可重复 |

---

## 3. 单元测试用例

### 3.1 规则引擎测试（M2）

| 编号 | 场景 | 输入 | 预期输出 | 状态 |
|---|---|---|---|---|
| UT-R01 | 重复选课 | 学生已选C003，再次选C003 | RuleDecision=BLOCK, rule=DUPLICATE | 待执行 |
| UT-R02 | 缺少先修 | 学生未完成C001，选需要C001的C003 | RuleDecision=BLOCK, rule=PREREQUISITE | 待执行 |
| UT-R03 | 时间冲突 | 目标课程与已选课程同一时间段 | RuleDecision=BLOCK, rule=TIME_CONFLICT | 待执行 |
| UT-R04 | 资格通过+有容量 | 规则全通过，课程capacity>enrolled | RuleDecision=PASS, status=ENROLLED | 待执行 |
| UT-R05 | 资格通过+满员 | 规则全通过，课程capacity=enrolled | RuleDecision=PASS, status=WAITLISTED | 待执行 |
| UT-R06 | 重复候补 | 学生已在候补队列，重复提交 | 不创建第二条记录 | 待执行 |
| UT-R07 | 规则确定性 | 同一输入执行两次 | 两次结果完全一致 | 待执行 |
| UT-R08 | 规则不修改状态 | 执行规则检查后 | 学生和课程状态不变 | 待执行 |

### 3.2 模型校验测试（M1）

| 编号 | 场景 | 输入 | 预期输出 | 状态 |
|---|---|---|---|---|
| UT-M01 | 合法MiMo响应 | 标准JSON响应 | RecommendationResponse, source=MODEL | 待执行 |
| UT-M02 | 非法JSON | 非JSON格式响应 | 重试一次，失败后source=FALLBACK | 待执行 |
| UT-M03 | 目录外课程 | 响应包含不存在的course_id | 过滤掉非法课程，保留合法部分 | 待执行 |
| UT-M04 | 超时 | 模型响应超过设定时间 | 重试一次，失败后source=FALLBACK | 待执行 |
| UT-M05 | API Key安全 | 检查所有响应和日志 | 不包含API Key | 待执行 |
| UT-M06 | 过滤后为空 | 所有推荐都是目录外课程 | 进入fallback流程 | 待执行 |

### 3.3 候补重算测试（M3）

| 编号 | 场景 | 输入 | 预期输出 | 状态 |
|---|---|---|---|---|
| UT-W01 | 第一名合格 | 释放1个名额，第一名资格有效 | 第一名PROMOTED, status=ENROLLED | 待执行 |
| UT-W02 | 第一名失效 | 第一名资格失效（如新增冲突） | 第一名SKIPPED, 继续检查第二名 | 待执行 |
| UT-W03 | 第二名补入 | 第一名失效，第二名合格 | 第二名PROMOTED, enrolled_count+1 | 待执行 |
| UT-W04 | 无空位 | 释放0个名额 | 不改变队列 | 待执行 |
| UT-W05 | 名额用完 | 释放1个名额，检查到第二名时名额已用完 | 停止重算 | 待执行 |
| UT-W06 | 队列结束 | 释放多个名额，所有候补都检查完 | 正常结束 | 待执行 |
| UT-W07 | 追溯完整性 | 重算完成 | 包含释放、重检、跳过/补入事件 | 待执行 |
| UT-W08 | 种子数据只读 | reset后 | 恢复到初始状态，种子文件不变 | 待执行 |

### 3.4 状态转换测试

| 编号 | 场景 | 输入 | 预期输出 | 状态 |
|---|---|---|---|---|
| UT-S01 | PASS+有容量 | RuleDecision=PASS, capacity>0 | EnrollmentStatus=ENROLLED | 待执行 |
| UT-S02 | PASS+满员 | RuleDecision=PASS, capacity=0 | EnrollmentStatus=WAITLISTED | 待执行 |
| UT-S03 | BLOCK | RuleDecision=BLOCK | EnrollmentStatus=REJECTED | 待执行 |
| UT-S04 | WAITING→PROMOTED | 候补重检合格 | WaitlistStatus=PROMOTED | 待执行 |
| UT-S05 | WAITING→SKIPPED | 候补重检不合格 | WaitlistStatus=SKIPPED | 待执行 |

---

## 4. API集成测试用例

| 编号 | 场景 | 步骤 | 预期结果 | 状态 |
|---|---|---|---|---|
| IT-01 | 推荐→选课成功 | POST /recommend → POST /enroll → GET /student/status | source=MODEL, ENROLLED, trace_id有效 | 待执行 |
| IT-02 | 推荐→时间冲突 | POST /recommend → POST /enroll（冲突课程） | BLOCK/REJECTED, 不写入状态 | 待执行 |
| IT-03 | 推荐→满员候补 | POST /recommend → POST /enroll（满员课程） | PASS/WAITLISTED, 候补排名 | 待执行 |
| IT-04 | 释放→重算→补入 | POST /release-seat → POST /recompute-waitlist | 第一名SKIPPED, 第二名PROMOTED | 待执行 |
| IT-05 | 追溯查询 | 使用IT-01的trace_id调用GET /trace/{id} | 包含模型、规则、状态事件 | 待执行 |
| IT-06 | 场景重置 | POST /demo/reset → 重新执行IT-01 | 结果与IT-01一致 | 待执行 |
| IT-07 | MiMo fallback | 模拟MiMo失败 → POST /recommend | source=FALLBACK, 页面显示降级 | 待执行 |
| IT-08 | 空目标校验 | POST /recommend（空goal） | 返回字段校验错误，不调用模型 | 待执行 |

---

## 5. 边界测试用例

| 编号 | 边界场景 | 预期行为 | 状态 |
|---|---|---|---|
| BT-01 | 学习目标为空 | 不调用模型，返回缺失字段提示 | 待执行 |
| BT-02 | 课程目录为空 | 返回空推荐或明确错误 | 待执行 |
| BT-03 | 候补队列为空 | 释放名额后重算无操作 | 待执行 |
| BT-04 | 同时释放多个名额 | 按顺序逐个检查候补 | 待执行 |
| BT-05 | 所有候补都失效 | 重算结束，名额保留 | 待执行 |
| BT-06 | 课程状态为CANCELLED | 不允许选课 | 待执行 |
| BT-07 | 重复reset | 恢复到初始状态 | 待执行 |
| BT-08 | 前后端枚举不一致 | Pydantic拒绝，返回校验错误 | 待执行 |

---

## 6. 风险说明

| 风险 | 可能性 | 影响 | 控制措施 | 验证方式 |
|---|---|---|---|---|
| MiMo API不可用 | 中 | 无法演示真实AI调用 | fallback降级 + 已验证调用记录 | IT-07 |
| 模型输出不稳定 | 中 | 不同调用返回格式不同 | 结构化输出校验 + 重试一次 | UT-M01~M06 |
| 三人字段不一致 | 低 | 联调时接口报错 | Step 0冻结Schema + 契约测试 | IT-08 |
| 候补逻辑错误 | 低 | 公平性问题 | 单测覆盖8种场景 | UT-W01~W08 |
| 内存状态污染 | 低 | 演示结果不可预测 | reset接口恢复种子数据 | IT-06 |
| 前端复制硬规则 | 中 | 规则判断不一致 | 代码审查 + 以后端结果为准 | 手动审查 |
| 集成后残留Fake | 低 | 正式运行使用假数据 | bootstrap.py只注入真实实现 | 集成门禁检查 |

---

## 7. 测试执行记录模板

> 每项测试完成后实时更新，不得预填通过。

| 模块 | 测试命令 | 总数 | 通过 | 失败 | 状态 | 执行时间 | 证据/备注 |
|---|---|---|---|---|---|---|---|
| M1后端 | `pytest backend/tests/recommendation -q` | 待执行 | — | — | 待执行 | — | — |
| M1前端 | `npm run test -- recommendation` | 待执行 | — | — | 待执行 | — | — |
| M2后端 | `pytest backend/tests/enrollment -q` | 待执行 | — | — | 待执行 | — | — |
| M2前端 | `npm run test -- enrollment` | 待执行 | — | — | 待执行 | — | — |
| M3后端 | `pytest backend/tests/waitlist -q` | 待执行 | — | — | 待执行 | — | — |
| M3前端 | `npm run test -- waitlist` | 待执行 | — | — | 待执行 | — | — |
| 全部后端 | `pytest backend/tests -q` | 待执行 | — | — | 待执行 | — | — |
| 全部前端 | `npm run test` | 待执行 | — | — | 待执行 | — | — |
| 前端build | `npm run build` | 待执行 | — | — | 待执行 | — | — |

---

## 8. 验收场景验证矩阵

| 场景 | 对应AC | 测试覆盖 | 手动验证 | 证据来源 | 状态 |
|---|---|---|---|---|---|
| V1 正常推荐并选课 | AC-R1-1, AC-R1-2, AC-R2-4, AC-R3-1 | IT-01, UT-R04, UT-M01 | 演示脚本场景一 | trace_id + 截图 | 待执行 |
| V2 时间冲突拒绝 | AC-R2-3, AC-R3-3 | IT-02, UT-R03 | 演示脚本场景二 | trace_id + 截图 | 待执行 |
| V3 满员进入候补 | AC-R2-5, AC-R3-2 | IT-03, UT-R05 | 演示脚本场景三 | trace_id + 截图 | 待执行 |
| V4 第一名失效补入 | AC-R4-1~R4-5 | IT-04, UT-W01~W06 | 演示脚本场景四 | trace_id + 截图 | 待执行 |
| Fallback | AC-R1-3, AC-R1-5, AC-R5-2 | IT-07, UT-M02~M04 | 演示脚本fallback | trace_id + 截图 | 待执行 |
