# 共享契约说明

本目录定义推荐、规则选课和候补追溯模块共同遵守的HTTP接口、领域字段、枚举和前端事件。GitHub负责同步文件，契约内容本身才是模块之间的协作边界。

## 1. 当前版本

- 版本：`1.1.0`
- 状态：已用于三模块集成和自动化契约测试
- HTTP/JSON字段：`snake_case`
- Vue组件事件属性：`camelCase`
- 时间：ISO 8601；课程时刻使用24小时制 `HH:mm`

`CHANGELOG.md` 仍保留“三名成员确认”的原始待办。现有代码、分支集成和测试可以证明契约已经被实现采用，但正式书面确认记录尚未归档。

## 2. 文件结构

```text
contracts/
├─ README.md
├─ CHANGELOG.md
├─ openapi.yaml                       # 10个正式HTTP接口
├─ domain.schema.json                 # 领域对象Schema
├─ enums.json                         # 推荐、规则、选课和候补枚举
├─ frontend-events.ts                 # 前端模块事件
└─ examples/
   ├─ recommend-model.json
   ├─ recommend-fallback.json
   ├─ course-list.json
   ├─ student-list.json
   ├─ enroll-enrolled.json
   ├─ enroll-waitlisted.json
   ├─ enroll-rejected.json
   ├─ recompute-result.json
   └─ trace.json
```

## 3. 冻结边界

- 推荐模块通过 `POST /api/recommend` 输出推荐，并在前端发出 `course-selected` 事件。
- 规则选课模块通过 `POST /api/enroll` 输出选课决定，并实现候补重算使用的 `EligibilityPort`。
- 候补模块实现共享内存状态、候补重算和追溯，并提供 `CatalogPort`、`StatePort` 和 `TracePort`。
- 独立测试可以使用Fake或Stub；正式集成入口不得把Fake或Stub作为真实业务依赖。

10个正式HTTP路径以 `openapi.yaml` 为准。其中 `/api/courses` 和 `/api/students` 是1.1.0新增的只读目录接口，分别为课程切换和学生切换提供ID与显示名称。

## 4. “释放一个名额”的语义

当前原型将该操作定义为：

```text
capacity增加1
enrolled_count保持不变
available_seats增加1
随后由教师操作触发候补重算
```

这样可以避免减少已选人数却没有对应退课学生的事实矛盾。如果改为“指定学生退课”，必须升级契约并同步修改接口、示例和测试。

## 5. 验证位置

- 冻结接口检查：`../backend/tests/integration/test_frozen_contract.py`
- 端到端场景：`../backend/tests/integration/test_end_to_end.py`
- 候补契约一致性：`../backend/tests/waitlist/test_shared_contract_conformance.py`

从 `project/backend/` 执行：

```powershell
python -m pytest -q
```

当前基线为包含10个正式接口契约检查在内的53项后端测试通过。

## 6. 变更流程

1. 在 `CHANGELOG.md` 记录变更原因和影响。
2. 同步修改 `openapi.yaml`、`domain.schema.json`、`enums.json`、`frontend-events.ts` 及相关示例。
3. 三名成员确认版本变化及模块影响。
4. 更新实现和契约测试，全部通过后再合并。

不得只修改某一个模块中的同名字段来绕过共享契约。
