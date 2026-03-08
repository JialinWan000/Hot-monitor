"""Google 搜索爬虫"""
from typing import List, Optional
from bs4 import BeautifulSoup

from .base import BaseCrawler, CrawlResult


class GoogleCrawler(BaseCrawler):
    """Google 搜索爬虫"""
    
    source_id = "google"
    source_name = "Google"
    
    async def search(self, keyword: str) -> List[CrawlResult]:
        """搜索 Google"""
        results = []
        
        response = await self._safe_request(
            "GET",
            "https://www.google.com/search",
            params={
                "q": keyword,
                "num": 20,
                "hl": "en",
            }
        )
        
        if response:
            soup = BeautifulSoup(response.text, "lxml")
            
            # 解析搜索结果
            result_items = soup.select("div.g")[:20]
            
            for item in result_items:
                title_elem = item.select_one("h3")
                link_elem = item.select_one("a")
                snippet_elem = item.select_one("div[data-sncf]") or item.select_one(".VwiC3b")
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    url = link_elem.get("href", "")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    # 过滤无效 URL
                    if url.startswith("/url?"):
                        import urllib.parse
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                        url = parsed.get("q", [url])[0]
                    
                    if url.startswith("http"):
                        results.append(CrawlResult(
                            title=title,
                            content=snippet,
                            source=self.source_id,
                            source_url=url,
                        ))
        
        return results
    
    async def get_trending(self, category: Optional[str] = None) -> List[CrawlResult]:
        """获取 Google 新闻趋势"""
        results = []
        
        search_term = f"{category} news" if category else "technology AI news today"
        
        response = await self._safe_request(
            "GET",
            "https://news.google.com/search",
            params={
                "q": search_term,
                "hl": "en-US",
                "gl": "US",
                "ceid": "US:en",
            }
        )
        
        if response:
            soup = BeautifulSoup(response.text, "lxml")
            
            # Google News 文章
            articles = soup.select("article")[:20]
            
            for article in articles:
                title_elem = article.select_one("h3") or article.select_one("h4")
                link_elem = article.select_one("a")
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    url = link_elem.get("href", "")
                    
                    # Google News URL 处理
                    if url.startswith("./"):
                        url = f"https://news.google.com/{url[2:]}"
                    
                    results.append(CrawlResult(
                        title=title,
                        content="",
                        source=self.source_id,
                        source_url=url,
                    ))
        
        return results
