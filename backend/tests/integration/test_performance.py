"""
Performance benchmarking tests for the AI Scientist Platform.

These tests verify that each pipeline stage meets its latency requirements.
They use mocked external APIs to measure pure processing overhead.

Performance requirements:
- Hypothesis validation: < 5 seconds
- Literature QC: < 30 seconds
- Plan generation: < 60 seconds
- End-to-end pipeline: < 90 seconds (P95)
- Similarity search: < 500ms

Run with:
    pytest backend/tests/integration/test_performance.py -v --timeout=120
"""
import asyncio
import json
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestHypothesisValidationPerformance:
    """Performance tests for hypothesis validation stage"""

    @pytest.mark.asyncio
    async def test_validation_completes_within_5_seconds(self):
        """Hypothesis validation should complete within 5 seconds"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_client = AsyncMock()
        mock_client.chat_completion = AsyncMock(
            return_value=json.dumps({
                "is_testable": True,
                "domain": "Cell Biology",
                "testable_claim": "DMSO provides better cryoprotection",
                "clarification_questions": [],
                "reasoning": "Clear measurable outcome"
            })
        )

        validator = HypothesisValidator(openai_client=mock_client)

        start = time.time()
        result = await validator.validate(
            "DMSO at 10% v/v will provide superior cryoprotection compared to glycerol "
            "for HeLa cell cryopreservation, resulting in ≥ 85% post-thaw viability "
            "measured by trypan blue exclusion after 6 months at -80°C."
        )
        duration = time.time() - start

        assert result.is_valid is True
        assert duration < 5.0, f"Validation took {duration:.2f}s, expected < 5s"

    @pytest.mark.asyncio
    async def test_validation_input_check_is_instant(self):
        """Input validation (length/empty checks) should be near-instant"""
        from app.services.hypothesis_validator import HypothesisValidator

        mock_client = AsyncMock()
        validator = HypothesisValidator(openai_client=mock_client)

        # Test length validation
        start = time.time()
        result = await validator.validate("A" * 5001)
        duration = time.time() - start

        assert result.is_valid is False
        assert duration < 0.1, f"Input validation took {duration:.3f}s, expected < 0.1s"


class TestSSEManagerPerformance:
    """Performance tests for SSE event streaming"""

    @pytest.mark.asyncio
    async def test_event_emission_is_fast(self):
        """Emitting 100 events should complete in under 1 second"""
        from app.services.sse_manager import SSEManager

        manager = SSEManager(max_queue_size=200)

        start = time.time()
        for i in range(100):
            await manager.emit_progress(
                stage="validation",
                progress_percent=i,
                message=f"Step {i}"
            )
        duration = time.time() - start

        assert duration < 1.0, f"Emitting 100 events took {duration:.3f}s, expected < 1s"
        assert manager.queue_size == 100

    @pytest.mark.asyncio
    async def test_event_consumption_throughput(self):
        """Should consume 50 events in under 2 seconds"""
        from app.services.sse_manager import SSEManager

        manager = SSEManager(max_queue_size=100)

        # Pre-fill queue
        for i in range(49):
            await manager.emit_progress(
                stage="validation",
                progress_percent=i,
                message=f"Step {i}"
            )
        await manager.emit_complete(plan_id="test-id", total_duration=45.0, summary={})

        # Consume all events
        start = time.time()
        events = []
        async for event_str in manager.event_stream():
            if event_str.startswith(": keep-alive"):
                continue
            events.append(event_str)
            if len(events) >= 50:
                break
        duration = time.time() - start

        assert len(events) == 50
        assert duration < 2.0, f"Consuming 50 events took {duration:.3f}s, expected < 2s"


class TestMetricsPerformance:
    """Performance tests for metrics collection"""

    def test_recording_1000_metrics_is_fast(self):
        """Recording 1000 metric points should complete in under 100ms"""
        from app.utils.monitoring import MetricsCollector

        collector = MetricsCollector(window_seconds=300)

        start = time.time()
        for i in range(1000):
            collector.record("test_metric", float(i))
        duration = time.time() - start

        assert duration < 0.1, f"Recording 1000 metrics took {duration:.3f}s, expected < 0.1s"

    def test_percentile_calculation_is_fast(self):
        """P95 calculation over 1000 points should complete in under 50ms"""
        from app.utils.monitoring import MetricsCollector

        collector = MetricsCollector(window_seconds=300)
        for i in range(1000):
            collector.record("latency", float(i))

        start = time.time()
        p95 = collector.get_percentile("latency", 95)
        duration = time.time() - start

        assert p95 is not None
        assert duration < 0.05, f"P95 calculation took {duration:.3f}s, expected < 0.05s"

    def test_alert_check_is_fast(self):
        """Alert checking should complete in under 10ms"""
        from app.utils.monitoring import MetricsCollector

        collector = MetricsCollector(window_seconds=300)
        for i in range(100):
            collector.record("request_total", 1)
        for i in range(5):
            collector.record("request_error", 1)

        start = time.time()
        alerts = collector.check_alerts()
        duration = time.time() - start

        assert duration < 0.01, f"Alert check took {duration:.3f}s, expected < 0.01s"


class TestPipelinePerformanceBenchmarks:
    """
    Performance benchmark documentation tests.
    
    These tests document the expected performance thresholds for the full pipeline.
    They use mocked components to verify the pipeline orchestration overhead is minimal.
    """

    @pytest.mark.asyncio
    async def test_pipeline_orchestration_overhead_is_minimal(self):
        """
        Pipeline orchestration (excluding AI API calls) should add < 2 seconds overhead.
        
        This test mocks all AI components with instant responses to measure
        pure LangGraph orchestration overhead.
        """
        pytest.importorskip("langgraph", reason="langgraph not installed")

        from app.services.sse_manager import SSEManager
        from app.graph.ai_pipeline import AIPipeline

        # Mock all components with instant responses
        mock_validator = AsyncMock()
        mock_validator.validate = AsyncMock(return_value=MagicMock(
            is_valid=True,
            domain="Cell Biology",
            testable_claim="Test claim",
            clarification_questions=[]
        ))

        mock_qc = AsyncMock()
        mock_qc.assess_novelty = AsyncMock(return_value=MagicMock(
            classification=MagicMock(value="not_found"),
            similar_papers=[],
            search_duration=0.1
        ))

        mock_generator = AsyncMock()
        mock_plan = MagicMock()
        mock_plan.domain = "Cell Biology"
        mock_plan.novelty_classification = MagicMock(value="not_found")
        mock_plan.materials = MagicMock(total_budget=1000.0, items=[])
        mock_plan.protocol = MagicMock(steps=[])
        mock_plan.metadata = MagicMock(few_shot_examples_used=0, requires_expert_review=[])
        mock_plan.dict = MagicMock(return_value={"domain": "Cell Biology"})
        mock_generator.generate_plan = AsyncMock(return_value=mock_plan)

        sse_manager = SSEManager()
        pipeline = AIPipeline(
            hypothesis_validator=mock_validator,
            literature_qc_engine=mock_qc,
            plan_generator=mock_generator,
            sse_manager=sse_manager
        )

        start = time.time()
        final_state = await pipeline.execute(
            hypothesis="Test hypothesis for performance benchmarking.",
            user_id="perf-test-user"
        )
        duration = time.time() - start

        assert final_state["error"] is None
        assert duration < 2.0, (
            f"Pipeline orchestration overhead was {duration:.2f}s, expected < 2s. "
            f"This measures LangGraph overhead only (AI calls are mocked)."
        )

    def test_performance_thresholds_documented(self):
        """
        Document the expected performance thresholds for production deployment.
        
        These are the SLA targets for the AI Scientist Platform:
        - Hypothesis validation: < 5 seconds (GPT-4o call)
        - Literature QC: < 30 seconds (concurrent Semantic Scholar + Serper)
        - Plan generation: < 60 seconds (GPT-4o call with RAG context)
        - End-to-end pipeline: < 90 seconds P95
        - Similarity search (RAG): < 500ms
        - Health check: < 5 seconds
        - API response (non-streaming): < 200ms
        """
        thresholds = {
            "hypothesis_validation_seconds": 5,
            "literature_qc_seconds": 30,
            "plan_generation_seconds": 60,
            "end_to_end_p95_seconds": 90,
            "similarity_search_ms": 500,
            "health_check_seconds": 5,
            "api_response_ms": 200,
        }

        # Verify thresholds are reasonable
        assert thresholds["hypothesis_validation_seconds"] <= thresholds["end_to_end_p95_seconds"]
        assert thresholds["literature_qc_seconds"] <= thresholds["end_to_end_p95_seconds"]
        assert thresholds["plan_generation_seconds"] <= thresholds["end_to_end_p95_seconds"]
        assert thresholds["similarity_search_ms"] < 1000

        # Document thresholds
        print("\nPerformance Thresholds:")
        for name, value in thresholds.items():
            print(f"  {name}: {value}")
