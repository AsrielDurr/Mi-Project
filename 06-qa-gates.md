# M1 AI推荐模块 · QA Gate 验收清单

> 5 道门，全部 PASS 才算交付。任何一道 FAIL 则打回修改。

---

## G1: Spec 完整性检查

**目标**：确认 PRD、设计方案、实现计划、测试策略四份文档齐全且互相对齐。

### 检查项

| # | 检查内容 | 文件 | 通过标准 |
|---|---------|------|---------|
| 1.1 | PRD 齐全 | `02-project-prd.md` | 包含项目概述、用户场景、功能需求(R1-R8)、非目标、完成定义 |
| 1.2 | 设计方案有取舍 | `03-design-options.md` | 至少 3 个方案，含优缺点、风险、选择理由 |
| 1.3 | 实现计划有验证 | `04-dev-workflow.md` | 每步含函数名、输入、输出、验证命令、风险 |
| 1.4 | 测试策略覆盖四类 | `05-test-strategy.md` | 含正确用例、拒答用例、工具失败用例、回归用例 |
| 1.5 | 文档间无冲突 | 全部文档 | PRD 需求项在设计方案中有对应；设计方案的选定方案在实现计划中落地；实现计划的步骤在测试策略中有覆盖 |

### 验证方法

```bash
# 检查文件存在
dir 02-project-prd.md 03-design-options.md 04-dev-workflow.md 05-test-strategy.md

# 检查 PRD 包含所有需求项
grep -c "^## R[0-9]" 02-project-prd.md   # 应为 8

# 检查设计方案包含 3 个方案
grep -c "^## 方案" 03-design-options.md   # 应为 3

# 检查测试策略包含 4 类用例
grep -c "^## [0-9]" 05-test-strategy.md   # 应为 4
```

### 判定

- **PASS**: 全部 5 项通过
- **FAIL**: 任何一项不满足，列出缺失项

---

## G2: 测试覆盖率检查

**目标**：确认测试套件覆盖 PRD 所有需求项，且全部通过。

### 检查项

| # | 检查内容 | 通过标准 |
|---|---------|---------|
| 2.1 | 测试全部通过 | `python test_api.py` 返回所有 [PASS] |
| 2.2 | P0 需求全覆盖 | R1(画像接收)、R2(规则推荐)、R4(结果返回)、R5(先修检查)、R6(时间冲突) 均有对应测试 |
| 2.3 | P1 需求覆盖 | R3(LLM预留)、R8(健康检查) 有测试验证 |
| 2.4 | 错误路径覆盖 | API 无 body、缺字段、数据缺失 均有测试 |
| 2.5 | 需求-测试追溯表 | 每个 PRD 需求项能对应到至少一个测试用例 |

### 验证方法

```bash
# 运行全部测试
python test_api.py

# 检查需求-测试对应
grep -o "TC-[0-9.]*" 05-test-strategy.md | sort -u | wc -l
```

### 需求-测试追溯表

| PRD 需求 | 测试用例 | 状态 |
|----------|---------|------|
| R1 接收学生画像 | TC-1.1, TC-1.2 | 待验证 |
| R2 规则推荐 | TC-1.1 ~ TC-1.5, TC-4.2, TC-4.3 | 待验证 |
| R3 MiMo 模型预留 | TC-3.1 | 待验证 |
| R4 返回推荐结果 | TC-1.6, TC-4.1 | 待验证 |
| R5 先修课程检查 | TC-1.5, TC-2.1 | 待验证 |
| R6 时间冲突检测 | TC-2.2 | 待验证 |
| R7 前端事件 | TC-4.7 | 待验证 |
| R8 健康检查 | TC-4.7 | 待验证 |

### 判定

- **PASS**: 2.1-2.4 全部通过，追溯表完整
- **FAIL**: 测试失败或需求项无对应测试

---

## G3: 数据来源 / 契约一致性检查

**目标**：确认测试数据来源合法、推荐结果符合共享契约 v1.0.0、无幻觉数据。

### 检查项

| # | 检查内容 | 通过标准 |
|---|---------|---------|
| 3.1 | 测试数据可溯源 | 课程数据来自 ai-course-selection-data/courses.json |
| 3.2 | 契约一致性 | 推荐结果字段名、类型、枚举值完全符合 domain.schema.json |
| 3.3 | 无硬编码路径 | 代码中不出现绝对路径硬编码 |
| 3.4 | 无幻觉数据 | 所有测试用例的预期输出基于代码逻辑推导 |
| 3.5 | 异常路径有兜底 | API 无 body、数据缺失 均有错误处理 |

### 验证方法

```bash
# 检查无硬编码绝对路径
grep -rn "C:\\\\" *.py   # 应无结果

# 检查契约字段一致
python -c "from recommend import recommend; from models import StudentProfile; import json; s=StudentProfile('S001','人工智能',[],[],[],[]); r=recommend(s,'上午'); d={'trace_id':r.trace_id,'source':r.source,'model':r.model,'prompt_version':r.prompt_version,'fallback_reason':r.fallback_reason,'recommendations':[{'course_id':x.course_id,'score':x.score,'reason':x.reason,'uncertainty':x.uncertainty} for x in r.recommendations]}; print(json.dumps(d,indent=2))"

# 检查枚举值
grep -n "MODEL\|FALLBACK" recommend.py   # source 枚举
```

### 判定

- **PASS**: 全部 5 项通过
- **FAIL**: 存在硬编码路径、幻觉数据、或契约不一致

---

## G4: README 可复现性检查

**目标**：确认新人拿到代码后能按 README 独立完成环境搭建、运行、测试。

### 检查项

| # | 检查内容 | 通过标准 |
|---|---------|---------|
| 4.1 | README 存在 | 项目目录有 `README.md` |
| 4.2 | 环境要求明确 | 写明 Python 版本要求、依赖 |
| 4.3 | 安装步骤可执行 | `pip install -r requirements.txt` 一条命令完成 |
| 4.4 | 运行命令可复制 | `python main.py` 可直接复制执行 |
| 4.5 | 测试命令可复制 | `python test_api.py` 命令可直接复制执行 |
| 4.6 | API 使用示例有参考 | README 包含 curl 示例 |

### 验证方法

```bash
# 在全新目录克隆后执行
pip install -r requirements.txt   # 应成功
python main.py &                   # 应启动服务
python test_api.py                 # 应全部 PASS
curl http://localhost:8001/health  # 应返回 200
```

### 判定

- **PASS**: 新人 5 分钟内可完成搭建并看到测试通过
- **FAIL**: 缺少任何步骤或命令不可执行

---

## G5: 人工抽查验收

**目标**：人工随机抽查 3 个测试用例，验证工具行为符合直觉。

### 抽查用例（随机选取）

| # | 抽查内容 | 验证方式 |
|---|---------|---------|
| 5.1 | AI 方向学生 → 推荐 AI 课程 | 手动构造 S001 画像，调用 API，肉眼确认推荐结果合理 |
| 5.2 | 软件开发学生 → 推荐 Web/DB 课程 | 手动构造 S009 画像，调用 API，肉眼确认推荐结果合理 |
| 5.3 | 已满课程 → 不在推荐中 | 检查 AI201/ALG201/CV401 不在推荐列表中 |

### 抽查流程

```
1. 启动服务: python main.py
2. 手动发送 curl 请求
3. 肉眼检查：
   - 推荐课程是否合理
   - score 是否在 0-100 范围
   - reason 是否清晰可读
   - 已满课程是否被排除
4. 检查 trace_id 格式是否正确
```

### 人工检查清单

- [ ] 推荐课程符合学生目标方向
- [ ] 已满课程未被推荐
- [ ] 已选课程未被推荐
- [ ] 先修不满足的课程未被推荐
- [ ] 推荐理由清晰可读
- [ ] trace_id 格式为 "trace-rec-xxxxxxxx"

### 判定

- **PASS**: 3 个抽查用例全部符合预期
- **FAIL**: 任何用例输出不符合直觉

---

## 汇总

| Gate | 名称 | 判定 | 备注 |
|------|------|------|------|
| G1 | Spec 完整性 | 待验收 | |
| G2 | 测试覆盖率 | 待验收 | |
| G3 | 数据来源/契约 | 待验收 | |
| G4 | README 可复现 | 待验收 | |
| G5 | 人工抽查 | 待验收 | |

**全部 PASS → 交付。任何 FAIL → 列出问题，打回修改。**
