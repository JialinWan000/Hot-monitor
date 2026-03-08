"""爬虫管理器 - 统一管理所有爬虫"""
from typing import List, Dict, Optional, Type
from datetime import datetime

from .crawlers.base import BaseCrawler, CrawlResult
from .crawlers.hackernews import HackerNewsCrawler
from .crawlers.github import GitHubCrawler
from .crawlers.duckduckgo import DuckDuckGoCrawler
from .crawlers.zhihu import ZhihuCrawler
from .crawlers.reddit import RedditCrawler
from .crawlers.bing import BingCrawler
from .crawlers.google import GoogleCrawler
from .crawlers.twitter import TwitterCrawler

from ..database import async_session_maker
from ..models import Keyword, Hotspot, KeywordHotspot


class CrawlerManager:
    """爬虫管理器"""
    
    # 注册所有爬虫
    CRAWLERS: Dict[str, Type[BaseCrawler]] = {
        "hackernews": HackerNewsCrawler,
        "github": GitHubCrawler,
        "duckduckgo": DuckDuckGoCrawler,
        "zhihu": ZhihuCrawler,
        "reddit": RedditCrawler,
        "bing": BingCrawler,
        "google": GoogleCrawler,
        "twitter": TwitterCrawler,
    }
    
    @classmethod
    def get_crawler(cls, source_id: str) -> Optional[BaseCrawler]:
        """获取指定爬虫实例"""
        crawler_class = cls.CRAWLERS.get(source_id)
        if crawler_class:
            return crawler_class()
        return None
    
    @classmethod
    def get_all_crawlers(cls) -> List[BaseCrawler]:
        """获取所有爬虫实例"""
        return [crawler_class() for crawler_class in cls.CRAWLERS.values()]
    
    @classmethod
    async def search_keyword(
        cls,
        keyword: str,
        sources: Optional[List[str]] = None
    ) -> List[CrawlResult]:
        """搜索关键词"""
        all_results = []
        
        if sources:
            crawlers = [cls.get_crawler(s) for s in sources if cls.get_crawler(s)]
        else:
            crawlers = cls.get_all_crawlers()
        
        for crawler in crawlers:
            try:
                results = await crawler.search(keyword)
                all_results.extend(results)
                print(f"[{crawler.source_name}] 搜索 '{keyword}' 获取 {len(results)} 条结果")
            except Exception as e:
                print(f"[{crawler.source_name}] 搜索失败: {e}")
        
        return all_results
    
    @classmethod
    async def get_trending(
        cls,
        category: Optional[str] = None,
        sources: Optional[List[str]] = None
    ) -> List[CrawlResult]:
        """获取热门内容"""
        all_results = []
        
        if sources:
            crawlers = [cls.get_crawler(s) for s in sources if cls.get_crawler(s)]
        else:
            crawlers = cls.get_all_crawlers()
        
        for crawler in crawlers:
            try:
                results = await crawler.get_trending(category)
                all_results.extend(results)
                print(f"[{crawler.source_name}] 获取趋势 {len(results)} 条结果")
            except Exception as e:
                print(f"[{crawler.source_name}] 获取趋势失败: {e}")
        
        return all_results
    
    @classmethod
    async def refresh_all_keywords(cls):
        """刷新所有关键词的监控"""
        from sqlalchemy import select
        from .ai_service import AIService
        
        async with async_session_maker() as session:
            # 获取所有启用的关键词
            result = await session.execute(
                select(Keyword).where(Keyword.is_active == True)
            )
            keywords = result.scalars().all()
            
            for keyword in keywords:
                print(f"监控关键词: {keyword.keyword}")
                
                # 搜索关键词
                results = await cls.search_keyword(keyword.keyword)
                
                # AI 分析和保存
                for crawl_result in results:
                    await cls._save_hotspot(session, crawl_result, keyword)
            
            await session.commit()
    
    @classmethod
    async def search_domain(
        cls,
        domain: str,
        sources: Optional[List[str]] = None
    ):
        """搜索指定领域的热点"""
        from .ai_service import AIService
        
        async with async_session_maker() as session:
            print(f"搜索领域热点: {domain}")
            
            # 获取趋势
            results = await cls.get_trending(domain, sources)
            
            # 搜索领域关键词
            search_results = await cls.search_keyword(domain, sources)
            results.extend(search_results)
            
            # 保存热点
            for crawl_result in results:
                await cls._save_hotspot(session, crawl_result)
            
            await session.commit()
    
    @classmethod
    async def _save_hotspot(
        cls,
        session,
        crawl_result: CrawlResult,
        keyword: Optional[Keyword] = None
    ):
        """保存热点到数据库"""
        from sqlalchemy import select
        from .ai_service import AIService
        
        # 检查是否已存在（根据标题和来源）
        existing = await session.execute(
            select(Hotspot).where(
                Hotspot.title == crawl_result.title,
                Hotspot.source == crawl_result.source
            )
        )
        
        if existing.scalar_one_or_none():
            return  # 已存在，跳过
        
        # 创建热点记录
        hotspot = Hotspot(
            title=crawl_result.title,
            content=crawl_result.content,
            source=crawl_result.source,
            source_url=crawl_result.source_url,
            published_at=crawl_result.published_at,
        )
        
        # AI 分析
        try:
            analysis = await AIService.analyze_hotspot(
                title=crawl_result.title,
                content=crawl_result.content or "",
                source=crawl_result.source,
            )
            
            hotspot.score = analysis.get("score", 50)
            hotspot.is_verified = analysis.get("is_verified", False)
            hotspot.is_fake = analysis.get("is_fake", False)
            hotspot.summary = analysis.get("summary", "")
            hotspot.ai_analysis = analysis.get("analysis", "")
            hotspot.tags = analysis.get("tags", [])
        except Exception as e:
            print(f"AI 分析失败: {e}")
        
        session.add(hotspot)
        await session.flush()
        
        # 关联关键词
        if keyword:
            link = KeywordHotspot(keyword_id=keyword.id, hotspot_id=hotspot.id)
            session.add(link)
