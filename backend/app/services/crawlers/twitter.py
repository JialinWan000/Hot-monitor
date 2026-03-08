"""Twitter/X 爬虫"""
from typing import List, Optional

from .base import BaseCrawler, CrawlResult


class TwitterCrawler(BaseCrawler):
    """Twitter/X 爬虫 - 使用 Nitter 实例或搜索引擎"""
    
    source_id = "twitter"
    source_name = "Twitter/X"
    
    # Nitter 实例列表（公共实例可能不稳定）
    NITTER_INSTANCES = [
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
    ]
    
    async def search(self, keyword: str) -> List[CrawlResult]:
        """搜索 Twitter（通过 Nitter）"""
        results = []
        
        for instance in self.NITTER_INSTANCES:
            try:
                response = await self._safe_request(
                    "GET",
                    f"{instance}/search",
                    params={"f": "tweets", "q": keyword}
                )
                
                if response:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, "lxml")
                    
                    tweets = soup.select(".timeline-item")[:20]
                    
                    for tweet in tweets:
                        username_elem = tweet.select_one(".username")
                        content_elem = tweet.select_one(".tweet-content")
                        link_elem = tweet.select_one(".tweet-link")
                        
                        if content_elem:
                            username = username_elem.get_text(strip=True) if username_elem else ""
                            content = content_elem.get_text(strip=True)
                            link = link_elem.get("href", "") if link_elem else ""
                            
                            results.append(CrawlResult(
                                title=f"{username}: {content[:100]}...",
                                content=content,
                                source=self.source_id,
                                source_url=f"https://twitter.com{link}" if link else "",
                                extra={
                                    "username": username,
                                }
                            ))
                    
                    if results:
                        break  # 成功获取结果，退出循环
                        
            except Exception as e:
                print(f"[Twitter] Nitter 实例 {instance} 请求失败: {e}")
                continue
        
        return results
    
    async def get_trending(self, category: Optional[str] = None) -> List[CrawlResult]:
        """获取 Twitter 趋势（通过搜索热门话题）"""
        # 由于 Twitter API 需要认证，这里使用搜索方式获取热门
        if category:
            return await self.search(f"{category} trending")
        else:
            return await self.search("AI technology trending today")
