# 三层架构设计：Skill · MCP · Harness

> 分清三个概念，各司其职，协同完成 M1 推荐模块全流程

---

## 概念区分

| 层 | 问题 | 答案 | 产出物 |
|----|------|------|--------|
| **Skill** | 怎么做？ | 推荐流程模板和决策规则 | `SKILL.md` |
| **MCP** | 接什么？ | 定义可访问资源、接入对象、权限边界 | `mcp-config.json` |
| **Harness** | 自动跑什么？ | 串联画像采集→推荐→选课→追溯 | `harness.js` |

```
┌─────────────────────────────────────────────────┐
│                   Harness                        │
│  画像采集 → 推荐 → 选课 → 候补 → 追溯           │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │  调用 Skill │  │  通过 MCP  │  │  输出结果  │   │
│  └───────────┘  └───────────┘  └───────────┘   │
└─────────────────────────────────────────────────┘
         │                │                │
    ┌────▼────┐    ┌─────▼─────┐    ┌────▼────┐
    │  Skill   │    │    MCP    │    │  报告   │
    │ 怎么做   │    │  接什么   │    │  结果   │
    └─────────┘    └───────────┘    └─────────┘
```

---

## 一、Skill — 怎么做

### 定义

Skill 是**推荐流程的可复制模板**。它回答"学生请求推荐时，按什么步骤处理"，不关心底层 LLM 或规则引擎实现，只关注流程和决策。

### 推荐 Skill

**触发条件**：学生填写画像后请求课程推荐

**输入**：StudentProfile JSON

**流程**：

```
Step 1: 画像校验
  ├── 确认 student_id 非空
  ├── 确认 goal 为有效值（人工智能/软件开发）
  └── 确认 completed_course_ids 格式正确

Step 2: 课程数据加载
  ├── 加载 courses.json
  ├── 转换为契约格式（weekday→day, id→course_id）
  └── 过滤已满课程

Step 3: 推荐计算
  ├── 检查先修课程是否满足
  ├── 检查时间冲突
  ├── 计算推荐分数（目标+30, 先修+10, 时间+10, 名额+5~10）
  └── 按分数排序，取 Top-N

Step 4: 结果封装
  ├── 生成 trace_id
  ├── 标记 source（MODEL/FALLBACK）
  ├── 填充 fallback_reason（如适用）
  └── 返回 RecommendationResponse
```

**决策模板**：

| 条件 | 动作 | source |
|------|------|--------|
| MiMo API 可用 | 调用 LLM 推荐 | MODEL |
| MiMo API 不可用 | 规则引擎推荐 | FALLBACK |
| 所有课程不满足 | 返回 N/A 占位 | FALLBACK |

**异常处理模板**：

| 异常 | 处理 |
|------|------|
| 课程数据缺失 | 返回 500 INTERNAL_ERROR |
| 学生画像格式错误 | 返回 500 + 错误详情 |
| 推荐列表为空 | 返回 N/A 占位推荐 |

### Skill 文件位置

```
.claude/skills/course-recommend/SKILL.md
```

---

## 二、MCP — 接什么

### 定义

MCP（Model Context Protocol）定义**可访问的外部资源和操作边界**。它回答"哪些数据可以读、哪些操作可以执行、谁有权访问"。

### MCP 资源清单

| 资源 ID | 类型 | 路径/URL | 权限 | 说明 |
|---------|------|---------|------|------|
| `course:data` | file | `ai-course-selection-data/courses.json` | read | 课程数据 |
| `student:data` | file | `ai-course-selection-data/students.json` | read | 学生数据 |
| `recommendation:examples` | file | `ai-course-selection-data/recommendation_examples.json` | read | 推荐示例 |
| `contract:schema` | file | `project/contracts/domain.schema.json` | read | 共享契约 |
| `mimo:api` | api | `https://api.mimo.com/v1/chat` | write | MiMo 模型 API |
| `trace:log` | file | `logs/recommend-trace.jsonl` | read/write | 推荐追溯日志 |

### 权限边界矩阵

| 角色 | course:data | student:data | mimo:api | trace:log |
|------|:-:|:-:|:-:|:-:|
| 学生 | - | - | - | - |
| M1 服务 | read | read | write | read/write |
| M2 服务 | read | read | - | read |
| M3 服务 | read | read | - | read/write |
| 管理员 | read | read | read | read/write |

### MCP 接入配置

```json
{
  "mcpServers": {
    "m1-recommend": {
      "command": "python",
      "args": ["main.py"],
      "env": {
        "DATA_DIR": "../ai-course-selection-data",
        "CONTRACT_DIR": "../project/contracts",
        "MIMO_API_KEY": "<REDACTED>"
      },
      "permissions": {
        "read": ["course:data", "student:data", "recommendation:examples", "contract:schema"],
        "write": ["trace:log"],
        "execute": ["python main.py"]
      }
    }
  }
}
```

### MCP 工具定义

| 工具名 | 输入 | 输出 | 权限 |
|--------|------|------|------|
| `recommend` | `{ student: StudentProfile }` | `{ RecommendationResponse }` | execute |
| `get_courses` | `{}` | `Array<Course>` | read |
| `get_student` | `{ student_id: string }` | `StudentProfile` | read |
| `health_check` | `{}` | `{ status, module, version }` | read |

---

## 三、Harness — 自动跑什么

### 定义

Harness 是**自动化编排层**。它把 Skill 的流程和 MCP 的资源串成一条完整的流水线，定时触发、自动执行、自动通知。

### 完整流程

```
┌──────────────────────────────────────────────────────────────┐
│                    Harness 自动流程                           │
│                                                              │
│  ① 画像采集    ② 推荐计算    ③ 结果展示    ④ 选课触发    ⑤ 追溯  │
│  ┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐│
│  │学生填表│──→│调用推荐│──→│前端展示│──→│触发选课│──→│记录日志││
│  │前端验证│    │规则/LLM│    │课程列表│    │M2接口│    │trace││
│  └─────┘      └─────┘      └─────┘      └─────┘      └─────┘│
│      │            │            │            │            │     │
│   MCP:读取     Skill:推荐   MCP:输出     MCP:调用    MCP:写入  │
└──────────────────────────────────────────────────────────────┘
```

### 阶段详情

#### ① 画像采集阶段

| 项目 | 内容 |
|------|------|
| **触发** | 学生打开推荐页面 |
| **动作** | 1. 前端展示画像表单 2. 学生填写 goal, skills, timePreference 3. 前端校验必填字段 4. 提交到 M1 API |
| **MCP 调用** | `student:data` → 读取已完成课程列表 |
| **输出** | StudentProfile JSON |

#### ② 推荐计算阶段

| 项目 | 内容 |
|------|------|
| **触发** | 收到 StudentProfile |
| **动作** | 1. 加载课程数据 2. 执行推荐规则 3. 尝试调用 MiMo（如可用） 4. 降级为规则推荐（如需要） 5. 生成 trace_id |
| **Skill 调用** | `recommend` 工具 |
| **输出** | RecommendationResponse JSON |

#### ③ 结果展示阶段

| 项目 | 内容 |
|------|------|
| **触发** | 收到 RecommendationResponse |
| **动作** | 1. 前端渲染推荐列表 2. 显示 score、reason、uncertainty 3. 高亮 Top-3 推荐 4. 提供"选择此课程"按钮 |
| **MCP 调用** | `course:data` → 获取课程详情 |
| **输出** | 推荐列表 UI |

#### ④ 选课触发阶段

| 项目 | 内容 |
|------|------|
| **触发** | 学生点击"选择此课程" |
| **动作** | 1. 前端发出 `course-selected` 事件 2. 调用 M2 `POST /api/enroll` 3. 获取选课决策 4. 展示结果 |
| **MCP 调用** | M2 API → 选课决策 |
| **输出** | 选课结果（ENROLLED/WAITLISTED/REJECTED） |

#### ⑤ 追溯记录阶段

| 项目 | 内容 |
|------|------|
| **触发** | 选课决策完成 |
| **动作** | 1. 记录推荐请求事件 2. 记录选课决策事件 3. 写入 trace 日志 4. 供 M3 模块查询 |
| **MCP 调用** | `trace:log` → 写入追溯日志 |
| **输出** | trace 事件记录 |

### Harness 配置

```json
{
  "harness": {
    "name": "m1-recommend-pipeline",
    "version": "1.0.0",
    "stages": [
      {
        "id": "collect-profile",
        "name": "画像采集",
        "trigger": "student-request",
        "action": "collect_student_profile",
        "config": "config/profile-form.json"
      },
      {
        "id": "compute-recommend",
        "name": "推荐计算",
        "trigger": "after:collect-profile",
        "action": "run_recommendation",
        "timeout": 5000,
        "fallback": "rule-based"
      },
      {
        "id": "display-results",
        "name": "结果展示",
        "trigger": "after:compute-recommend",
        "action": "render_recommendations",
        "notify": ["student"]
      },
      {
        "id": "handle-selection",
        "name": "选课触发",
        "trigger": "student-click",
        "action": "call_enroll_api",
        "target": "M2-service"
      },
      {
        "id": "record-trace",
        "name": "追溯记录",
        "trigger": "after:handle-selection",
        "action": "write_trace_log",
        "target": "M3-service"
      }
    ]
  }
}
```

---

## 三层协作关系

```
学生/前端
    │
    ▼
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Skill   │────▶│   MCP   │────▶│ Harness │
│          │     │         │     │         │
│ 定义流程 │     │ 暴露资源 │     │ 自动编排 │
│ 模板决策 │     │ 权限管控 │     │ 定时触发 │
│ 异常处理 │     │ 工具接口 │     │ 结果汇总 │
└─────────┘     └─────────┘     └─────────┘
     │               │               │
     ▼               ▼               ▼
  SKILL.md    mcp-config.json    harness.js
```

| 如果只改 Skill | 只影响推荐逻辑，不动基础设施 |
|---------------|---------------------------|
| **如果只改 MCP** | 只影响资源访问，不动推荐流程 |
| **如果只改 Harness** | 只影响触发和编排，不动推荐逻辑 |

---

## 文件清单

```
.claude/skills/course-recommend/
  └── SKILL.md                    — Skill 定义（推荐流程模板）

config/
  ├── mcp-config.json             — MCP 服务配置
  └── profile-form.json           — 画像表单配置

m1-recommend/
  ├── models.py                   — 数据模型
  ├── recommend.py                — 推荐引擎
  ├── main.py                     — HTTP 入口
  └── test_api.py                 — 测试

harness.config.json               — Harness 流程配置
```
