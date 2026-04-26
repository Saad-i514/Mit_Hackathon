"""
Safety Assessment Service
Generates risk and safety assessments using GPT-4o and PubChem GHS data
"""
import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from app.services.openai_client import OpenAIClient
from app.services.pubchem import get_pubchem_client, PubChemClient

logger = logging.getLogger(__name__)


class HazardousReagent(BaseModel):
    """Hazardous reagent with GHS information"""
    name: str
    ghs_codes: List[str]
    hazard: str
    ppe_addition: str
    disposal: str


class SafetyAssessment(BaseModel):
    """Complete safety assessment for an experiment"""
    bsl_level: int  # 1-4
    bsl_rationale: str
    requires_iacuc: bool
    requires_irb: bool
    requires_biosafety_committee: bool
    ppe_required: List[str]
    hazardous_reagents: List[HazardousReagent]
    waste_disposal: Dict[str, str]
    emergency_contacts: List[str]


class SafetyAssessor:
    """Generates safety assessments for experiment plans"""
    
    def __init__(self, openai_client: OpenAIClient):
        """
        Initialize SafetyAssessor
        
        Args:
            openai_client: OpenAI client for GPT-4o
        """
        self.openai_client = openai_client
        self.pubchem_client: PubChemClient = get_pubchem_client()
    
    async def assess_safety(self, plan: Dict[str, Any]) -> Optional[SafetyAssessment]:
        """
        Generate safety assessment for an experiment plan
        
        Args:
            plan: Experiment plan dictionary
            
        Returns:
            SafetyAssessment object or None if assessment fails
        """
        try:
            # Extract materials from plan
            materials = plan.get("materials", {}).get("items", [])
            protocol = plan.get("protocol", {}).get("steps", [])
            
            # Build context for GPT-4o
            materials_text = "\n".join([
                f"- {m.get('name', '')}: {m.get('catalog_no', '')}"
                for m in materials
            ])
            
            protocol_text = "\n".join([
                f"- {s.get('title', '')}: {s.get('description', '')}"
                for s in protocol[:5]  # First 5 steps
            ])
            
            # Call GPT-4o for safety assessment
            prompt = f"""You are a laboratory safety expert. Assess the safety requirements for this experiment:

Hypothesis: {plan.get('hypothesis', '')}
Domain: {plan.get('domain', '')}

Materials:
{materials_text}

Protocol (first 5 steps):
{protocol_text}

Provide a JSON safety assessment with:
- bsl_level (1-4): Biosafety level required
- bsl_rationale: Why this BSL level
- requires_iacuc (true/false): If vertebrate animals used
- requires_irb (true/false): If human subjects used
- requires_biosafety_committee (true/false): If BSL-2+
- ppe_required: List of required PPE items
- hazardous_reagents: List of hazardous materials with GHS codes
- waste_disposal: Dict of waste categories and disposal methods
- emergency_contacts: List of emergency contact guidance

Return ONLY valid JSON."""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a laboratory safety expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # Parse response
            assessment_data = json.loads(response.choices[0].message.content)
            
            # Enrich with PubChem GHS data for hazardous reagents
            hazardous_reagents = []
            for reagent in assessment_data.get("hazardous_reagents", []):
                try:
                    # Query PubChem for GHS codes
                    pubchem_data = await self.pubchem_client.enrich_reagent(reagent.get("name", ""))
                    
                    if pubchem_data.get("pubchem_found"):
                        ghs_codes = pubchem_data.get("ghs_codes", [])
                    else:
                        ghs_codes = reagent.get("ghs_codes", [])
                    
                    hazardous_reagents.append(HazardousReagent(
                        name=reagent.get("name", ""),
                        ghs_codes=ghs_codes,
                        hazard=reagent.get("hazard", ""),
                        ppe_addition=reagent.get("ppe_addition", ""),
                        disposal=reagent.get("disposal", "")
                    ))
                except Exception as e:
                    logger.warning(f"Error enriching reagent {reagent.get('name', '')}: {e}")
                    hazardous_reagents.append(HazardousReagent(
                        name=reagent.get("name", ""),
                        ghs_codes=reagent.get("ghs_codes", []),
                        hazard=reagent.get("hazard", ""),
                        ppe_addition=reagent.get("ppe_addition", ""),
                        disposal=reagent.get("disposal", "")
                    ))
            
            # Create SafetyAssessment object
            safety_assessment = SafetyAssessment(
                bsl_level=assessment_data.get("bsl_level", 1),
                bsl_rationale=assessment_data.get("bsl_rationale", ""),
                requires_iacuc=assessment_data.get("requires_iacuc", False),
                requires_irb=assessment_data.get("requires_irb", False),
                requires_biosafety_committee=assessment_data.get("requires_biosafety_committee", False),
                ppe_required=assessment_data.get("ppe_required", []),
                hazardous_reagents=hazardous_reagents,
                waste_disposal=assessment_data.get("waste_disposal", {}),
                emergency_contacts=assessment_data.get("emergency_contacts", [])
            )
            
            logger.info(f"Safety assessment completed: BSL-{safety_assessment.bsl_level}")
            return safety_assessment
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse safety assessment JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error assessing safety: {e}")
            return None


# Singleton instance
_safety_assessor: Optional[SafetyAssessor] = None


def get_safety_assessor(openai_client: OpenAIClient) -> SafetyAssessor:
    """Get or create SafetyAssessor singleton"""
    global _safety_assessor
    if _safety_assessor is None:
        _safety_assessor = SafetyAssessor(openai_client)
    return _safety_assessor
