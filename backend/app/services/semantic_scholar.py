"""
Semantic Scholar API client with retry logic
"""
import httpx
import asyncio
import logging
from typing import List, Dict, Any, Optional
from app.config import settings


logger = logging.getLogger(__name__)


class SemanticScholarClient:
    """Async Semantic Scholar API client with exponential backoff"""
    
    def __init__(self):
        """Initialize Semantic Scholar client"""
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.api_key = settings.semantic_scholar_api_key
        self.max_retries = 3
        self.timeout = 15.0
    
    async def search_papers(
        self,
        query: str,
        limit: int = 20,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using Semantic Scholar API
        
        Args:
            query: Search query string
            limit: Maximum number of results
            fields: List of fields to return
        
        Returns:
            List[Dict]: List of paper objects
        
        Raises:
            httpx.HTTPError: If request fails after retries
        """
        if fields is None:
            fields = ["title", "authors", "year", "abstract", "citationCount", "externalIds", "url"]
        
        params = {
            "query": query[:200],  # Limit query length
            "fields": ",".join(fields),
            "limit": limit
        }
        
        headers = {"x-api-key": self.api_key}
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.base_url}/paper/search",
                        params=params,
                        headers=headers
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data.get("data", [])
            
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    if attempt < self.max_retries - 1:
                        delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(
                            f"Semantic Scholar rate limit hit, retrying in {delay}s "
                            f"(attempt {attempt + 1}/{self.max_retries})"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Semantic Scholar rate limit exceeded after {self.max_retries} attempts")
                        raise
                else:
                    logger.error(f"Semantic Scholar HTTP error: {e.response.status_code}")
                    raise
            
            except httpx.TimeoutException:
                if attempt < self.max_retries - 1:
                    delay = 2 ** attempt
                    logger.warning(
                        f"Semantic Scholar timeout, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Semantic Scholar timeout after {self.max_retries} attempts")
                    raise
            
            except Exception as e:
                logger.error(f"Unexpected error in Semantic Scholar search: {e}")
                raise
        
        return []
    
    async def get_paper(
        self,
        paper_id: str,
        fields: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get paper details by ID
        
        Args:
            paper_id: Semantic Scholar paper ID
            fields: List of fields to return
        
        Returns:
            Optional[Dict]: Paper object or None if not found
        """
        if fields is None:
            fields = ["title", "authors", "year", "abstract", "citationCount", "externalIds", "url"]
        
        params = {"fields": ",".join(fields)}
        headers = {"x-api-key": self.api_key}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/paper/{paper_id}",
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Paper not found: {paper_id}")
                return None
            logger.error(f"Semantic Scholar HTTP error: {e.response.status_code}")
            raise
        
        except Exception as e:
            logger.error(f"Error fetching paper {paper_id}: {e}")
            raise


# Global Semantic Scholar client instance
semantic_scholar_client = SemanticScholarClient()


def get_semantic_scholar_client() -> SemanticScholarClient:
    """Get the global Semantic Scholar client instance"""
    return semantic_scholar_client
