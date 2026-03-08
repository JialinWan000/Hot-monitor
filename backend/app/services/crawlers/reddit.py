"""Reddit 爬虫"""
from typing import List, Optional
from datetime import datetime

from .base import BaseCrawler, CrawlResult


class RedditCrawler(BaseCrawler):
    """Reddit 爬虫 - 使用公开 API"""
    
    source_id = "reddit"
    source_name = "Reddit"
    
    def __init__(self):
        super().__init__()
        self.headers.update({
            "Accept": "application/json",
        })
    
    async def search(self, keyword: str) -> List[CrawlResult]:
        """搜索 Reddit"""
        results = []
        
        response = await self._safe_request(
            "GET",
            "https://www.reddit.com/search.json",
            params={
                "q": keyword,
                "sort": "relevance",
                "t": "week",
                "limit": 25,
            }
        )
        
        if response:
            data = response.json()
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                
                results.append(CrawlResult(
                    title=post.get("title", ""),
                    content=post.get("selftext", "") or post.get("url", ""),
                    source=self.source_id,
                    source_url=f"https://www.reddit.com{post.get('permalink', '')}",
                    published_at=datetime.fromtimestamp(post.get("created_utc", 0)) if post.get("created_utc") else None,
                    extra={
                        "subreddit": post.get("subreddit"),
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "upvote_ratio": post.get("upvote_ratio", 0),
                    }
                ))
        
        return results
    
    async def get_trending(self, category: Optional[str] = None) -> List[CrawlResult]:
        """获取 Reddit 热门"""
        results = []
        
        # 默认获取科技相关 subreddit
        subreddits = ["technology", "programming", "machinelearning", "artificial"]
        
        if category:
            subreddits = [category.lower()]
        
        for subreddit in subreddits:
            response = await self._safe_request(
                "GET",
                f"https://www.reddit.com/r/{subreddit}/hot.json",
                params={"limit": 15}
            )
            
            if response:
                data = response.json()
                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    
                    # 跳过置顶帖
                    if post.get("stickied"):
                        continue
                    
                    results.append(CrawlResult(
                        title=post.get("title", ""),
                        content=post.get("selftext", "") or post.get("url", ""),
                        source=self.source_id,
                        source_url=f"https://www.reddit.com{post.get('permalink', '')}",
                        published_at=datetime.fromtimestamp(post.get("created_utc", 0)) if post.get("created_utc") else None,
                        extra={
                            "subreddit": post.get("subreddit"),
                            "score": post.get("score", 0),
                            "num_comments": post.get("num_comments", 0),
                        }
                    ))
        
        return results
