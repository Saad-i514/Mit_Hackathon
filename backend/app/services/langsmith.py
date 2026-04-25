"""
LangSmith tracing configuration and utilities
"""
import os
import logging
from typing import Dict, Any, Optional
from langsmith import Client
from app.config import settings


logger = logging.getLogger(__name__)


def configure_langsmith():
    """
    Configure LangSmith tracing environment variables
    Should be called at application startup
    """
    os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        logger.info(f"LangSmith tracing enabled for project: {settings.langchain_project}")
    else:
        logger.warning("LangSmith API key not provided, tracing will be disabled")


class LangSmithLogger:
    """Utility class for logging custom metrics to LangSmith"""
    
    def __init__(self):
        """Initialize LangSmith client"""
        self.client = None
        if settings.langchain_api_key:
            try:
                self.client = Client()
                logger.info("LangSmith client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize LangSmith client: {e}")
    
    def log_pipeline_metrics(
        self,
        run_id: str,
        hypothesis_id: str,
        total_duration: float,
        stage_durations: Dict[str, float],
        few_shot_examples_used: int,
        novelty_classification: str
    ):
        """
        Log custom pipeline metrics to LangSmith
        
        Args:
            run_id: LangSmith run ID
            hypothesis_id: Experiment hypothesis ID
            total_duration: Total pipeline execution time in seconds
            stage_durations: Duration of each pipeline stage
            few_shot_examples_used: Number of few-shot examples used
            novelty_classification: Literature QC novelty result
        """
        if not self.client:
            return
        
        try:
            self.client.create_feedback(
                run_id=run_id,
                key="pipeline_metrics",
                score=1.0,
                value={
                    "hypothesis_id": hypothesis_id,
                    "total_duration_seconds": total_duration,
                    "stage_durations": stage_durations,
                    "few_shot_examples_used": few_shot_examples_used,
                    "novelty_classification": novelty_classification
                }
            )
            logger.info(f"Logged pipeline metrics to LangSmith for run {run_id}")
        
        except Exception as e:
            logger.warning(f"Failed to log pipeline metrics to LangSmith: {e}")
    
    def log_plan_quality(
        self,
        run_id: str,
        plan_id: str,
        average_rating: Optional[float] = None,
        requires_expert_review: Optional[list] = None
    ):
        """
        Log plan quality metrics to LangSmith
        
        Args:
            run_id: LangSmith run ID
            plan_id: Experiment plan ID
            average_rating: Average scientist rating (1-5)
            requires_expert_review: List of sections requiring review
        """
        if not self.client:
            return
        
        try:
            self.client.create_feedback(
                run_id=run_id,
                key="plan_quality",
                score=average_rating if average_rating else 0.0,
                value={
                    "plan_id": plan_id,
                    "average_rating": average_rating,
                    "requires_expert_review": requires_expert_review or []
                }
            )
            logger.info(f"Logged plan quality to LangSmith for run {run_id}")
        
        except Exception as e:
            logger.warning(f"Failed to log plan quality to LangSmith: {e}")


# Global LangSmith logger instance
langsmith_logger = LangSmithLogger()


def get_langsmith_logger() -> LangSmithLogger:
    """Get the global LangSmith logger instance"""
    return langsmith_logger
