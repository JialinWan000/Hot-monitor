"""定时任务调度器"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import settings


# 全局调度器实例
scheduler = AsyncIOScheduler()


async def monitor_keywords_job():
    """关键词监控任务"""
    print("⏰ 执行关键词监控任务...")
    from .services.crawler_manager import CrawlerManager
    
    try:
        await CrawlerManager.refresh_all_keywords()
        print("✅ 关键词监控完成")
    except Exception as e:
        print(f"❌ 关键词监控失败: {e}")


async def discover_hotspots_job():
    """热点发现任务"""
    print("⏰ 执行热点发现任务...")
    from .services.crawler_manager import CrawlerManager
    
    try:
        # 获取多个领域的热点
        domains = ["AI", "科技", "编程"]
        for domain in domains:
            await CrawlerManager.search_domain(domain)
        print("✅ 热点发现完成")
    except Exception as e:
        print(f"❌ 热点发现失败: {e}")


async def process_notifications_job():
    """处理待发送通知"""
    print("⏰ 处理待发送通知...")
    from sqlalchemy import select
    from .database import async_session_maker
    from .models import Hotspot
    from .services.notifier import NotificationService
    
    try:
        async with async_session_maker() as db:
            # 获取未通知的高分热点
            result = await db.execute(
                select(Hotspot).where(
                    Hotspot.notified == False,
                    Hotspot.is_fake == False,
                    Hotspot.score >= 70,  # 只通知高分热点
                ).limit(10)
            )
            hotspots = result.scalars().all()
            
            for hotspot in hotspots:
                await NotificationService.send_hotspot_notification(db, hotspot)
            
            print(f"✅ 已处理 {len(hotspots)} 条通知")
    except Exception as e:
        print(f"❌ 通知处理失败: {e}")


def setup_scheduler():
    """配置定时任务"""
    # 关键词监控 - 每 N 分钟
    scheduler.add_job(
        monitor_keywords_job,
        trigger=IntervalTrigger(minutes=settings.CRAWL_INTERVAL_MINUTES),
        id="monitor_keywords",
        name="关键词监控",
        replace_existing=True,
    )
    
    # 热点发现 - 每 N 分钟
    scheduler.add_job(
        discover_hotspots_job,
        trigger=IntervalTrigger(minutes=settings.HOTSPOT_INTERVAL_MINUTES),
        id="discover_hotspots",
        name="热点发现",
        replace_existing=True,
    )
    
    # 通知处理 - 每分钟
    scheduler.add_job(
        process_notifications_job,
        trigger=IntervalTrigger(minutes=1),
        id="process_notifications",
        name="通知处理",
        replace_existing=True,
    )
    
    print("📅 定时任务已配置:")
    print(f"   - 关键词监控: 每 {settings.CRAWL_INTERVAL_MINUTES} 分钟")
    print(f"   - 热点发现: 每 {settings.HOTSPOT_INTERVAL_MINUTES} 分钟")
    print(f"   - 通知处理: 每 1 分钟")


def start_scheduler():
    """启动调度器"""
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()
        print("🚀 定时任务调度器已启动")


def stop_scheduler():
    """停止调度器"""
    if scheduler.running:
        scheduler.shutdown()
        print("⏹️ 定时任务调度器已停止")
