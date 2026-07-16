# Contract Changelog

所有契约变化必须在这里记录，并同步修改OpenAPI、JSON Schema、TypeScript类型和相关示例。

## 1.1.0 - 2026-07-16

### Added

- 将 `GET /api/courses` 纳入正式共享契约，返回课程ID和显示名称列表。
- 将 `GET /api/students` 纳入正式共享契约，返回学生ID和显示名称列表。
- 新增 `CourseListItem`、`CourseListResponse`、`StudentListItem` 和 `StudentListResponse` OpenAPI Schema。
- 新增课程列表和学生列表响应示例。
- 将集成契约测试从8个正式接口扩展为10个。

### Changed

- OpenAPI、领域Schema、枚举文件和前端事件中的契约版本统一提升为 `1.1.0`。
- 集成FastAPI应用的文档版本同步提升为 `1.1.0`。
- 两个原界面辅助接口现在属于正式只读目录接口，不再作为契约外实现。

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
