# M3 候补重算与追溯模块交付说明

## 1. 交付状态

M3 已按 `04_dev-workflow.md` 完成独立开发与验证，包含：

- 只读加载 `ai-course-selection-data` 种子数据的内存 Store。
- `CatalogPort + StatePort + TracePort` 的真实实现。
- 释放名额、候补顺序重算、失效跳过、合格补入和状态重置。
- 教师候补面板、重算结果和追溯时间线。
- FastAPI 独立 Demo、Vue 独立入口及前后端测试。

状态保存在进程内，重启后允许丢失；源 JSON 不会被修改。

## 2. 目录

```text
project/
├─ backend/
│  ├─ app/contracts/                 # 冻结模型和 Ports
│  ├─ app/modules/waitlist/          # M3 后端实现及独立 Demo
│  └─ tests/waitlist/                # Store、Service、API 测试
├─ frontend/
│  ├─ src/modules/waitlist/          # M3 Vue 组件和 API 适配器
│  └─ tests/waitlist/                # 组件测试
└─ contracts/                        # 团队共享契约
```

默认数据目录为 `Day5/ai-course-selection-data`。也可以通过环境变量覆盖：

```powershell
$env:COURSE_DATA_DIR="D:\path\to\ai-course-selection-data"
```

## 3. 独立运行

后端：

```powershell
cd D:\xiaomi\Day5\project\backend
python -m pip install -r requirements.txt
python -m uvicorn app.modules.waitlist.demo:app --host 127.0.0.1 --port 8103
```

前端：

```powershell
cd D:\xiaomi\Day5\project\frontend
npm.cmd install
$env:VITE_API_BASE_URL="http://127.0.0.1:8103"
npm.cmd run dev
```

访问 `http://127.0.0.1:5173`；接口文档位于 `http://127.0.0.1:8103/docs`。

建议演示顺序：选择 `AI201`，点击“释放一个名额”，再点击“重算候补”。结果应为 `S002` 因冲突被跳过，`S005` 成功补入。

## 4. 对外接口

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/admin/course-status?course_id=AI201` | 读取课程、容量和候补队列 |
| POST | `/api/admin/release-seat` | 释放一个名额 |
| POST | `/api/admin/recompute-waitlist` | 按原顺序重检并补入 |
| GET | `/api/trace/{trace_id}` | 读取完整追溯事件 |
| POST | `/api/demo/reset` | 恢复固定演示状态 |

请求、响应和枚举以 `project/contracts/openapi.yaml` 为准。

## 5. 三模块合并接线

后端组合入口只需创建一个 Store，并把 M2 的真实规则引擎注入 M3：

```python
store = InMemoryStore.from_data_dir(data_dir)
rule_engine = RuleEngine(state=store)  # M2 实现 EligibilityPort
waitlist_service = WaitlistService(
    state=store,
    eligibility=rule_engine,
    trace=store,
)
app.include_router(create_waitlist_router(store, waitlist_service))
```

独立 Demo 中的 `FakeEligibilityPort` 仅用于在 M2 尚未合并时稳定演示；正式组合入口必须替换成 M2 的 `RuleEngine`。M1、M2 必须复用同一个 `InMemoryStore`，不能各自新建状态实例。

前端导出位于 `src/modules/waitlist/index.ts`：

- `WaitlistModule`
- `TraceTimeline`
- `createWaitlistApi`
- M3 TypeScript 类型

## 6. Red—Green 证据

Red：

- 后端测试在实现前收集失败：`ModuleNotFoundError: No module named 'app'`。
- 前端两套测试在实现前因 `WaitlistModule.vue`、`TraceTimeline.vue` 不存在而失败。

Green（2026-07-16）：

- `python -m pytest -q`：`14 passed`，其中2项直接使用冻结的 `openapi.yaml` 校验 M3 成功与错误响应。
- `npm.cmd run test:waitlist`：`2 files / 4 tests passed`。
- `npm.cmd run build`：类型检查和 Vite 生产构建通过。
- 8103 HTTP 冒烟：`AI201` 容量 `30 → 31`，`S002:SKIPPED`，`S005:PROMOTED`。

当前仅有一条第三方测试工具弃用警告：FastAPI `TestClient` 所用 Starlette/httpx 兼容层提示未来改用 `httpx2`，不影响本模块运行与测试结果。

## 7. 数据说明与限制

- `courses.json` 的 `enrolled` 是课程总人数；`enrollments.json` 只包含演示所需的样例学生记录，因此 `enrolled_student_ids` 不是完整花名册。
- M3 会保证本次运行中新补入学生同时写入课程人数、学生已选课程和候补状态。
- 当前没有数据库、并发锁和持久化恢复，这与一天薄原型及“接受状态丢失”的选型一致。
