"""通知服务 - Web Push 和邮件通知"""
import json
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import Hotspot, Notification, PushSubscription, Setting


class NotificationService:
    """通知服务"""
    
    @classmethod
    async def send_hotspot_notification(
        cls,
        db: AsyncSession,
        hotspot: Hotspot,
    ):
        """发送热点通知"""
        # 检查通知设置
        push_enabled = await cls._get_setting(db, "push_enabled", "false") == "true"
        email_enabled = await cls._get_setting(db, "email_enabled", "false") == "true"
        
        if push_enabled:
            await cls._send_push_notification(db, hotspot)
        
        if email_enabled:
            await cls._send_email_notification(db, hotspot)
        
        # 标记热点已通知
        hotspot.notified = True
        await db.commit()
    
    @classmethod
    async def _send_push_notification(
        cls,
        db: AsyncSession,
        hotspot: Hotspot,
    ):
        """发送 Web Push 通知"""
        if not settings.VAPID_PRIVATE_KEY:
            print("Web Push 未配置")
            return
        
        try:
            from pywebpush import webpush, WebPushException
            
            # 获取所有活跃订阅
            result = await db.execute(
                select(PushSubscription).where(PushSubscription.is_active == True)
            )
            subscriptions = result.scalars().all()
            
            if not subscriptions:
                print("没有活跃的推送订阅")
                return
            
            # 构建通知内容
            payload = json.dumps({
                "title": "🔥 发现新热点",
                "body": hotspot.title[:100],
                "icon": "/icon-192.png",
                "badge": "/badge-72.png",
                "data": {
                    "hotspot_id": hotspot.id,
                    "url": hotspot.source_url or f"/hotspots/{hotspot.id}",
                },
                "tag": f"hotspot-{hotspot.id}",
            })
            
            vapid_claims = {
                "sub": f"mailto:{settings.VAPID_CLAIMS_EMAIL}"
            }
            
            for sub in subscriptions:
                try:
                    subscription_info = {
                        "endpoint": sub.endpoint,
                        "keys": {
                            "p256dh": sub.p256dh,
                            "auth": sub.auth,
                        }
                    }
                    
                    webpush(
                        subscription_info=subscription_info,
                        data=payload,
                        vapid_private_key=settings.VAPID_PRIVATE_KEY,
                        vapid_claims=vapid_claims,
                    )
                    
                    # 记录通知
                    notification = Notification(
                        hotspot_id=hotspot.id,
                        type="push",
                        status="sent",
                        sent_at=datetime.now(),
                    )
                    db.add(notification)
                    
                except WebPushException as e:
                    print(f"Push 通知发送失败: {e}")
                    if e.response and e.response.status_code in [404, 410]:
                        # 订阅已失效
                        sub.is_active = False
                    
                    # 记录失败
                    notification = Notification(
                        hotspot_id=hotspot.id,
                        type="push",
                        status="failed",
                        error_message=str(e),
                    )
                    db.add(notification)
            
            await db.commit()
            
        except ImportError:
            print("pywebpush 未安装")
        except Exception as e:
            print(f"Push 通知异常: {e}")
    
    @classmethod
    async def _send_email_notification(
        cls,
        db: AsyncSession,
        hotspot: Hotspot,
    ):
        """发送邮件通知"""
        if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.NOTIFICATION_EMAIL]):
            print("邮件通知未配置")
            return
        
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # 构建邮件
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🔥 Hot Monitor: {hotspot.title[:50]}"
            msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
            msg["To"] = settings.NOTIFICATION_EMAIL
            
            # HTML 内容
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #e74c3c;">🔥 发现新热点</h2>
                <h3>{hotspot.title}</h3>
                <p><strong>来源：</strong>{hotspot.source}</p>
                <p><strong>评分：</strong>{hotspot.score or 'N/A'}</p>
                {f'<p><strong>摘要：</strong>{hotspot.summary}</p>' if hotspot.summary else ''}
                {f'<p><a href="{hotspot.source_url}">查看原文</a></p>' if hotspot.source_url else ''}
                <hr>
                <p style="color: #888; font-size: 12px;">
                    此邮件由 Hot Monitor 自动发送
                </p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            # 发送邮件
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
            
            # 记录通知
            notification = Notification(
                hotspot_id=hotspot.id,
                type="email",
                status="sent",
                sent_at=datetime.now(),
            )
            db.add(notification)
            await db.commit()
            
            print(f"邮件通知已发送: {hotspot.title[:30]}...")
            
        except ImportError:
            print("aiosmtplib 未安装")
        except Exception as e:
            print(f"邮件发送失败: {e}")
            
            # 记录失败
            notification = Notification(
                hotspot_id=hotspot.id,
                type="email",
                status="failed",
                error_message=str(e),
            )
            db.add(notification)
            await db.commit()
    
    @classmethod
    async def send_test_push(cls, db: AsyncSession):
        """发送测试推送"""
        if not settings.VAPID_PRIVATE_KEY:
            raise ValueError("Web Push 未配置")
        
        try:
            from pywebpush import webpush
            
            result = await db.execute(
                select(PushSubscription).where(PushSubscription.is_active == True).limit(1)
            )
            sub = result.scalar_one_or_none()
            
            if not sub:
                raise ValueError("没有活跃的推送订阅")
            
            payload = json.dumps({
                "title": "🔔 测试通知",
                "body": "Hot Monitor 推送测试成功！",
                "icon": "/icon-192.png",
            })
            
            subscription_info = {
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
            }
            
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_CLAIMS_EMAIL}"},
            )
            
        except ImportError:
            raise ValueError("pywebpush 未安装")
    
    @classmethod
    async def send_test_email(cls):
        """发送测试邮件"""
        if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.NOTIFICATION_EMAIL]):
            raise ValueError("邮件通知未配置")
        
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            
            msg = MIMEText("Hot Monitor 邮件测试成功！", "plain", "utf-8")
            msg["Subject"] = "🔔 Hot Monitor 测试邮件"
            msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
            msg["To"] = settings.NOTIFICATION_EMAIL
            
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
            
        except ImportError:
            raise ValueError("aiosmtplib 未安装")
    
    @classmethod
    async def _get_setting(cls, db: AsyncSession, key: str, default: str = "") -> str:
        """获取设置值"""
        result = await db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        return setting.value if setting else default
