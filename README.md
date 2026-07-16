# M1 · AI课程推荐模块

选课系统的智能推荐服务，为学生提供个性化课程推荐。

## 功能

- 接收学生画像（目标、技能、已选课程、时间偏好）
- 优先调用MiMo大模型生成推荐
- 模型不可用时自动降级为本地规则推荐
- 输出符合共享契约1.0.0的RecommendationResponse

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
python main.py
```

服务启动后监听 `http://localhost:8001`

### 调用推荐接口

```bash
curl -X POST http://localhost:8001/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "student": {
      "student_id": "S001",
      "goal": "人工智能",
      "skills": ["Python"],
      "available_times": ["上午"],
      "completed_course_ids": ["CS101"],
      "enrolled_course_ids": ["DB202"]
    }
  }'
```

### 响应示例

```json
{
  "trace_id": "trace-rec-abc12345",
  "source": "FALLBACK",
  "model": null,
  "prompt_version": "v1",
  "fallback_reason": "MiMo模型暂不可用，使用本地规则推荐",
  "recommendations": [
    {
      "course_id": "WEB201",
      "score": 70,
      "reason": "名额充足",
      "uncertainty": "当前结果未经过MiMo生成，推荐质量可能下降"
    }
  ]
}
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/recommend` | 课程推荐 |
| POST | `/api/events/course-selected` | 前端课程选择事件 |

## 文件结构

```
m1-recommend/
├── main.py              # HTTP服务入口
├── recommend.py         # 推荐引擎
├── models.py            # 数据模型
├── test_api.py          # 测试脚本
├── requirements.txt     # 依赖
├── 01-project-flow-map.md
├── 02-project-prd.md
├── 03-design-options.md
├── 04-dev-workflow.md
├── 05-test-strategy.md
├── 06-qa-gates.md
├── 07-skill-mcp-harness.md
└── 08-token-strategy.md
```

## 契约一致性

本模块严格遵循共享契约1.0.0：

- 数据模型定义：`domain.schema.json`
- API接口定义：`openapi.yaml`
- 枚举值定义：`enums.json`
- 前端事件定义：`frontend-events.ts`

## 测试

```bash
# 运行测试
python test_api.py

# 健康检查
curl http://localhost:8001/health
```

## 设计决策

采用方案C（MiMo+降级混合）：

- MiMo可用时：source="MODEL"，使用AI推荐
- MiMo不可用时：source="FALLBACK"，使用规则推荐
- 确保服务始终可用
