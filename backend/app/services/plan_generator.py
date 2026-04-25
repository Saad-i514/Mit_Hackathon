"""
Plan Generator Component
Generates complete experiment plans using GPT-4o with few-shot learning
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.services.openai_client import OpenAIClient
from app.services.learning_engine import LearningEngine, FeedbackEmbedding
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
        novelty_assessment: NoveltyAssessment
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
                few_shot_context=few_shot_context
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
            
            # Validate and construct ExperimentPlan
            plan = self._construct_experiment_plan(
                plan_data=plan_data,
                hypothesis=hypothesis,
                domain=domain,
                novelty_classification=novelty_assessment.classification,
                few_shot_examples_used=len(similar_corrections)
            )
            
            logger.info(f"Generated experiment plan for domain {domain} with {len(similar_corrections)} few-shot examples")
            
            return plan
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4o response: {e}")
            raise Exception(f"Plan generation failed: Invalid JSON response")
        
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            raise Exception(f"Plan generation failed: {str(e)}")
    
    def _build_user_prompt(
        self,
        hypothesis: str,
        domain: str,
        novelty_assessment: NoveltyAssessment,
        few_shot_context: str
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
        
        prompt = f"""Generate a complete, operationally realistic experiment plan for this hypothesis:

Hypothesis: "{hypothesis}"
Domain: {domain}
{literature_context}
{few_shot_context}

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
        few_shot_examples_used: int
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
            generated_at=datetime.utcnow().isoformat(),
            model_version="gpt-4o",
            few_shot_examples_used=few_shot_examples_used,
            requires_expert_review=requires_expert_review
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
            metadata=metadata
        )
    
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
