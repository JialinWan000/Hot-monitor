"""爬虫基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import httpx

from ...config import settings


@dataclass
class CrawlResult:
    """爬取结果"""
    title: str
    content: Optional[str] = None
    source: str = ""
    source_url: Optional[str] = None
    published_at: Optional[datetime] = None
    extra: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "source_url": self.source_url,
            "published_at": self.published_at,
            "extra": self.extra or {},
        }


class BaseCrawler(ABC):
    """爬虫基类"""
    
    source_id: str = ""
    source_name: str = ""
    
    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT
        self.proxy = settings.HTTP_PROXY
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        return httpx.AsyncClient(
            timeout=self.timeout,
            proxy=self.proxy if self.proxy else None,
            headers=self.headers,
            follow_redirects=True,
        )
    
    @abstractmethod
    async def search(self, keyword: str) -> List[CrawlResult]:
        """搜索关键词相关内容"""
        pass
    
    @abstractmethod
    async def get_trending(self, category: Optional[str] = None) -> List[CrawlResult]:
        """获取热门/趋势内容"""
        pass
    
    async def _safe_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[httpx.Response]:
        """安全的 HTTP 请求"""
        try:
            async with self._get_client() as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
        except httpx.HTTPError as e:
            print(f"[{self.source_name}] HTTP请求失败: {e}")
            return None
        except Exception as e:
            print(f"[{self.source_name}] 请求异常: {e}")
            return None
