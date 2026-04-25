"""
Monitoring and Alerting Utilities
Provides metrics collection, error rate tracking, and alerting for the AI Scientist Platform
"""
import time
import logging
import asyncio
from collections import deque, defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class AlertConfig:
    """Configuration for an alert rule"""
    name: str
    metric: str
    threshold: float
    window_seconds: int
    comparison: str  # "gt", "lt", "gte", "lte"
    description: str


class MetricsCollector:
    """
    In-process metrics collector for tracking request rates, error rates,
    latencies, and pipeline performance.
    
    Designed to work alongside LangSmith for AI-specific metrics.
    """
    
    def __init__(self, window_seconds: int = 300):
        """
        Initialize metrics collector.
        
        Args:
            window_seconds: Rolling window for metric aggregation (default 5 minutes)
        """
        self.window_seconds = window_seconds
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque())
        self._counters: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()
        
        # Alert configurations
        self._alert_configs: List[AlertConfig] = [
            AlertConfig(
                name="high_error_rate",
                metric="error_rate",
                threshold=0.05,  # 5% error rate
                window_seconds=300,  # 5 minutes
                comparison="gt",
                description="Error rate exceeded 5% over 5 minutes"
            ),
            AlertConfig(
                name="slow_pipeline",
                metric="pipeline_duration_p95",
                threshold=90.0,  # 90 seconds
                window_seconds=300,
                comparison="gt",
                description="Pipeline P95 latency exceeded 90 seconds"
            ),
            AlertConfig(
                name="high_validation_failure_rate",
                metric="validation_failure_rate",
                threshold=0.20,  # 20% failure rate
                window_seconds=300,
                comparison="gt",
                description="Hypothesis validation failure rate exceeded 20%"
            ),
        ]
        
        self._fired_alerts: Dict[str, datetime] = {}
        self._alert_cooldown_seconds = 300  # 5 minutes between repeated alerts
    
    def _cleanup_old_points(self, metric_name: str):
        """Remove metric points outside the rolling window"""
        cutoff = time.time() - self.window_seconds
        queue = self._metrics[metric_name]
        while queue and queue[0].timestamp < cutoff:
            queue.popleft()
    
    def record(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Record a metric value.
        
        Args:
            metric_name: Name of the metric
            value: Numeric value to record
            labels: Optional key-value labels for the metric
        """
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        )
        self._metrics[metric_name].append(point)
        self._cleanup_old_points(metric_name)
    
    def increment(self, counter_name: str, amount: int = 1):
        """Increment a counter"""
        self._counters[counter_name] += amount
    
    def get_values(self, metric_name: str, window_seconds: Optional[int] = None) -> List[float]:
        """Get metric values within the window"""
        self._cleanup_old_points(metric_name)
        cutoff = time.time() - (window_seconds or self.window_seconds)
        return [p.value for p in self._metrics[metric_name] if p.timestamp >= cutoff]
    
    def get_average(self, metric_name: str, window_seconds: Optional[int] = None) -> Optional[float]:
        """Get average of metric values"""
        values = self.get_values(metric_name, window_seconds)
        return sum(values) / len(values) if values else None
    
    def get_percentile(self, metric_name: str, percentile: float, window_seconds: Optional[int] = None) -> Optional[float]:
        """Get percentile of metric values (e.g., p95 = 95.0)"""
        values = sorted(self.get_values(metric_name, window_seconds))
        if not values:
            return None
        idx = int(len(values) * percentile / 100)
        idx = min(idx, len(values) - 1)
        return values[idx]
    
    def get_count(self, metric_name: str, window_seconds: Optional[int] = None) -> int:
        """Get count of metric points in window"""
        return len(self.get_values(metric_name, window_seconds))
    
    def get_rate(self, success_metric: str, total_metric: str, window_seconds: Optional[int] = None) -> Optional[float]:
        """Calculate rate (e.g., error rate = errors / total)"""
        success_count = self.get_count(success_metric, window_seconds)
        total_count = self.get_count(total_metric, window_seconds)
        if total_count == 0:
            return None
        return success_count / total_count
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all current metrics"""
        now = time.time()
        window = self.window_seconds
        
        # Request metrics
        total_requests = self.get_count("request_total", window)
        error_requests = self.get_count("request_error", window)
        error_rate = (error_requests / total_requests) if total_requests > 0 else 0.0
        
        # Pipeline metrics
        pipeline_durations = self.get_values("pipeline_duration", window)
        pipeline_p50 = self.get_percentile("pipeline_duration", 50, window)
        pipeline_p95 = self.get_percentile("pipeline_duration", 95, window)
        
        # Validation metrics
        validation_total = self.get_count("validation_total", window)
        validation_failures = self.get_count("validation_failure", window)
        validation_failure_rate = (validation_failures / validation_total) if validation_total > 0 else 0.0
        
        # Literature QC metrics
        qc_durations = self.get_values("literature_qc_duration", window)
        qc_avg = self.get_average("literature_qc_duration", window)
        
        return {
            "window_seconds": window,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requests": {
                "total": total_requests,
                "errors": error_requests,
                "error_rate": round(error_rate, 4),
                "error_rate_pct": f"{error_rate * 100:.1f}%"
            },
            "pipeline": {
                "total_runs": len(pipeline_durations),
                "p50_seconds": round(pipeline_p50, 2) if pipeline_p50 else None,
                "p95_seconds": round(pipeline_p95, 2) if pipeline_p95 else None,
            },
            "validation": {
                "total": validation_total,
                "failures": validation_failures,
                "failure_rate": round(validation_failure_rate, 4),
                "failure_rate_pct": f"{validation_failure_rate * 100:.1f}%"
            },
            "literature_qc": {
                "total_searches": len(qc_durations),
                "avg_duration_seconds": round(qc_avg, 2) if qc_avg else None,
            },
            "counters": dict(self._counters)
        }
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Check all alert conditions and return any that are firing.
        
        Returns:
            List of firing alert dicts with name, description, current_value, threshold
        """
        firing_alerts = []
        now = datetime.now(timezone.utc)
        
        for config in self._alert_configs:
            # Check cooldown
            last_fired = self._fired_alerts.get(config.name)
            if last_fired and (now - last_fired).total_seconds() < self._alert_cooldown_seconds:
                continue
            
            # Get current metric value
            current_value = None
            
            if config.metric == "error_rate":
                total = self.get_count("request_total", config.window_seconds)
                errors = self.get_count("request_error", config.window_seconds)
                current_value = (errors / total) if total > 0 else 0.0
                
            elif config.metric == "pipeline_duration_p95":
                current_value = self.get_percentile("pipeline_duration", 95, config.window_seconds)
                
            elif config.metric == "validation_failure_rate":
                total = self.get_count("validation_total", config.window_seconds)
                failures = self.get_count("validation_failure", config.window_seconds)
                current_value = (failures / total) if total > 0 else 0.0
            
            if current_value is None:
                continue
            
            # Check threshold
            is_firing = False
            if config.comparison == "gt" and current_value > config.threshold:
                is_firing = True
            elif config.comparison == "gte" and current_value >= config.threshold:
                is_firing = True
            elif config.comparison == "lt" and current_value < config.threshold:
                is_firing = True
            elif config.comparison == "lte" and current_value <= config.threshold:
                is_firing = True
            
            if is_firing:
                self._fired_alerts[config.name] = now
                alert = {
                    "name": config.name,
                    "description": config.description,
                    "current_value": round(current_value, 4),
                    "threshold": config.threshold,
                    "comparison": config.comparison,
                    "fired_at": now.isoformat()
                }
                firing_alerts.append(alert)
                logger.warning(f"ALERT FIRED: {config.name} - {config.description} "
                             f"(current={current_value:.4f}, threshold={config.threshold})")
        
        return firing_alerts


# Global metrics collector instance
metrics = MetricsCollector()


class RequestTimer:
    """Context manager for timing requests and recording metrics"""
    
    def __init__(self, endpoint: str, method: str = "GET"):
        self.endpoint = endpoint
        self.method = method
        self.start_time = None
        self.status_code = 200
    
    def __enter__(self):
        self.start_time = time.time()
        metrics.increment("request_total")
        metrics.record("request_total", 1, {"endpoint": self.endpoint, "method": self.method})
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        metrics.record("request_duration", duration, {
            "endpoint": self.endpoint,
            "method": self.method,
            "status": str(self.status_code)
        })
        
        if exc_type is not None or self.status_code >= 500:
            metrics.increment("request_error")
            metrics.record("request_error", 1, {"endpoint": self.endpoint})
        
        return False  # Don't suppress exceptions


class PipelineTimer:
    """Context manager for timing pipeline executions"""
    
    def __init__(self, hypothesis_id: Optional[str] = None):
        self.hypothesis_id = hypothesis_id
        self.start_time = None
        self.stage_times: Dict[str, float] = {}
        self._current_stage: Optional[str] = None
        self._stage_start: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def start_stage(self, stage_name: str):
        """Mark the start of a pipeline stage"""
        if self._current_stage and self._stage_start:
            # Record previous stage duration
            duration = time.time() - self._stage_start
            self.stage_times[self._current_stage] = duration
            metrics.record(f"stage_{self._current_stage}_duration", duration)
        
        self._current_stage = stage_name
        self._stage_start = time.time()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Record final stage
        if self._current_stage and self._stage_start:
            duration = time.time() - self._stage_start
            self.stage_times[self._current_stage] = duration
            metrics.record(f"stage_{self._current_stage}_duration", duration)
        
        # Record total pipeline duration
        total_duration = time.time() - self.start_time
        metrics.record("pipeline_duration", total_duration)
        
        if exc_type is not None:
            metrics.increment("pipeline_error")
            metrics.record("pipeline_error", 1)
        else:
            metrics.increment("pipeline_success")
        
        return False
