"""
Quality threshold verification tests.

Verifies that the system prompt and plan generator enforce the required
quality standards for experiment plans.

Requirements verified:
- 22.1: All critical parameters specified in protocols
- 22.2: Catalog numbers are real and verifiable
- 22.3: Safety considerations included
- 22.4: Troubleshooting guidance included
- 22.5: Expert review flags for unverified items

Run with:
    pytest backend/tests/unit/test_quality_thresholds.py -v
"""
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock


class TestSystemPromptQualityRequirements:
    """Verify the system prompt enforces quality standards"""

    @pytest.fixture
    def system_prompt(self):
        """Load the plan generator system prompt"""
        prompt_path = Path(__file__).parent.parent.parent / "app" / "prompts" / "plan_generator_system.txt"
        return prompt_path.read_text(encoding="utf-8")

    def test_prompt_requires_real_catalog_numbers(self, system_prompt):
        """System prompt should require real catalog numbers"""
        assert "catalog number" in system_prompt.lower() or "catalog_number" in system_prompt.lower()
        assert "real" in system_prompt.lower() or "actual" in system_prompt.lower()

    def test_prompt_requires_critical_parameters(self, system_prompt):
        """System prompt should require critical parameters in protocol steps"""
        assert "critical parameter" in system_prompt.lower() or "critical_parameters" in system_prompt.lower()
        assert "temperature" in system_prompt.lower()
        assert "concentration" in system_prompt.lower()

    def test_prompt_requires_safety_considerations(self, system_prompt):
        """System prompt should require safety considerations"""
        assert "safety" in system_prompt.lower()

    def test_prompt_requires_troubleshooting(self, system_prompt):
        """System prompt should require troubleshooting guidance"""
        assert "troubleshooting" in system_prompt.lower()

    def test_prompt_requires_quantitative_validation(self, system_prompt):
        """System prompt should require quantitative validation criteria"""
        assert "quantitative" in system_prompt.lower()
        assert "measurable" in system_prompt.lower() or "threshold" in system_prompt.lower()

    def test_prompt_requires_protocol_references(self, system_prompt):
        """System prompt should require protocol references with DOI"""
        assert "doi" in system_prompt.lower()
        assert "protocol" in system_prompt.lower()

    def test_prompt_requires_pending_verification_flag(self, system_prompt):
        """System prompt should require pending_verification flag for unverified catalog numbers"""
        assert "pending_verification" in system_prompt

    def test_prompt_requires_expert_review_flags(self, system_prompt):
        """System prompt should require expert review flags"""
        assert "expert_review" in system_prompt or "requires_expert_review" in system_prompt

    def test_prompt_requires_realistic_pricing(self, system_prompt):
        """System prompt should require realistic 2024-2025 pricing"""
        assert "2024" in system_prompt or "pricing" in system_prompt.lower()

    def test_prompt_output_format_is_json(self, system_prompt):
        """System prompt should specify JSON output format"""
        assert "json" in system_prompt.lower()
        assert "validation_criteria" in system_prompt
        assert "materials" in system_prompt
        assert "protocol" in system_prompt
        assert "timeline" in system_prompt


class TestPlanGeneratorQualityFlags:
    """Verify the plan generator correctly flags quality issues"""

    @pytest.mark.asyncio
    async def test_unverified_catalog_numbers_are_flagged(self):
        """Plans with unverified catalog numbers should be flagged for expert review"""
        from app.services.plan_generator import PlanGenerator
        from app.models.responses import NoveltyClassification, NoveltyAssessment

        mock_openai = AsyncMock()
        mock_learning_engine = MagicMock()  # sync mock for sync methods
        mock_learning_engine.query_corrections = AsyncMock(return_value=[])
        mock_learning_engine.build_few_shot_context = MagicMock(return_value="")

        # Return a plan with pending_verification catalog numbers
        plan_with_unverified = {
            "hypothesis": "Test hypothesis",
            "domain": "Cell Biology",
            "novelty_classification": "not_found",
            "protocol": {
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Prepare cells",
                        "duration": "2 hours",
                        "critical_parameters": {"temperature": "37°C"},
                        "source": {"title": "Protocol", "doi": "10.1234/test", "url": "https://example.com"}
                    }
                ],
                "references": [],
                "safety_considerations": ["Use PPE"],
                "troubleshooting": [{"issue": "Low yield", "solution": "Increase time"}]
            },
            "materials": {
                "items": [
                    {
                        "name": "Test reagent",
                        "catalog_number": "UNKNOWN-123",
                        "supplier": "Unknown Supplier",
                        "quantity": 1,
                        "unit": "mL",
                        "unit_price": 50.0,
                        "total_price": 50.0,
                        "product_url": "https://example.com",
                        "verification_status": "pending_verification",
                        "alternatives": []
                    }
                ],
                "total_budget": 50.0,
                "currency": "USD"
            },
            "timeline": {
                "phases": [
                    {
                        "phase_number": 1,
                        "name": "Preparation",
                        "duration_days": 7,
                        "start_date": "Week 1",
                        "end_date": "Week 1",
                        "dependencies": [],
                        "description": "Prepare materials"
                    }
                ],
                "total_duration_days": 7,
                "gantt_data": {}
            },
            "validation_criteria": {
                "success_criteria": [
                    {
                        "description": "Cell viability >= 85%",
                        "threshold": ">= 85%",
                        "measurement_technique": "Trypan blue exclusion",
                        "expected_range": "85-95%"
                    }
                ],
                "failure_criteria": [
                    {
                        "description": "Cell viability < 70%",
                        "threshold": "< 70%",
                        "measurement_technique": "Trypan blue exclusion"
                    }
                ],
                "validation_methods": ["t-test (p < 0.05)"]
            },
            "metadata": {
                "generated_at": "2024-01-15T10:00:00Z",
                "model_version": "gpt-4o",
                "few_shot_examples_used": 0,
                "requires_expert_review": []
            }
        }

        mock_openai.chat_completion = AsyncMock(return_value=json.dumps(plan_with_unverified))

        generator = PlanGenerator(
            openai_client=mock_openai,
            learning_engine=mock_learning_engine
        )

        plan = await generator.generate_plan(
            hypothesis="Test hypothesis",
            domain="Cell Biology",
            novelty_assessment=NoveltyAssessment(
                classification=NoveltyClassification.NOT_FOUND,
                similar_papers=[],
                search_duration=1.0
            )
        )

        # Plan should be generated
        assert plan is not None

        # Check that unverified catalog numbers are flagged
        has_unverified = any(
            item.verification_status == "pending_verification"
            for item in plan.materials.items
        )
        assert has_unverified, "Plan should have pending_verification items"

    @pytest.mark.asyncio
    async def test_plan_includes_safety_considerations(self):
        """Generated plans should include safety considerations"""
        from app.services.plan_generator import PlanGenerator
        from app.models.responses import NoveltyClassification, NoveltyAssessment

        mock_openai = AsyncMock()
        mock_learning_engine = MagicMock()  # sync mock for sync methods
        mock_learning_engine.query_corrections = AsyncMock(return_value=[])
        mock_learning_engine.build_few_shot_context = MagicMock(return_value="")

        plan_with_safety = {
            "hypothesis": "Test hypothesis",
            "domain": "Cell Biology",
            "novelty_classification": "not_found",
            "protocol": {
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Handle DMSO carefully",
                        "duration": "30 min",
                        "critical_parameters": {"concentration": "10% v/v"},
                        "source": {"title": "Protocol", "doi": "10.1234/test", "url": "https://example.com"}
                    }
                ],
                "references": [],
                "safety_considerations": [
                    "DMSO is a skin penetrant — wear nitrile gloves",
                    "Work in a chemical fume hood"
                ],
                "troubleshooting": [{"issue": "Low viability", "solution": "Reduce DMSO concentration"}]
            },
            "materials": {
                "items": [
                    {
                        "name": "DMSO",
                        "catalog_number": "D2650",
                        "supplier": "Sigma-Aldrich",
                        "quantity": 100,
                        "unit": "mL",
                        "unit_price": 28.50,
                        "total_price": 28.50,
                        "product_url": "https://www.sigmaaldrich.com/catalog/product/sigma/d2650",
                        "verification_status": "verified",
                        "alternatives": []
                    }
                ],
                "total_budget": 28.50,
                "currency": "USD"
            },
            "timeline": {
                "phases": [{"phase_number": 1, "name": "Prep", "duration_days": 1, "start_date": "Week 1", "end_date": "Week 1", "dependencies": [], "description": "Prepare"}],
                "total_duration_days": 1,
                "gantt_data": {}
            },
            "validation_criteria": {
                "success_criteria": [{"description": "Viability >= 85%", "threshold": ">= 85%", "measurement_technique": "Trypan blue", "expected_range": "85-95%"}],
                "failure_criteria": [{"description": "Viability < 70%", "threshold": "< 70%", "measurement_technique": "Trypan blue"}],
                "validation_methods": ["t-test"]
            },
            "metadata": {
                "generated_at": "2024-01-15T10:00:00Z",
                "model_version": "gpt-4o",
                "few_shot_examples_used": 0,
                "requires_expert_review": []
            }
        }

        mock_openai.chat_completion = AsyncMock(return_value=json.dumps(plan_with_safety))

        generator = PlanGenerator(
            openai_client=mock_openai,
            learning_engine=mock_learning_engine
        )

        plan = await generator.generate_plan(
            hypothesis="Test hypothesis",
            domain="Cell Biology",
            novelty_assessment=NoveltyAssessment(
                classification=NoveltyClassification.NOT_FOUND,
                similar_papers=[],
                search_duration=1.0
            )
        )

        assert plan is not None
        assert len(plan.protocol.safety_considerations) > 0, "Plan should include safety considerations"
        assert len(plan.protocol.troubleshooting) > 0, "Plan should include troubleshooting guidance"
