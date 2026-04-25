"""
Serper Web Search API client
"""
import httpx
import asyncio
import logging
from typing import List, Dict, Any, Optional
from app.config import settings


logger = logging.getLogger(__name__)


class SerperClient:
    """Async Serper API client for web search"""
    
    def __init__(self):
        """Initialize Serper client"""
        self.base_url = "https://google.serper.dev"
        self.api_key = settings.serper_api_key
        self.timeout = 15.0
    
    async def search(
        self,
        query: str,
        num_results: int = 20,
        search_type: str = "search"
    ) -> Dict[str, Any]:
        """
        Perform web search using Serper API
        
        Args:
            query: Search query string
            num_results: Number of results to return
            search_type: Type of search ('search', 'news', 'images', etc.)
        
        Returns:
            Dict: Search results with organic results, knowledge graph, etc.
        
        Raises:
            httpx.HTTPError: If request fails
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": num_results,
            "gl": "us",  # Geographic location
            "hl": "en"   # Language
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/{search_type}",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Serper HTTP error: {e.response.status_code}")
            raise
        
        except httpx.TimeoutException:
            logger.error("Serper request timeout")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error in Serper search: {e}")
            raise
    
    async def search_scientific(
        self,
        query: str,
        num_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for scientific content with filtering
        
        Args:
            query: Search query string
            num_results: Number of results to return
        
        Returns:
            List[Dict]: List of search results
        """
        # Add scientific keywords to improve results
        scientific_query = f"{query} (site:scholar.google.com OR site:pubmed.ncbi.nlm.nih.gov OR site:arxiv.org OR site:biorxiv.org OR site:protocols.io OR site:bio-protocol.org)"
        
        try:
            results = await self.search(scientific_query, num_results)
            return results.get("organic", [])
        
        except Exception as e:
            logger.warning(f"Scientific search failed, falling back to general search: {e}")
            # Fallback to general search
            results = await self.search(query, num_results)
            return results.get("organic", [])


# Global Serper client instance
serper_client = SerperClient()


def get_serper_client() -> SerperClient:
    """Get the global Serper client instance"""
    return serper_client
