"""
Grant Methods Generator Service
Rewrites experiment protocols as formal grant Methods sections
"""
import logging
from typing import Dict, Any, Optional
from app.services.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class GrantMethodsGenerator:
    """Generates grant Methods sections from experiment plans"""
    
    def __init__(self, openai_client: OpenAIClient):
        """
        Initialize GrantMethodsGenerator
        
        Args:
            openai_client: OpenAI client for GPT-4o
        """
        self.openai_client = openai_client
        
        self.grant_templates = {
            "NIH": {
                "name": "National Institutes of Health R01",
                "style": "NIH R01 grant format",
                "length": "400-600 words"
            },
            "NSF": {
                "name": "National Science Foundation",
                "style": "NSF CAREER grant format",
                "length": "400-600 words"
            },
            "ERC": {
                "name": "European Research Council",
                "style": "ERC Starting Grant format",
                "length": "400-600 words"
            }
        }
    
    async def generate_grant_methods(
        self,
        plan: Dict[str, Any],
        grant_body: str = "NIH"
    ) -> Optional[str]:
        """
        Generate grant Methods section from experiment plan
        
        Args:
            plan: Experiment plan dictionary
            grant_body: Grant body (NIH, NSF, or ERC)
            
        Returns:
            Methods section text or None if generation fails
        """
        try:
            if grant_body not in self.grant_templates:
                logger.warning(f"Unknown grant body: {grant_body}, defaulting to NIH")
                grant_body = "NIH"
            
            template = self.grant_templates[grant_body]
            
            # Extract protocol and materials from plan
            protocol_steps = plan.get("protocol", {}).get("steps", [])
            materials = plan.get("materials", {}).get("items", [])
            validation = plan.get("validation_criteria", {})
            safety = plan.get("safety_assessment", {})
            power_analysis = plan.get("power_analysis", {})
            
            # Build protocol text
            protocol_text = "\n".join([
                f"{i+1}. {step.get('description', step.get('title', ''))}"
                for i, step in enumerate(protocol_steps)
            ])
            
            # Build materials text with catalog numbers
            materials_text = "\n".join([
                f"- {m.get('name', '')}: {m.get('catalog_number', m.get('catalog_no', ''))} ({m.get('supplier', '')})"
                for m in materials
            ])
            
            # Build validation text
            validation_text = ""
            if validation:
                success_criteria = validation.get("success_criteria", [])
                validation_text = "\n".join([
                    f"- {c.get('description', c.get('criterion', ''))}: {c.get('expected_range', c.get('threshold', ''))}"
                    for c in success_criteria
                ])
            
            # Build statistical analysis text
            stats_text = ""
            if power_analysis:
                stats_text = f"""Statistical analysis will be performed using {power_analysis.get('recommended_test', 'appropriate statistical test')}.
Effect size: {power_analysis.get('suggested_effect_size', 'N/A')}
Alpha level: {power_analysis.get('suggested_alpha', 0.05)}
Power: {power_analysis.get('suggested_power', 0.80)}
Sample size: {power_analysis.get('total_sample_size', 'N/A')} ({power_analysis.get('calculated_n_per_group', 'N/A')} per group)"""
            
            # Build IACUC/IRB text
            approval_text = ""
            if safety:
                if safety.get("requires_iacuc"):
                    approval_text += "This study requires IACUC approval for use of vertebrate animals. "
                if safety.get("requires_irb"):
                    approval_text += "This study requires IRB approval for human subjects research. "
            
            # Create prompt for GPT-4o
            prompt = f"""You are an experienced grant writer with a track record of {template['name']} awards.

Rewrite the following experiment plan as a formal Methods section suitable for submission to {template['name']}.

Hypothesis: {plan.get('hypothesis', '')}
Domain: {plan.get('domain', '')}

Protocol Steps:
{protocol_text}

Materials:
{materials_text}

Validation Criteria:
{validation_text}

Statistical Analysis:
{stats_text}

Institutional Approvals:
{approval_text if approval_text else 'No special approvals required.'}

Requirements:
- Write in past tense, third person (e.g., 'Cells were seeded at 5x10^4 per well...')
- All reagents must include source and catalog number on first mention
- Include a statistical analysis paragraph specifying test, alpha, power, and software
- Include institutional approval sentence if applicable
- Target length: {template['length']}
- Use passive voice throughout
- Format for {template['style']}

Output ONLY the Methods section text — no preamble, no headers, no section numbering."""
            
            # Call GPT-4o via the wrapper
            methods_section = await self.openai_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert grant writer specializing in {template['name']} proposals. Write formal, professional Methods sections."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            methods_section = methods_section.strip() if methods_section else None
            logger.info(f"Grant Methods section generated for {grant_body}")
            return methods_section
            
        except Exception as e:
            logger.error(f"Error generating grant methods: {e}")
            return None


# Singleton instance
_grant_methods_generator: Optional[GrantMethodsGenerator] = None


def get_grant_methods_generator(openai_client: OpenAIClient) -> GrantMethodsGenerator:
    """Get or create GrantMethodsGenerator singleton"""
    global _grant_methods_generator
    if _grant_methods_generator is None:
        _grant_methods_generator = GrantMethodsGenerator(openai_client)
    return _grant_methods_generator
