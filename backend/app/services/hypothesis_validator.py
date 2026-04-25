"""
Hypothesis Validator Component
Validates scientific hypotheses and extracts domain information
"""
import json
import logging
from typing import List, Optional
from app.services.openai_client import OpenAIClient
from app.models.responses import ValidationResult


logger = logging.getLogger(__name__)


class HypothesisValidator:
    """Validates scientific hypotheses and extracts domain information"""
    
    # 20 supported scientific domains
    DOMAIN_TAXONOMY = [
        "diagnostics",
        "gut_health",
        "cell_biology",
        "climate_science",
        "materials_science",
        "neuroscience",
        "immunology",
        "microbiology",
        "genetics",
        "biochemistry",
        "pharmacology",
        "toxicology",
        "ecology",
        "bioinformatics",
        "synthetic_biology",
        "tissue_engineering",
        "regenerative_medicine",
        "cancer_biology",
        "virology",
        "structural_biology"
    ]
    
    def __init__(self, openai_client: OpenAIClient):
        """
        Initialize HypothesisValidator
        
        Args:
            openai_client: OpenAI client for GPT-4o calls
        """
        self.openai_client = openai_client
    
    async def validate(self, hypothesis: str) -> ValidationResult:
        """
        Validate hypothesis and extract domain
        
        Args:
            hypothesis: Scientific hypothesis text
        
        Returns:
            ValidationResult with validation status, domain, testable claim, etc.
        """
        # Step 1: Length validation
        if len(hypothesis) > 5000:
            return ValidationResult(
                is_valid=False,
                error_message="Hypothesis exceeds 5000 character limit",
                domain=None,
                testable_claim=None,
                clarification_questions=[],
                reasoning="Input validation failed"
            )
        
        if len(hypothesis.strip()) < 20:
            return ValidationResult(
                is_valid=False,
                error_message="Hypothesis must be at least 20 characters long",
                domain=None,
                testable_claim=None,
                clarification_questions=[],
                reasoning="Input validation failed"
            )
        
        # Step 2: Extract domain and validate testability using GPT-4o
        try:
            prompt = self._build_validation_prompt(hypothesis)
            
            response = await self.openai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            return ValidationResult(
                is_valid=result.get("is_testable", False),
                domain=result.get("domain"),
                testable_claim=result.get("testable_claim"),
                clarification_questions=result.get("clarification_questions", []),
                error_message=None if result.get("is_testable") else "Hypothesis is not testable or lacks measurable outcomes",
                reasoning=result.get("reasoning")
            )
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4o response: {e}")
            return ValidationResult(
                is_valid=False,
                error_message="Failed to validate hypothesis due to parsing error",
                domain=None,
                testable_claim=None,
                clarification_questions=[],
                reasoning="JSON parsing failed"
            )
        
        except Exception as e:
            logger.error(f"Hypothesis validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation failed: {str(e)}",
                domain=None,
                testable_claim=None,
                clarification_questions=[],
                reasoning="Unexpected error"
            )
    
    def _build_validation_prompt(self, hypothesis: str) -> str:
        """
        Build validation prompt for GPT-4o
        
        Args:
            hypothesis: Scientific hypothesis text
        
        Returns:
            str: Formatted prompt
        """
        return f"""Analyze this scientific hypothesis and determine if it is testable and falsifiable.

Hypothesis: "{hypothesis}"

Tasks:
1. Identify the scientific domain from this list: {', '.join(self.DOMAIN_TAXONOMY)}
2. Extract the testable claim (must be falsifiable and measurable)
3. Determine if the hypothesis is testable (has clear success/failure criteria)
4. If ambiguous or incomplete, generate 2-3 specific clarification questions

Return JSON with this exact structure:
{{
  "domain": "domain_name",
  "testable_claim": "extracted claim with measurable outcomes",
  "is_testable": true/false,
  "clarification_questions": ["question1", "question2"],
  "reasoning": "brief explanation of your assessment"
}}

Requirements for testability:
- Must have measurable outcomes (percentages, concentrations, counts, etc.)
- Must be falsifiable (can prove it wrong)
- Must specify conditions or comparisons
- Must be specific enough to design an experiment

If the hypothesis is vague, lacks measurable outcomes, or is not falsifiable, set is_testable to false and provide clarification questions."""


def get_hypothesis_validator(openai_client: OpenAIClient) -> HypothesisValidator:
    """
    Factory function to create HypothesisValidator instance
    
    Args:
        openai_client: OpenAI client instance
    
    Returns:
        HypothesisValidator: Configured validator instance
    """
    return HypothesisValidator(openai_client)
