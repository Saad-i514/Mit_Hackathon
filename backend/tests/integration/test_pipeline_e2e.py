"""
End-to-end integration tests for the AI Scientist Platform pipeline.

These tests verify the complete flow from hypothesis submission through
plan generation, including SSE streaming and database storage.

Run with:
    pytest backend/tests/integration/ -v --timeout=120

Requires environment variables:
    OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY,
    SEMANTIC_SCHOLAR_API_KEY, SERPER_API_KEY
"""
import asyncio
import json
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator, Dict, Any

# Skip all tests if required env vars are not set
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set — skipping integration tests"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_hypotheses():
    """Sample hypotheses for testing across domains"""
    return {
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


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI response for validation"""
    return {
        "is_valid": True,
        "domain": "Cell Biology",
        "testable_claim": "DMSO provides better cryoprotection than glycerol for HeLa cells",
        "clarification_questions": [],
        "confidence_score": 0.95
    }


@pytest.fixture
def mock_novelty_response():
    """Mock novelty assessment response"""
    return {
        "classification": "similar_exists",
        "similar_papers": [
            {
                "title": "Cryoprotectant comparison for mammalian cell lines",
                "authors": ["Smith, J.", "Jones, A."],
                "year": 2022,
                "doi": "10.1016/j.cryobiol.2022.01.001",
                "relevance_score": 0.78
            }
        ],
        "search_duration": 4.2,
        "sources_searched": ["semantic_scholar", "serper"]
    }


# ---------------------------------------------------------------------------
# Unit-level integration tests (mocked external APIs)
# ---------------------------------------------------------------------------

class TestHypothesisValidatorIntegration:
    """Integration tests for HypothesisValidator with mocked OpenAI"""

    @pytest.mark.asyncio
    async def test_valid_hypothesis_returns_domain(self, sample_hypotheses):
        """Valid hypothesis should return domain and testable claim"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_client = AsyncMock()
        mock_client.chat_completion = AsyncMock(return_value=json.dumps({
            "is_testable": True,
            "domain": "Cell Biology",
            "testable_claim": "DMSO provides better cryoprotection than glycerol",
            "clarification_questions": [],
            "reasoning": "Clear measurable outcome"
        }))

        validator = HypothesisValidator(openai_client=mock_client)
        result = await validator.validate(sample_hypotheses["cell_biology"])

        assert result.is_valid is True
        assert result.domain == "Cell Biology"
        assert result.testable_claim is not None
        assert len(result.clarification_questions) == 0

    @pytest.mark.asyncio
    async def test_hypothesis_too_long_is_rejected(self):
        """Hypothesis exceeding 5000 characters should be rejected"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_client = AsyncMock()
        validator = HypothesisValidator(openai_client=mock_client)

        long_hypothesis = "A" * 5001
        result = await validator.validate(long_hypothesis)

        assert result.is_valid is False
        # OpenAI should NOT be called for length validation
        mock_client.chat_completion.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_hypothesis_is_rejected(self):
        """Empty hypothesis should be rejected without calling OpenAI"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_client = AsyncMock()
        validator = HypothesisValidator(openai_client=mock_client)

        result = await validator.validate("")

        assert result.is_valid is False
        mock_client.chat_completion.assert_not_called()

    @pytest.mark.asyncio
    async def test_ambiguous_hypothesis_generates_questions(self):
        """Ambiguous hypothesis should generate clarification questions"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_client = AsyncMock()
        mock_client.chat_completion = AsyncMock(return_value=json.dumps({
            "is_testable": True,
            "domain": "Molecular Biology",
            "testable_claim": "Treatment affects gene expression",
            "clarification_questions": [
                "What specific gene are you targeting?",
                "What cell type or organism will you use?",
                "What concentration of treatment will you apply?"
            ],
            "reasoning": "Ambiguous — lacks specifics"
        }))

        validator = HypothesisValidator(openai_client=mock_client)
        result = await validator.validate("Treatment will affect gene expression in cells.")

        assert result.is_valid is True
        assert len(result.clarification_questions) > 0


class TestLiteratureQCIntegration:
    """Integration tests for LiteratureQCEngine with mocked external APIs"""

    @pytest.mark.asyncio
    async def test_novelty_classification_not_found(self):
        """Should classify as not_found when no papers match"""
        from app.services.literature_qc import LiteratureQCEngine

        mock_openai = AsyncMock()
        mock_openai.chat_completion = AsyncMock(return_value=json.dumps({
            "classification": "not_found",
            "reasoning": "No closely related work found",
            "similar_papers": []
        }))

        mock_ss = AsyncMock()
        mock_serper = AsyncMock()

        engine = LiteratureQCEngine(
            semantic_scholar_client=mock_ss,
            serper_client=mock_serper,
            openai_client=mock_openai
        )
        engine._search_semantic_scholar = AsyncMock(return_value=[])
        engine._search_serper = AsyncMock(return_value=[])

        result = await engine.assess_novelty(
            hypothesis="A completely novel hypothesis with no prior work",
            domain="Synthetic Biology"
        )

        assert result.classification.value == "not_found"

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Should handle timeout gracefully and return degraded result"""
        from app.services.literature_qc import LiteratureQCEngine
        import httpx

        mock_openai = AsyncMock()
        mock_ss = AsyncMock()
        mock_serper = AsyncMock()

        engine = LiteratureQCEngine(
            semantic_scholar_client=mock_ss,
            serper_client=mock_serper,
            openai_client=mock_openai
        )
        engine._search_semantic_scholar = AsyncMock(
            side_effect=asyncio.TimeoutError("timeout")
        )
        engine._search_serper = AsyncMock(
            side_effect=asyncio.TimeoutError("timeout")
        )

        # Should not raise, should return graceful result
        result = await engine.assess_novelty(
            hypothesis="Test hypothesis",
            domain="Cell Biology"
        )

        # Graceful degradation — classification may be not_found or similar
        assert result.classification.value in ["not_found", "similar_exists", "exact_match"]


class TestSSEManagerIntegration:
    """Integration tests for SSEManager"""

    @pytest.mark.asyncio
    async def test_event_emission_and_consumption(self):
        """Events emitted should be consumable from the stream"""
        from app.services.sse_manager import SSEManager

        manager = SSEManager()

        # Emit events
        await manager.emit_progress(stage="validation", progress_percent=33, message="Validating hypothesis")
        await manager.emit_progress(stage="literature_qc", progress_percent=66, message="Searching literature")
        await manager.emit_complete(plan_id="test-plan-id", total_duration=45.2, summary={})

        # Consume events
        events = []
        async for event_str in manager.event_stream():
            if event_str.startswith(": keep-alive"):
                continue
            events.append(event_str)
            if len(events) >= 3:
                break

        assert len(events) == 3
        # Verify event structure — SSE format: "event: ...\ndata: {...}\n\n"
        first_event_data = json.loads(events[0].split("data: ")[1].strip())
        assert first_event_data["event_type"] == "progress"
        assert first_event_data["data"]["stage"] == "validation"
        assert first_event_data["data"]["progress_percent"] == 33

    @pytest.mark.asyncio
    async def test_error_event_emission(self):
        """Error events should be properly formatted"""
        from app.services.sse_manager import SSEManager

        manager = SSEManager()
        await manager.emit_error(
            error_code="VALIDATION_FAILED",
            error_message="Hypothesis is not testable"
        )

        events = []
        async for event_str in manager.event_stream():
            if event_str.startswith(": keep-alive"):
                continue
            events.append(event_str)
            break

        assert len(events) == 1
        event_data = json.loads(events[0].split("data: ")[1].strip())
        assert event_data["event_type"] == "error"
        assert event_data["data"]["error_code"] == "VALIDATION_FAILED"


class TestPipelineStateIntegration:
    """Integration tests for LangGraph pipeline state"""

    @pytest.mark.asyncio
    async def test_pipeline_state_initialization(self):
        """Pipeline state should initialize with correct defaults"""
        from app.graph.pipeline_state import PipelineState

        state: PipelineState = {
            "hypothesis": "Test hypothesis",
            "user_id": "user-123",
            "validation_result": None,
            "domain": None,
            "novelty_assessment": None,
            "experiment_plan": None,
            "error": None,
            "current_stage": "validation",
            "progress_events": []
        }

        assert state["hypothesis"] == "Test hypothesis"
        assert state["current_stage"] == "validation"
        assert state["error"] is None

    @pytest.mark.asyncio
    async def test_full_pipeline_with_mocks(self, sample_hypotheses):
        """Full pipeline should complete successfully with mocked components"""
        pytest.importorskip("langgraph", reason="langgraph not installed")

        from app.services.sse_manager import SSEManager
        from app.graph.ai_pipeline import AIPipeline

        # Mock all components
        mock_validator = AsyncMock()
        mock_validator.validate = AsyncMock(return_value=MagicMock(
            is_valid=True,
            domain="Cell Biology",
            testable_claim="DMSO provides better cryoprotection",
            clarification_questions=[]
        ))

        mock_qc = AsyncMock()
        mock_qc.assess_novelty = AsyncMock(return_value=MagicMock(
            classification=MagicMock(value="similar_exists"),
            similar_papers=[],
            search_duration=3.5
        ))

        mock_generator = AsyncMock()
        mock_plan = MagicMock()
        mock_plan.domain = "Cell Biology"
        mock_plan.novelty_classification = MagicMock(value="similar_exists")
        mock_plan.materials = MagicMock(total_budget=5000.0, items=[])
        mock_plan.protocol = MagicMock(steps=[MagicMock(), MagicMock()])
        mock_plan.metadata = MagicMock(
            few_shot_examples_used=0,
            requires_expert_review=[]
        )
        mock_plan.dict = MagicMock(return_value={"domain": "Cell Biology"})
        mock_generator.generate_plan = AsyncMock(return_value=mock_plan)

        sse_manager = SSEManager()

        pipeline = AIPipeline(
            hypothesis_validator=mock_validator,
            literature_qc_engine=mock_qc,
            plan_generator=mock_generator,
            sse_manager=sse_manager
        )

        final_state = await pipeline.execute(
            hypothesis=sample_hypotheses["cell_biology"],
            user_id="test-user-123"
        )

        assert final_state["error"] is None
        assert final_state["experiment_plan"] is not None
        assert final_state["domain"] == "Cell Biology"

        # Verify all stages were called
        mock_validator.validate.assert_called_once()
        mock_qc.assess_novelty.assert_called_once()
        mock_generator.generate_plan.assert_called_once()


class TestAPIEndpointsIntegration:
    """Integration tests for FastAPI endpoints"""

    @pytest.fixture
    def test_client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_health_endpoint_returns_200(self, test_client):
        """Health endpoint should return 200 with dependency status"""
        with patch("app.api.v1.health.check_database", return_value={"status": "healthy", "latency_ms": 5.0}), \
             patch("app.api.v1.health.check_openai", return_value={"status": "healthy", "latency_ms": 120.0}), \
             patch("app.api.v1.health.check_semantic_scholar", return_value={"status": "healthy", "latency_ms": 80.0}), \
             patch("app.api.v1.health.check_serper", return_value={"status": "healthy", "latency_ms": 60.0}):

            response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "dependencies" in data
        assert "database" in data["dependencies"]

    def test_metrics_endpoint_returns_200(self, test_client):
        """Metrics endpoint should return 200 with metrics summary"""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "requests" in data
        assert "pipeline" in data
        assert "alerts" in data

    def test_root_endpoint(self, test_client):
        """Root endpoint should return API info"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_generate_plan_requires_auth(self, test_client):
        """Plan generation should require authentication"""
        response = test_client.post(
            "/api/v1/plans/generate",
            json={"hypothesis": "Test hypothesis"}
        )
        assert response.status_code == 401

    def test_get_plan_requires_auth(self, test_client):
        """Plan retrieval should require authentication"""
        response = test_client.get("/api/v1/plans/some-plan-id")
        assert response.status_code == 401

    def test_list_plans_requires_auth(self, test_client):
        """Plan listing should require authentication"""
        response = test_client.get("/api/v1/plans")
        assert response.status_code == 401

    def test_submit_review_requires_auth(self, test_client):
        """Review submission should require authentication"""
        response = test_client.post(
            "/api/v1/plans/some-plan-id/reviews",
            json={
                "protocol_rating": 4,
                "materials_rating": 4,
                "timeline_rating": 4,
                "validation_rating": 4
            }
        )
        assert response.status_code == 401

    def test_openapi_docs_accessible(self, test_client):
        """OpenAPI docs should be accessible"""
        response = test_client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_accessible(self, test_client):
        """OpenAPI JSON schema should be accessible"""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/v1/plans/generate" in schema["paths"]


class TestMonitoringIntegration:
    """Integration tests for monitoring utilities"""

    def test_metrics_collector_records_and_retrieves(self):
        """MetricsCollector should record and retrieve values"""
        from app.utils.monitoring import MetricsCollector

        collector = MetricsCollector(window_seconds=60)
        collector.record("test_metric", 1.5)
        collector.record("test_metric", 2.5)
        collector.record("test_metric", 3.5)

        values = collector.get_values("test_metric")
        assert len(values) == 3
        assert 1.5 in values

        avg = collector.get_average("test_metric")
        assert avg == pytest.approx(2.5)

    def test_metrics_collector_percentile(self):
        """MetricsCollector should calculate percentiles correctly"""
        from app.utils.monitoring import MetricsCollector

        collector = MetricsCollector(window_seconds=60)
        for i in range(1, 101):
            collector.record("latency", float(i))

        p50 = collector.get_percentile("latency", 50)
        p95 = collector.get_percentile("latency", 95)

        assert p50 == pytest.approx(50.0, abs=2.0)
        assert p95 == pytest.approx(95.0, abs=2.0)

    def test_alert_fires_on_high_error_rate(self):
        """Alert should fire when error rate exceeds threshold"""
        from app.utils.monitoring import MetricsCollector

        collector = MetricsCollector(window_seconds=60)

        # Record 10 total requests, 6 errors (60% error rate > 5% threshold)
        for _ in range(10):
            collector.record("request_total", 1)
        for _ in range(6):
            collector.record("request_error", 1)

        alerts = collector.check_alerts()
        alert_names = [a["name"] for a in alerts]
        assert "high_error_rate" in alert_names

    def test_no_alert_on_low_error_rate(self):
        """No alert should fire when error rate is below threshold"""
        from app.utils.monitoring import MetricsCollector

        collector = MetricsCollector(window_seconds=60)

        # Record 100 total requests, 2 errors (2% error rate < 5% threshold)
        for _ in range(100):
            collector.record("request_total", 1)
        for _ in range(2):
            collector.record("request_error", 1)

        alerts = collector.check_alerts()
        alert_names = [a["name"] for a in alerts]
        assert "high_error_rate" not in alert_names

    def test_summary_returns_all_sections(self):
        """Metrics summary should include all required sections"""
        from app.utils.monitoring import MetricsCollector

        collector = MetricsCollector(window_seconds=60)
        summary = collector.get_summary()

        assert "requests" in summary
        assert "pipeline" in summary
        assert "validation" in summary
        assert "literature_qc" in summary
        assert "timestamp" in summary
