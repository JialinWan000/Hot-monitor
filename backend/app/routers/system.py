"""系统设置路由

提供系统级别的配置管理和统计查询功能，包括：
- 仪表盘统计数据
- 系统配置管理
- VAPID密钥获取（用于Web Push）
- 系统信息查询
"""
from typing import Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Keyword, Hotspot, Notification, Setting
from ..schemas import (
    DashboardStats,
    SettingResponse,
    SettingUpdate,
    MessageResponse,
)
from ..config import settings as app_settings

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="获取仪表盘统计数据",
    description="""
获取系统的综合统计数据，用于仪表盘页面展示。

**返回统计项：**
| 字段 | 说明 |
|---|---|
| total_keywords | 总关键词数量 |
| active_keywords | 已启用的关键词数量 |
| total_hotspots | 总热点数量 |
| unread_hotspots | 未读热点数量 |
| today_hotspots | 今日发现的热点数量（从今日0点开始计算） |
| notifications_sent | 已成功发送的通知数量 |

**数据说明：**
- 今日热点：统计 discovered_at >= 今日00:00:00 的记录
- 通知发送：统计 status='sent' 的通知记录
- 所有数值均为实时计算
""",
    responses={
        200: {"description": "成功返回统计数据"}
    }
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db)
):
    # 关键词统计
    total_keywords = await db.scalar(select(func.count()).select_from(Keyword))
    active_keywords = await db.scalar(
        select(func.count()).select_from(Keyword).where(Keyword.is_active == True)
    )
    
    # 热点统计
    total_hotspots = await db.scalar(select(func.count()).select_from(Hotspot))
    unread_hotspots = await db.scalar(
        select(func.count()).select_from(Hotspot).where(Hotspot.read == False)
    )
    
    # 今日热点
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_hotspots = await db.scalar(
        select(func.count()).select_from(Hotspot).where(Hotspot.discovered_at >= today)
    )
    
    # 已发送通知数
    notifications_sent = await db.scalar(
        select(func.count()).select_from(Notification).where(Notification.status == "sent")
    )
    
    return DashboardStats(
        total_keywords=total_keywords or 0,
        active_keywords=active_keywords or 0,
        total_hotspots=total_hotspots or 0,
        unread_hotspots=unread_hotspots or 0,
        today_hotspots=today_hotspots or 0,
        notifications_sent=notifications_sent or 0,
    )


@router.get(
    "/settings",
    summary="获取系统设置",
    description="""
获取系统的全局配置参数。

**返回配置项：**
| 字段 | 说明 | 默认值 |
|---|---|---|
| crawl_interval | 关键词监控间隔（分钟） | 5 |
| hotspot_interval | 热点发现间隔（分钟） | 30 |
| ai_model | 使用的AI模型 | anthropic/claude-3.5-sonnet |
| openrouter_configured | OpenRouter API是否已配置 | - |
| email_configured | 邮件服务是否已配置 | - |
| push_configured | Web Push是否已配置 | - |

**配置项说明：**
- `crawl_interval`: 定时任务检查关键词匹配的间隔
- `hotspot_interval`: 定时任务抓取热点的间隔
- `ai_model`: OpenRouter API使用的模型名称
- `*_configured`: 判断对应功能是否已配置（环境变量已设置）

**说明：**
配置值优先从数据库读取，如果未设置则使用环境变量中的默认值。
""",
    responses={
        200: {"description": "成功返回系统设置"}
    }
)
async def get_system_settings(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    result = await db.execute(select(Setting))
    settings_list = result.scalars().all()
    
    settings_dict = {s.key: s.value for s in settings_list}
    
    # 添加默认配置值
    return {
        "crawl_interval": int(settings_dict.get("crawl_interval", app_settings.CRAWL_INTERVAL_MINUTES)),
        "hotspot_interval": int(settings_dict.get("hotspot_interval", app_settings.HOTSPOT_INTERVAL_MINUTES)),
        "ai_model": settings_dict.get("ai_model", app_settings.OPENROUTER_MODEL),
        "openrouter_configured": bool(app_settings.OPENROUTER_API_KEY),
        "email_configured": bool(app_settings.SMTP_HOST),
        "push_configured": bool(app_settings.VAPID_PUBLIC_KEY),
    }


@router.post(
    "/settings",
    response_model=MessageResponse,
    summary="更新系统设置",
    description="""
更新系统的配置参数。

**可更新的配置项：**
| key | 说明 | 值类型 | 示例 |
|---|---|---|---|
| crawl_interval | 关键词监控间隔 | 数字（分钟） | "10" |
| hotspot_interval | 热点发现间隔 | 数字（分钟） | "60" |
| ai_model | AI模型名称 | 字符串 | "openai/gpt-4" |

**请求示例：**
```json
{
    "key": "crawl_interval",
    "value": "10"
}
```

**注意事项：**
- 每次只能更新一个配置项
- 值必须是字符串类型
- 部分配置更改需重启服务才能生效（如定时任务间隔）
- AI模型必须是OpenRouter支持的有效模型名称
""",
    responses={
        200: {"description": "设置更新成功"}
    }
)
async def update_system_setting(
    setting: SettingUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Setting).where(Setting.key == setting.key))
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.value = setting.value
    else:
        new_setting = Setting(key=setting.key, value=setting.value)
        db.add(new_setting)
    
    await db.commit()
    return MessageResponse(message="设置已更新")


@router.get(
    "/vapid-public-key",
    summary="获取 VAPID 公钥",
    description="""
获取 Web Push 的 VAPID 公钥，前端需要此公钥来订阅推送通知。

**VAPID（Voluntary Application Server Identification）说明：**
- 是 Web Push 协议的身份验证机制
- 公钥用于前端订阅时标识服务端
- 私钥用于服务端发送推送时签名

**返回值：**
```json
{
    "public_key": "BNcRdreALRFXTkOOUH...",   // Base64编码的公钥
    "configured": true                         // 是否已配置
}
```

**使用方式：**
前端获取公钥后，调用 PushManager.subscribe() 时传入：
```javascript
const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(publicKey)
});
```

**注意事项：**
如果返回 `configured: false`，说明服务端未配置VAPID密钥，需要：
1. 生成 VAPID 密钥对
2. 在环境变量中配置 VAPID_PUBLIC_KEY 和 VAPID_PRIVATE_KEY
""",
    responses={
        200: {"description": "成功返回VAPID公钥信息"}
    }
)
async def get_vapid_public_key():
    if not app_settings.VAPID_PUBLIC_KEY:
        return {"public_key": None, "configured": False}
    
    return {
        "public_key": app_settings.VAPID_PUBLIC_KEY,
        "configured": True
    }


@router.get(
    "/info",
    summary="获取系统信息",
    description="""
获取应用的基本信息。

**返回信息：**
- `name`: 应用名称（Hot Monitor）
- `version`: 应用版本号
- `debug`: 是否为调试模式

**使用场景：**
- 前端页面显示版本信息
- API客户端版本兼容性检查
- 调试和排错
""",
    responses={
        200: {"description": "成功返回系统信息"}
    }
)
async def get_system_info():
    return {
        "name": app_settings.APP_NAME,
        "version": app_settings.APP_VERSION,
        "debug": app_settings.DEBUG,
    }
