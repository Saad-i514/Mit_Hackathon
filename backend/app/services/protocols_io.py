"""
protocols.io public API integration.
Searches for similar public protocols for grounding plan generation.
"""
import logging
from typing import Any, Dict, List

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ProtocolsIOClient:
    """Client for protocols.io public protocol search."""

    BASE_URL = "https://www.protocols.io/api/v3/protocols"

    def __init__(self) -> None:
        self.token = settings.protocols_io_token
        self.timeout = 12.0

    async def search_protocols(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search public protocols related to a hypothesis/query."""
        if not self.token:
            return []

        params = {
            "filter": "public",
            "key": query[:150],
            "order_field": "activity",
        }
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.BASE_URL, params=params, headers=headers)
            if response.status_code != 200:
                logger.warning("protocols.io returned non-200 status: %s", response.status_code)
                return []

            payload = response.json()
            items = payload.get("items", [])
            matches: List[Dict[str, Any]] = []
            for item in items[: max(1, min(limit, 10))]:
                stats = item.get("stats") or {}
                matches.append(
                    {
                        "title": item.get("title", ""),
                        "doi": item.get("doi"),
                        "url": item.get("link") or item.get("uri"),
                        "citations": stats.get("number_of_citations", 0),
                        "steps": stats.get("number_of_steps"),
                        "published_on": item.get("publish_date") or item.get("published_on"),
                        "source": "protocols.io",
                    }
                )
            return matches
        except Exception as exc:
            logger.warning("protocols.io search failed: %s", exc)
            return []


_protocols_io_client = ProtocolsIOClient()


def get_protocols_io_client() -> ProtocolsIOClient:
    """Dependency accessor for protocols.io client."""
    return _protocols_io_client

