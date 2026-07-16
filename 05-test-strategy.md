# M1 AI推荐模块 · 测试策略

> 基于混合管道架构（规则引擎 + MiMo 降级）
> 测试目标：验证推荐正确性 + 契约一致性 + 降级兜底

---

## 1. 正确用例（Happy Path）

验证系统在正常输入下输出符合 PRD 预期。

### TC-1.1 AI 方向学生 → 推荐 AI 相关课程

| 项目 | 内容 |
|------|------|
| **输入** | student_id=S001, goal="人工智能", completed=["CS101"], enrolled=["DB202"], timePreference="上午" |
| **预期输出** | source="FALLBACK", recommendations 包含 AI 相关课程（如有名额） |
| **验证命令** | `python -c "from recommend import recommend; from models import StudentProfile; s=StudentProfile('S001','人工智能',['Python'],['上午'],['CS101'],['DB202']); r=recommend(s,'上午'); assert r.source=='FALLBACK'"` |
| **断言** | source 为 FALLBACK；recommendations 非空；包含 AI 类课程 |

### TC-1.2 软件开发学生 → 推荐开发相关课程

| 项目 | 内容 |
|------|------|
| **输入** | student_id=S009, goal="软件开发", completed=["CS101","AI201"], enrolled=[], timePreference="下午" |
| **预期输出** | recommendations 包含 WEB201（Web开发）且 score 较高 |
| **验证命令** | `python -c "from recommend import recommend; from models import StudentProfile; s=StudentProfile('S009','软件开发',[],['下午'],['CS101','AI201'],[]); r=recommend(s,'下午'); ids=[x.course_id for x in r.recommendations]; assert 'WEB201' in ids"` |
| **断言** | WEB201 在推荐列表中；score >= 80 |

### TC-1.3 已满课程不推荐

| 项目 | 内容 |
|------|------|
| **输入** | 任何学生画像 |
| **预期输出** | recommendations 中不包含 enrolled=capacity 的课程 |
| **验证命令** | `python -c "from recommend import recommend, load_contract_courses; from models import StudentProfile; courses=load_contract_courses(); full=[c['course_id'] for c in courses if c['enrolled_count']>=c['capacity']]; s=StudentProfile('S001','人工智能',['Python'],['上午'],['CS101'],['DB202']); r=recommend(s,'上午'); ids=[x.course_id for x in r.recommendations]; assert not any(f in ids for f in full)"` |
| **断言** | AI201, ALG201, CV401 不在推荐列表中 |

### TC-1.4 已选课程不推荐

| 项目 | 内容 |
|------|------|
| **输入** | S001, enrolled=["DB202"] |
| **预期输出** | recommendations 中不包含 DB202 |
| **验证命令** | `python -c "from recommend import recommend; from models import StudentProfile; s=StudentProfile('S001','人工智能',['Python'],['上午'],['CS101'],['DB202']); r=recommend(s,'上午'); ids=[x.course_id for x in r.recommendations]; assert 'DB202' not in ids"` |
| **断言** | DB202 不在推荐列表 |

### TC-1.5 先修课程满足 → 可推荐

| 项目 | 内容 |
|------|------|
| **输入** | S009, completed=["CS101","AI201"] |
| **预期输出** | ML301（需要 AI201）在推荐列表中 |
| **验证命令** | `python -c "from recommend import recommend; from models import StudentProfile; s=StudentProfile('S009','软件开发',[],['下午'],['CS101','AI201'],[]); r=recommend(s,'下午'); ids=[x.course_id for x in r.recommendations]; assert 'ML301' in ids"` |
| **断言** | ML301 在推荐列表中 |

### TC-1.6 推荐结果符合契约格式

| 项目 | 内容 |
|------|------|
| **输入** | 任意合法学生画像 |
| **预期输出** | RecommendationResponse 包含 trace_id, source, model, prompt_version, fallback_reason, recommendations |
| **验证命令** | `python test_api.py` → test_recommendation_response_fields |
| **断言** | 所有必需字段存在；score 在 0-100 范围 |

---

## 2. 拒答用例（Edge Cases / Boundary）

验证系统在边界条件下不崩溃、不误判。

### TC-2.1 缺少先修课程 → 不推荐该课程

| 项目 | 内容 |
|------|------|
| **输入** | S001, completed=["CS101"]（未修 AI201） |
| **预期输出** | ML301（需要 AI201）不在推荐列表 |
| **验证命令** | `python -c "from recommend import recommend; from models import StudentProfile; s=StudentProfile('S001','人工智能',['Python'],['上午'],['CS101'],[]); r=recommend(s,'上午'); ids=[x.course_id for x in r.recommendations]; assert 'ML301' not in ids"` |
| **断言** | ML301 不在推荐列表 |

### TC-2.2 时间冲突 → 不推荐冲突课程

| 项目 | 内容 |
|------|------|
| **输入** | S001, enrolled=["DB202"]（周二 10:00-12:00），推荐 DB202 同时段课程 |
| **预期输出** | 与 DB202 同时段的 AI201 不在推荐列表 |
| **验证命令** | `python -c "from recommend import check_time_conflict; from models import StudentProfile; s=StudentProfile('S001','人工智能',[],[],[],['DB202']); course={'course_id':'AI201','name':'人工智能基础','schedule':{'day':'TUE','start':'10:00','end':'12:00'}}; ok,_=check_time_conflict(s,course,[]); assert not ok"` |
| **断言** | 时间冲突检测返回 False |

### TC-2.3 上午偏好 → 优先推荐上午课程

| 项目 | 内容 |
|------|------|
| **输入** | timePreference="上午" |
| **预期输出** | 上午课程的 score 高于下午课程 |
| **验证命令** | `python -c "from recommend import compute_score; from models import StudentProfile; s=StudentProfile('S001','人工智能',['Python'],['上午'],['CS101'],[]); am,_=compute_score(s,{'course_id':'X','name':'测试','schedule':{'day':'MON','start':'08:00','end':'10:00'},'capacity':40,'enrolled_count':30,'prerequisite_ids':[]},'上午'); pm,_=compute_score(s,{'course_id':'Y','name':'测试','schedule':{'day':'MON','start':'14:00','end':'16:00'},'capacity':40,'enrolled_count':30,'prerequisite_ids':[]},'上午'); assert am > pm"` |
| **断言** | 上午课程 score > 下午课程 score |

### TC-2.4 空推荐列表 → 返回占位推荐

| 项目 | 内容 |
|------|------|
| **输入** | 所有课程已满或不满足条件 |
| **预期输出** | recommendations 包含 course_id="N/A", score=0 的占位项 |
| **验证命令** | 手动构造全部不满足条件的场景 |
| **断言** | recommendations 非空；包含 N/A 占位 |

### TC-2.5 无效学生 ID → 正常处理

| 项目 | 内容 |
|------|------|
| **输入** | student_id="INVALID" |
| **预期输出** | 正常返回推荐结果（M1 不校验学生是否存在） |
| **验证命令** | `python -c "from recommend import recommend; from models import StudentProfile; s=StudentProfile('INVALID','人工智能',['Python'],['上午'],[],[]); r=recommend(s,'上午'); assert r.trace_id.startswith('trace-rec')"` |
| **断言** | 不崩溃，返回有效 trace_id |

### TC-2.6 响应时间 < 100ms

| 项目 | 内容 |
|------|------|
| **输入** | 任意合法请求 |
| **预期输出** | 响应时间 < 100ms（纯规则，无网络调用） |
| **验证命令** | `python -c "import time; from recommend import recommend; from models import StudentProfile; s=StudentProfile('S001','人工智能',['Python'],['上午'],['CS101'],[]); t=time.time(); recommend(s,'上午'); print(f'{(time.time()-t)*1000:.1f}ms')"` |
| **断言** | 响应时间 < 100ms |

---

## 3. 工具失败用例（Failure / Error Handling）

验证系统在异常条件下的兜底行为。

### TC-3.1 MiMo API 不可用 → 降级为规则推荐

| 项目 | 内容 |
|------|------|
| **输入** | MiMo API 超时（当前实现 model_recommend 返回 None） |
| **预期输出** | source="FALLBACK"，fallback_reason 非空 |
| **验证命令** | `python -c "from recommend import recommend; from models import StudentProfile; s=StudentProfile('S001','人工智能',['Python'],['上午'],['CS101'],[]); r=recommend(s,'上午'); assert r.source=='FALLBACK'; assert r.fallback_reason is not None"` |
| **断言** | source 为 FALLBACK；fallback_reason 非空 |

### TC-3.2 课程数据文件缺失 → 错误处理

| 项目 | 内容 |
|------|------|
| **输入** | courses.json 不存在 |
| **预期输出** | 抛出 FileNotFoundError |
| **验证命令** | 手动重命名 courses.json 后运行 |
| **断言** | 不崩溃，输出明确错误信息 |

### TC-3.3 课程数据格式错误 → 错误处理

| 项目 | 内容 |
|------|------|
| **输入** | courses.json 内容不是合法 JSON |
| **预期输出** | 抛出 JSON 解析错误 |
| **验证命令** | 手动修改 courses.json 为非法内容后运行 |
| **断言** | 不崩溃，输出明确错误信息 |

### TC-3.4 HTTP 请求无 body → 500 错误

| 项目 | 内容 |
|------|------|
| **输入** | POST /api/recommend 无 body |
| **预期输出** | 500 错误，error.code="INTERNAL_ERROR" |
| **验证命令** | `curl -X POST http://localhost:8001/api/recommend` |
| **断言** | 返回 500；JSON 包含 error.code |

### TC-3.5 HTTP 请求 body 缺少必填字段 → 500 错误

| 项目 | 内容 |
|------|------|
| **输入** | POST /api/recommend body={"student":{"goal":"AI"}}（缺少 student_id） |
| **预期输出** | 500 错误 |
| **验证命令** | `curl -X POST http://localhost:8001/api/recommend -H "Content-Type: application/json" -d '{"student":{"goal":"AI"}}'` |
| **断言** | 返回 500；不崩溃 |

### TC-3.6 并发请求 → 不互相干扰

| 项目 | 内容 |
|------|------|
| **输入** | 同时发送 2 个不同学生的推荐请求 |
| **预期输出** | 两个响应各自独立，trace_id 不同 |
| **验证命令** | 并发 curl 请求 |
| **断言** | 两个 trace_id 不同；各自返回正确推荐 |

---

## 4. 回归用例（Regression）

每次代码变更后必须通过的基准测试。

### TC-4.1 契约一致性 — 所有字段匹配

| 项目 | 内容 |
|------|------|
| **目的** | 确保响应格式完全符合 domain.schema.json |
| **用例** | 运行 test_api.py 全部 5 个测试 |
| **验证命令** | `python test_api.py` |
| **断言** | 所有 [PASS] |

### TC-4.2 AI 目标推荐 — S001

| 项目 | 内容 |
|------|------|
| **目的** | 确保 AI 方向学生获得正确推荐 |
| **用例** | S001, goal="人工智能", completed=["CS101"], enrolled=["DB202"] |
| **验证命令** | `python -c "from recommend import recommend; from models import StudentProfile; s=StudentProfile('S001','人工智能',['Python'],['上午'],['CS101'],['DB202']); r=recommend(s,'上午'); print([(x.course_id,x.score) for x in r.recommendations])"` |
| **断言** | 推荐列表非空；不含已满课程 |

### TC-4.3 软件开发目标推荐 — S009

| 项目 | 内容 |
|------|------|
| **目的** | 确保软件开发方向学生获得正确推荐 |
| **用例** | S009, goal="软件开发", completed=["CS101","AI201"], enrolled=[] |
| **验证命令** | `python -c "from recommend import recommend; from models import StudentProfile; s=StudentProfile('S009','软件开发',[],['下午'],['CS101','AI201'],[]); r=recommend(s,'下午'); ids=[x.course_id for x in r.recommendations]; assert 'WEB201' in ids"` |
| **断言** | WEB201 在推荐列表中 |

### TC-4.4 降级兜底 — source 字段正确

| 项目 | 内容 |
|------|------|
| **目的** | 确保降级时 source 和 fallback_reason 正确 |
| **用例** | 任意学生画像 |
| **验证命令** | `python -c "from recommend import recommend; from models import StudentProfile; s=StudentProfile('S001','人工智能',[],[],[],[]); r=recommend(s,'上午'); assert r.source=='FALLBACK'; assert 'MiMo' in r.fallback_reason"` |
| **断言** | source="FALLBACK"；fallback_reason 包含 "MiMo" |

### TC-4.5 数据转换 — weekday 整数转枚举

| 项目 | 内容 |
|------|------|
| **目的** | 确保课程数据正确转换为契约格式 |
| **用例** | CS101 weekday=1 → schedule.day="MON" |
| **验证命令** | `python -c "from recommend import load_contract_courses; c=load_contract_courses(); assert c[0]['schedule']['day']=='MON'"` |
| **断言** | weekday 1→MON, 2→TUE, ... 7→SUN |

### TC-4.6 幂等性 — 同一请求多次结果一致

| 项目 | 内容 |
|------|------|
| **目的** | 确保推荐结果可复现 |
| **用例** | 同一学生画像请求两次，比对 recommendations |
| **验证命令** | `python -c "from recommend import recommend; from models import StudentProfile; s=StudentProfile('S001','人工智能',[],[],[],[]); r1=recommend(s,'上午'); r2=recommend(s,'上午'); assert [(x.course_id,x.score) for x in r1.recommendations]==[(x.course_id,x.score) for x in r2.recommendations]"` |
| **断言** | 两次推荐列表完全一致（除 trace_id 外） |

### TC-4.7 HTTP 端到端 — 健康检查 + 推荐

| 项目 | 内容 |
|------|------|
| **目的** | 确保 HTTP 服务正常工作 |
| **用例** | GET /health + POST /api/recommend |
| **验证命令** | `curl http://localhost:8001/health && curl -X POST http://localhost:8001/api/recommend -H "Content-Type: application/json" -d '{"student":{"student_id":"S001","goal":"人工智能","skills":[],"available_times":[],"completed_course_ids":[],"enrolled_course_ids":[]}}'` |
| **断言** | 健康检查返回 200；推荐返回有效 JSON |

---

## 测试用例汇总

| 类别 | 用例数 | ID 范围 |
|------|--------|---------|
| 正确用例 | 6 | TC-1.1 ~ TC-1.6 |
| 拒答用例 | 6 | TC-2.1 ~ TC-2.6 |
| 工具失败用例 | 6 | TC-3.1 ~ TC-3.6 |
| 回归用例 | 7 | TC-4.1 ~ TC-4.7 |
| **合计** | **25** | |

---

## 测试数据准备清单

| 数据 | 来源 | 用途 |
|------|------|------|
| courses.json | ai-course-selection-data/ | 8 门课程数据 |
| students.json | ai-course-selection-data/ | 15 名学生数据 |
| S001 画像 | 手动构造 | AI 方向测试 |
| S009 画像 | 手动构造 | 软件开发方向测试 |
| recommendation_examples.json | ai-course-selection-data/ | 目标推荐映射 |
