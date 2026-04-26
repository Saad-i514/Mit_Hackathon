"""
Lab Notebook Generator Service
Generates pre-filled electronic lab notebook templates from experiment plans
"""
import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from app.services.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class NotebookSection(BaseModel):
    """A section of the lab notebook"""
    title: str
    instructions: str
    fields: List[Dict[str, Any]]


class NotebookTemplate(BaseModel):
    """Complete lab notebook template"""
    header: Dict[str, Any]
    objective: str
    materials_receipt: List[Dict[str, Any]]
    protocol_steps: List[Dict[str, Any]]
    raw_data_tables: List[Dict[str, Any]]
    statistical_analysis: Dict[str, Any]
    conclusions: Dict[str, Any]
    deviations_log: str


class NotebookGenerator:
    """Generates lab notebook templates from experiment plans"""
    
    def __init__(self, openai_client: OpenAIClient):
        """
        Initialize NotebookGenerator
        
        Args:
            openai_client: OpenAI client for GPT-4o
        """
        self.openai_client = openai_client
    
    async def generate_notebook(self, plan: Dict[str, Any]) -> Optional[NotebookTemplate]:
        """
        Generate lab notebook template from experiment plan
        
        Args:
            plan: Experiment plan dictionary
            
        Returns:
            NotebookTemplate object or None if generation fails
        """
        try:
            # Extract plan components
            hypothesis = plan.get("hypothesis", "")
            domain = plan.get("domain", "")
            protocol_steps = plan.get("protocol", {}).get("steps", [])
            materials = plan.get("materials", {}).get("items", [])
            validation = plan.get("validation_criteria", {})
            power_analysis = plan.get("power_analysis", {})
            
            # Build context for GPT-4o
            protocol_text = "\n".join([
                f"{i+1}. {step.get('description', step.get('title', ''))}"
                for i, step in enumerate(protocol_steps)
            ])
            
            materials_text = "\n".join([
                f"- {m.get('name', '')}: {m.get('catalog_number', m.get('catalog_no', ''))} ({m.get('supplier', '')})"
                for m in materials
            ])
            
            # Create prompt for GPT-4o
            prompt = f"""Generate a structured lab notebook template as JSON for this experiment:

Hypothesis: {hypothesis}
Domain: {domain}

Protocol Steps:
{protocol_text}

Materials:
{materials_text}

Create a JSON notebook with these sections:
1. header: {{hypothesis, pi_name, date, experiment_id, start_date, lab_location}}
2. objective: Brief objective text
3. materials_receipt: Array of {{name, catalog_no, supplier, lot_number, expiry_date, actual_supplier}}
4. protocol_steps: Array of {{step_number, title, observation_field}}
5. raw_data_tables: Array of {{table_name, columns, rows}}
6. statistical_analysis: {{test_name, alpha, n, p_value_field, ci_field}}
7. conclusions: {{expected_outcome, actual_outcome}}
8. deviations_log: Empty string for scientist to fill in

Return ONLY valid JSON with all fields pre-populated where possible."""
            
            # Call GPT-4o via the wrapper
            raw_response = await self.openai_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a laboratory notebook expert. Generate structured notebook templates as valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            notebook_data = json.loads(raw_response)
            
            # Create NotebookTemplate object
            notebook = NotebookTemplate(
                header={
                    "hypothesis": hypothesis,
                    "pi_name": notebook_data.get("header", {}).get("pi_name", ""),
                    "date": notebook_data.get("header", {}).get("date", ""),
                    "experiment_id": plan.get("id", ""),
                    "start_date": "",  # To be filled by scientist
                    "lab_location": ""  # To be filled by scientist
                },
                objective=notebook_data.get("objective", ""),
                materials_receipt=[
                    {
                        "name": m.get("name", ""),
                        "catalog_no": m.get("catalog_number", m.get("catalog_no", "")),
                        "supplier": m.get("supplier", ""),
                        "lot_number": "",  # To be filled by scientist
                        "expiry_date": "",  # To be filled by scientist
                        "actual_supplier": ""  # To be filled by scientist
                    }
                    for m in materials
                ],
                protocol_steps=[
                    {
                        "step_number": i + 1,
                        "title": step.get("description", step.get("title", "")),
                        "description": step.get("description", ""),
                        "observation_field": ""  # To be filled by scientist
                    }
                    for i, step in enumerate(protocol_steps)
                ],
                raw_data_tables=notebook_data.get("raw_data_tables", []),
                statistical_analysis={
                    "test_name": power_analysis.get("recommended_test", ""),
                    "alpha": power_analysis.get("suggested_alpha", 0.05),
                    "n": power_analysis.get("total_sample_size", ""),
                    "p_value_field": "",  # To be filled by scientist
                    "ci_field": ""  # To be filled by scientist
                },
                conclusions={
                    "expected_outcome": validation.get("success_criteria", [{}])[0].get("criterion", ""),
                    "actual_outcome": ""  # To be filled by scientist
                },
                deviations_log=""  # To be filled by scientist
            )
            
            logger.info("Lab notebook template generated")
            return notebook
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse notebook JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating notebook: {e}")
            return None


# Singleton instance
_notebook_generator: Optional[NotebookGenerator] = None


def get_notebook_generator(openai_client: OpenAIClient) -> NotebookGenerator:
    """Get or create NotebookGenerator singleton"""
    global _notebook_generator
    if _notebook_generator is None:
        _notebook_generator = NotebookGenerator(openai_client)
    return _notebook_generator
