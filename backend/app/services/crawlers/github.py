"""GitHub Trending 爬虫"""
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from .base import BaseCrawler, CrawlResult


class GitHubCrawler(BaseCrawler):
    """GitHub Trending 爬虫"""
    
    source_id = "github"
    source_name = "GitHub Trending"
    
    BASE_URL = "https://github.com"
    
    async def search(self, keyword: str) -> List[CrawlResult]:
        """搜索 GitHub 仓库"""
        results = []
        
        response = await self._safe_request(
            "GET",
            f"{self.BASE_URL}/search",
            params={
                "q": keyword,
                "type": "repositories",
                "s": "stars",
                "o": "desc",
            }
        )
        
        if response:
            soup = BeautifulSoup(response.text, "lxml")
            repo_items = soup.select(".repo-list-item")[:20]
            
            for item in repo_items:
                title_elem = item.select_one("a.v-align-middle")
                desc_elem = item.select_one("p.mb-1")
                stars_elem = item.select_one("a.Link--muted")
                
                if title_elem:
                    repo_name = title_elem.get_text(strip=True)
                    repo_url = f"{self.BASE_URL}{title_elem.get('href', '')}"
                    
                    results.append(CrawlResult(
                        title=repo_name,
                        content=desc_elem.get_text(strip=True) if desc_elem else "",
                        source=self.source_id,
                        source_url=repo_url,
                        extra={
                            "stars": stars_elem.get_text(strip=True) if stars_elem else "0",
                        }
                    ))
        
        return results
    
    async def get_trending(self, category: Optional[str] = None) -> List[CrawlResult]:
        """获取 GitHub Trending"""
        results = []
        
        # 支持语言过滤
        url = f"{self.BASE_URL}/trending"
        if category:
            url += f"/{category.lower()}"
        
        response = await self._safe_request("GET", url, params={"since": "daily"})
        
        if response:
            soup = BeautifulSoup(response.text, "lxml")
            repo_items = soup.select("article.Box-row")[:30]
            
            for item in repo_items:
                # 仓库名称
                h2 = item.select_one("h2 a")
                if not h2:
                    continue
                
                repo_path = h2.get("href", "").strip("/")
                repo_name = repo_path.replace("/", " / ")
                repo_url = f"{self.BASE_URL}/{repo_path}"
                
                # 描述
                desc_elem = item.select_one("p")
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # 语言
                lang_elem = item.select_one("[itemprop='programmingLanguage']")
                language = lang_elem.get_text(strip=True) if lang_elem else ""
                
                # Stars
                stars_elem = item.select_one("a[href$='/stargazers']")
                stars = stars_elem.get_text(strip=True) if stars_elem else "0"
                
                # 今日 Stars
                today_stars_elem = item.select_one(".float-sm-right")
                today_stars = today_stars_elem.get_text(strip=True) if today_stars_elem else ""
                
                results.append(CrawlResult(
                    title=repo_name,
                    content=description,
                    source=self.source_id,
                    source_url=repo_url,
                    extra={
                        "language": language,
                        "stars": stars,
                        "today_stars": today_stars,
                    }
                ))
        
        return results
