# M1 AI推荐模块 · 开发计划

## T1 数据模型定义

入：共享契约 domain.schema.json + enums.json

出：models.py（StudentProfile, Recommendation, RecommendationResponse, Schedule, Course, CourseSelectedEvent, to_dict）

验：`python -c "from models import *; print('OK')"` 无报错

△ 风险：pydantic DLL 问题 → 使用纯 dataclass 实现

---

## T2 课程数据加载与转换

入：ai-course-selection-data/courses.json（weekday 整数, id, enrolled, prerequisites）

出：load_raw_courses(), load_contract_courses(), load_course_to_contract()

验：`python -c "from recommend import load_contract_courses; c=load_contract_courses(); assert c[0]['course_id']=='CS101'; assert c[0]['schedule']['day']=='MON'"`

△ 风险：字段名不一致 → load_course_to_contract 做映射（id→course_id, enrolled→enrolled_count, prerequisites→prerequisite_ids, weekday→schedule.day）

---

## T3 先修课程检查

入：StudentProfile + Course

出：check_prerequisites(student, course) → (bool, str)

验：
- 无先修 → (True, "无先修要求")
- 已满足 → (True, "已满足先修要求")
- 缺少 → (False, "缺少先修课程: AI201")

△ 风险：学生正在修读的课程也应视为已满足 → 用 completed_course_ids | enrolled_course_ids

---

## T4 时间冲突检测

入：StudentProfile + Course + courses[]

出：check_time_conflict(student, course, courses) → (bool, str)

验：
- 同一天同时段 → (False, "与X上课时间冲突")
- 不同天 → (True, "无时间冲突")

△ 风险：weekday 整数转枚举字符串 → weekday_int_to_str() 映射表

---

## T5 推荐评分引擎

入：StudentProfile + Course + time_preference

出：compute_score(student, course, time_preference) → (int, str)

验：
- AI 目标 + AI 课程 → score >= 80
- 软件开发目标 + Web 课程 → score >= 80
- 名额充足 → +10
- 符合时间偏好 → +10

△ 风险：评分维度遗漏 → 基础分 50 + 目标匹配 +30 + 先修满足 +10 + 时间偏好 +10 + 名额 +5~10

---

## T6 降级推荐流程

入：StudentProfile + courses[] + time_preference

出：fallback_recommend(student, courses, time_preference) → [Recommendation]

验：
- S001（AI目标）→ 推荐包含 AI 相关课程
- S009（软件开发目标）→ 推荐包含 WEB201
- 已满课程不推荐
- 已选/已修课程不推荐
- 先修不满足课程不推荐

△ 风险：推荐列表为空 → 返回 N/A 占位推荐

---

## T7 主推荐流程

入：StudentProfile + time_preference

出：recommend(student, time_preference) → RecommendationResponse

验：
- 返回 trace_id 格式正确
- source 为 "FALLBACK"（当前）
- recommendations 非空
- 每个 recommendation 包含 course_id, score, reason, uncertainty

△ 风险：模型接口预留 → model_recommend() 返回 None，触发降级

---

## T8 HTTP 服务

入：main.py

出：HTTP server（port 8001）

验：
- GET /health → 200 + {"status": "ok"}
- POST /api/recommend → 200 + RecommendationResponse
- POST /api/recommend（无 body）→ 500 错误

△ 风险：CORS 问题 → 添加 Access-Control-Allow-Origin 头

---

## T9 契约一致性测试

入：test_api.py

出：5 个测试函数全部通过

验：`python test_api.py` → 所有 [PASS]

△ 风险：字段名不一致 → 测试覆盖 weekday 转换、课程格式、响应字段、推荐结果

---

# 任务依赖关系

```
T1 (models)
 ├── T2 (data load) ──┐
 │                     ├── T6 (fallback) ── T7 (main) ── T8 (HTTP)
 ├── T3 (prereq) ─────┤
 ├── T4 (time conflict)┤
 └── T5 (score) ───────┘
                             └── T9 (tests)
```

# 开发顺序

1. T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9
2. 每步完成后运行验证命令
3. 全部完成后运行 `python test_api.py` 做回归
