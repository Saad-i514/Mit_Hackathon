"""
Unit tests for HypothesisValidator component.

Run with:
    pytest backend/tests/unit/test_hypothesis_validator.py -v
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestHypothesisValidatorUnit:
    """Unit tests for HypothesisValidator"""

    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client"""
        return AsyncMock()

    def _make_openai_response(self, content: dict):
        """Helper to create a mock chat_completion return value (returns JSON string)"""
        return json.dumps(content)

    @pytest.mark.asyncio
    async def test_valid_molecular_biology_hypothesis(self, mock_openai_client):
        """Should validate a well-formed molecular biology hypothesis"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_openai_client.chat_completion = AsyncMock(
            return_value=self._make_openai_response({
                "is_testable": True,
                "domain": "Molecular Biology",
                "testable_claim": "CRISPR-Cas9 knockout of PCSK9 reduces LDL receptor degradation",
                "clarification_questions": [],
                "reasoning": "Clear measurable outcome with comparison"
            })
        )

        validator = HypothesisValidator(openai_client=mock_openai_client)
        result = await validator.validate(
            "CRISPR-Cas9 knockout of PCSK9 in HepG2 cells will reduce LDL receptor "
            "degradation by 60% compared to scrambled controls, measured by Western blot."
        )

        assert result.is_valid is True
        assert result.domain == "Molecular Biology"
        assert result.testable_claim is not None
        assert len(result.clarification_questions) == 0

    @pytest.mark.asyncio
    async def test_hypothesis_at_character_limit(self, mock_openai_client):
        """Hypothesis at exactly 5000 characters should be accepted"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_openai_client.chat_completion = AsyncMock(
            return_value=self._make_openai_response({
                "is_testable": True,
                "domain": "Cell Biology",
                "testable_claim": "Test claim",
                "clarification_questions": [],
                "reasoning": "Valid"
            })
        )

        validator = HypothesisValidator(openai_client=mock_openai_client)
        hypothesis_at_limit = "A" * 4999 + "."  # 5000 chars
        result = await validator.validate(hypothesis_at_limit)

        # Should call chat_completion (not rejected for length)
        mock_openai_client.chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_hypothesis_exceeds_character_limit(self, mock_openai_client):
        """Hypothesis exceeding 5000 characters should be rejected without calling OpenAI"""
        from app.services.hypothesis_validator import HypothesisValidator

        validator = HypothesisValidator(openai_client=mock_openai_client)
        long_hypothesis = "A" * 5001

        result = await validator.validate(long_hypothesis)

        assert result.is_valid is False
        mock_openai_client.chat.completions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_hypothesis_rejected(self, mock_openai_client):
        """Empty hypothesis should be rejected without calling OpenAI"""
        from app.services.hypothesis_validator import HypothesisValidator

        validator = HypothesisValidator(openai_client=mock_openai_client)

        result = await validator.validate("")

        assert result.is_valid is False
        mock_openai_client.chat.completions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_whitespace_only_hypothesis_rejected(self, mock_openai_client):
        """Whitespace-only hypothesis should be rejected"""
        from app.services.hypothesis_validator import HypothesisValidator

        validator = HypothesisValidator(openai_client=mock_openai_client)

        result = await validator.validate("   \n\t  ")

        assert result.is_valid is False
        mock_openai_client.chat.completions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_ambiguous_hypothesis_generates_questions(self, mock_openai_client):
        """Ambiguous hypothesis should generate clarification questions"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_openai_client.chat_completion = AsyncMock(
            return_value=self._make_openai_response({
                "is_testable": True,
                "domain": "Molecular Biology",
                "testable_claim": "Treatment affects gene expression",
                "clarification_questions": [
                    "What specific gene are you targeting?",
                    "What cell type will you use?",
                    "What concentration of treatment?"
                ],
                "reasoning": "Ambiguous — lacks specifics"
            })
        )

        validator = HypothesisValidator(openai_client=mock_openai_client)
        result = await validator.validate("Treatment will affect gene expression.")

        assert result.is_valid is True
        assert len(result.clarification_questions) == 3

    @pytest.mark.asyncio
    async def test_openai_error_handled_gracefully(self, mock_openai_client):
        """OpenAI API error should be handled gracefully"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_openai_client.chat_completion = AsyncMock(
            side_effect=Exception("OpenAI API error")
        )

        validator = HypothesisValidator(openai_client=mock_openai_client)
        result = await validator.validate("A valid scientific hypothesis about protein folding in E. coli cells.")

        # Should not raise, should return invalid result
        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_domain_extraction_for_neuroscience(self, mock_openai_client):
        """Should correctly extract Neuroscience domain"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_openai_client.chat_completion = AsyncMock(
            return_value=self._make_openai_response({
                "is_testable": True,
                "domain": "Neuroscience",
                "testable_claim": "Fluoxetine increases hippocampal neurogenesis",
                "clarification_questions": [],
                "reasoning": "Clear measurable outcome"
            })
        )

        validator = HypothesisValidator(openai_client=mock_openai_client)
        result = await validator.validate(
            "Chronic fluoxetine administration increases hippocampal neurogenesis in mice."
        )

        assert result.domain == "Neuroscience"

    @pytest.mark.asyncio
    async def test_domain_extraction_for_immunology(self, mock_openai_client):
        """Should correctly extract Immunology domain"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_openai_client.chat_completion = AsyncMock(
            return_value=self._make_openai_response({
                "is_testable": True,
                "domain": "Immunology",
                "testable_claim": "Anti-PD-1 restores T cell function",
                "clarification_questions": [],
                "reasoning": "Clear measurable outcome"
            })
        )

        validator = HypothesisValidator(openai_client=mock_openai_client)
        result = await validator.validate(
            "Anti-PD-1 checkpoint blockade will restore CD8+ T cell cytotoxicity in tumor co-culture."
        )

        assert result.domain == "Immunology"
