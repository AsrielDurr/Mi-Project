# AI课程选课冲突与候补调整系统：交付说明

## 1. 交付基线

本目录是课程提交用交付包。业务代码以远程仓库 `WangJX` 分支提交 `14d967b` 为当前版本，并从 Git 跟踪文件导出到 `SRC/project/`；交付包内的README已按最终目录重新整理，因此不再与远程README逐字相同。目录不包含 `.git`、`node_modules`、构建产物和运行缓存。

- 远程仓库：`git@github.com:AsrielDurr/Mi-Project.git`
- 源码分支：`WangJX`
- 源码提交：`14d967b`
- 最近验证：后端 53 项测试通过；前端 5 个测试文件、19 项测试通过；生产构建通过

## 2. 目录结构

```text
delivery/
├─ README.md
├─ SRC/
│  ├─ README.md
│  ├─ project/                         # FastAPI、Vue、共享契约和自动化测试
│  │  ├─ README.md
│  │  ├─ backend/
│  │  ├─ frontend/
│  │  └─ contracts/
│  └─ ai-course-selection-data/        # 8门课程、15名学生及固定演示数据
├─ PROTOTYPE/
│  ├─ prototype-guide.md               # 原型能力与边界
│  ├─ demo-script.md                   # 六分钟演示流程
│  └─ evidence-checklist.md             # 截图和录屏待办
└─ DOCS/
   ├─ diagnosis/problem-diagnosis.md
   ├─ options/solution-options.md
   ├─ design/system-design.md
   ├─ decision/decision-memo.md
   ├─ validation/test-plan-and-results.md
   ├─ validation/qa-review.md
   ├─ ai/ai-log.md
   └─ collaboration/team-collaboration.md
```

课程清单中的 `DOCS/reflection/` 尚未建立，原因和待补内容见第 5 节。

## 3. 快速入口

| 目的 | 文件 |
|---|---|
| 安装、启动和测试 | [`SRC/README.md`](SRC/README.md) |
| 完整项目运行说明 | [`SRC/project/README.md`](SRC/project/README.md) |
| 共享接口契约 | [`SRC/project/contracts/README.md`](SRC/project/contracts/README.md) |
| 原型演示 | [`PROTOTYPE/demo-script.md`](PROTOTYPE/demo-script.md) |
| 原型证据待办 | [`PROTOTYPE/evidence-checklist.md`](PROTOTYPE/evidence-checklist.md) |
| 问题与范围 | [`DOCS/diagnosis/problem-diagnosis.md`](DOCS/diagnosis/problem-diagnosis.md) |
| 方案比较 | [`DOCS/options/solution-options.md`](DOCS/options/solution-options.md) |
| 系统设计 | [`DOCS/design/system-design.md`](DOCS/design/system-design.md) |
| 决策记录 | [`DOCS/decision/decision-memo.md`](DOCS/decision/decision-memo.md) |
| 测试结果 | [`DOCS/validation/test-plan-and-results.md`](DOCS/validation/test-plan-and-results.md) |
| QA放行结论 | [`DOCS/validation/qa-review.md`](DOCS/validation/qa-review.md) |
| AI使用记录 | [`DOCS/ai/ai-log.md`](DOCS/ai/ai-log.md) |
| 团队协作记录 | [`DOCS/collaboration/team-collaboration.md`](DOCS/collaboration/team-collaboration.md) |

## 4. 当前完成状态

- 学生端已覆盖学习目标输入、MiMo推荐或明确降级、资格检查、选课和学生状态查询。
- 教师端已覆盖8门课程切换、课程容量、等待候补、已处理记录、释放演示名额、候补重算和Trace。
- AI只负责理解目标、推荐和解释；重复、先修、冲突、容量和候补顺序由确定性代码处理。
- 后端使用内存状态，重启后允许状态丢失；reset恢复种子场景，不修改JSON源文件。
- 真实MiMo适配器和验证脚本已具备，但成功调用截图仍待归档。

## 5. 对照最终交付清单的未完成项

| 项目 | 当前状态 | 需要补充 |
|---|---|---|
| `SRC/` | 已具备 | 无阻断项 |
| `PROTOTYPE/` | 原型和演示脚本已具备 | P01—P10截图或录屏尚未归档 |
| `DOCS/diagnosis/` | 已具备 | 可直接提交 |
| `DOCS/options/` | 已具备 | 可直接提交 |
| `DOCS/design/` | 已具备 | 可直接提交 |
| `DOCS/decision/` | 已具备 | 可直接提交 |
| `DOCS/validation/` | 已具备，结论为 `GO WITH WARN` | 真实MiMo证据补齐后更新G2 |
| `DOCS/ai/` | 已具备 | 如新增关键AI协作需继续追加真实记录 |
| `DOCS/collaboration/` | 有整理文档 | 缺会议纪要或录音索引、Issue/PR Review等原始证据 |
| `DOCS/reflection/` | 缺失 | 需补团队复盘、三人个人贡献和证据索引 |

共享契约已升级到 `1.1.0`，`/api/courses` 和 `/api/students` 已纳入OpenAPI及自动化契约检查，当前共10个正式HTTP接口。

## 6. 交付原则

- 不提交API Key、真实密钥截图、`.env`、`node_modules`、`dist`、`__pycache__`或`.pytest_cache`。
- 文档只能引用已经存在的证据；未归档的截图、会议和Review记录保持“待补”状态。
- 代码更新后应重新执行后端测试、前端测试和生产构建，并同步更新本页的版本与结果。
