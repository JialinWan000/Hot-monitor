"""关键词管理路由

提供关键词的增删改查功能，关键词用于监控特定主题的热点内容。
系统会定时检查各数据源中与关键词匹配的内容，并进行AI分析。
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Keyword, KeywordHotspot
from ..schemas import (
    KeywordCreate,
    KeywordUpdate,
    KeywordResponse,
    MessageResponse,
)

router = APIRouter()


def keyword_to_response(keyword: Keyword, match_count: int = 0) -> dict:
    """将 Keyword 模型转换为响应 dict，包含 match_count"""
    return {
        "id": keyword.id,
        "keyword": keyword.keyword,
        "category": keyword.category,
        "priority": keyword.priority,
        "description": keyword.description,
        "is_active": keyword.is_active,
        "match_count": match_count,
        "created_at": keyword.created_at,
        "updated_at": keyword.updated_at,
    }


@router.get(
    "",
    response_model=List[KeywordResponse],
    summary="获取关键词列表",
    description="""
获取所有已添加的监控关键词列表，支持分页和过滤。

**功能说明：**
- 返回关键词的完整信息，包括ID、关键词内容、分类、优先级、描述、是否启用、匹配热点数等
- 支持通过 `active_only` 参数仅获取已启用的关键词
- 结果按创建时间倒序排列（最新添加的在前）

**使用场景：**
- 前端关键词管理页面展示
- 获取活跃关键词用于爬虫任务
""",
    responses={
        200: {"description": "成功返回关键词列表"}
    }
)
async def get_keywords(
    skip: int = Query(0, ge=0, description="跳过的记录数，用于分页。例如：skip=20 表示跳过前20条"),
    limit: int = Query(100, ge=1, le=500, description="返回的最大记录数，范围1-500，默认100"),
    active_only: bool = Query(False, description="是否仅返回已启用的关键词。True=仅活跃，False=全部"),
    db: AsyncSession = Depends(get_db)
):
    # 使用 selectinload 加载关联的热点
    query = select(Keyword).options(selectinload(Keyword.hotspots))
    if active_only:
        query = query.where(Keyword.is_active == True)
    query = query.offset(skip).limit(limit).order_by(Keyword.created_at.desc())
    
    result = await db.execute(query)
    keywords = result.scalars().unique().all()
    
    # 转换为响应格式，包含 match_count
    return [keyword_to_response(k, len(k.hotspots)) for k in keywords]


@router.get(
    "/{keyword_id}",
    response_model=KeywordResponse,
    summary="获取单个关键词详情",
    description="""
根据关键词ID获取单个关键词的详细信息。

**返回信息包括：**
- `id`: 关键词唯一标识
- `keyword`: 关键词内容
- `category`: 分类（如：AI、编程、科技等）
- `priority`: 优先级（low/normal/high/critical）
- `description`: 关键词描述
- `is_active`: 是否启用监控
- `created_at`: 创建时间
- `updated_at`: 最后更新时间
""",
    responses={
        200: {"description": "成功返回关键词详情"},
        404: {"description": "关键词不存在"}
    }
)
async def get_keyword(
    keyword_id: int = Path(..., description="关键词ID，必须是有效的整数", ge=1, example=1),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Keyword).options(selectinload(Keyword.hotspots)).where(Keyword.id == keyword_id)
    )
    keyword = result.scalar_one_or_none()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")
    
    return keyword_to_response(keyword, len(keyword.hotspots))


@router.post(
    "",
    response_model=KeywordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建新关键词",
    description="""
添加一个新的监控关键词。系统会自动检查关键词是否重复。

**请求参数说明：**
- `keyword` (必填): 要监控的关键词，如 "GPT-5"、"Claude 4" 等
- `category` (可选): 分类标签，如 "AI"、"编程"、"科技"
- `priority` (可选): 优先级，可选值：low/normal/high/critical，默认为 normal
- `description` (可选): 关键词的描述说明
- `is_active` (可选): 是否立即启用监控，默认为 true

**业务逻辑：**
1. 检查关键词是否已存在（不区分大小写）
2. 如果已存在则返回400错误
3. 创建成功后返回完整的关键词信息

**示例请求体：**
```json
{
    "keyword": "GPT-5",
    "category": "AI",
    "priority": "high",
    "description": "监控OpenAI最新大模型发布",
    "is_active": true
}
```
""",
    responses={
        201: {"description": "关键词创建成功"},
        400: {"description": "关键词已存在"}
    }
)
async def create_keyword(
    keyword_data: KeywordCreate,
    db: AsyncSession = Depends(get_db)
):
    # 检查是否已存在
    result = await db.execute(
        select(Keyword).where(Keyword.keyword == keyword_data.keyword)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="关键词已存在")
    
    keyword = Keyword(**keyword_data.model_dump())
    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)
    
    return keyword_to_response(keyword, 0)


@router.put(
    "/{keyword_id}",
    response_model=KeywordResponse,
    summary="更新关键词",
    description="""
更新指定关键词的信息。支持部分更新，只需传入要修改的字段。

**可更新的字段：**
- `keyword`: 关键词内容
- `category`: 分类
- `priority`: 优先级（low/normal/high/critical）
- `description`: 描述
- `is_active`: 是否启用

**示例 - 仅更新优先级：**
```json
{
    "priority": "critical"
}
```

**示例 - 更新多个字段：**
```json
{
    "category": "AI大模型",
    "priority": "high",
    "description": "新的描述内容"
}
```
""",
    responses={
        200: {"description": "更新成功，返回更新后的关键词信息"},
        404: {"description": "关键词不存在"}
    }
)
async def update_keyword(
    keyword_id: int = Path(..., description="要更新的关键词ID", ge=1),
    keyword_data: KeywordUpdate = ...,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    keyword = result.scalar_one_or_none()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")
    
    update_data = keyword_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(keyword, field, value)
    
    await db.commit()
    
    # 重新加载并计算 match_count
    result = await db.execute(
        select(Keyword).options(selectinload(Keyword.hotspots)).where(Keyword.id == keyword_id)
    )
    keyword = result.scalar_one()
    
    return keyword_to_response(keyword, len(keyword.hotspots))


@router.delete(
    "/{keyword_id}",
    response_model=MessageResponse,
    summary="删除关键词",
    description="""
删除指定的关键词。删除后将停止对该关键词的监控。

**注意事项：**
- 删除操作不可恢复
- 关联的热点数据不会被删除，但会解除关联关系
- 如果只是想暂停监控，建议使用 toggle 接口禁用关键词
""",
    responses={
        200: {"description": "删除成功"},
        404: {"description": "关键词不存在"}
    }
)
async def delete_keyword(
    keyword_id: int = Path(..., description="要删除的关键词ID", ge=1),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    keyword = result.scalar_one_or_none()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")
    
    await db.delete(keyword)
    await db.commit()
    
    return MessageResponse(message="关键词已删除")


@router.post(
    "/{keyword_id}/toggle",
    response_model=KeywordResponse,
    summary="切换关键词启用状态",
    description="""
快速切换关键词的启用/禁用状态。

**功能说明：**
- 如果当前是启用状态（is_active=true），调用后变为禁用
- 如果当前是禁用状态（is_active=false），调用后变为启用

**使用场景：**
- 临时暂停某个关键词的监控
- 重新启用之前禁用的关键词
- 前端开关按钮的后端接口

**返回值：**
返回更新后的完整关键词信息，其中 `is_active` 字段反映新的状态。
""",
    responses={
        200: {"description": "切换成功，返回更新后的关键词信息"},
        404: {"description": "关键词不存在"}
    }
)
async def toggle_keyword(
    keyword_id: int = Path(..., description="要切换状态的关键词ID", ge=1),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    keyword = result.scalar_one_or_none()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")
    
    keyword.is_active = not keyword.is_active
    await db.commit()
    
    # 重新加载并计算 match_count
    result = await db.execute(
        select(Keyword).options(selectinload(Keyword.hotspots)).where(Keyword.id == keyword_id)
    )
    keyword = result.scalar_one()
    
    return keyword_to_response(keyword, len(keyword.hotspots))
