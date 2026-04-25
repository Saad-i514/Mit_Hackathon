"""
Health check endpoint with dependency status and metrics
"""
from fastapi import APIRouter, Depends
from datetime import datetime
import time
import httpx
from app.config import settings
from app.database import get_db
from app.utils.monitoring import metrics


router = APIRouter()


async def check_database() -> dict:
    """Check database connectivity and latency"""
    try:
        start = time.time()
        db = get_db()
        # Simple query to test connection
        result = db.table("users").select("id").limit(1).execute()
        latency = (time.time() - start) * 1000
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_openai() -> dict:
    """Check OpenAI API connectivity"""
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"}
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "latency_ms": round(latency, 2)
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_semantic_scholar() -> dict:
    """Check Semantic Scholar API connectivity"""
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={"query": "test", "limit": 1},
                headers={"x-api-key": settings.semantic_scholar_api_key}
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "latency_ms": round(latency, 2)
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_serper() -> dict:
    """Check Serper API connectivity"""
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                json={"q": "test", "num": 1},
                headers={"X-API-KEY": settings.serper_api_key}
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "latency_ms": round(latency, 2)
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Checks status of all dependencies: database, OpenAI, Semantic Scholar, Serper
    """
    # Check all dependencies concurrently
    import asyncio
    
    db_status, openai_status, ss_status, serper_status = await asyncio.gather(
        check_database(),
        check_openai(),
        check_semantic_scholar(),
        check_serper(),
        return_exceptions=True
    )
    
    # Handle exceptions
    def handle_exception(result):
        if isinstance(result, Exception):
            return {"status": "unhealthy", "error": str(result)}
        return result
    
    db_status = handle_exception(db_status)
    openai_status = handle_exception(openai_status)
    ss_status = handle_exception(ss_status)
    serper_status = handle_exception(serper_status)
    
    # Determine overall status
    all_healthy = all(
        s.get("status") == "healthy"
        for s in [db_status, openai_status, ss_status, serper_status]
    )
    
    overall_status = "healthy" if all_healthy else "degraded"
    
    # Record health check result
    metrics.record("health_check", 1 if all_healthy else 0)

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "database": db_status,
            "openai": openai_status,
            "semantic_scholar": ss_status,
            "serper": serper_status
        },
        "version": "1.0.0"
    }


@router.get("/metrics")
async def get_metrics():
    """
    Application metrics endpoint.
    Returns request rates, error rates, pipeline performance, and active alerts.
    Intended for internal monitoring dashboards and alerting systems.
    """
    summary = metrics.get_summary()
    firing_alerts = metrics.check_alerts()

    return {
        **summary,
        "alerts": {
            "firing": firing_alerts,
            "count": len(firing_alerts)
        }
    }
