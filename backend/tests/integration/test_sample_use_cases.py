"""
Sample use case tests for the AI Scientist Platform.

Tests the four primary use cases from the requirements:
1. Diagnostics - paper-based biosensors
2. Gut health - probiotic effects
3. Cell biology - cryoprotectant comparison
4. Climate science - CO2 fixation

These tests use mocked AI components to verify the pipeline handles
each domain correctly without requiring real API keys.

Run with:
    pytest backend/tests/integration/test_sample_use_cases.py -v --timeout=60
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock


# Sample hypotheses from the requirements
SAMPLE_HYPOTHESES = {
    "diagnostics": (
        "Paper-based biosensors functionalized with anti-CRP antibodies will detect "
        "C-reactive protein at concentrations as low as 1 ng/mL in whole blood within "
        "15 minutes, validated by ELISA comparison with R² > 0.95."
    ),
    "gut_health": (
        "Daily oral administration of Lactobacillus rhamnosus GG at 10^9 CFU for 8 weeks "
        "will reduce intestinal permeability in C57BL/6 mice fed a high-fat diet by at least "
        "40% compared to vehicle controls, measured by FITC-dextran permeability assay."
    ),
    "cell_biology": (
        "DMSO at 10% v/v will provide superior cryoprotection compared to glycerol at 10% v/v "
        "for HeLa cell cryopreservation, resulting in ≥ 85% post-thaw viability measured by "
        "trypan blue exclusion after 6 months at -80°C."
    ),
    "climate_science": (
        "Engineered Synechococcus elongatus PCC 7942 expressing a heterologous RuBisCO variant "
        "with 20% higher carboxylation efficiency will fix CO2 at a rate 30% greater than "
        "wild-type under 400 ppm CO2 and 200 µmol photons/m²/s, measured by 14C incorporation."
    ),
}

# Expected domain mappings
EXPECTED_DOMAINS = {
    "diagnostics": ["diagnostics", "Diagnostics", "Biochemistry", "Cell Biology"],
    "gut_health": ["gut_health", "Microbiology", "Immunology", "Physiology"],
    "cell_biology": ["cell_biology", "Cell Biology"],
    "climate_science": ["climate_science", "Synthetic Biology", "Biochemistry"],
}


class TestDiagnosticsUseCase:
    """Test the diagnostics biosensor hypothesis"""

    @pytest.mark.asyncio
    async def test_diagnostics_hypothesis_is_valid(self):
        """Diagnostics hypothesis should be validated as testable"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_client = AsyncMock()
        mock_client.chat_completion = AsyncMock(
            return_value=json.dumps({
                "is_testable": True,
                "domain": "diagnostics",
                "testable_claim": "Paper biosensor detects CRP at 1 ng/mL within 15 minutes",
                "clarification_questions": [],
                "reasoning": "Clear measurable outcome with quantitative threshold and validation method"
            })
        )

        validator = HypothesisValidator(openai_client=mock_client)
        result = await validator.validate(SAMPLE_HYPOTHESES["diagnostics"])

        assert result.is_valid is True
        assert result.domain is not None
        assert len(result.clarification_questions) == 0

    @pytest.mark.asyncio
    async def test_diagnostics_hypothesis_length_is_valid(self):
        """Diagnostics hypothesis should be within character limit"""
        hypothesis = SAMPLE_HYPOTHESES["diagnostics"]
        assert len(hypothesis) <= 5000, f"Hypothesis is {len(hypothesis)} chars, max 5000"
        assert len(hypothesis.strip()) >= 20, "Hypothesis is too short"


class TestGutHealthUseCase:
    """Test the gut health probiotic hypothesis"""

    @pytest.mark.asyncio
    async def test_gut_health_hypothesis_is_valid(self):
        """Gut health hypothesis should be validated as testable"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_client = AsyncMock()
        mock_client.chat_completion = AsyncMock(
            return_value=json.dumps({
                "is_testable": True,
                "domain": "gut_health",
                "testable_claim": "L. rhamnosus GG reduces intestinal permeability by 40%",
                "clarification_questions": [],
                "reasoning": "Specific organism, dose, duration, and measurable outcome"
            })
        )

        validator = HypothesisValidator(openai_client=mock_client)
        result = await validator.validate(SAMPLE_HYPOTHESES["gut_health"])

        assert result.is_valid is True
        assert result.testable_claim is not None

    @pytest.mark.asyncio
    async def test_gut_health_hypothesis_length_is_valid(self):
        """Gut health hypothesis should be within character limit"""
        hypothesis = SAMPLE_HYPOTHESES["gut_health"]
        assert len(hypothesis) <= 5000


class TestCellBiologyUseCase:
    """Test the cell biology cryoprotectant hypothesis"""

    @pytest.mark.asyncio
    async def test_cell_biology_hypothesis_is_valid(self):
        """Cell biology hypothesis should be validated as testable"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_client = AsyncMock()
        mock_client.chat_completion = AsyncMock(
            return_value=json.dumps({
                "is_testable": True,
                "domain": "cell_biology",
                "testable_claim": "DMSO provides ≥85% post-thaw viability vs glycerol",
                "clarification_questions": [],
                "reasoning": "Direct comparison with quantitative threshold"
            })
        )

        validator = HypothesisValidator(openai_client=mock_client)
        result = await validator.validate(SAMPLE_HYPOTHESES["cell_biology"])

        assert result.is_valid is True
        assert result.testable_claim is not None

    @pytest.mark.asyncio
    async def test_cell_biology_novelty_assessment(self):
        """Cell biology hypothesis should get a novelty assessment"""
        from app.services.literature_qc import LiteratureQCEngine

        mock_openai = AsyncMock()
        mock_openai.chat_completion = AsyncMock(
            return_value=json.dumps({
                "classification": "similar_exists",
                "reasoning": "Related cryoprotectant comparison studies exist",
                "similar_papers": [
                    {
                        "title": "Comparison of cryoprotectants for mammalian cell lines",
                        "year": 2021,
                        "doi": "10.1016/j.cryobiol.2021.01.001"
                    }
                ]
            })
        )

        mock_ss_client = AsyncMock()
        mock_serper_client = AsyncMock()

        engine = LiteratureQCEngine(
            semantic_scholar_client=mock_ss_client,
            serper_client=mock_serper_client,
            openai_client=mock_openai
        )

        # Patch the search methods directly
        engine._search_semantic_scholar = AsyncMock(return_value=[])
        engine._search_serper = AsyncMock(return_value=[])

        result = await engine.assess_novelty(
            hypothesis=SAMPLE_HYPOTHESES["cell_biology"],
            domain="cell_biology"
        )

        assert result.classification is not None
        assert result.classification.value in ["not_found", "similar_exists", "exact_match"]


class TestClimateScienceUseCase:
    """Test the climate science CO2 fixation hypothesis"""

    @pytest.mark.asyncio
    async def test_climate_science_hypothesis_is_valid(self):
        """Climate science hypothesis should be validated as testable"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_client = AsyncMock()
        mock_client.chat_completion = AsyncMock(
            return_value=json.dumps({
                "is_testable": True,
                "domain": "climate_science",
                "testable_claim": "Engineered RuBisCO variant increases CO2 fixation by 30%",
                "clarification_questions": [],
                "reasoning": "Specific organism, genetic modification, and measurable CO2 fixation rate"
            })
        )

        validator = HypothesisValidator(openai_client=mock_client)
        result = await validator.validate(SAMPLE_HYPOTHESES["climate_science"])

        assert result.is_valid is True
        assert result.testable_claim is not None

    @pytest.mark.asyncio
    async def test_climate_science_hypothesis_length_is_valid(self):
        """Climate science hypothesis should be within character limit"""
        hypothesis = SAMPLE_HYPOTHESES["climate_science"]
        assert len(hypothesis) <= 5000


class TestAllSampleHypotheses:
    """Cross-cutting tests for all sample hypotheses"""

    @pytest.mark.parametrize("use_case,hypothesis", SAMPLE_HYPOTHESES.items())
    def test_all_hypotheses_within_character_limit(self, use_case, hypothesis):
        """All sample hypotheses should be within the 5000 character limit"""
        assert len(hypothesis) <= 5000, (
            f"{use_case} hypothesis is {len(hypothesis)} chars, max 5000"
        )

    @pytest.mark.parametrize("use_case,hypothesis", SAMPLE_HYPOTHESES.items())
    def test_all_hypotheses_have_measurable_outcomes(self, use_case, hypothesis):
        """All sample hypotheses should contain quantitative measurements"""
        # Check for common quantitative indicators
        quantitative_indicators = [
            "%", "ng/mL", "CFU", "µmol", "ppm", "°C", "R²",
            "fold", "times", "ratio", "concentration"
        ]
        has_quantitative = any(indicator in hypothesis for indicator in quantitative_indicators)
        assert has_quantitative, (
            f"{use_case} hypothesis lacks quantitative measurements: {hypothesis[:100]}..."
        )

    @pytest.mark.parametrize("use_case,hypothesis", SAMPLE_HYPOTHESES.items())
    def test_all_hypotheses_have_comparison(self, use_case, hypothesis):
        """All sample hypotheses should specify a comparison or control"""
        comparison_indicators = [
            "compared to", "versus", "vs", "control", "wild-type",
            "vehicle", "compared with", "relative to", "comparison",
            "greater than", "superior"
        ]
        has_comparison = any(
            indicator.lower() in hypothesis.lower()
            for indicator in comparison_indicators
        )
        assert has_comparison, (
            f"{use_case} hypothesis lacks a comparison/control: {hypothesis[:100]}..."
        )

    @pytest.mark.parametrize("use_case,hypothesis", SAMPLE_HYPOTHESES.items())
    def test_all_hypotheses_specify_measurement_method(self, use_case, hypothesis):
        """All sample hypotheses should specify how the outcome will be measured"""
        measurement_indicators = [
            "measured by", "assay", "staining", "blot", "PCR", "ELISA",
            "spectroscopy", "microscopy", "sequencing", "incorporation",
            "exclusion", "permeability"
        ]
        has_measurement = any(
            indicator.lower() in hypothesis.lower()
            for indicator in measurement_indicators
        )
        assert has_measurement, (
            f"{use_case} hypothesis lacks measurement method: {hypothesis[:100]}..."
        )
