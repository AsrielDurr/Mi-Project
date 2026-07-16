# SRC：源码、数据与运行入口

## 1. 版本来源

`SRC/project/` 的业务代码来自远程仓库 `WangJX` 分支提交 `14d967b`；`SRC/ai-course-selection-data/` 是与该项目配套的模拟数据。为适配交付目录，`project/README.md` 和 `project/contracts/README.md` 已在交付包内重新核对和整理。

```text
git@github.com:AsrielDurr/Mi-Project.git
```

交付副本不包含 Git 元数据、依赖目录、构建产物或Python缓存。

## 2. 目录职责

```text
SRC/
├─ README.md
├─ ai-course-selection-data/
│  ├─ courses.json
│  ├─ students.json
│  ├─ enrollments.json
│  ├─ waitlist.json
│  ├─ rules.json
│  ├─ course_change.json
│  └─ recommendation_examples.json
└─ project/
   ├─ README.md
   ├─ .env.example
   ├─ backend/                         # FastAPI应用和pytest测试
   ├─ frontend/                        # Vue 3应用和Vitest测试
   └─ contracts/                       # OpenAPI、Schema、枚举和示例
```

## 3. 环境要求

- Python 3.11或更高版本
- Node.js 20或更高版本
- npm
- 可选：有效的MiMo API Key；未配置时推荐接口会明确进入 `FALLBACK`

以下命令假设已经把交付包解压到本机，并将 `$DeliveryRoot` 改为实际的 `delivery` 目录：

```powershell
$DeliveryRoot = "D:\path\to\delivery"
$ProjectRoot = Join-Path $DeliveryRoot "SRC\project"
$DataRoot = Join-Path $DeliveryRoot "SRC\ai-course-selection-data"
```

## 4. 安装依赖

后端：

```powershell
Set-Location "$ProjectRoot\backend"
python -m pip install -r requirements.txt
```

前端：

```powershell
Set-Location "$ProjectRoot\frontend"
npm.cmd install
```

## 5. 启动系统

终端一启动后端：

```powershell
$env:COURSE_DATA_DIR = $DataRoot
$env:FRONTEND_ORIGIN = "http://127.0.0.1:5173"
Set-Location "$ProjectRoot\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

接口文档：`http://127.0.0.1:8000/docs`

终端二启动前端：

```powershell
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
Set-Location "$ProjectRoot\frontend"
npm.cmd run dev
```

- 学生端：`http://127.0.0.1:5173/student`
- 教师端：`http://127.0.0.1:5173/teacher`

MiMo Key和供应商地址的完整配置方法见 [`project/README.md`](project/README.md)。

## 6. 验证命令

后端：

```powershell
Set-Location "$ProjectRoot\backend"
python -m pytest -q
```

当前基线：`53 passed`。

前端：

```powershell
Set-Location "$ProjectRoot\frontend"
npm.cmd test
npm.cmd run build
```

当前基线：5个测试文件、19项测试通过，生产构建通过。

真实MiMo验证：

```powershell
Set-Location "$ProjectRoot\backend"
python scripts\verify_real_mimo.py
```

API Key不得写入源码、README、截图或Git提交。
