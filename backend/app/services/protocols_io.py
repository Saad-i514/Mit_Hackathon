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

        headers = {"Authorization": f"Bearer {self.token}"}
        candidate_queries = self._build_candidate_queries(query)
        merged: List[Dict[str, Any]] = []
        seen_titles = set()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for candidate in candidate_queries:
                    params = {
                        "filter": "public",
                        "key": candidate[:150],
                        "order_field": "activity",
                    }
                    response = await client.get(self.BASE_URL, params=params, headers=headers)
                    if response.status_code != 200:
                        logger.warning("protocols.io returned non-200 status: %s", response.status_code)
                        continue

                    payload = response.json()
                    items = payload.get("items", [])
                    for item in items:
                        title = (item.get("title") or "").strip()
                        if not title:
                            continue
                        title_key = title.lower()
                        if title_key in seen_titles:
                            continue
                        seen_titles.add(title_key)

                        stats = item.get("stats") or {}
                        merged.append(
                            {
                                "title": title,
                                "doi": item.get("doi"),
                                "url": item.get("link") or item.get("uri"),
                                "citations": stats.get("number_of_citations", 0),
                                "steps": stats.get("number_of_steps"),
                                "published_on": item.get("publish_date") or item.get("published_on"),
                                "source": "protocols.io",
                            }
                        )
                        if len(merged) >= max(1, min(limit, 10)):
                            return merged
            return merged
        except Exception as exc:
            logger.warning("protocols.io search failed: %s", exc)
            return []

    def _build_candidate_queries(self, query: str) -> List[str]:
        """Build fallback search keys from narrow to broad."""
        q = " ".join((query or "").strip().split())
        if not q:
            return ["protocol"]

        terms = [t for t in q.split(" ") if len(t) > 3]
        stop = {
            "will", "with", "from", "into", "this", "that", "than", "then",
            "using", "compared", "resulting", "measured", "analysis",
        }
        keywords = [t for t in terms if t.lower() not in stop]

        candidates = [q]
        if keywords:
            candidates.append(" ".join(keywords[:6]))
            candidates.append(" ".join(keywords[:3]))

        # Domain-style broad fallbacks to avoid zero results on narrow phrasing.
        broad = ["cell culture protocol", "assay protocol", "sample preparation protocol"]
        candidates.extend(broad)

        # De-duplicate while preserving order.
        seen = set()
        deduped: List[str] = []
        for c in candidates:
            key = c.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(c)
        return deduped


_protocols_io_client = ProtocolsIOClient()


def get_protocols_io_client() -> ProtocolsIOClient:
    """Dependency accessor for protocols.io client."""
    return _protocols_io_client

