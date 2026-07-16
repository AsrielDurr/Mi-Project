# Contract Changelog

所有契约变化必须在这里记录，并同步修改OpenAPI、JSON Schema、TypeScript类型和相关示例。

## 1.0.0 - 2026-07-16

### Added

- 冻结M1、M2、M3共享领域对象和状态枚举。
- 定义8个HTTP接口及统一错误响应。
- 定义`CourseSelectedEvent`与`EnrollmentDecidedEvent`。
- 添加MODEL、FALLBACK、三种选课结果、候补重算和追溯样例。
- 将“释放一个名额”定义为课程`capacity + 1`。

### Pending confirmation

- 三名成员确认契约版本`1.0.0`。
- 确认具体MiMo模型名称和接口参数。
