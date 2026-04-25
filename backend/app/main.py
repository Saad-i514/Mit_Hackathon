"""
AI Scientist Platform - FastAPI Application
Main entry point for the backend API
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv

# Import routers
from app.api.v1.health import router as health_router
from app.api.v1.plans import router as plans_router

# Import LangSmith configuration
from app.services.langsmith import configure_langsmith

# Import error handlers
from app.utils.errors import (
    APIError,
    api_error_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.utils.monitoring import metrics

# Load environment variables
load_dotenv()

# Configure LangSmith tracing
configure_langsmith()

# Initialize FastAPI app
app = FastAPI(
    title="AI Scientist Platform API",
    description="""
## AI Scientist Platform

A production-grade AI-powered experiment planning system that transforms natural-language scientific hypotheses into fully operational experiment plans.

### Pipeline Stages

1. **Hypothesis Validation** — GPT-4o extracts domain, testable claim, and clarification questions
2. **Literature QC** — Concurrent Semantic Scholar + Serper search with novelty classification
3. **Plan Generation** — GPT-4o generates structured experiment plan with RAG few-shot examples

### Authentication

All plan endpoints require a valid Supabase JWT token in the `Authorization: Bearer <token>` header.

### Rate Limiting

- Plan generation: **10 requests per minute** per user
- Other endpoints: **60 requests per minute** per IP

### Real-time Streaming

Plan generation uses **Server-Sent Events (SSE)**. Connect to `POST /api/v1/plans/generate` and consume the event stream for real-time progress updates.

### Supported Domains

Molecular Biology, Cell Biology, Biochemistry, Genetics, Neuroscience, Immunology, Microbiology, Pharmacology, Biophysics, Structural Biology, Genomics, Proteomics, Metabolomics, Ecology, Evolutionary Biology, Developmental Biology, Physiology, Pathology, Bioinformatics, Synthetic Biology
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "AI Scientist Platform",
        "url": "https://github.com/ai-scientist-platform",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check and metrics endpoints for monitoring"
        },
        {
            "name": "Plans",
            "description": "Experiment plan generation, retrieval, and review submission"
        }
    ]
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request for tracing and record metrics"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    request.state.start_time = time.time()

    # Track request count
    metrics.record("request_total", 1, {"path": request.url.path, "method": request.method})

    response = await call_next(request)

    # Calculate request duration
    duration = time.time() - request.state.start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{duration:.3f}"

    # Record duration and error metrics
    metrics.record("request_duration", duration, {
        "path": request.url.path,
        "method": request.method,
        "status": str(response.status_code)
    })
    if response.status_code >= 500:
        metrics.record("request_error", 1, {"path": request.url.path})

    return response

# Error handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(plans_router, prefix="/api/v1", tags=["Plans"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Scientist Platform API",
        "version": "1.0.0",
        "description": "Production-grade AI-powered experiment planning system",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
