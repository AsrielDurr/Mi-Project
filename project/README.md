# AI课程选课冲突与候补调整系统

这是一个面向课程演示的AI选课薄原型。系统使用MiMo理解学生学习目标并推荐课程，使用确定性规则判断重复选课、先修课程和时间冲突，再通过统一状态服务完成选课、候补、教师释放名额、候补重算和决策追溯。

项目采用Vue 3 + TypeScript前端、FastAPI后端、JSON种子数据和内存状态。三个业务模块已经接入同一个FastAPI应用和同一个`InMemoryStore`：

- M1：AI课程推荐、MiMo结构化输出、白名单校验和明确fallback。
- M2：重复、先修、时间冲突规则，以及`ENROLLED/WAITLISTED/REJECTED`状态决策。
- M3：候补队列、释放名额、资格重检、跳过/补入和Trace追溯。

## 1. 核心边界

- MiMo只负责理解、推荐和解释，不决定最终选课资格、容量或候补顺序。
- M2规则引擎负责确定性资格检查；相同状态输入应得到相同结果。
- M1、M2、M3共享同一个Store和Trace事实来源。
- 模型失败最多重试一次，之后进入`FALLBACK`；前端必须明显显示“降级推荐”。
- fallback不能替代真实MiMo接入验收。
- 运行状态保存在内存中，进程重启后允许丢失；种子JSON不会被运行过程覆盖。
- 请求、响应、枚举和前端事件以`contracts/`中的冻结契约为准。

## 2. 目录结构

```text
project/
├─ .env.example                         # 环境变量名称和非敏感默认值
├─ README.md
├─ contracts/                           # 团队冻结的共享契约
│  ├─ openapi.yaml                      # 8个正式HTTP接口
│  ├─ domain.schema.json                # 领域对象Schema
│  ├─ enums.json                        # 规则、选课和候补枚举
│  ├─ frontend-events.ts                # 前端模块事件
│  └─ examples/                         # 合法响应示例，仅供契约参考
├─ backend/
│  ├─ requirements.txt
│  ├─ scripts/
│  │  └─ verify_real_mimo.py            # 真实MiMo验收脚本
│  ├─ app/
│  │  ├─ main.py                        # 正式FastAPI入口
│  │  ├─ contracts/                     # Python领域模型和Ports
│  │  ├─ integration/
│  │  │  └─ bootstrap.py                # 单Store和真实依赖注入
│  │  └─ modules/
│  │     ├─ recommendation/              # M1
│  │     ├─ enrollment/                  # M2
│  │     └─ waitlist/                    # M3
│  └─ tests/
│     ├─ recommendation/
│     ├─ enrollment/
│     ├─ waitlist/
│     └─ integration/                    # V1—V4和8接口契约验证
└─ frontend/
   ├─ package.json
   ├─ src/
   │  ├─ main.ts                         # Vue启动入口
   │  ├─ integration/App.vue             # 学生端/教师端组合入口
   │  └─ modules/
   │     ├─ recommendation/              # M1推荐组件
   │     ├─ enrollment/                  # M2选课组件
   │     └─ waitlist/                    # M3教师候补组件
   └─ tests/                             # 三模块组件测试
```

种子数据位于项目目录的上一级：

```text
D:\xiaomi\Day5\ai-course-selection-data
```

后端默认会自动定位该目录，也可以使用`COURSE_DATA_DIR`显式指定。

## 3. 环境要求

- Windows PowerShell
- Conda base或其他Python 3.11+环境
- Node.js 20+
- npm
- 可选：有效的MiMo API Key

当前验证环境：Python 3.14.6、pytest 8.4.2、Node.js 24.18.0、npm 11.16.0。

## 4. 安装依赖

### 4.1 后端

```powershell
conda activate base
cd D:\xiaomi\Day5\project\backend
python -m pip install -r requirements.txt
```

### 4.2 前端

```powershell
cd D:\xiaomi\Day5\project\frontend
npm.cmd install
```

## 5. 配置MiMo

不要把真实API Key写入代码、`.env.example`、README或Git提交。推荐只在准备运行后端的当前PowerShell终端中配置。

### 5.1 安全输入Key

```powershell
$secureKey = Read-Host "粘贴 MiMo API Key" -AsSecureString
$env:MIMO_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password.Trim()
Remove-Variable secureKey
```

输入时终端不会显示字符，这是正常现象。

### 5.2 普通按量付费Key

如果Key以`sk-`开头：

```powershell
$env:MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
$env:MIMO_MODEL = "mimo-v2.5-pro"
$env:MIMO_TIMEOUT_SECONDS = "30"
```

### 5.3 Token Plan Key

如果Key以`tp-`开头：

```powershell
$env:MIMO_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
$env:MIMO_MODEL = "mimo-v2.5-pro"
$env:MIMO_TIMEOUT_SECONDS = "30"
```

### 5.4 数据和前端来源

```powershell
$env:COURSE_DATA_DIR = "D:\xiaomi\Day5\ai-course-selection-data"
$env:FRONTEND_ORIGIN = "http://localhost:5173"
```

这些变量只对当前PowerShell窗口有效。关闭窗口后需重新配置。

## 6. 验证真实MiMo

在已经配置MiMo环境变量的同一个终端执行：

```powershell
cd D:\xiaomi\Day5\project\backend
python scripts\verify_real_mimo.py
```

成功时输出类似：

```text
REAL_MIMO_OK model=mimo-v2.5-pro trace_id=trace-... courses=WEB201,DB202
```

如果没有配置Key，系统仍可运行，但推荐接口会明确返回`source=FALLBACK`。该模式适合离线演示故障降级，不代表真实MiMo验收通过。

## 7. 启动集成系统

需要两个PowerShell终端。

### 7.1 终端一：后端

先在准备启动后端的PowerShell终端配置MiMo。API Key使用安全输入，输入时终端不显示字符属于正常现象：

```powershell
$secureKey = Read-Host "粘贴 MiMo API Key" -AsSecureString
$env:MIMO_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password.Trim()
Remove-Variable secureKey

if ([string]::IsNullOrWhiteSpace($env:MIMO_API_KEY)) {
    throw "未读取到 MiMo API Key，请重新输入"
}

if ($env:MIMO_API_KEY -like "tp-*") {
    $env:MIMO_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
} elseif ($env:MIMO_API_KEY -like "sk-*") {
    $env:MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
} else {
    throw "API Key格式不正确，应以 sk- 或 tp- 开头"
}

$env:MIMO_MODEL = "mimo-v2.5-pro"
$env:MIMO_TIMEOUT_SECONDS = "30"
$env:COURSE_DATA_DIR = "D:\xiaomi\Day5\integration-workspace\ai-course-selection-data"
$env:FRONTEND_ORIGIN = "http://127.0.0.1:5173"
```

可用下面的命令确认变量已经配置。该命令只显示Key是否存在，不会输出Key正文：

```powershell
Write-Host "MIMO_API_KEY configured:" (-not [string]::IsNullOrWhiteSpace($env:MIMO_API_KEY))
Write-Host "MIMO_BASE_URL:" $env:MIMO_BASE_URL
Write-Host "MIMO_MODEL:" $env:MIMO_MODEL
Write-Host "COURSE_DATA_DIR:" $env:COURSE_DATA_DIR
```

这些环境变量只在当前PowerShell终端有效，因此必须继续在同一个终端启动后端：

```powershell
conda activate base
cd D:\xiaomi\Day5\integration-workspace\project\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

### 7.2 终端二：前端

```powershell
cd D:\xiaomi\Day5\project\frontend
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
npm.cmd run dev
```

页面地址：

- 学生端：`http://127.0.0.1:5173/student`
- 教师端：`http://127.0.0.1:5173/teacher`

如果Vite提示使用其他端口，请以终端实际显示的地址为准，并同步修改后端`FRONTEND_ORIGIN`后重新启动后端。

## 8. 演示流程

### 8.1 学生主流程

1. 打开学生端。
2. 输入学习目标，例如“软件开发”或“人工智能”。
3. 点击“获取AI推荐”。
4. 正常MiMo结果显示“AI推荐 · MiMo”；异常时显示“降级推荐”和失败原因。
5. 选择推荐课程。
6. M2展示重复、先修和时间冲突的逐条检查。
7. 页面返回`ENROLLED`、`WAITLISTED`或`REJECTED`。

### 8.2 教师候补流程

1. 打开教师端，查看AI201课程。
2. 初始状态为容量30、已选30、S002和S005处于候补。
3. 点击“释放一个名额”，容量变为31，可用名额变为1。
4. 点击“重算候补”。
5. M2真实规则重新检查候补资格。
6. S002因与DB202时间冲突变为`SKIPPED`。
7. 系统继续检查S005并将其变为`PROMOTED/ENROLLED`。
8. 页面Trace展示释放、重算、逐人检查、跳过和补入事件。
9. 点击reset可以恢复固定演示状态。

## 9. 正式接口

| 方法 | 路径 | 模块 | 用途 |
|---|---|---|---|
| POST | `/api/recommend` | M1 | 获取MiMo或fallback推荐 |
| POST | `/api/enroll` | M2 | 执行规则检查和选课状态决策 |
| GET | `/api/student/status` | M2/M3 | 查询学生已选和候补状态 |
| GET | `/api/admin/course-status` | M3 | 查询课程容量、人数和候补队列 |
| POST | `/api/admin/release-seat` | M3 | 释放一个演示名额 |
| POST | `/api/admin/recompute-waitlist` | M2/M3 | 使用真实规则重新计算候补 |
| GET | `/api/trace/{trace_id}` | 全模块 | 查询按时间排序的决策事件 |
| POST | `/api/demo/reset` | M3 | 恢复固定演示场景 |

完整请求、响应和错误码请查看`contracts/openapi.yaml`或启动后的`/docs`。

## 10. 运行测试

### 10.1 后端全量测试

```powershell
cd D:\xiaomi\Day5\project\backend
python -m compileall -q app tests scripts
python -m pytest -q
python -m pip check
```

当前集成基线：

```text
53 passed
```

### 10.2 前端测试和构建

```powershell
cd D:\xiaomi\Day5\project\frontend
npm.cmd run test
npm.cmd run build
npm.cmd ls --depth=0
```

当前集成基线：

```text
4 test files / 16 tests passed
Vite production build succeeded
```

### 10.3 契约保护

在Day5 Git仓库执行：

```powershell
cd D:\xiaomi\Day5
git diff --exit-code origin/main -- project/contracts
```

如果命令产生差异，不要直接修改共享契约来迁就某个模块；应先判断实现是否偏离冻结契约。

## 11. 四个集成验收场景

| 场景 | 路径 | 预期结果 |
|---|---|---|
| V1 正常推荐并选课 | 真实MiMo→选择课程→M2规则→Store | `source=MODEL`，最终`ENROLLED`，同一Trace包含推荐与选课 |
| V2 推荐课程冲突 | M1选择→M2时间冲突 | `BLOCK/REJECTED`，不写入已选或候补 |
| V3 满员进入候补 | M2规则PASS→M3写入队列 | `WAITLISTED/WAITING`，教师端立即可见 |
| V4 第一名失效 | 释放名额→M2真实规则重检→M3更新 | S002=`SKIPPED`，S005=`PROMOTED/ENROLLED` |

自动化集成测试位于`backend/tests/integration/`。其中V1使用可控Stub验证模块接线；最终真实模型验收由`scripts/verify_real_mimo.py`完成。

## 12. 已知限制

- 这是课程薄原型，不包含登录、权限和真实用户身份。
- 状态位于单进程内存，不支持重启恢复、集群或多实例共享。
- 不支持多人并发抢最后名额；没有数据库事务或锁。
- “释放名额”按冻结契约使用课程容量加1模拟，不是完整退课流程。
- 不支持课程改时后批量重新处理所有学生。
- 不支持例外审批和`REVIEW`状态。
- MiMo调用需要有效Key、余额和网络；失败时系统会明确进入fallback。
- pytest当前可能显示一条FastAPI TestClient相关的Starlette/httpx弃用警告，不影响现有测试结果。

## 13. 安全注意事项

- 不要把API Key提交到Git、README、前端代码、截图或聊天记录。
- Key必须只存在服务端环境变量中。
- 不要在浏览器前端直接调用MiMo。
- 如果Key泄露，请立即在MiMo控制台撤销并创建新Key。
- 使用结束后可以清除当前终端中的Key：

```powershell
Remove-Item Env:MIMO_API_KEY -ErrorAction SilentlyContinue
```

## 14. 关键文件入口

- 后端正式入口：`backend/app/main.py`
- 依赖注入：`backend/app/integration/bootstrap.py`
- M1：`backend/app/modules/recommendation/`
- M2：`backend/app/modules/enrollment/`
- M3：`backend/app/modules/waitlist/`
- 前端组合页面：`frontend/src/integration/App.vue`
- 共享契约：`contracts/openapi.yaml`
- 真实MiMo验收：`backend/scripts/verify_real_mimo.py`

