# Hot Monitor - 热点监控系统

一个为 AI 编程博主打造的热点资讯监控系统，自动追踪 AI 领域最新动态。

## 功能特点

- 🔍 **多源数据聚合** - 支持 Hacker News、GitHub、Twitter、Reddit、知乎、搜索引擎等 8 个数据源
- 🎯 **关键词监控** - 自定义关键词，精准捕获相关热点
- 🤖 **AI 智能分析** - 利用 OpenRouter API 进行内容评分和真假识别
- 🔔 **实时通知** - 浏览器推送 + 邮件通知，第一时间获取重要信息
- 🌐 **赛博朋克风格** - 独特的科幻 UI 界面

## 技术栈

**后端:**
- Python 3.10+
- FastAPI (异步 Web 框架)
- SQLAlchemy 2.1 (异步 ORM)
- SQLite + aiosqlite
- APScheduler (定时任务)
- OpenRouter API (AI 分析)

**前端:**
- Vue 3 (Composition API)
- Vite 5
- TailwindCSS 3
- Pinia (状态管理)

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- npm 或 pnpm

### 后端配置

1. 进入后端目录并创建虚拟环境：
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/MacOS
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 创建 `.env` 文件（参考 `.env.example`）：
```env
OPENROUTER_API_KEY=your_openrouter_api_key
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_password
```

4. 启动后端服务：
```bash
uvicorn app.main:app --reload --port 8000
```

### 前端配置

1. 进入前端目录并安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

3. 访问 http://localhost:3000

### 生产部署

后端：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

前端：
```bash
npm run build
# 将 dist 目录部署到静态服务器
```

## 项目结构

```
hot-monitor/
├── backend/
│   ├── app/
│   │   ├── routers/        # API 路由
│   │   ├── services/       # 业务逻辑层
│   │   │   └── crawlers/   # 数据源爬虫
│   │   ├── config.py       # 配置
│   │   ├── database.py     # 数据库
│   │   ├── models.py       # ORM 模型
│   │   ├── schemas.py      # Pydantic 模式
│   │   ├── scheduler.py    # 定时任务
│   │   └── main.py         # 应用入口
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # API 服务
│   │   ├── stores/         # Pinia 状态
│   │   ├── views/          # 页面组件
│   │   ├── App.vue
│   │   └── main.js
│   └── package.json
└── docs/
    ├── REQUIREMENTS.md
    └── TECHNICAL_DESIGN.md
```

## API 文档

启动后端后访问 http://localhost:8000/docs 查看 Swagger API 文档。

## 配置说明

### 数据源

在设置页面可以启用/禁用各数据源：
- **Hacker News** - 技术新闻
- **GitHub Trending** - 热门仓库
- **Twitter/X** - 社交媒体动态
- **Reddit** - 社区讨论
- **知乎热榜** - 中文热点
- **Bing/Google/DuckDuckGo** - 搜索引擎新闻

### 通知

- **浏览器推送** - 需要允许浏览器通知权限
- **邮件通知** - 需要配置 SMTP 服务

### AI 分析

使用 OpenRouter API 进行：
- 内容相关性评分（1-10分）
- 热点真假识别
- 内容摘要生成

## 许可证

MIT License
