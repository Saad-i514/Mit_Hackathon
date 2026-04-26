"""
API endpoints for experiment plan management
"""
import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse

from app.auth import get_current_user
from app.database import get_db_session
from app.models.requests import GeneratePlanRequest, ReviewSubmission
from app.models.responses import ExperimentPlan, PaginatedResponse
from app.services.openai_client import get_openai_client, OpenAIClient
from app.services.hypothesis_validator import get_hypothesis_validator, HypothesisValidator
from app.services.literature_qc import get_literature_qc_engine, LiteratureQCEngine
from app.services.learning_engine import get_learning_engine, LearningEngine
from app.services.plan_generator import get_plan_generator, PlanGenerator
from app.services.sse_manager import create_sse_manager, SSEManager
from app.services.semantic_scholar import get_semantic_scholar_client, SemanticScholarClient
from app.services.serper import get_serper_client, SerperClient
from app.services.protocols_io import get_protocols_io_client, ProtocolsIOClient
from app.services.hypothesis_refiner import get_hypothesis_refiner, HypothesisRefiner
from app.services.reproducibility_scorer import get_reproducibility_scorer, ReproducibilityScorer
from app.graph.ai_pipeline import create_ai_pipeline, AIPipeline
from app.utils.monitoring import metrics, PipelineTimer
from supabase import Client as AsyncClient


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plans", tags=["plans"])


async def get_pipeline_components(
    openai_client: OpenAIClient = Depends(get_openai_client),
    ss_client: SemanticScholarClient = Depends(get_semantic_scholar_client),
    serper_client: SerperClient = Depends(get_serper_client),
    protocols_io_client: ProtocolsIOClient = Depends(get_protocols_io_client),
    db: AsyncClient = Depends(get_db_session)
) -> Dict[str, Any]:
    """Dependency to create all pipeline components"""
    learning_engine = get_learning_engine(openai_client, db)
    hypothesis_validator = get_hypothesis_validator(openai_client)
    literature_qc_engine = get_literature_qc_engine(ss_client, serper_client, openai_client)
    plan_generator = get_plan_generator(openai_client, learning_engine)
    hypothesis_refiner = get_hypothesis_refiner(openai_client)
    reproducibility_scorer = get_reproducibility_scorer(openai_client)

    return {
        "hypothesis_validator": hypothesis_validator,
        "literature_qc_engine": literature_qc_engine,
        "plan_generator": plan_generator,
        "learning_engine": learning_engine,
        "hypothesis_refiner": hypothesis_refiner,
        "protocols_io_client": protocols_io_client,
        "reproducibility_scorer": reproducibility_scorer,
    }


@router.post(
    "/generate",
    summary="Generate experiment plan",
    description="""
Generate a fully operational experiment plan from a natural-language scientific hypothesis.

**Process:**
1. Validates the hypothesis (domain extraction, testability check)
2. Searches literature for novelty assessment (Semantic Scholar + Serper)
3. Generates structured plan with protocol, materials, budget, timeline, and validation criteria

**Streaming:** Returns a Server-Sent Events (SSE) stream. Events have the format:
```
data: {"type": "progress", "stage": "validation", "progress": 33, "message": "..."}
data: {"type": "complete", "plan_id": "uuid", "summary": {...}}
data: {"type": "error", "error_code": "...", "message": "..."}
```

**Rate limit:** 10 requests per minute per user.
    """,
    response_description="SSE stream of progress events ending with plan_id on completion",
    tags=["Plans"]
)
async def generate_plan(
    request: GeneratePlanRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    components: Dict[str, Any] = Depends(get_pipeline_components),
    db: AsyncClient = Depends(get_db_session)
):
    """
    Generate experiment plan with real-time SSE streaming
    
    Args:
        request: Plan generation request
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        components: Pipeline components
        db: Database session
    
    Returns:
        EventSourceResponse: SSE stream with progress events
    """
    try:
        # Create SSE manager for this request
        sse_manager = create_sse_manager()
        
        # Create AI pipeline
        ai_pipeline = create_ai_pipeline(
            hypothesis_validator=components["hypothesis_validator"],
            literature_qc_engine=components["literature_qc_engine"],
            plan_generator=components["plan_generator"],
            sse_manager=sse_manager,
            hypothesis_refiner=components["hypothesis_refiner"],
            protocols_io_client=components["protocols_io_client"],
            reproducibility_scorer=components["reproducibility_scorer"],
        )
        
        # Start pipeline execution immediately.
        # Using FastAPI BackgroundTasks with a streaming response can delay task
        # execution until response completion, which causes no SSE progress events.
        pipeline_task = asyncio.create_task(
            execute_pipeline_and_store(
                ai_pipeline=ai_pipeline,
                sse_manager=sse_manager,
                hypothesis=request.hypothesis,
                user_id=current_user.id,
                db=db,
            )
        )

        def _log_pipeline_task_result(task: asyncio.Task):
            try:
                exc = task.exception()
                if exc:
                    logger.error(f"Pipeline task failed with unhandled exception: {exc}")
            except asyncio.CancelledError:
                logger.warning("Pipeline task was cancelled")

        pipeline_task.add_done_callback(_log_pipeline_task_result)
        
        # Return SSE stream
        return EventSourceResponse(
            sse_manager.event_stream(),
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to start plan generation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "GENERATION_START_FAILED",
                "message": "Failed to start plan generation",
                "details": str(e)
            }
        )


async def execute_pipeline_and_store(
    ai_pipeline: AIPipeline,
    sse_manager: SSEManager,
    hypothesis: str,
    user_id: str,
    db: AsyncClient
):
    """
    Execute AI pipeline and store results in database
    
    Args:
        ai_pipeline: AI pipeline instance
        sse_manager: SSE manager for progress updates
        hypothesis: Scientific hypothesis
        user_id: User ID
        db: Database session
    """
    try:
        # Execute pipeline
        with PipelineTimer(hypothesis_id=user_id) as timer:
            timer.start_stage("validation")
            final_state = await ai_pipeline.execute(
                hypothesis=hypothesis,
                user_id=user_id,
                run_name=f"plan_generation_{user_id}"
            )
        
        # Check if pipeline completed successfully
        if final_state.get("error"):
            logger.error(f"Pipeline failed: {final_state['error']}")
            metrics.increment("pipeline_error")
            return
        
        experiment_plan = final_state.get("experiment_plan")
        if not experiment_plan:
            logger.error("Pipeline completed but no experiment plan generated")
            await sse_manager.emit_error(
                error_code="NO_PLAN_GENERATED",
                error_message="Pipeline completed but no plan was generated"
            )
            return
        
        # Store plan in database
        plan_id = str(uuid.uuid4())

        # Insert into hypotheses table (sync Supabase client)
        # Note: user_id FK references auth.users via Supabase, not our users table
        try:
            db.table("hypotheses").insert({
                "id": plan_id,
                "user_id": user_id,
                "hypothesis_text": hypothesis,
                "domain": experiment_plan.domain,
                "validation_status": "valid",
            }).execute()
        except Exception as e:
            logger.warning(f"Could not insert hypothesis record: {e} — continuing")

        # Insert into experiment_plans table
        plan_result = db.table("experiment_plans").insert({
            "id": plan_id,
            "hypothesis_id": plan_id,
            "user_id": user_id,
            "plan_data": experiment_plan.model_dump(),
            "novelty_classification": experiment_plan.novelty_classification.value,
            "model_version": experiment_plan.metadata.model_version,
            "few_shot_examples_used": experiment_plan.metadata.few_shot_examples_used,
            "requires_expert_review": experiment_plan.metadata.requires_expert_review,
            "status": "draft",
        }).execute()

        if not plan_result.data:
            raise Exception("Failed to insert experiment plan")
        
        # Calculate total duration
        total_duration = sum(final_state.get("stage_durations", {}).values())
        
        # Emit completion event
        await sse_manager.emit_complete(
            plan_id=plan_id,
            total_duration=total_duration,
            summary={
                "domain": experiment_plan.domain,
                "novelty_classification": experiment_plan.novelty_classification.value,
                "total_budget": experiment_plan.materials.total_budget,
                "protocol_steps": len(experiment_plan.protocol.steps),
                "materials_count": len(experiment_plan.materials.items),
                "few_shot_examples_used": experiment_plan.metadata.few_shot_examples_used,
                "requires_expert_review": len(experiment_plan.metadata.requires_expert_review) > 0
            }
        )
        
        logger.info(f"Plan generation completed successfully: {plan_id}")
    
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        await sse_manager.emit_error(
            error_code="PIPELINE_EXECUTION_ERROR",
            error_message=f"Pipeline execution failed: {str(e)}"
        )


@router.get(
    "/{plan_id}",
    summary="Get experiment plan",
    description="Retrieve a specific experiment plan by ID. Only returns plans owned by the authenticated user.",
    response_model=ExperimentPlan,
    responses={
        404: {"description": "Plan not found"},
        403: {"description": "Access denied"}
    },
    tags=["Plans"]
)
async def get_plan(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncClient = Depends(get_db_session)
) -> ExperimentPlan:
    """
    Get experiment plan by ID
    
    Args:
        plan_id: Plan ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        ExperimentPlan: Experiment plan data
    """
    try:
        # Fetch plan from database with RLS enforcement
        result = db.table("experiment_plans").select(
            "*"
        ).eq("id", plan_id).eq("user_id", current_user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "PLAN_NOT_FOUND",
                    "message": "Experiment plan not found"
                }
            )
        
        plan_data_row = result.data[0]
        raw_plan_data = plan_data_row.get("plan_data")
        if not raw_plan_data:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "PLAN_DATA_MISSING", "message": "Plan data is empty"}
            )

        # Get average rating (graceful fallback)
        try:
            rating_result = db.rpc(
                "get_average_plan_rating",
                {"plan_uuid": plan_id}
            ).execute()
            average_rating = float(rating_result.data) if rating_result.data else None
        except Exception:
            average_rating = None

        # Parse plan data
        experiment_plan = ExperimentPlan(**raw_plan_data)

        # Inject average rating into metadata if available
        if average_rating is not None:
            experiment_plan.metadata.average_rating = average_rating

        return experiment_plan
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "PLAN_FETCH_ERROR",
                "message": "Failed to fetch experiment plan",
                "details": str(e)
            }
        )


@router.get(
    "",
    summary="List experiment plans",
    description="List all experiment plans for the authenticated user with optional status filtering and pagination.",
    response_model=PaginatedResponse,
    tags=["Plans"]
)
async def list_plans(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Number of plans to return"),
    offset: int = Query(0, ge=0, description="Number of plans to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncClient = Depends(get_db_session)
) -> PaginatedResponse:
    """
    List user's experiment plans with pagination
    
    Args:
        status: Optional status filter
        limit: Number of plans to return
        offset: Number of plans to skip
        current_user: Authenticated user
        db: Database session
    
    Returns:
        PaginatedResponse: Paginated list of plans
    """
    try:
        # Build query - select all columns, filter client-side for domain/budget
        query = db.table("experiment_plans").select(
            "id, status, generated_at, plan_data",
            count="exact"
        ).eq("user_id", current_user.id)
        
        # Add status filter if provided
        if status:
            query = query.eq("status", status)
        
        # Add pagination
        query = query.range(offset, offset + limit - 1).order("generated_at", desc=True)
        
        # Execute query
        result = query.execute()
        
        # Format response
        plans = []
        for plan in result.data:
            plan_data = plan.get("plan_data", {})
            plans.append({
                "id": plan["id"],
                "status": plan["status"],
                "domain": plan_data.get("domain"),
                "total_budget": plan_data.get("materials", {}).get("total_budget"),
                "created_at": plan.get("generated_at") or plan.get("created_at"),
            })
        
        return PaginatedResponse(
            items=plans,
            total=result.count,
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        logger.error(f"Failed to list plans: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "PLANS_LIST_ERROR",
                "message": "Failed to list experiment plans",
                "details": str(e)
            }
        )


@router.post(
    "/{plan_id}/reviews",
    summary="Submit expert review",
    description="""
Submit an expert review for an experiment plan. Ratings are 1-5 for each section.
Corrections are stored as text and asynchronously embedded for RAG-based learning.
    """,
    responses={
        404: {"description": "Plan not found"},
    },
    tags=["Plans"]
)
async def submit_review(
    plan_id: str,
    review: ReviewSubmission,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    components: Dict[str, Any] = Depends(get_pipeline_components),
    db: AsyncClient = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Submit review for experiment plan
    
    Args:
        plan_id: Plan ID
        review: Review submission data
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        components: Pipeline components
        db: Database session
    
    Returns:
        Dict: Review submission result
    """
    try:
        # Verify plan exists and user has access
        plan_result_data = db.table("experiment_plans").select(
            "id, plan_data"
        ).eq("id", plan_id).eq("user_id", current_user.id).execute()

        if not plan_result_data.data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "PLAN_NOT_FOUND",
                    "message": "Experiment plan not found"
                }
            )
        
        # Calculate overall rating
        ratings = [
            review.protocol_rating,
            review.materials_rating,
            review.timeline_rating,
            review.validation_rating
        ]
        overall_rating = sum(ratings) / len(ratings)
        
        # Insert review into database
        # overall_rating is GENERATED ALWAYS AS computed column - don't insert it
        review_id = str(uuid.uuid4())
        review_result = db.table("reviews").insert({
            "id": review_id,
            "plan_id": plan_id,
            "user_id": current_user.id,
            "protocol_rating": review.protocol_rating,
            "materials_rating": review.materials_rating,
            "budget_rating": review.materials_rating,
            "timeline_rating": review.timeline_rating,
            "validation_rating": review.validation_rating,
            "corrections": {
                "protocol": review.protocol_corrections,
                "materials": review.materials_corrections,
                "timeline": review.timeline_corrections,
                "validation": review.validation_corrections,
            },
        }).execute()

        if not review_result.data:
            raise Exception("Failed to insert review")
        
        # Generate embeddings for corrections in background
        background_tasks.add_task(
            generate_correction_embeddings,
            learning_engine=components["learning_engine"],
            plan_data=plan_result_data.data[0]["plan_data"],
            review=review,
            review_id=review_id
        )
        
        return {
            "review_id": review_id,
            "overall_rating": overall_rating,
            "embeddings_generated": "processing"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit review for plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "REVIEW_SUBMISSION_ERROR",
                "message": "Failed to submit review",
                "details": str(e)
            }
        )


async def generate_correction_embeddings(
    learning_engine: LearningEngine,
    plan_data: Dict[str, Any],
    review: ReviewSubmission,
    review_id: str
):
    """
    Generate embeddings for review corrections in background
    
    Args:
        learning_engine: Learning engine instance
        plan_data: Original plan data
        review: Review submission
        review_id: Review ID
    """
    try:
        corrections = []
        
        # Collect non-empty corrections
        if review.protocol_corrections:
            corrections.append({
                "section": "protocol",
                "original": json.dumps(plan_data.get("protocol", {})),
                "correction": review.protocol_corrections,
                "rating": review.protocol_rating
            })
        
        if review.materials_corrections:
            corrections.append({
                "section": "materials",
                "original": json.dumps(plan_data.get("materials", {})),
                "correction": review.materials_corrections,
                "rating": review.materials_rating
            })
        
        if review.timeline_corrections:
            corrections.append({
                "section": "timeline",
                "original": json.dumps(plan_data.get("timeline", {})),
                "correction": review.timeline_corrections,
                "rating": review.timeline_rating
            })
        
        if review.validation_corrections:
            corrections.append({
                "section": "validation_criteria",
                "original": json.dumps(plan_data.get("validation_criteria", {})),
                "correction": review.validation_corrections,
                "rating": review.validation_rating
            })
        
        # Generate embeddings for each correction
        embeddings_count = 0
        for correction in corrections:
            await learning_engine.embed_correction(
                section=correction["section"],
                original_content=correction["original"],
                corrected_content=correction["correction"],
                domain=plan_data.get("domain", "unknown"),
                rating=correction["rating"],
                review_id=review_id,
            )
            embeddings_count += 1
        
        logger.info(f"Generated {embeddings_count} correction embeddings for review {review_id}")
    
    except Exception as e:
        logger.error(f"Failed to generate correction embeddings for review {review_id}: {e}")
