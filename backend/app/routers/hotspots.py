"""热点管理路由

提供热点内容的查询、筛选、刷新和管理功能。
热点是系统从各个数据源抓取并经过AI分析后的内容。
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Path
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Hotspot, Keyword
from ..schemas import (
    HotspotResponse,
    HotspotListResponse,
    HotspotSearchRequest,
    MessageResponse,
)

router = APIRouter()


@router.get(
    "",
    response_model=HotspotListResponse,
    summary="获取热点列表",
    description="""
获取热点内容列表，支持多种筛选条件和分页。

**筛选条件：**
- `source`: 按数据源筛选（twitter/bing/google/duckduckgo/hackernews/github/zhihu/reddit）
- `unread_only`: 仅显示未读热点
- `verified_only`: 仅显示已验证且非虚假的热点
- `keyword_id`: 按关联的关键词筛选

**返回数据：**
- `items`: 热点列表，每条包含标题、内容、来源、AI分析结果等
- `total`: 符合条件的总数
- `page`: 当前页码
- `page_size`: 每页数量

**AI分析字段说明：**
- `score`: AI评分（0-100），分数越高表示热点越重要
- `is_verified`: 是否经过AI验证
- `is_fake`: 是否可能是虚假信息
- `summary`: AI生成的内容摘要
- `tags`: AI生成的标签列表

**排序说明：**
默认按发现时间倒序排列（最新发现的在前）
""",
    responses={
        200: {"description": "成功返回热点列表"}
    }
)
async def get_hotspots(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，范围1-100，默认20"),
    source: Optional[str] = Query(None, description="数据源ID，可选值：twitter/bing/google/duckduckgo/hackernews/github/zhihu/reddit"),
    unread_only: bool = Query(False, description="是否仅返回未读热点"),
    verified_only: bool = Query(False, description="是否仅返回已验证且非虚假的热点"),
    keyword_id: Optional[int] = Query(None, description="关联的关键词ID，用于筛选特定关键词匹配的热点"),
    db: AsyncSession = Depends(get_db)
):
    """获取热点列表"""
    query = select(Hotspot).options(selectinload(Hotspot.keywords))
    
    # 过滤条件
    filters = []
    if source:
        filters.append(Hotspot.source == source)
    if unread_only:
        filters.append(Hotspot.read == False)
    if verified_only:
        filters.append(Hotspot.is_verified == True)
        filters.append(Hotspot.is_fake == False)
    
    if filters:
        query = query.where(and_(*filters))
    
    # 如果指定了关键词ID，需要关联查询
    if keyword_id:
        query = query.join(Hotspot.keywords).where(Keyword.id == keyword_id)
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    offset = (page - 1) * page_size
    query = query.order_by(Hotspot.discovered_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    hotspots = result.scalars().unique().all()
    
    return HotspotListResponse(
        items=hotspots,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/sources",
    summary="获取支持的数据源列表",
    description="""
获取系统支持的所有数据源信息。

**数据源列表：**
| ID | 名称 | 图标 | 说明 |
|---|---|---|---|
| twitter | Twitter/X | 🐦 | 社交媒体，科技圈一手消息 |
| bing | Bing | 🔍 | 微软搜索引擎，新闻聚合 |
| google | Google | 🔎 | 全球最大搜索引擎 |
| duckduckgo | DuckDuckGo | 🦆 | 隐私友好的搜索引擎 |
| hackernews | Hacker News | 📰 | 技术社区，深度讨论 |
| github | GitHub Trending | 💻 | 开源项目趋势 |
| zhihu | 知乎热榜 | 🎯 | 中文问答社区 |
| reddit | Reddit | 🤖 | 国际社区讨论 |

**返回格式：**
```json
{
    "sources": [
        {"id": "twitter", "name": "Twitter/X", "icon": "🐦"},
        ...
    ]
}
```
""",
    responses={
        200: {"description": "成功返回数据源列表"}
    }
)
async def get_sources():
    """获取支持的数据源列表"""
    return {
        "sources": [
            {"id": "twitter", "name": "Twitter/X", "icon": "🐦"},
            {"id": "bing", "name": "Bing", "icon": "🔍"},
            {"id": "google", "name": "Google", "icon": "🔎"},
            {"id": "duckduckgo", "name": "DuckDuckGo", "icon": "🦆"},
            {"id": "hackernews", "name": "Hacker News", "icon": "📰"},
            {"id": "github", "name": "GitHub Trending", "icon": "💻"},
            {"id": "zhihu", "name": "知乎热榜", "icon": "🎯"},
            {"id": "reddit", "name": "Reddit", "icon": "🤖"},
        ]
    }


@router.get(
    "/{hotspot_id}",
    response_model=HotspotResponse,
    summary="获取热点详情",
    description="""
根据热点ID获取单个热点的完整详细信息。

**返回信息包括：**
- 基本信息：标题、内容、来源、原文链接
- AI分析结果：评分、验证状态、摘要、详细分析、标签
- 关联信息：匹配的关键词列表
- 时间信息：发布时间、发现时间
- 状态信息：是否已读、是否已通知

**AI分析字段详解：**
- `score`: 0-100评分，>=70为高分热点
- `is_verified`: AI是否完成验证
- `is_fake`: 是否可能是假新闻/虚假信息
- `summary`: 50字以内的内容摘要
- `ai_analysis`: 100字以内的详细分析
- `tags`: 自动生成的标签，如 ["AI", "GPT", "发布"] 
""",
    responses={
        200: {"description": "成功返回热点详情"},
        404: {"description": "热点不存在"}
    }
)
async def get_hotspot(
    hotspot_id: int = Path(..., description="热点ID", ge=1, example=1),
    db: AsyncSession = Depends(get_db)
):
    """获取热点详情"""
    result = await db.execute(
        select(Hotspot)
        .options(selectinload(Hotspot.keywords))
        .where(Hotspot.id == hotspot_id)
    )
    hotspot = result.scalar_one_or_none()
    
    if not hotspot:
        raise HTTPException(status_code=404, detail="热点不存在")
    
    return hotspot


@router.post(
    "/{hotspot_id}/read",
    response_model=MessageResponse,
    summary="标记热点为已读",
    description="""
将指定的热点标记为已读状态。

**使用场景：**
- 用户点击查看热点详情后自动调用
- 前端列表中点击"标记已读"按钮

**说明：**
- 已读状态仅用于前端显示区分
- 不会影响热点的其他属性
- 可重复调用，幂等操作
""",
    responses={
        200: {"description": "标记成功"},
        404: {"description": "热点不存在"}
    }
)
async def mark_as_read(
    hotspot_id: int = Path(..., description="要标记为已读的热点ID", ge=1),
    db: AsyncSession = Depends(get_db)
):
    """标记热点为已读"""
    result = await db.execute(select(Hotspot).where(Hotspot.id == hotspot_id))
    hotspot = result.scalar_one_or_none()
    
    if not hotspot:
        raise HTTPException(status_code=404, detail="热点不存在")
    
    hotspot.read = True
    await db.commit()
    
    return MessageResponse(message="已标记为已读")


@router.post(
    "/read-all",
    response_model=MessageResponse,
    summary="标记所有热点为已读",
    description="""
批量将所有未读热点标记为已读状态。

**使用场景：**
- 用户点击"全部标记已读"按钮
- 清理未读消息

**说明：**
- 此操作会影响所有 read=False 的热点
- 操作不可撤销
- 是一个批量更新操作，可能需要较长时间
""",
    responses={
        200: {"description": "批量标记成功"}
    }
)
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db)
):
    """标记所有热点为已读"""
    from sqlalchemy import update
    
    stmt = update(Hotspot).where(Hotspot.read == False).values(read=True)
    await db.execute(stmt)
    await db.commit()
    
    return MessageResponse(message="已全部标记为已读")


@router.post(
    "/refresh",
    response_model=MessageResponse,
    summary="手动刷新热点",
    description="""
手动触发热点抓取任务，从所有数据源抓取最新热点。

**功能说明：**
- 触发后会在后台异步执行爬虫任务
- 接口立即返回，不等待爬取完成
- 爬取的内容会经过AI分析后存入数据库

**执行流程：**
1. 获取所有活跃的监控关键词
2. 对每个关键词在各数据源中搜索
3. AI分析每条结果（真实性、相关性、摘要等）
4. 保存到数据库并关联关键词
5. 高分热点会自动触发通知

**注意事项：**
- 频繁调用可能导致IP被数据源限制
- 建议间隔至少5分钟调用一次
- 可通过定时任务自动执行，无需手动刷新

**预计耗时：**
根据关键词数量和网络情况，通常需要30秒-2分钟
""",
    responses={
        200: {"description": "刷新任务已启动"}
    }
)
async def refresh_hotspots(
    background_tasks: BackgroundTasks,
):
    """手动刷新热点（后台任务）"""
    from ..services.crawler_manager import CrawlerManager
    
    # 在后台执行爬取任务
    background_tasks.add_task(CrawlerManager.refresh_all_keywords)
    
    return MessageResponse(message="已开始刷新，请稍后查看结果")


@router.post(
    "/search",
    response_model=MessageResponse,
    summary="搜索指定领域的热点",
    description="""
搜索特定领域/主题的热点内容，不依赖已配置的关键词。

**请求参数：**
- `domain` (必填): 要搜索的领域/主题，如 "AI大模型"、"区块链"、"Web3"
- `sources` (可选): 指定数据源列表，默认搜索所有数据源

**请求示例：**
```json
{
    "domain": "AI大模型",
    "sources": ["hackernews", "github", "reddit"]
}
```

**执行流程：**
1. 在指定数据源中搜索关键词
2. 收集搜索结果
3. AI分析每条结果
4. 保存到数据库

**使用场景：**
- 临时搜索某个话题的热点
- 快速浏览特定领域的最新动态
- 不想添加永久关键词时使用

**注意事项：**
- 任务在后台异步执行
- 搜索结果不会关联到任何关键词
- 结果可以通过热点列表接口查看
""",
    responses={
        200: {"description": "搜索任务已启动"}
    }
)
async def search_hotspots(
    request: HotspotSearchRequest,
    background_tasks: BackgroundTasks,
):
    """搜索指定领域的热点"""
    from ..services.crawler_manager import CrawlerManager
    
    # 在后台执行搜索任务
    background_tasks.add_task(
        CrawlerManager.search_domain,
        domain=request.domain,
        sources=request.sources
    )
    
    return MessageResponse(message=f"已开始搜索'{request.domain}'领域热点")


@router.delete(
    "/{hotspot_id}",
    response_model=MessageResponse,
    summary="删除热点",
    description="""
删除指定的热点记录。

**注意事项：**
- 删除操作不可恢复
- 关联的通知记录也会被删除
- 关键词关联关系会被解除

**使用场景：**
- 删除低质量或不相关的热点
- 清理过期的热点内容
- 删除误判的虚假信息
""",
    responses={
        200: {"description": "删除成功"},
        404: {"description": "热点不存在"}
    }
)
async def delete_hotspot(
    hotspot_id: int = Path(..., description="要删除的热点ID", ge=1),
    db: AsyncSession = Depends(get_db)
):
    """删除热点"""
    result = await db.execute(select(Hotspot).where(Hotspot.id == hotspot_id))
    hotspot = result.scalar_one_or_none()
    
    if not hotspot:
        raise HTTPException(status_code=404, detail="热点不存在")
    
    await db.delete(hotspot)
    await db.commit()
    
    return MessageResponse(message="热点已删除")
