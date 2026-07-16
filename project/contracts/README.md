# Shared Contract

本目录是M1推荐、M2规则选课、M3候补追溯三个模块的唯一共享契约。GitHub只是同步这些文件的方式；真正需要共同遵守的是这里定义的接口、字段、枚举和示例。

## 契约版本

- 当前版本：`1.0.0`
- 状态：初始冻结候选，等待三名成员确认
- 命名规则：HTTP/JSON字段统一使用`snake_case`；Vue组件事件属性使用TypeScript常见的`camelCase`
- 时间格式：ISO 8601；课程时刻使用24小时制`HH:mm`
- 未经三人确认，不得在任一模块中创建同名但含义不同的字段

## 文件说明

```text
contracts/
|-- README.md
|-- openapi.yaml
|-- domain.schema.json
|-- enums.json
|-- frontend-events.ts
|-- examples/
|   |-- recommend-model.json
|   |-- recommend-fallback.json
|   |-- enroll-enrolled.json
|   |-- enroll-waitlisted.json
|   |-- enroll-rejected.json
|   |-- recompute-result.json
|   `-- trace.json
`-- CHANGELOG.md
```

## 已冻结的模块边界

- M1通过`POST /api/recommend`输出推荐，并在前端发出`course-selected`事件。
- M2通过`POST /api/enroll`输出选课决定，并实现供M3调用的`EligibilityPort`。
- M3实现共享内存状态、候补重算和追溯，并向M1/M2提供`CatalogPort`、`StatePort`和`TracePort`。
- 独立开发可以使用Fake/Stub；集成入口不得引用Fake/Stub。

## “释放一个名额”语义

当前契约将“释放一个名额”定义为：

```text
课程capacity增加1
enrolled_count保持不变
available_seats增加1
随后由教师操作触发候补重算
```

这样不会出现减少`enrolled_count`却没有对应退课学生的数据矛盾。如果团队改为“指定学生退课”，必须升级契约并同步修改接口、示例和测试。

## 契约变更流程

1. 在`CHANGELOG.md`记录待变更字段和原因。
2. 同时修改`domain.schema.json`、`openapi.yaml`、`frontend-events.ts`和相关示例。
3. 三名成员确认后提升契约版本。
4. 三个模块同步同一契约提交后继续开发。
