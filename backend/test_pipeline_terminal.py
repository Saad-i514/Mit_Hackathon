import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.services.openai_client import get_openai_client
from app.services.semantic_scholar import get_semantic_scholar_client
from app.services.serper import get_serper_client
from app.services.learning_engine import get_learning_engine
from app.services.hypothesis_validator import get_hypothesis_validator
from app.services.literature_qc import get_literature_qc_engine
from app.services.plan_generator import get_plan_generator
from app.services.sse_manager import create_sse_manager
from app.graph.ai_pipeline import create_ai_pipeline
from supabase import create_client, Client

async def test_pipeline():
    # Load env
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        print("Missing Supabase credentials in .env")
        return
        
    db: Client = create_client(supabase_url, supabase_key)
    
    # Init components
    openai_client = get_openai_client()
    ss_client = get_semantic_scholar_client()
    serper_client = get_serper_client()
    
    learning_engine = get_learning_engine(openai_client, db)
    hypothesis_validator = get_hypothesis_validator(openai_client)
    literature_qc_engine = get_literature_qc_engine(ss_client, serper_client, openai_client)
    plan_generator = get_plan_generator(openai_client, learning_engine)
    
    sse_manager = create_sse_manager()
    
    pipeline = create_ai_pipeline(
        hypothesis_validator=hypothesis_validator,
        literature_qc_engine=literature_qc_engine,
        plan_generator=plan_generator,
        sse_manager=sse_manager
    )
    
    hypothesis = "DMSO at 10% v/v will provide superior cryoprotection compared to glycerol at 10% v/v for HeLa cell cryopreservation, resulting in ≥ 85% post-thaw viability measured by trypan blue exclusion after 6 months at -80°C."
    user_id = "test-user-terminal"
    
    print("Starting pipeline execution...")
    
    async def consume_events():
        async for event in sse_manager.event_stream():
            print(f"Event Received: {event}")
    
    # Run pipeline and event consumer concurrently
    import threading
    
    task1 = asyncio.create_task(pipeline.execute(hypothesis, user_id))
    task2 = asyncio.create_task(consume_events())
    
    await task1
    sse_manager.close() # signal consumer to stop
    
    try:
        await asyncio.wait_for(task2, timeout=2.0)
    except asyncio.TimeoutError:
        pass
    
    state = task1.result()
    if state.get("error"):
        print(f"Pipeline failed: {state['error']}")
    else:
        print("Pipeline succeeded!")
        plan = state.get("experiment_plan")
        if plan:
            print(f"Plan generated for domain: {plan.domain}")
            print(f"Total budget: ${plan.materials.total_budget}")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
