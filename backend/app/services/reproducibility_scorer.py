"""
Reproducibility scoring service based on ARRIVE/TOP-style criteria.
"""
import json
import logging
from typing import Any, Dict

from app.services.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

SCORER_PROMPT = """
You are a senior scientific reviewer applying ARRIVE 2.0 and TOP guidelines.
Score the experiment plan on each criterion from 0 to max_points.

Return ONLY valid JSON with this schema:
{
  "total_score": <int>,
  "criteria": [
    {"id":"R1","score":<int>,"max":12,"issue":"...","suggestion":"..."}
  ]
}
"""


class ReproducibilityScorer:
    """Scores generated plans for reproducibility quality."""

    def __init__(self, openai_client: OpenAIClient) -> None:
        self.openai_client = openai_client

    async def score(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Return reproducibility score JSON."""
        try:
            response = await self.openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": SCORER_PROMPT},
                    {"role": "user", "content": f"Plan: {json.dumps(plan)}"},
                ],
                temperature=0.2,
                max_tokens=1200,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(response)
            parsed["total_score"] = int(parsed.get("total_score", 0))
            return parsed
        except Exception as exc:
            logger.warning("Reproducibility scoring failed: %s", exc)
            return {"total_score": 0, "criteria": []}


def get_reproducibility_scorer(openai_client: OpenAIClient) -> ReproducibilityScorer:
    """Factory for reproducibility scorer."""
    return ReproducibilityScorer(openai_client)

