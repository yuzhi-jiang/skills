"""搜索引擎集成（SerpAPI）"""
import asyncio
import os
from typing import Any, Dict, List, Optional

from logger import setup_logger

try:
    import serpapi
except Exception:
    serpapi = None


logger = setup_logger(__name__)


class SearchIntegration:
    """SerpAPI 搜索封装。"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.location = os.getenv("SERPAPI_LOCATION", "Austin, Texas, United States")
        self.hl = os.getenv("SERPAPI_HL", "zh-cn")
        self.gl = os.getenv("SERPAPI_GL", "cn")
        self.google_domain = os.getenv("SERPAPI_GOOGLE_DOMAIN", "google.com")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and serpapi is not None)

    async def search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """执行一次 Google 搜索并返回原始结果。"""
        if not query.strip():
            return {"organic_results": []}

        if not self.enabled:
            logger.info("SerpAPI is disabled: missing package or SERPAPI_API_KEY")
            return {"organic_results": []}

        params = {
            "q": query,
            "location": self.location,
            "hl": self.hl,
            "gl": self.gl,
            "google_domain": self.google_domain,
            "num": num_results,
        }

        def _do_search() -> Dict[str, Any]:
            client = serpapi.Client(api_key=self.api_key)
            result = client.search(params)
            if hasattr(result, "data"):
                return result.data
            return {}

        try:
            result = await asyncio.to_thread(_do_search)
            if not isinstance(result, dict):
                return {"organic_results": []}
            return result
        except Exception as exc:
            logger.warning(f"SerpAPI search failed: {exc}")
            return {"organic_results": []}

    @staticmethod
    def extract_sources(results: Dict[str, Any]) -> List[str]:
        """从搜索结果中提取 source / 域名。"""
        sources: List[str] = []
        organic_results = results.get("organic_results", [])
        if not isinstance(organic_results, list):
            return sources

        for item in organic_results:
            if not isinstance(item, dict):
                continue

            source = item.get("source")
            if isinstance(source, str) and source.strip():
                sources.append(source.strip())
                continue

            link = item.get("link")
            if isinstance(link, str) and link.strip():
                domain = SearchIntegration._domain_from_url(link)
                if domain:
                    sources.append(domain)

        return sources

    @staticmethod
    def _domain_from_url(url: str) -> str:
        try:
            cleaned = url.replace("https://", "").replace("http://", "")
            domain = cleaned.split("/")[0]
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""
