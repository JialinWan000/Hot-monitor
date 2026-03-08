"""通知管理路由

提供通知功能的配置和管理，包括：
- 浏览器推送通知（Web Push）
- 邮件通知
- 通知历史记录查询
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Notification, Setting, PushSubscription
from ..schemas import (
    NotificationResponse,
    NotificationSettingsUpdate,
    NotificationSettingsResponse,
    PushSubscriptionCreate,
    MessageResponse,
)

router = APIRouter()


@router.get(
    "",
    response_model=List[NotificationResponse],
    summary="获取通知历史记录",
    description="""
获取系统发送的通知历史记录，支持分页。

**返回信息包括：**
- `id`: 通知记录ID
- `hotspot_id`: 关联的热点ID
- `type`: 通知类型（push/email）
- `status`: 发送状态（pending/sent/failed）
- `error_message`: 失败时的错误信息
- `created_at`: 创建时间
- `sent_at`: 发送时间

**状态说明：**
- `pending`: 等待发送
- `sent`: 发送成功
- `failed`: 发送失败

**排序说明：**
按创建时间倒序排列（最新的在前）
""",
    responses={
        200: {"description": "成功返回通知记录列表"}
    }
)
async def get_notifications(
    skip: int = Query(0, ge=0, description="跳过的记录数，用于分页"),
    limit: int = Query(50, ge=1, le=200, description="返回的最大记录数，范围1-200，默认50"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    notifications = result.scalars().all()
    return notifications


@router.get(
    "/settings",
    response_model=NotificationSettingsResponse,
    summary="获取通知设置",
    description="""
获取当前的通知配置状态。

**返回信息：**
- `email_enabled`: 邮件通知是否启用
- `push_enabled`: 浏览器推送是否启用
- `notification_email`: 接收通知的邮箱地址

**说明：**
- 设置存储在数据库的 settings 表中
- 返回的是当前配置的启用状态
- 如果未配置，则返回默认值（通常为 false/null）
""",
    responses={
        200: {"description": "成功返回通知设置"}
    }
)
async def get_notification_settings(
    db: AsyncSession = Depends(get_db)
):
    settings_dict = {}
    
    result = await db.execute(
        select(Setting).where(
            Setting.key.in_([
                "email_enabled",
                "push_enabled", 
                "notification_email"
            ])
        )
    )
    
    for setting in result.scalars():
        if setting.key in ["email_enabled", "push_enabled"]:
            settings_dict[setting.key] = setting.value.lower() == "true"
        else:
            settings_dict[setting.key] = setting.value
    
    return NotificationSettingsResponse(**settings_dict)


@router.post(
    "/settings",
    response_model=MessageResponse,
    summary="更新通知设置",
    description="""
更新通知相关的配置项。支持部分更新，只需传入要修改的字段。

**可配置字段：**
- `email_enabled`: 是否启用邮件通知（true/false）
- `push_enabled`: 是否启用浏览器推送（true/false）
- `notification_email`: 接收通知的邮箱地址

**请求示例 - 启用邮件通知：**
```json
{
    "email_enabled": true,
    "notification_email": "user@example.com"
}
```

**请求示例 - 仅启用推送：**
```json
{
    "push_enabled": true
}
```

**注意事项：**
- 启用邮件通知前，需确保后端已配置SMTP服务器
- 启用推送通知前，需确保浏览器已订阅推送
- 配置会立即生效，影响后续的通知发送
""",
    responses={
        200: {"description": "设置更新成功"}
    }
)
async def update_notification_settings(
    settings_data: NotificationSettingsUpdate,
    db: AsyncSession = Depends(get_db)
):
    update_data = settings_data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        # 查找或创建设置
        result = await db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = str(value).lower() if isinstance(value, bool) else str(value)
        else:
            new_setting = Setting(
                key=key,
                value=str(value).lower() if isinstance(value, bool) else str(value)
            )
            db.add(new_setting)
    
    await db.commit()
    return MessageResponse(message="通知设置已更新")


@router.post(
    "/subscribe",
    response_model=MessageResponse,
    summary="订阅 Web Push 通知",
    description="""
注册浏览器的 Web Push 推送订阅。

**功能说明：**
当用户在浏览器中授权推送通知后，前端会获取订阅信息（endpoint、keys等），
然后调用此接口将订阅信息保存到服务端。

**请求参数：**
- `endpoint`: 推送服务端点URL（由浏览器生成）
- `keys`: 加密密钥对象，包含：
  - `p256dh`: 用于加密的公钥
  - `auth`: 认证密钥

**请求示例：**
```json
{
    "endpoint": "https://fcm.googleapis.com/fcm/send/xxx...",
    "keys": {
        "p256dh": "BNcRdreALRFX...",
        "auth": "tBHItJI5sv..."
    }
}
```

**注意事项：**
- 如果相同endpoint已存在，会更新其密钥信息
- 订阅信息由浏览器生成，每个浏览器-设备组合唯一
- 用户清除浏览器数据会导致订阅失效
""",
    responses={
        200: {"description": "订阅成功"}
    }
)
async def subscribe_push(
    subscription: PushSubscriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    # 检查是否已存在
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.endpoint == subscription.endpoint
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # 更新现有订阅
        existing.p256dh = subscription.keys.get("p256dh", "")
        existing.auth = subscription.keys.get("auth", "")
        existing.is_active = True
    else:
        # 创建新订阅
        new_sub = PushSubscription(
            endpoint=subscription.endpoint,
            p256dh=subscription.keys.get("p256dh", ""),
            auth=subscription.keys.get("auth", ""),
        )
        db.add(new_sub)
    
    await db.commit()
    return MessageResponse(message="已订阅推送通知")


@router.post(
    "/unsubscribe",
    response_model=MessageResponse,
    summary="取消订阅 Web Push 通知",
    description="""
取消浏览器的 Web Push 推送订阅。

**功能说明：**
将指定的订阅标记为不活跃状态，后续不会再向该端点发送推送。

**请求参数：**
- `endpoint`: 要取消的推送服务端点URL

**使用场景：**
- 用户关闭通知开关
- 用户注销时清理订阅

**注意事项：**
- 订阅记录不会被删除，只是标记为不活跃
- 用户重新订阅时会更新原有记录
""",
    responses={
        200: {"description": "取消订阅成功"}
    }
)
async def unsubscribe_push(
    endpoint: str = Body(..., embed=True, description="要取消订阅的推送端点URL"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        subscription.is_active = False
        await db.commit()
    
    return MessageResponse(message="已取消订阅")


@router.post(
    "/test",
    response_model=MessageResponse,
    summary="测试通知",
    description="""
发送一条测试通知，用于验证通知配置是否正确。

**支持的通知类型：**
- `push`: 发送浏览器推送测试通知
- `email`: 发送邮件测试通知

**使用场景：**
- 配置通知后测试是否生效
- 排查通知功能问题

**Push通知测试：**
会向所有活跃的订阅端点发送一条标题为"测试通知"的推送。

**邮件通知测试：**
会向配置的通知邮箱发送一封测试邮件。

**前置条件：**
- Push测试：需要有活跃的推送订阅
- 邮件测试：需要配置SMTP服务器和通知邮箱
""",
    responses={
        200: {"description": "测试通知已发送"},
        400: {"description": "不支持的通知类型"}
    }
)
async def test_notification(
    notification_type: str = Query("push", description="通知类型：push（浏览器推送）或 email（邮件）"),
    db: AsyncSession = Depends(get_db)
):
    from ..services.notifier import NotificationService
    
    if notification_type == "push":
        await NotificationService.send_test_push(db)
    elif notification_type == "email":
        await NotificationService.send_test_email()
    else:
        raise HTTPException(status_code=400, detail="不支持的通知类型")
    
    return MessageResponse(message=f"{notification_type} 测试通知已发送")
