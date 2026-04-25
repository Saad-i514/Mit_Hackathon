"""
Unit tests for monitoring utilities.

Run with:
    pytest backend/tests/unit/test_monitoring.py -v
"""
import time
import pytest
from unittest.mock import patch


class TestMetricsCollector:
    """Unit tests for MetricsCollector"""

    @pytest.fixture
    def collector(self):
        from app.utils.monitoring import MetricsCollector
        return MetricsCollector(window_seconds=60)

    def test_record_and_retrieve_values(self, collector):
        """Should record and retrieve metric values"""
        collector.record("test_metric", 1.0)
        collector.record("test_metric", 2.0)
        collector.record("test_metric", 3.0)

        values = collector.get_values("test_metric")
        assert len(values) == 3
        assert set(values) == {1.0, 2.0, 3.0}

    def test_average_calculation(self, collector):
        """Should calculate correct average"""
        collector.record("latency", 10.0)
        collector.record("latency", 20.0)
        collector.record("latency", 30.0)

        avg = collector.get_average("latency")
        assert avg == pytest.approx(20.0)

    def test_average_returns_none_for_empty(self, collector):
        """Should return None when no values recorded"""
        avg = collector.get_average("nonexistent_metric")
        assert avg is None

    def test_percentile_p50(self, collector):
        """Should calculate P50 correctly"""
        for i in range(1, 101):
            collector.record("values", float(i))

        p50 = collector.get_percentile("values", 50)
        assert p50 == pytest.approx(50.0, abs=2.0)

    def test_percentile_p95(self, collector):
        """Should calculate P95 correctly"""
        for i in range(1, 101):
            collector.record("values", float(i))

        p95 = collector.get_percentile("values", 95)
        assert p95 == pytest.approx(95.0, abs=2.0)

    def test_percentile_returns_none_for_empty(self, collector):
        """Should return None when no values recorded"""
        p95 = collector.get_percentile("nonexistent", 95)
        assert p95 is None

    def test_count_within_window(self, collector):
        """Should count values within the window"""
        collector.record("events", 1.0)
        collector.record("events", 1.0)
        collector.record("events", 1.0)

        count = collector.get_count("events")
        assert count == 3

    def test_increment_counter(self, collector):
        """Should increment counters correctly"""
        collector.increment("requests")
        collector.increment("requests")
        collector.increment("requests", 5)

        assert collector._counters["requests"] == 7

    def test_old_points_cleaned_up(self):
        """Points outside the window should be cleaned up"""
        from app.utils.monitoring import MetricsCollector

        collector = MetricsCollector(window_seconds=1)  # 1 second window

        collector.record("metric", 1.0)
        collector.record("metric", 2.0)

        # Wait for window to expire
        time.sleep(1.1)

        # Add a new point to trigger cleanup
        collector.record("metric", 3.0)

        values = collector.get_values("metric")
        assert len(values) == 1
        assert values[0] == 3.0

    def test_summary_structure(self, collector):
        """Summary should contain all required sections"""
        summary = collector.get_summary()

        assert "requests" in summary
        assert "pipeline" in summary
        assert "validation" in summary
        assert "literature_qc" in summary
        assert "timestamp" in summary
        assert "window_seconds" in summary

        # Check nested structure
        assert "total" in summary["requests"]
        assert "errors" in summary["requests"]
        assert "error_rate" in summary["requests"]

    def test_alert_fires_on_high_error_rate(self, collector):
        """Alert should fire when error rate exceeds 5%"""
        # 10 total, 6 errors = 60% error rate
        for _ in range(10):
            collector.record("request_total", 1)
        for _ in range(6):
            collector.record("request_error", 1)

        alerts = collector.check_alerts()
        alert_names = [a["name"] for a in alerts]
        assert "high_error_rate" in alert_names

    def test_no_alert_below_threshold(self, collector):
        """No alert should fire when error rate is below threshold"""
        # 100 total, 2 errors = 2% error rate
        for _ in range(100):
            collector.record("request_total", 1)
        for _ in range(2):
            collector.record("request_error", 1)

        alerts = collector.check_alerts()
        alert_names = [a["name"] for a in alerts]
        assert "high_error_rate" not in alert_names

    def test_alert_cooldown_prevents_repeated_firing(self, collector):
        """Same alert should not fire twice within cooldown period"""
        # Trigger high error rate
        for _ in range(10):
            collector.record("request_total", 1)
        for _ in range(6):
            collector.record("request_error", 1)

        # First check — should fire
        alerts1 = collector.check_alerts()
        assert any(a["name"] == "high_error_rate" for a in alerts1)

        # Second check immediately — should NOT fire (cooldown)
        alerts2 = collector.check_alerts()
        assert not any(a["name"] == "high_error_rate" for a in alerts2)

    def test_alert_for_slow_pipeline(self, collector):
        """Alert should fire when P95 pipeline duration exceeds 90 seconds"""
        # Record 20 pipeline durations, most > 90s
        for _ in range(19):
            collector.record("pipeline_duration", 100.0)  # 100s > 90s threshold
        collector.record("pipeline_duration", 5.0)

        alerts = collector.check_alerts()
        alert_names = [a["name"] for a in alerts]
        assert "slow_pipeline" in alert_names

    def test_no_alert_for_fast_pipeline(self, collector):
        """No alert should fire when pipeline is fast"""
        for _ in range(20):
            collector.record("pipeline_duration", 30.0)  # 30s < 90s threshold

        alerts = collector.check_alerts()
        alert_names = [a["name"] for a in alerts]
        assert "slow_pipeline" not in alert_names


class TestRequestTimer:
    """Unit tests for RequestTimer context manager"""

    def test_records_request_on_entry(self):
        """Should record request metric on entry"""
        from app.utils.monitoring import RequestTimer, metrics

        initial_count = metrics.get_count("request_total")

        with RequestTimer("/api/v1/plans", "POST"):
            pass

        new_count = metrics.get_count("request_total")
        assert new_count > initial_count

    def test_records_error_on_5xx_status(self):
        """Should record error metric for 5xx status codes"""
        from app.utils.monitoring import RequestTimer, metrics

        initial_errors = metrics.get_count("request_error")

        timer = RequestTimer("/api/v1/plans", "POST")
        with timer:
            timer.status_code = 500

        new_errors = metrics.get_count("request_error")
        assert new_errors > initial_errors

    def test_no_error_on_2xx_status(self):
        """Should not record error metric for 2xx status codes"""
        from app.utils.monitoring import RequestTimer, metrics

        initial_errors = metrics.get_count("request_error")

        timer = RequestTimer("/api/v1/plans", "GET")
        with timer:
            timer.status_code = 200

        new_errors = metrics.get_count("request_error")
        assert new_errors == initial_errors


class TestPipelineTimer:
    """Unit tests for PipelineTimer context manager"""

    def test_records_pipeline_duration(self):
        """Should record total pipeline duration"""
        from app.utils.monitoring import PipelineTimer, MetricsCollector

        collector = MetricsCollector(window_seconds=60)

        with patch("app.utils.monitoring.metrics", collector):
            with PipelineTimer():
                time.sleep(0.01)  # Small delay

        durations = collector.get_values("pipeline_duration")
        assert len(durations) == 1
        assert durations[0] > 0

    def test_records_stage_durations(self):
        """Should record individual stage durations"""
        from app.utils.monitoring import PipelineTimer, MetricsCollector

        collector = MetricsCollector(window_seconds=60)

        with patch("app.utils.monitoring.metrics", collector):
            with PipelineTimer() as timer:
                timer.start_stage("validation")
                time.sleep(0.01)
                timer.start_stage("literature_qc")
                time.sleep(0.01)

        validation_durations = collector.get_values("stage_validation_duration")
        assert len(validation_durations) == 1
        assert validation_durations[0] > 0
