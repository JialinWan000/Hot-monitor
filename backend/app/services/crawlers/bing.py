"""Bing 搜索爬虫"""
from typing import List, Optional
from bs4 import BeautifulSoup

from .base import BaseCrawler, CrawlResult


class BingCrawler(BaseCrawler):
    """Bing 搜索爬虫"""
    
    source_id = "bing"
    source_name = "Bing"
    
    async def search(self, keyword: str) -> List[CrawlResult]:
        """搜索 Bing"""
        results = []
        
        response = await self._safe_request(
            "GET",
            "https://www.bing.com/search",
            params={
                "q": keyword,
                "count": 20,
            }
        )
        
        if response:
            soup = BeautifulSoup(response.text, "lxml")
            
            # 解析搜索结果
            result_items = soup.select(".b_algo")[:20]
            
            for item in result_items:
                title_elem = item.select_one("h2 a")
                snippet_elem = item.select_one(".b_caption p")
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get("href", "")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append(CrawlResult(
                        title=title,
                        content=snippet,
                        source=self.source_id,
                        source_url=url,
                    ))
        
        return results
    
    async def get_trending(self, category: Optional[str] = None) -> List[CrawlResult]:
        """获取 Bing 热门新闻"""
        results = []
        
        # 搜索新闻
        search_term = f"{category} news" if category else "technology news today"
        
        response = await self._safe_request(
            "GET",
            "https://www.bing.com/news/search",
            params={
                "q": search_term,
                "qft": "sortbydate",
            }
        )
        
        if response:
            soup = BeautifulSoup(response.text, "lxml")
            
            news_items = soup.select(".news-card")[:20]
            
            for item in news_items:
                title_elem = item.select_one("a.title")
                snippet_elem = item.select_one(".snippet")
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get("href", "")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append(CrawlResult(
                        title=title,
                        content=snippet,
                        source=self.source_id,
                        source_url=url,
                    ))
        
        return results
