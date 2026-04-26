"""
Plan Generator Component
Generates complete experiment plans using GPT-4o with few-shot learning
"""
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.services.openai_client import OpenAIClient
from app.services.learning_engine import LearningEngine, FeedbackEmbedding
from app.services.pubchem import get_pubchem_client, PubChemClient
from app.models.responses import (
    ExperimentPlan, Protocol, Materials, Timeline, ValidationCriteria,
    ExperimentPlanMetadata, NoveltyAssessment, NoveltyClassification
)


logger = logging.getLogger(__name__)


class PlanGenerator:
    """Generates experiment plans using GPT-4o with RAG-based few-shot learning"""
    
    def __init__(
        self,
        openai_client: OpenAIClient,
        learning_engine: LearningEngine
    ):
        """
        Initialize PlanGenerator
        
        Args:
            openai_client: OpenAI client for GPT-4o
            learning_engine: Learning engine for RAG
        """
        self.openai_client = openai_client
        self.learning_engine = learning_engine
        self.pubchem_client: PubChemClient = get_pubchem_client()
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file"""
        try:
            with open("app/prompts/plan_generator_system.txt", "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load system prompt: {e}")
            return "You are an expert scientific experiment planner."
    
    async def generate_plan(
        self,
        hypothesis: str,
        domain: str,
        novelty_assessment: NoveltyAssessment,
        protocol_matches: Optional[List[Dict[str, Any]]] = None
    ) -> ExperimentPlan:
        """
        Generate complete experiment plan with few-shot learning
        
        Args:
            hypothesis: Scientific hypothesis
            domain: Scientific domain
            novelty_assessment: Literature QC results
        
        Returns:
            ExperimentPlan: Complete structured experiment plan
        
        Raises:
            Exception: If plan generation fails
        """
        try:
            # Query Learning Engine for similar corrections
            similar_corrections = await self.learning_engine.query_corrections(
                hypothesis=hypothesis,
                domain=domain,
                top_k=5,
                similarity_threshold=0.75
            )
            
            # Build few-shot context
            few_shot_context = self.learning_engine.build_few_shot_context(
                similar_corrections
            )
            
            # Build user prompt
            user_prompt = self._build_user_prompt(
                hypothesis=hypothesis,
                domain=domain,
                novelty_assessment=novelty_assessment,
                few_shot_context=few_shot_context,
                protocol_matches=protocol_matches or [],
            )
            
            # Generate plan using GPT-4o
            response = await self.openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            plan_data = json.loads(response)
            await self._enrich_materials_with_pubchem(plan_data)
            
            # Validate and construct ExperimentPlan
            plan = self._construct_experiment_plan(
                plan_data=plan_data,
                hypothesis=hypothesis,
                domain=domain,
                novelty_classification=novelty_assessment.classification,
                few_shot_examples_used=len(similar_corrections),
                protocol_matches=protocol_matches or [],
            )
            
            logger.info(f"Generated experiment plan for domain {domain} with {len(similar_corrections)} few-shot examples")
            
            return plan
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4o response: {e}")
            raise Exception(f"Plan generation failed: Invalid JSON response")
        
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            raise Exception(f"Plan generation failed: {str(e)}")

    async def _enrich_materials_with_pubchem(self, plan_data: Dict[str, Any]) -> None:
        """Enrich generated materials with PubChem metadata."""
        items = (plan_data.get("materials") or {}).get("items") or []
        if not items:
            return

        async def _enrich(item: Dict[str, Any]) -> Dict[str, Any]:
            data = await self.pubchem_client.enrich_reagent(item.get("name", ""))
            if not data.get("pubchem_found"):
                return item
            item["pubchem_found"] = True
            item["cid"] = data.get("cid")
            item["cas_number"] = data.get("cas_number")
            item["molecular_weight"] = data.get("molecular_weight")
            item["molecular_formula"] = data.get("molecular_formula")
            item["ghs_codes"] = data.get("ghs_codes", [])
            item["pubchem_url"] = data.get("pubchem_url")
            return item

        enriched = await asyncio.gather(*[_enrich(item) for item in items], return_exceptions=True)
        out = []
        for idx, result in enumerate(enriched):
            if isinstance(result, Exception):
                out.append(items[idx])
            else:
                out.append(result)
        plan_data.setdefault("materials", {})["items"] = out
    
    def _build_user_prompt(
        self,
        hypothesis: str,
        domain: str,
        novelty_assessment: NoveltyAssessment,
        few_shot_context: str,
        protocol_matches: List[Dict[str, Any]]
    ) -> str:
        """Build user prompt for plan generation"""
        
        # Build literature context
        literature_context = f"\nNovelty Assessment: {novelty_assessment.classification.value}"
        
        if novelty_assessment.similar_papers:
            literature_context += f"\n\nSimilar Research Found ({len(novelty_assessment.similar_papers)} papers):"
            for paper in novelty_assessment.similar_papers[:3]:
                literature_context += f"\n- {paper.title} ({paper.year if paper.year else 'N/A'})"
                if paper.abstract:
                    literature_context += f"\n  Abstract: {paper.abstract[:150]}..."
        
        protocols_context = ""
        if protocol_matches:
            top_matches = protocol_matches[:2]
            lines = []
            for idx, match in enumerate(top_matches, start=1):
                lines.append(
                    f"Protocol {idx}: {match.get('title', 'N/A')} "
                    f"({match.get('citations', 0)} citations, {match.get('steps', 'N/A')} steps)\n"
                    f"DOI: {match.get('doi') or 'N/A'}\n"
                    f"URL: {match.get('url') or 'N/A'}"
                )
            protocols_context = (
                "\n\nSIMILAR_PROTOCOLS_CONTEXT:\n"
                "Use the following protocols.io matches as methodological anchors where applicable:\n"
                + "\n".join(lines)
            )

        prompt = f"""Generate a complete, operationally realistic experiment plan for this hypothesis:

Hypothesis: "{hypothesis}"
Domain: {domain}
{literature_context}
{few_shot_context}
{protocols_context}

REQUIREMENTS:
1. Ground ALL protocol steps in real published protocols (protocols.io, bio-protocol.org, peer-reviewed papers)
2. Use REAL catalog numbers from actual suppliers (Thermo Fisher, Sigma-Aldrich, etc.)
3. Provide 2024-2025 pricing based on current supplier catalogs
4. Create realistic timeline with explicit phase dependencies
5. Define quantitative success/failure criteria with measurement methods
6. Include safety considerations and troubleshooting guidance

CRITICAL: Return ONLY valid JSON matching the schema in the system prompt. No additional text."""
        
        return prompt
    
    def _construct_experiment_plan(
        self,
        plan_data: Dict[str, Any],
        hypothesis: str,
        domain: str,
        novelty_classification: NoveltyClassification,
        few_shot_examples_used: int,
        protocol_matches: List[Dict[str, Any]]
    ) -> ExperimentPlan:
        """
        Construct ExperimentPlan from parsed JSON
        
        Args:
            plan_data: Parsed JSON from GPT-4o
            hypothesis: Original hypothesis
            domain: Scientific domain
            novelty_classification: Novelty classification
            few_shot_examples_used: Number of few-shot examples
        
        Returns:
            ExperimentPlan: Validated experiment plan
        """
        # Identify sections requiring expert review
        requires_expert_review = self._identify_review_flags(plan_data)
        
        # Construct metadata
        metadata = ExperimentPlanMetadata(
            generated_at=datetime.now(timezone.utc).isoformat(),
            model_version="gpt-4o",
            few_shot_examples_used=few_shot_examples_used,
            requires_expert_review=requires_expert_review,
            protocols_io_matches=protocol_matches,
        )
        
        # Parse and validate each section
        protocol = Protocol(**plan_data.get("protocol", {}))
        materials = Materials(**plan_data.get("materials", {}))
        timeline = Timeline(**plan_data.get("timeline", {}))
        validation_criteria = ValidationCriteria(**plan_data.get("validation_criteria", {}))
        
        return ExperimentPlan(
            hypothesis=hypothesis,
            domain=domain,
            novelty_classification=novelty_classification,
            protocol=protocol,
            materials=materials,
            timeline=timeline,
            validation_criteria=validation_criteria,
            power_analysis=plan_data.get("power_analysis"),
            safety_assessment=plan_data.get("safety_assessment"),
            variants=self._normalize_variants(plan_data.get("variants")),
            equipment_required=plan_data.get("equipment_required", []),
            metadata=metadata
        )
    
    def _normalize_variants(self, variants: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Normalize AI-generated variants to the expected frontend schema.
        GPT-4o may use different field names (total_cost_usd, timeline_weeks, etc.)
        so we map them to the canonical names (total_budget, timeline_days).
        """
        if not variants or not isinstance(variants, dict):
            return None

        def normalize_one(v: Any) -> Dict[str, Any]:
            if not isinstance(v, dict):
                return {}
            # Resolve total_budget from multiple possible field names
            total_budget = (
                v.get("total_budget")
                or v.get("total_cost_usd")
                or v.get("total_cost")
                or v.get("cost_usd")
                or 0
            )
            # Resolve timeline_days from multiple possible field names
            timeline_days = v.get("timeline_days")
            if timeline_days is None:
                weeks = v.get("timeline_weeks") or v.get("duration_weeks")
                timeline_days = int(weeks) * 7 if weeks is not None else None

            # Resolve materials — may be a list or a dict with items key
            raw_materials = v.get("materials", [])
            if isinstance(raw_materials, list):
                materials = {"items": raw_materials, "total_budget": total_budget, "currency": "USD"}
            elif isinstance(raw_materials, dict):
                materials = raw_materials
                if "total_budget" not in materials:
                    materials["total_budget"] = total_budget
            else:
                materials = {"items": [], "total_budget": total_budget, "currency": "USD"}

            # Resolve protocol_modifications
            protocol_modifications = (
                v.get("protocol_modifications")
                or v.get("key_tradeoffs")
                or v.get("key_advantages")
                or v.get("modifications")
                or []
            )
            if isinstance(protocol_modifications, str):
                protocol_modifications = [protocol_modifications]

            return {
                "total_budget": total_budget,
                "timeline_days": timeline_days,
                "description": v.get("description", ""),
                "materials": materials,
                "protocol_modifications": protocol_modifications,
            }

        result = {}
        for key in ("budget", "standard", "premium"):
            if key in variants:
                result[key] = normalize_one(variants[key])

        return result if result else None

    def _identify_review_flags(self, plan_data: Dict[str, Any]) -> List[str]:
        """
        Identify sections requiring expert review
        
        Args:
            plan_data: Parsed plan JSON
        
        Returns:
            List[str]: List of review flags
        """
        flags = []
        
        # Check for unverified catalog numbers
        materials = plan_data.get("materials", {}).get("items", [])
        unverified = [
            m["name"] for m in materials
            if m.get("verification_status") == "pending_verification"
        ]
        if unverified:
            flags.append(f"Materials: {len(unverified)} items pending verification")
        
        # Check for missing critical parameters
        protocol_steps = plan_data.get("protocol", {}).get("steps", [])
        missing_params = [
            s["step_number"] for s in protocol_steps
            if not s.get("critical_parameters")
        ]
        if missing_params:
            flags.append(f"Protocol: Steps {missing_params} missing critical parameters")
        
        # Check for vague validation criteria
        success_criteria = plan_data.get("validation_criteria", {}).get("success_criteria", [])
        vague_criteria = [
            c["description"] for c in success_criteria
            if not c.get("threshold") or "TBD" in c.get("threshold", "")
        ]
        if vague_criteria:
            flags.append(f"Validation: {len(vague_criteria)} criteria need refinement")
        
        return flags


def get_plan_generator(
    openai_client: OpenAIClient,
    learning_engine: LearningEngine
) -> PlanGenerator:
    """
    Factory function to create PlanGenerator instance
    
    Args:
        openai_client: OpenAI client
        learning_engine: Learning engine
    
    Returns:
        PlanGenerator: Configured generator instance
    """
    return PlanGenerator(openai_client, learning_engine)
