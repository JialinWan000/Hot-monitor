"""Hacker News 爬虫"""
from typing import List, Optional
from datetime import datetime

from .base import BaseCrawler, CrawlResult


class HackerNewsCrawler(BaseCrawler):
    """Hacker News 爬虫 - 使用官方 API"""
    
    source_id = "hackernews"
    source_name = "Hacker News"
    
    API_BASE = "https://hacker-news.firebaseio.com/v0"
    
    async def search(self, keyword: str) -> List[CrawlResult]:
        """搜索 Hacker News（使用 Algolia API）"""
        results = []
        
        # 使用 Algolia 搜索 API
        search_url = "https://hn.algolia.com/api/v1/search"
        response = await self._safe_request(
            "GET",
            search_url,
            params={
                "query": keyword,
                "tags": "story",
                "hitsPerPage": 20,
            }
        )
        
        if response:
            data = response.json()
            for hit in data.get("hits", []):
                results.append(CrawlResult(
                    title=hit.get("title", ""),
                    content=hit.get("story_text") or hit.get("url", ""),
                    source=self.source_id,
                    source_url=hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    published_at=datetime.fromtimestamp(hit.get("created_at_i", 0)) if hit.get("created_at_i") else None,
                    extra={
                        "points": hit.get("points", 0),
                        "num_comments": hit.get("num_comments", 0),
                        "author": hit.get("author"),
                    }
                ))
        
        return results
    
    async def get_trending(self, category: Optional[str] = None) -> List[CrawlResult]:
        """获取 Hacker News 热门文章"""
        results = []
        
        # 获取 Top Stories
        response = await self._safe_request("GET", f"{self.API_BASE}/topstories.json")
        
        if response:
            story_ids = response.json()[:30]  # 取前30个
            
            for story_id in story_ids:
                story_response = await self._safe_request(
                    "GET",
                    f"{self.API_BASE}/item/{story_id}.json"
                )
                
                if story_response:
                    story = story_response.json()
                    if story and story.get("title"):
                        results.append(CrawlResult(
                            title=story.get("title", ""),
                            content=story.get("text") or story.get("url", ""),
                            source=self.source_id,
                            source_url=story.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                            published_at=datetime.fromtimestamp(story.get("time", 0)) if story.get("time") else None,
                            extra={
                                "points": story.get("score", 0),
                                "num_comments": story.get("descendants", 0),
                                "author": story.get("by"),
                            }
                        ))
        
        return results
