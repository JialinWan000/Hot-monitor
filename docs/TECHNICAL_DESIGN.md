# 热点监控工具 - 技术方案

## 技术栈 (基于 Context7 最新文档)

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 后端框架 | FastAPI | Latest | 高性能异步Web框架 |
| ORM | SQLAlchemy | 2.1+ | 使用最新的 DeclarativeBase + AsyncSession |
| 数据库 | SQLite | 3.x | 轻量级本地存储 (aiosqlite异步驱动) |
| AI服务 | OpenRouter API | v1 | 统一AI模型接口 (兼容OpenAI SDK) |
| 定时任务 | APScheduler | 3.x | 后台任务调度 |
| HTTP客户端 | httpx | Latest | 异步HTTP请求 |
| 前端框架 | Vue 3 | 3.x | Composition API + script setup |
| CSS框架 | TailwindCSS | 3.x | 原子化CSS |
| 构建工具 | Vite | 5.x | 快速开发构建 |

## SQLAlchemy 异步配置 (Context7 最新文档)

```python
from __future__ import annotations
from typing import List, Optional
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(AsyncAttrs, DeclarativeBase):
    pass

# 创建异步引擎
engine = create_async_engine("sqlite+aiosqlite:///./data/hot_monitor.db", echo=True)

# 异步 Session 工厂
async_session = async_sessionmaker(engine, expire_on_commit=False)

# FastAPI 依赖注入
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

## FastAPI CORS 配置

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境，生产环境需限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Vue 3 Composition API (Context7 最新文档)

```javascript
import { ref, reactive, onMounted } from 'vue'

// 使用 ref 声明响应式状态
const count = ref(0)
const keywords = ref([])

// 使用 reactive 声明复杂对象
const state = reactive({
  hotspots: [],
  loading: false,
  error: null
})

// 生命周期钩子
onMounted(async () => {
  await fetchHotspots()
})
```

## 项目结构

```
hot-monitor/
├── docs/                      # 文档
│   ├── REQUIREMENTS.md        # 需求文档
│   └── TECHNICAL_DESIGN.md    # 技术方案
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   ├── models.py          # SQLAlchemy 模型
│   │   ├── schemas.py         # Pydantic 模型
│   │   ├── routers/           # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── keywords.py    # 关键词管理
│   │   │   ├── hotspots.py    # 热点管理
│   │   │   └── notifications.py # 通知管理
│   │   ├── services/          # 业务服务
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py  # OpenRouter AI服务
│   │   │   ├── notifier.py    # 通知服务
│   │   │   └── crawlers/      # 爬虫模块
│   │   │       ├── __init__.py
│   │   │       ├── base.py    # 爬虫基类
│   │   │       ├── twitter.py
│   │   │       ├── bing.py
│   │   │       ├── google.py
│   │   │       ├── duckduckgo.py
│   │   │       ├── hackernews.py
│   │   │       ├── github.py
│   │   │       ├── zhihu.py
│   │   │       └── reddit.py
│   │   └── scheduler.py       # 定时任务
│   ├── data/                  # SQLite 数据文件
│   ├── requirements.txt
│   └── run.py                 # 启动脚本
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── components/        # Vue 组件
│   │   ├── views/             # 页面视图
│   │   ├── stores/            # Pinia 状态管理
│   │   └── api/               # API 调用
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
└── skills/                    # Agent Skills
    └── hot-monitor/
        └── SKILL.md
```

## 数据库设计

### 关键词表 (keywords)
```sql
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY,
    keyword TEXT NOT NULL,
    category TEXT,              -- 分类：AI、编程、科技等
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 热点表 (hotspots)
```sql
CREATE TABLE hotspots (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    source TEXT NOT NULL,       -- 来源平台
    source_url TEXT,
    score REAL,                 -- AI评分
    is_verified BOOLEAN,        -- AI验证真实性
    matched_keywords TEXT,      -- 匹配的关键词JSON
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notified BOOLEAN DEFAULT 0
);
```

### 通知记录表 (notifications)
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY,
    hotspot_id INTEGER,
    type TEXT,                  -- push/email
    status TEXT,                -- pending/sent/failed
    sent_at DATETIME,
    FOREIGN KEY (hotspot_id) REFERENCES hotspots(id)
);
```

### 设置表 (settings)
```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## API 设计

### 关键词管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/keywords | 获取关键词列表 |
| POST | /api/keywords | 添加关键词 |
| PUT | /api/keywords/{id} | 更新关键词 |
| DELETE | /api/keywords/{id} | 删除关键词 |

### 热点管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/hotspots | 获取热点列表 |
| GET | /api/hotspots/{id} | 获取热点详情 |
| POST | /api/hotspots/refresh | 手动刷新热点 |
| POST | /api/hotspots/search | 搜索指定领域热点 |

### 通知管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/notifications | 获取通知记录 |
| POST | /api/notifications/settings | 更新通知设置 |
| GET | /api/notifications/settings | 获取通知设置 |

### 系统设置
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/settings | 获取系统设置 |
| PUT | /api/settings | 更新系统设置 |

## OpenRouter API 集成 (Context7 最新文档)

### 方式一：使用 OpenAI SDK（推荐）
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="<OPENROUTER_API_KEY>",
)

response = client.chat.completions.create(
    extra_headers={
        "HTTP-Referer": "https://hot-monitor.local",  # 应用URL
        "X-Title": "Hot Monitor",                      # 应用名称
    },
    model="anthropic/claude-3.5-sonnet",  # 或 openai/gpt-4o 等
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
)

reply = response.choices[0].message
```

### 方式二：直接调用 API
```python
import requests
import json

response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": "Bearer <OPENROUTER_API_KEY>",
        "HTTP-Referer": "https://hot-monitor.local",
        "X-Title": "Hot Monitor",
        "Content-Type": "application/json",
    },
    data=json.dumps({
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [
            {"role": "user", "content": "..."}
        ]
    })
)
```

### AI 功能
1. **真实性验证**: 分析内容是否为假冒/虚假信息
2. **热点评分**: 评估热点的重要性和相关性
3. **内容摘要**: 生成热点内容摘要
4. **分类标签**: 自动为热点打标签

## 爬虫设计

### 基类接口
```python
class BaseCrawler:
    async def search(self, keyword: str) -> list[dict]
    async def get_trending(self, category: str) -> list[dict]
```

### 各平台实现
| 平台 | 数据获取方式 | 频率限制 |
|------|-------------|----------|
| Twitter/X | API/网页解析 | 15分钟 |
| Bing | Search API | 无明显限制 |
| Google | Search API | 需API Key |
| DuckDuckGo | Instant Answer API | 无限制 |
| Hacker News | 官方API | 无限制 |
| GitHub | Trending页面 | 无限制 |
| 知乎 | 热榜页面 | 5分钟 |
| Reddit | 官方API | 需认证 |

## 通知服务

### 浏览器推送 (Web Push)
- 使用 VAPID 协议
- 需要生成公私钥对
- 前端请求通知权限

### 邮件通知
- 使用 SMTP 协议
- 支持配置邮件服务器
- 支持HTML模板

## 定时任务

| 任务 | 频率 | 说明 |
|------|------|------|
| 关键词监控 | 5分钟 | 检查关键词相关内容 |
| 热点发现 | 30分钟 | 发现指定领域热点 |
| 通知发送 | 1分钟 | 处理待发送通知 |

## 前端设计

### 页面结构
1. **仪表盘**: 热点概览、最新通知
2. **关键词管理**: 添加/编辑/删除关键词
3. **热点列表**: 浏览所有热点
4. **设置页面**: 通知设置、AI设置

### UI风格
- **设计风格**: 赛博朋克 + 极简主义混搭
- **配色方案**: 深色主题 + 霓虹色强调
- **动效**: 流畅的过渡动画
- **响应式**: 移动端优先

---

**文档版本**: v1.0  
**创建日期**: 2026-03-08
