"""
AI Pipeline Implementation using LangGraph
Orchestrates the complete experiment planning workflow
"""
import time
import logging
import uuid
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langsmith import traceable

from app.graph.pipeline_state import PipelineState
from app.services.hypothesis_validator import HypothesisValidator
from app.services.literature_qc import LiteratureQCEngine
from app.services.plan_generator import PlanGenerator
from app.services.sse_manager import SSEManager
from app.services.langsmith import get_langsmith_logger
from app.services.hypothesis_refiner import HypothesisRefiner
from app.services.protocols_io import ProtocolsIOClient
from app.services.reproducibility_scorer import ReproducibilityScorer
from app.models.responses import ValidationResult, NoveltyAssessment


logger = logging.getLogger(__name__)


class AIPipeline:
    """
    AI-powered experiment planning pipeline using LangGraph
    
    Orchestrates the complete workflow:
    1. Hypothesis validation and domain extraction
    2. Literature quality control and novelty assessment
    3. Experiment plan generation with few-shot learning
    """
    
    def __init__(
        self,
        hypothesis_validator: HypothesisValidator,
        literature_qc_engine: LiteratureQCEngine,
        plan_generator: PlanGenerator,
        sse_manager: SSEManager,
        hypothesis_refiner: Optional[HypothesisRefiner] = None,
        protocols_io_client: Optional[ProtocolsIOClient] = None,
        reproducibility_scorer: Optional[ReproducibilityScorer] = None,
    ):
        """
        Initialize AI Pipeline
        
        Args:
            hypothesis_validator: Hypothesis validation component
            literature_qc_engine: Literature QC component
            plan_generator: Plan generation component
            sse_manager: SSE stream manager for progress updates
        """
        self.hypothesis_validator = hypothesis_validator
        self.literature_qc_engine = literature_qc_engine
        self.plan_generator = plan_generator
        self.sse_manager = sse_manager
        self.hypothesis_refiner = hypothesis_refiner
        self.protocols_io_client = protocols_io_client
        self.reproducibility_scorer = reproducibility_scorer
        self.langsmith_logger = get_langsmith_logger()
        
        # Build the LangGraph workflow
        self.graph = self._build_graph()
        
        logger.info("AIPipeline initialized with LangGraph workflow")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine
        
        Returns:
            StateGraph: Compiled LangGraph workflow
        """
        # Create state graph
        workflow = StateGraph(PipelineState)
        
        # Add nodes for each pipeline stage
        workflow.add_node("validate_hypothesis", self._validate_hypothesis_node)
        workflow.add_node("assess_literature", self._assess_literature_node)
        workflow.add_node("generate_plan", self._generate_plan_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Set entry point
        workflow.set_entry_point("validate_hypothesis")
        
        # Define conditional edges between stages
        workflow.add_conditional_edges(
            "validate_hypothesis",
            self._should_continue_after_validation,
            {
                "continue": "assess_literature",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "assess_literature",
            self._should_continue_after_qc,
            {
                "continue": "generate_plan",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_plan",
            self._should_complete,
            {
                "complete": END,
                "error": "handle_error"
            }
        )
        
        # Error handling always ends the pipeline
        workflow.add_edge("handle_error", END)
        
        # Compile the graph
        return workflow.compile()
    
    async def _validate_hypothesis_node(self, state: PipelineState) -> PipelineState:
        """
        Pipeline node: Validate hypothesis and extract domain
        
        Args:
            state: Current pipeline state
        
        Returns:
            PipelineState: Updated state with validation results
        """
        stage_start_time = time.time()
        
        try:
            # Emit stage start event
            await self.sse_manager.emit_stage_start(
                stage="validation",
                stage_description="Validating hypothesis and extracting domain",
                estimated_duration=5
            )
            
            # Emit progress
            await self.sse_manager.emit_progress(
                stage="validation",
                progress_percent=10,
                message="Starting hypothesis validation..."
            )
            
            # Validate hypothesis
            active_hypothesis = state["hypothesis"]
            refinement = None
            if self.hypothesis_refiner:
                refinement = await self.hypothesis_refiner.refine(active_hypothesis)
                state["hypothesis_refinement"] = refinement
                score = int(refinement.get("score", 100))
                if score < 70:
                    rewrites = refinement.get("suggested_rewrites") or []
                    if rewrites:
                        best = rewrites[0].get("hypothesis")
                        if best:
                            active_hypothesis = best.strip()
                            state["hypothesis"] = active_hypothesis
                            await self.sse_manager.emit_progress(
                                stage="validation",
                                progress_percent=15,
                                message="Hypothesis auto-refined for higher scientific testability",
                                details={"quality_score": score},
                            )

            validation_result = await self.hypothesis_validator.validate(active_hypothesis)
            
            # Update state
            state["validation_result"] = validation_result
            state["domain"] = validation_result.domain
            state["current_stage"] = "validation"
            
            # Calculate stage duration
            stage_duration = time.time() - stage_start_time
            state["stage_durations"]["validation"] = stage_duration
            
            # Emit progress completion
            await self.sse_manager.emit_progress(
                stage="validation",
                progress_percent=33,
                message=f"Hypothesis validated - Domain: {validation_result.domain}",
                details={
                    "domain": validation_result.domain,
                    "is_valid": validation_result.is_valid,
                    "testable_claim": validation_result.testable_claim,
                    "hypothesis_quality_score": (
                        int(state.get("hypothesis_refinement", {}).get("score", 100))
                        if state.get("hypothesis_refinement") else None
                    ),
                }
            )
            
            # Emit stage completion
            await self.sse_manager.emit_stage_complete(
                stage="validation",
                duration=stage_duration,
                result_summary={
                    "domain": validation_result.domain,
                    "is_valid": validation_result.is_valid,
                    "clarification_questions_count": len(validation_result.clarification_questions)
                }
            )
            
            logger.info(f"Hypothesis validation completed - Domain: {validation_result.domain}")
            
        except Exception as e:
            logger.error(f"Hypothesis validation failed: {e}")
            state["error"] = str(e)
            state["error_code"] = "VALIDATION_ERROR"
            state["error_stage"] = "validation"
            
            await self.sse_manager.emit_error(
                error_code="VALIDATION_ERROR",
                error_message=f"Hypothesis validation failed: {str(e)}",
                stage="validation"
            )
        
        return state
    
    async def _assess_literature_node(self, state: PipelineState) -> PipelineState:
        """
        Pipeline node: Assess literature and determine novelty
        
        Args:
            state: Current pipeline state
        
        Returns:
            PipelineState: Updated state with novelty assessment
        """
        stage_start_time = time.time()
        
        try:
            # Emit stage start event
            await self.sse_manager.emit_stage_start(
                stage="literature_qc",
                stage_description="Searching literature and assessing novelty",
                estimated_duration=30
            )
            
            # Emit progress
            await self.sse_manager.emit_progress(
                stage="literature_qc",
                progress_percent=40,
                message="Searching scientific literature..."
            )
            
            # Assess novelty
            novelty_assessment = await self.literature_qc_engine.assess_novelty(
                hypothesis=state["hypothesis"],
                domain=state["domain"]
            )
            
            # Update state
            state["novelty_assessment"] = novelty_assessment
            state["current_stage"] = "literature_qc"
            
            # Calculate stage duration
            stage_duration = time.time() - stage_start_time
            state["stage_durations"]["literature_qc"] = stage_duration
            
            # Emit progress completion
            await self.sse_manager.emit_progress(
                stage="literature_qc",
                progress_percent=66,
                message=f"Literature assessment complete - Classification: {novelty_assessment.classification.value}",
                details={
                    "classification": novelty_assessment.classification.value,
                    "similar_papers_count": len(novelty_assessment.similar_papers),
                    "search_duration": novelty_assessment.search_duration
                }
            )
            
            # Emit stage completion
            await self.sse_manager.emit_stage_complete(
                stage="literature_qc",
                duration=stage_duration,
                result_summary={
                    "classification": novelty_assessment.classification.value,
                    "similar_papers_count": len(novelty_assessment.similar_papers),
                    "search_duration": novelty_assessment.search_duration
                }
            )
            
            logger.info(f"Literature QC completed - Classification: {novelty_assessment.classification.value}")
            
        except Exception as e:
            logger.error(f"Literature QC failed: {e}")
            state["error"] = str(e)
            state["error_code"] = "LITERATURE_QC_ERROR"
            state["error_stage"] = "literature_qc"
            
            await self.sse_manager.emit_error(
                error_code="LITERATURE_QC_ERROR",
                error_message=f"Literature assessment failed: {str(e)}",
                stage="literature_qc"
            )
        
        return state
    
    async def _generate_plan_node(self, state: PipelineState) -> PipelineState:
        """
        Pipeline node: Generate experiment plan with few-shot learning
        
        Args:
            state: Current pipeline state
        
        Returns:
            PipelineState: Updated state with experiment plan
        """
        stage_start_time = time.time()
        
        try:
            # Emit stage start event
            await self.sse_manager.emit_stage_start(
                stage="plan_generation",
                stage_description="Generating experiment plan with AI",
                estimated_duration=60
            )
            
            # Emit progress
            await self.sse_manager.emit_progress(
                stage="plan_generation",
                progress_percent=75,
                message="Generating detailed experiment plan..."
            )
            
            # Generate plan
            protocol_matches = []
            if self.protocols_io_client:
                protocol_matches = await self.protocols_io_client.search_protocols(
                    state["hypothesis"],
                    limit=5,
                )

            experiment_plan = await self.plan_generator.generate_plan(
                hypothesis=state["hypothesis"],
                domain=state["domain"],
                novelty_assessment=state["novelty_assessment"],
                protocol_matches=protocol_matches,
            )

            # Optional reproducibility scoring pass.
            if self.reproducibility_scorer:
                reproducibility = await self.reproducibility_scorer.score(
                    experiment_plan.model_dump()
                )
                experiment_plan.metadata.reproducibility_assessment = reproducibility

            if state.get("hypothesis_refinement"):
                score = int(state["hypothesis_refinement"].get("score", 100))
                experiment_plan.metadata.hypothesis_quality_score = score
                experiment_plan.metadata.hypothesis_refined = score < 70
            
            # Update state
            state["experiment_plan"] = experiment_plan
            state["current_stage"] = "plan_generation"
            state["few_shot_examples_used"] = experiment_plan.metadata.few_shot_examples_used
            
            # Calculate stage duration
            stage_duration = time.time() - stage_start_time
            state["stage_durations"]["plan_generation"] = stage_duration
            
            # Emit progress completion
            await self.sse_manager.emit_progress(
                stage="plan_generation",
                progress_percent=100,
                message="Experiment plan generated successfully",
                details={
                    "few_shot_examples_used": experiment_plan.metadata.few_shot_examples_used,
                    "requires_expert_review": experiment_plan.metadata.requires_expert_review,
                    "total_budget": experiment_plan.materials.total_budget,
                    "protocol_matches_found": len(protocol_matches),
                    "reproducibility_score": (
                        experiment_plan.metadata.reproducibility_assessment.get("total_score")
                        if experiment_plan.metadata.reproducibility_assessment else None
                    ),
                }
            )
            
            # Emit stage completion
            await self.sse_manager.emit_stage_complete(
                stage="plan_generation",
                duration=stage_duration,
                result_summary={
                    "few_shot_examples_used": experiment_plan.metadata.few_shot_examples_used,
                    "requires_expert_review": len(experiment_plan.metadata.requires_expert_review) > 0,
                    "total_budget": experiment_plan.materials.total_budget,
                    "protocol_steps": len(experiment_plan.protocol.steps),
                    "materials_count": len(experiment_plan.materials.items)
                }
            )
            
            logger.info(f"Plan generation completed - Budget: ${experiment_plan.materials.total_budget}")
            
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            state["error"] = str(e)
            state["error_code"] = "PLAN_GENERATION_ERROR"
            state["error_stage"] = "plan_generation"
            
            await self.sse_manager.emit_error(
                error_code="PLAN_GENERATION_ERROR",
                error_message=f"Plan generation failed: {str(e)}",
                stage="plan_generation"
            )
        
        return state
    
    async def _handle_error_node(self, state: PipelineState) -> PipelineState:
        """
        Pipeline node: Handle errors and cleanup
        
        Args:
            state: Current pipeline state
        
        Returns:
            PipelineState: Updated state with error handling
        """
        logger.error(f"Pipeline error in stage {state.get('error_stage', 'unknown')}: {state.get('error', 'Unknown error')}")
        
        # Emit final error event
        await self.sse_manager.emit_error(
            error_code=state.get("error_code", "PIPELINE_ERROR"),
            error_message=state.get("error", "Pipeline execution failed"),
            stage=state.get("error_stage"),
            details={
                "total_duration": time.time() - state.get("pipeline_start_time", time.time()),
                "completed_stages": list(state.get("stage_durations", {}).keys())
            }
        )
        
        return state
    
    def _should_continue_after_validation(self, state: PipelineState) -> str:
        """
        Conditional edge: Check if pipeline should continue after validation
        
        Args:
            state: Current pipeline state
        
        Returns:
            str: Next node ("continue" or "error")
        """
        if state.get("error"):
            return "error"
        
        validation_result = state.get("validation_result")
        if not validation_result or not validation_result.is_valid:
            state["error"] = "Hypothesis validation failed"
            state["error_code"] = "INVALID_HYPOTHESIS"
            state["error_stage"] = "validation"
            return "error"
        
        return "continue"
    
    def _should_continue_after_qc(self, state: PipelineState) -> str:
        """
        Conditional edge: Check if pipeline should continue after literature QC
        
        Args:
            state: Current pipeline state
        
        Returns:
            str: Next node ("continue" or "error")
        """
        if state.get("error"):
            return "error"
        
        novelty_assessment = state.get("novelty_assessment")
        if not novelty_assessment:
            state["error"] = "Literature QC failed"
            state["error_code"] = "LITERATURE_QC_FAILED"
            state["error_stage"] = "literature_qc"
            return "error"
        
        return "continue"
    
    def _should_complete(self, state: PipelineState) -> str:
        """
        Conditional edge: Check if pipeline should complete
        
        Args:
            state: Current pipeline state
        
        Returns:
            str: Next node ("complete" or "error")
        """
        if state.get("error"):
            return "error"
        
        experiment_plan = state.get("experiment_plan")
        if not experiment_plan:
            state["error"] = "Plan generation failed"
            state["error_code"] = "PLAN_GENERATION_FAILED"
            state["error_stage"] = "plan_generation"
            return "error"
        
        return "complete"
    
    @traceable(name="ai_pipeline_execute")
    async def execute(
        self,
        hypothesis: str,
        user_id: str,
        run_name: Optional[str] = None
    ) -> PipelineState:
        """
        Execute the complete AI pipeline with LangSmith tracing
        
        Args:
            hypothesis: Scientific hypothesis to process
            user_id: User ID for the request
            run_name: Optional LangSmith run name
        
        Returns:
            PipelineState: Final pipeline state
        """
        pipeline_start_time = time.time()
        run_id = str(uuid.uuid4())
        
        # Create initial state
        initial_state: PipelineState = {
            "hypothesis": hypothesis,
            "user_id": user_id,
            "validation_result": None,
            "domain": None,
            "novelty_assessment": None,
            "experiment_plan": None,
            "hypothesis_refinement": None,
            "error": None,
            "error_code": None,
            "error_stage": None,
            "current_stage": "initialization",
            "progress_events": [],
            "pipeline_start_time": pipeline_start_time,
            "stage_durations": {},
            "few_shot_examples_used": 0,
            "langsmith_run_id": run_id
        }
        
        try:
            logger.info(f"Starting AI pipeline execution for user {user_id}")
            
            # Execute the LangGraph workflow
            final_state = await self.graph.ainvoke(
                initial_state,
                config={
                    "run_name": run_name or f"ai_pipeline_{run_id}",
                    "tags": ["ai_pipeline", "experiment_planning"],
                    "metadata": {
                        "user_id": user_id,
                        "hypothesis_length": len(hypothesis),
                        "run_id": run_id
                    }
                }
            )
            
            # Calculate total duration
            total_duration = time.time() - pipeline_start_time
            
            # Log metrics to LangSmith
            if final_state.get("experiment_plan"):
                novelty_assessment = final_state.get("novelty_assessment")
                novelty_value = "unknown"
                if novelty_assessment and hasattr(novelty_assessment, "classification"):
                    novelty_value = novelty_assessment.classification.value
                self.langsmith_logger.log_pipeline_metrics(
                    run_id=run_id,
                    hypothesis_id=user_id,
                    total_duration=total_duration,
                    stage_durations=final_state.get("stage_durations", {}),
                    few_shot_examples_used=final_state.get("few_shot_examples_used", 0),
                    novelty_classification=novelty_value
                )
            
            logger.info(f"AI pipeline completed in {total_duration:.2f}s")
            
            return final_state
        
        except Exception as e:
            logger.error(f"AI pipeline execution failed: {e}")
            
            # Update state with error
            initial_state["error"] = str(e)
            initial_state["error_code"] = "PIPELINE_EXECUTION_ERROR"
            initial_state["error_stage"] = "execution"
            
            # Emit error event
            await self.sse_manager.emit_error(
                error_code="PIPELINE_EXECUTION_ERROR",
                error_message=f"Pipeline execution failed: {str(e)}",
                details={"total_duration": time.time() - pipeline_start_time}
            )
            
            return initial_state


def create_ai_pipeline(
    hypothesis_validator: HypothesisValidator,
    literature_qc_engine: LiteratureQCEngine,
    plan_generator: PlanGenerator,
    sse_manager: SSEManager,
    hypothesis_refiner: Optional[HypothesisRefiner] = None,
    protocols_io_client: Optional[ProtocolsIOClient] = None,
    reproducibility_scorer: Optional[ReproducibilityScorer] = None,
) -> AIPipeline:
    """
    Factory function to create AIPipeline instance
    
    Args:
        hypothesis_validator: Hypothesis validation component
        literature_qc_engine: Literature QC component
        plan_generator: Plan generation component
        sse_manager: SSE stream manager
    
    Returns:
        AIPipeline: Configured pipeline instance
    """
    return AIPipeline(
        hypothesis_validator=hypothesis_validator,
        literature_qc_engine=literature_qc_engine,
        plan_generator=plan_generator,
        sse_manager=sse_manager,
        hypothesis_refiner=hypothesis_refiner,
        protocols_io_client=protocols_io_client,
        reproducibility_scorer=reproducibility_scorer,
    )