"""FastAPI 主入口

热点监控工具 - Hot Monitor
自动发现和监控热点内容的工具
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from pathlib import Path

from .config import settings
from .database import init_db, close_db
from .scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    
    # 启动定时任务
    start_scheduler()
    
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动成功!")
    
    yield
    
    # 关闭定时任务
    stop_scheduler()
    
    # 关闭时清理资源
    await close_db()
    print("👋 应用已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 热点监控工具 API 文档

Hot Monitor 是一个自动发现和监控热点内容的工具，支持：

### 🔑 核心功能

- **关键词监控**: 自动监控指定关键词的相关内容
- **热点发现**: 自动从多个数据源抓取热点内容
- **AI分析**: 使用AI进行内容分析、真实性验证、重要性评分
- **实时通知**: 支持浏览器推送和邮件通知

### 📊 数据源

支持8个数据源的热点抓取：
- Twitter/X、Bing、Google、DuckDuckGo
- Hacker News、GitHub Trending
- 知乎热榜、Reddit

### 🔔 通知方式

- **Web Push**: 浏览器推送通知
- **Email**: 邮件通知

### 📖 使用说明

1. 在 **关键词管理** 中添加要监控的关键词
2. 系统会自动定时抓取热点（默认5分钟/30分钟）
3. 也可以手动触发刷新抓取
4. 高分热点会自动发送通知

---
**技术支持**: AI编程博主
""",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "健康检查",
            "description": "API服务健康状态检查接口"
        },
        {
            "name": "关键词管理",
            "description": "监控关键词的增删改查操作，关键词用于在各数据源中搜索匹配的内容"
        },
        {
            "name": "热点管理",
            "description": "热点内容的查询、筛选、刷新和管理，热点是从各数据源抓取并经AI分析后的内容"
        },
        {
            "name": "通知管理",
            "description": "通知功能的配置和管理，包括Web Push订阅、邮件通知设置、通知历史记录"
        },
        {
            "name": "系统设置",
            "description": "系统级配置管理，包括仪表盘统计、爬虫间隔设置、VAPID密钥等"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 导入路由
from .routers import keywords, hotspots, notifications, system

app.include_router(keywords.router, prefix="/api/keywords", tags=["关键词管理"])
app.include_router(hotspots.router, prefix="/api/hotspots", tags=["热点管理"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["通知管理"])
app.include_router(system.router, prefix="/api/system", tags=["系统设置"])


@app.get(
    "/",
    tags=["健康检查"],
    summary="根路径健康检查",
    description="返回应用的基本信息和运行状态，用于验证服务是否正常运行。",
    responses={
        200: {
            "description": "服务正常运行",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Hot Monitor",
                        "version": "1.0.0",
                        "status": "running"
                    }
                }
            }
        }
    }
)
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get(
    "/api/health",
    tags=["健康检查"],
    summary="API健康检查",
    description="""
API健康检查端点，返回服务健康状态。

**用途：**
- 负载均衡器健康检查
- 监控系统存活探测
- 前端连接状态检测

**返回值：**
```json
{"status": "healthy"}
```
""",
    responses={
        200: {
            "description": "API服务健康",
            "content": {
                "application/json": {
                    "example": {"status": "healthy"}
                }
            }
        }
    }
)
async def health_check():
    return {"status": "healthy"}
