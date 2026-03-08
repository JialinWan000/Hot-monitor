"""DuckDuckGo 爬虫"""
from typing import List, Optional
from datetime import datetime
import json
import re

from .base import BaseCrawler, CrawlResult


class DuckDuckGoCrawler(BaseCrawler):
    """DuckDuckGo 搜索爬虫"""
    
    source_id = "duckduckgo"
    source_name = "DuckDuckGo"
    
    async def search(self, keyword: str) -> List[CrawlResult]:
        """搜索 DuckDuckGo"""
        results = []
        
        # 使用 DuckDuckGo HTML 搜索
        response = await self._safe_request(
            "GET",
            "https://html.duckduckgo.com/html/",
            params={"q": keyword},
            headers={
                **self.headers,
                "Accept": "text/html",
            }
        )
        
        if response:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "lxml")
            
            # 解析搜索结果
            result_items = soup.select(".result")[:20]
            
            for item in result_items:
                title_elem = item.select_one(".result__title a")
                snippet_elem = item.select_one(".result__snippet")
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get("href", "")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    # DuckDuckGo 的 URL 可能需要解码
                    if url.startswith("//duckduckgo.com/l/?"):
                        # 提取真实 URL
                        import urllib.parse
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                        url = parsed.get("uddg", [url])[0]
                    
                    results.append(CrawlResult(
                        title=title,
                        content=snippet,
                        source=self.source_id,
                        source_url=url,
                    ))
        
        return results
    
    async def get_trending(self, category: Optional[str] = None) -> List[CrawlResult]:
        """DuckDuckGo 没有官方趋势，使用热门话题搜索"""
        # 搜索科技/AI相关热点
        search_terms = [
            "AI news today",
            "tech news today",
            "programming news",
        ]
        
        if category:
            search_terms = [f"{category} news today"]
        
        all_results = []
        for term in search_terms:
            results = await self.search(term)
            all_results.extend(results[:10])
        
        return all_results
