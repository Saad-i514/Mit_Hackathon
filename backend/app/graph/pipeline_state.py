"""
Pipeline State Definition for LangGraph
Defines the state structure for the AI experiment planning pipeline
"""
from typing import TypedDict, Optional, List, Dict, Any
from app.models.responses import (
    ValidationResult, NoveltyAssessment, ExperimentPlan
)


class PipelineState(TypedDict):
    """
    State structure for the AI experiment planning pipeline
    
    This TypedDict defines all the data that flows through the LangGraph
    pipeline stages during experiment plan generation.
    """
    
    # Input data
    hypothesis: str
    user_id: str
    
    # Stage results
    validation_result: Optional[ValidationResult]
    domain: Optional[str]
    novelty_assessment: Optional[NoveltyAssessment]
    experiment_plan: Optional[ExperimentPlan]
    hypothesis_refinement: Optional[Dict[str, Any]]
    
    # Error handling
    error: Optional[str]
    error_code: Optional[str]
    error_stage: Optional[str]
    
    # Progress tracking
    current_stage: str
    progress_events: List[Dict[str, Any]]
    
    # Metadata
    pipeline_start_time: Optional[float]
    stage_durations: Dict[str, float]
    few_shot_examples_used: int
    
    # LangSmith tracing
    langsmith_run_id: Optional[str]