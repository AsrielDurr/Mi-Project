# AI课程选课冲突与候补调整系统

这是一个两天开发范围内的课程薄原型。系统用MiMo理解学生的学习目标并推荐目录内课程，用确定性规则处理重复选课、先修要求和时间冲突，再完成选课、候补、教师释放演示名额、候补重算和决策追溯。

技术栈为Vue 3 + TypeScript、FastAPI、JSON种子数据和单进程内存状态。

## 1. 能力边界

- MiMo负责目标理解、课程推荐和理由解释，不决定最终选课资格、容量或候补顺序。
- 规则引擎负责重复、先修和时间冲突检查；相同事实输入应得到相同结果。
- 推荐、选课和候补共用同一个Store和Trace事实来源。
- 模型失败最多重试一次，之后返回 `FALLBACK`；前端必须显示“降级推荐”。
- 状态保存在内存中，进程重启后允许丢失；种子JSON不会被运行过程覆盖。

## 2. 目录结构

```text
project/
├─ .env.example
├─ README.md
├─ contracts/
│  ├─ README.md
│  ├─ CHANGELOG.md
│  ├─ openapi.yaml
│  ├─ domain.schema.json
│  ├─ enums.json
│  ├─ frontend-events.ts
│  └─ examples/
├─ backend/
│  ├─ requirements.txt
│  ├─ app/
│  │  ├─ main.py                     # 集成FastAPI入口
│  │  ├─ contracts/                  # Python领域模型和Ports
│  │  ├─ integration/bootstrap.py    # 单Store依赖装配
│  │  └─ modules/
│  │     ├─ recommendation/
│  │     ├─ enrollment/
│  │     └─ waitlist/
│  ├─ scripts/verify_real_mimo.py
│  └─ tests/
│     ├─ recommendation/
│     ├─ enrollment/
│     ├─ waitlist/
│     └─ integration/
└─ frontend/
   ├─ package.json
   ├─ src/
   │  ├─ main.ts
   │  ├─ integration/App.vue
   │  ├─ shared/courseCatalog.ts
   │  └─ modules/
   │     ├─ recommendation/
   │     ├─ enrollment/
   │     ├─ student-status/
   │     └─ waitlist/
   └─ tests/
      ├─ recommendation/
      ├─ enrollment/
      ├─ waitlist/
      └─ integration/
```

在交付包中，项目配套数据位于 `../ai-course-selection-data/`，即 `delivery/SRC/ai-course-selection-data/`。

## 3. 环境与路径

- Python 3.11+
- Node.js 20+
- npm
- Windows PowerShell命令如下；其他系统可使用等价环境变量写法

先把 `$DeliveryRoot` 改为本机实际路径：

```powershell
$DeliveryRoot = "D:\path\to\delivery"
$ProjectRoot = Join-Path $DeliveryRoot "SRC\project"
$DataRoot = Join-Path $DeliveryRoot "SRC\ai-course-selection-data"
```

安装依赖：

```powershell
Set-Location "$ProjectRoot\backend"
python -m pip install -r requirements.txt

Set-Location "$ProjectRoot\frontend"
npm.cmd install
```

## 4. 配置MiMo

不要把真实API Key写入代码、`.env.example`、README或Git提交。建议只在准备启动后端的当前PowerShell终端中输入：

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
$env:COURSE_DATA_DIR = $DataRoot
$env:FRONTEND_ORIGIN = "http://127.0.0.1:5173"
```

这些变量只对当前PowerShell窗口有效。关闭终端后需要重新配置。

验证真实MiMo：

```powershell
Set-Location "$ProjectRoot\backend"
python scripts\verify_real_mimo.py
```

成功输出应包含 `REAL_MIMO_OK`、模型名和 `trace_id`，不得包含Key正文。没有配置Key时系统仍能运行，但推荐接口会返回明确标记的 `FALLBACK`，不能将其作为真实MiMo验收证据。

## 5. 启动集成系统

终端一：

```powershell
$env:COURSE_DATA_DIR = $DataRoot
$env:FRONTEND_ORIGIN = "http://127.0.0.1:5173"
Set-Location "$ProjectRoot\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

接口文档：`http://127.0.0.1:8000/docs`

终端二：

```powershell
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
Set-Location "$ProjectRoot\frontend"
npm.cmd run dev
```

- 学生端：`http://127.0.0.1:5173/student`
- 教师端：`http://127.0.0.1:5173/teacher`

如果Vite使用了其他端口，应按终端实际地址访问；后端已允许本机 `localhost` 和 `127.0.0.1` 的开发端口。

## 6. 演示流程

学生端：

1. 选择学生并输入学习目标。
2. 获取AI推荐，说明 `MODEL` 与 `FALLBACK` 的区别。
3. 选择课程并提交，查看重复、先修和冲突检查。
4. 查看 `ENROLLED`、`WAITLISTED` 或 `REJECTED` 结果及学生状态。

教师端：

1. 切换8门种子课程，选择“人工智能基础（AI201）”。
2. 查看容量、等待候补和已处理记录。
3. 释放一个演示名额并重新计算候补。
4. 查看第一名 `SKIPPED`、后续候选人 `PROMOTED` 以及Trace事件。
5. 使用reset恢复固定演示场景。

完整口述顺序见 `../../PROTOTYPE/demo-script.md`。

## 7. HTTP接口

契约1.1.0中的10个正式接口：

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/courses` | 加载课程ID和名称 |
| GET | `/api/students` | 加载学生ID和姓名 |
| POST | `/api/recommend` | 获取MiMo或fallback推荐 |
| POST | `/api/enroll` | 规则检查并形成选课状态 |
| GET | `/api/student/status` | 查询学生已选和候补状态 |
| GET | `/api/admin/course-status` | 查询课程容量和候补队列 |
| POST | `/api/admin/release-seat` | 释放一个演示名额 |
| POST | `/api/admin/recompute-waitlist` | 重新检查并处理候补 |
| GET | `/api/trace/{trace_id}` | 查询决策追溯事件 |
| POST | `/api/demo/reset` | 恢复固定演示场景 |

## 8. 测试

后端：

```powershell
Set-Location "$ProjectRoot\backend"
python -m compileall -q app tests scripts
python -m pytest -q
python -m pip check
```

当前基线：`53 passed`。

前端：

```powershell
Set-Location "$ProjectRoot\frontend"
npm.cmd test
npm.cmd run build
npm.cmd ls --depth=0
```

当前基线：5个测试文件、19项测试通过，Vite生产构建通过。

## 9. 已知限制

- 不包含登录、权限、真实身份或生产部署。
- 不使用正式数据库，不支持重启恢复、多实例共享或高并发抢占。
- “释放一个名额”用 `capacity + 1` 模拟，不是完整退课流程。
- 不支持课程改时后的批量重算、例外审批和消息通知。
- 真实MiMo成功证据需要单独保存脱敏截图。

## 10. 关键文件

- 集成后端：`backend/app/main.py`
- 依赖装配：`backend/app/integration/bootstrap.py`
- MiMo适配器：`backend/app/modules/recommendation/client.py`
- 规则引擎：`backend/app/modules/enrollment/rule_engine.py`
- 候补服务：`backend/app/modules/waitlist/service.py`
- 共享状态：`backend/app/modules/waitlist/store.py`
- 集成前端：`frontend/src/integration/App.vue`
- 冻结契约：`contracts/openapi.yaml`
- 端到端测试：`backend/tests/integration/test_end_to_end.py`
