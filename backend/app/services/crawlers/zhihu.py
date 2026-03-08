"""知乎热榜爬虫"""
from typing import List, Optional
from datetime import datetime

from .base import BaseCrawler, CrawlResult


class ZhihuCrawler(BaseCrawler):
    """知乎热榜爬虫"""
    
    source_id = "zhihu"
    source_name = "知乎热榜"
    
    API_BASE = "https://www.zhihu.com/api/v3"
    
    def __init__(self):
        super().__init__()
        self.headers.update({
            "Referer": "https://www.zhihu.com/hot",
            "Accept": "application/json",
        })
    
    async def search(self, keyword: str) -> List[CrawlResult]:
        """搜索知乎"""
        results = []
        
        response = await self._safe_request(
            "GET",
            f"{self.API_BASE}/search",
            params={
                "q": keyword,
                "t": "general",
                "offset": 0,
                "limit": 20,
            }
        )
        
        if response:
            data = response.json()
            for item in data.get("data", []):
                obj = item.get("object", {})
                
                title = obj.get("title") or obj.get("question", {}).get("title", "")
                content = obj.get("excerpt", "")
                url = obj.get("url", "")
                
                if title:
                    results.append(CrawlResult(
                        title=title,
                        content=content,
                        source=self.source_id,
                        source_url=url if url.startswith("http") else f"https://www.zhihu.com{url}",
                        extra={
                            "type": item.get("type"),
                            "vote_count": obj.get("voteup_count", 0),
                        }
                    ))
        
        return results
    
    async def get_trending(self, category: Optional[str] = None) -> List[CrawlResult]:
        """获取知乎热榜"""
        results = []
        
        response = await self._safe_request(
            "GET",
            "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total",
            params={"limit": 50}
        )
        
        if response:
            data = response.json()
            for item in data.get("data", []):
                target = item.get("target", {})
                
                title = target.get("title", "")
                excerpt = target.get("excerpt", "")
                url = target.get("url", "")
                
                # 热度
                detail_text = item.get("detail_text", "")
                
                if title:
                    results.append(CrawlResult(
                        title=title,
                        content=excerpt,
                        source=self.source_id,
                        source_url=url if url.startswith("http") else f"https://www.zhihu.com/question/{target.get('id')}",
                        extra={
                            "heat": detail_text,
                            "answer_count": target.get("answer_count", 0),
                        }
                    ))
        
        return results
