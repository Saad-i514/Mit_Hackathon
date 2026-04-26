"""
Hypothesis refinement scoring and rewrite suggestions.
"""
import json
import logging
from typing import Any, Dict, List

from app.services.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

REFINER_PROMPT = """
Score the following scientific hypothesis on 5 criteria (0-100 total):
- specificity (0-25)
- measurability (0-25)
- comparison (0-20)
- timeframe (0-15)
- novelty_potential (0-15)

If score < 70, provide exactly 3 improved rewrite options.
Return ONLY valid JSON in this shape:
{
  "score": <int>,
  "criteria": {
    "specificity": <int>,
    "measurability": <int>,
    "comparison": <int>,
    "timeframe": <int>,
    "novelty_potential": <int>
  },
  "weaknesses": ["..."],
  "suggested_rewrites": [
    {"hypothesis":"...","improvement_rationale":"..."}
  ]
}
"""


class HypothesisRefiner:
    """Scores hypotheses and suggests improved rewrites."""

    def __init__(self, openai_client: OpenAIClient) -> None:
        self.openai_client = openai_client

    async def refine(self, hypothesis: str) -> Dict[str, Any]:
        """Return score + rubric + rewrite suggestions."""
        try:
            response = await self.openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": REFINER_PROMPT},
                    {"role": "user", "content": hypothesis},
                ],
                temperature=0.2,
                max_tokens=1200,
                response_format={"type": "json_object"},
            )
            data = json.loads(response)
            return {
                "score": int(data.get("score", 100)),
                "criteria": data.get("criteria", {}),
                "weaknesses": data.get("weaknesses", []),
                "suggested_rewrites": data.get("suggested_rewrites", []),
            }
        except Exception as exc:
            logger.warning("Hypothesis refinement failed: %s", exc)
            return {
                "score": 100,
                "criteria": {},
                "weaknesses": [],
                "suggested_rewrites": [],
            }


def get_hypothesis_refiner(openai_client: OpenAIClient) -> HypothesisRefiner:
    """Factory for hypothesis refiner."""
    return HypothesisRefiner(openai_client)

