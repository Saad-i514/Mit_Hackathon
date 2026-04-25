# Implementation Plan: AI Scientist Platform

## Overview

This implementation plan breaks down the AI Scientist Platform into discrete, actionable tasks. The platform is a production-grade, full-stack AI-powered experiment planning system that transforms natural-language scientific hypotheses into fully operational experiment plans using GPT-4o, LangGraph, FastAPI, Next.js, and Supabase.

The implementation follows a logical progression: project setup → database schema → backend core components → AI pipeline → frontend → review/learning loop → testing → deployment.

## Tasks

- [x] 1. Project Setup and Environment Configuration
  - Create backend directory structure (api/, models/, services/, utils/)
  - Create frontend directory structure (app/, components/, lib/)
  - Set up Python virtual environment (Python 3.12+)
  - Create requirements.txt with pinned dependencies: fastapi, langchain, langgraph, langsmith, openai, supabase, httpx, uvicorn, sse-starlette, slowapi, pydantic
  - Create package.json with Next.js 14, TypeScript, TailwindCSS, shadcn/ui dependencies
  - Create .env.example files for both backend and frontend with all required environment variables
  - Create .gitignore files excluding venv/, __pycache__/, node_modules/, .next/, .env
  - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_

- [x] 2. Database Schema and Migrations
  - [x] 2.1 Create initial database migration file (001_initial_schema.sql)
    - Enable uuid-ossp and vector extensions
    - Create users table with RLS policies
    - Create hypotheses table with domain indexing and RLS policies
    - Create experiment_plans table with JSONB plan_data and GIN index
    - Create reviews table with rating constraints and computed overall_rating
    - Create feedback_embeddings table with vector(1536) column and HNSW index
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 23.1, 23.2, 23.3, 23.4_

  - [x] 2.2 Create database utility functions
    - Implement match_feedback_embeddings() function for cosine similarity search
    - Implement get_average_plan_rating() function for review aggregation
    - _Requirements: 6.5, 9.2_

  - [x] 2.3 Create sample data migration (002_sample_data.sql)
    - Insert test user, hypothesis, and plan for development
    - _Requirements: 23.6_

  - [x] 2.4 Create rollback migration (rollback_001.sql)
    - Drop all tables, functions, and extensions in reverse order
    - _Requirements: 23.5_

- [x] 3. Backend Core Infrastructure
  - [x] 3.1 Create FastAPI application with CORS and middleware
    - Initialize FastAPI app with metadata
    - Configure CORS middleware for localhost:3000 and production domain
    - Add rate limiting middleware using slowapi
    - Add request ID middleware for tracing
    - _Requirements: 14.1, 14.2, 16.1, 27.1, 27.2_

  - [x] 3.2 Implement authentication and authorization
    - Create JWT validation dependency using Supabase JWT secret
    - Implement get_current_user() dependency for protected routes
    - Handle token expiration and invalid token errors
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

  - [x] 3.3 Create Supabase database client
    - Initialize async Supabase client with service key
    - Create database session dependency for route handlers
    - _Requirements: 14.2, 6.1_

  - [x] 3.4 Create Pydantic models for request/response validation
    - Define GeneratePlanRequest with hypothesis length validation
    - Define ReviewSubmission with rating constraints
    - Define ExperimentPlan schema matching design document
    - Define ValidationResult, NoveltyAssessment, ProgressEvent models
    - _Requirements: 1.1, 7.2, 7.6, 24.2_

  - [x] 3.5 Implement health check endpoint
    - Create /health endpoint with dependency status checks
    - Check database, OpenAI, Semantic Scholar, Serper concurrently
    - Return overall status and individual latencies
    - _Requirements: 18.4, 30.1_

- [x] 4. External API Client Setup
  - [x] 4.1 Create OpenAI async client
    - Initialize AsyncOpenAI with API key and timeout configuration
    - Implement retry logic with exponential backoff for rate limits
    - _Requirements: 14.3, 16.6_

  - [x] 4.2 Create Semantic Scholar async client
    - Initialize httpx.AsyncClient with base URL and API key header
    - Implement exponential backoff for 429 rate limit errors (max 3 retries)
    - _Requirements: 2.1, 2.6, 14.3_

  - [x] 4.3 Create Serper async client
    - Initialize httpx.AsyncClient with base URL and API key header
    - Configure timeout and retry logic
    - _Requirements: 2.2, 14.3_

  - [x] 4.4 Configure LangSmith tracing
    - Set environment variables for LangSmith integration
    - Create LangSmith client for custom metric logging
    - _Requirements: 5.5, 5.6, 19.1, 19.2, 19.3_

- [x] 5. Hypothesis Validator Component
  - [x] 5.1 Implement HypothesisValidator class
    - Create __init__ with OpenAI client and domain taxonomy (20 domains)
    - Implement validate() method with GPT-4o for domain extraction
    - Validate hypothesis length (max 5000 characters)
    - Extract testable claim and generate clarification questions
    - Return ValidationResult with is_valid, domain, testable_claim, clarification_questions
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 21.6_

  - [ ]* 5.2 Write unit tests for HypothesisValidator
    - Test valid hypothesis with clear testable claim
    - Test hypothesis exceeding 5000 characters
    - Test empty hypothesis
    - Test ambiguous hypothesis generating clarification questions
    - Test domain extraction for all 20 supported domains
    - _Requirements: 28.1, 28.4_

- [x] 6. Literature QC Engine Component
  - [x] 6.1 Implement LiteratureQCEngine class
    - Create __init__ with Semantic Scholar and Serper clients
    - Implement assess_novelty() method with 30-second timeout
    - Implement _search_semantic_scholar() with exponential backoff
    - Implement _search_serper() for supplementary web search
    - Implement _merge_results() to deduplicate papers by DOI
    - Implement _classify_novelty() using GPT-4o (not_found, similar_exists, exact_match)
    - Return NoveltyAssessment with classification, similar_papers, search_duration
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 14.4_

  - [ ]* 6.2 Write unit tests for LiteratureQCEngine
    - Test successful literature search with papers found
    - Test no papers found scenario
    - Test timeout handling (> 30 seconds)
    - Test rate limit retry logic
    - Test novelty classification for each category
    - _Requirements: 28.1, 28.4_

- [x] 7. Learning Engine Component (RAG)
  - [x] 7.1 Implement LearningEngine class
    - Create __init__ with OpenAI client and Supabase client
    - Implement embed_correction() method using text-embedding-3-small
    - Verify embedding dimensionality (1536 dimensions)
    - Store embedding in feedback_embeddings table with metadata
    - Implement _generate_embedding_with_retry() with exponential backoff (max 2 retries)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 7.2 Implement similarity search for corrections
    - Implement query_corrections() method calling match_feedback_embeddings RPC
    - Use cosine similarity threshold of 0.75
    - Return top-5 most similar corrections filtered by domain
    - _Requirements: 9.1, 9.2, 9.4, 9.5_

  - [ ]* 7.3 Write unit tests for LearningEngine
    - Test embedding generation and storage
    - Test embedding dimensionality validation
    - Test similarity search with various thresholds
    - Test retry logic for embedding failures
    - _Requirements: 28.1, 28.4_

- [x] 8. Plan Generator Component
  - [x] 8.1 Implement PlanGenerator class
    - Create __init__ with OpenAI client and LearningEngine
    - Load system prompt for experiment plan generation
    - Implement generate_plan() method using GPT-4o
    - Query LearningEngine for similar corrections (top-5, similarity ≥ 0.75)
    - Build few-shot context from corrections
    - Generate structured ExperimentPlan with protocol, materials, budget, timeline, validation
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 9.3_

  - [x] 8.2 Implement protocol grounding logic
    - Include protocol steps with references to protocols.io, bio-protocol.org, or publications
    - Add DOI or URL for each protocol source
    - Include critical parameters (temperature, concentration, pH, duration)
    - Add safety considerations and troubleshooting guidance
    - _Requirements: 3.2, 11.1, 11.2, 11.3, 11.4, 11.5, 22.3, 22.4_

  - [x] 8.3 Implement materials and budget generation
    - Include real catalog numbers from Thermo Fisher Scientific and Sigma-Aldrich
    - Add 2024-2025 supplier pricing with unit prices
    - Include supplier name and product URL for each material
    - Mark unverified catalog numbers as "pending_verification"
    - Calculate total budget with line-item breakdown
    - _Requirements: 3.3, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [x] 8.4 Implement timeline and dependency generation
    - Create phased timeline with names, durations, start/end dates
    - Identify explicit dependencies between phases
    - Generate Gantt-style visualization data structure
    - _Requirements: 3.5, 12.1, 12.2, 12.3, 12.4, 12.5_

  - [x] 8.5 Implement validation criteria generation
    - Define quantitative success criteria with measurable thresholds
    - Define failure criteria indicating when to stop
    - Specify validation methods (statistical tests, measurement techniques)
    - Include expected result ranges based on literature
    - _Requirements: 3.6, 13.1, 13.2, 13.3, 13.4, 13.5_

  - [x] 8.6 Implement expert review flagging
    - Implement _identify_review_flags() method
    - Flag unverified catalog numbers
    - Flag protocol steps missing critical parameters
    - Flag vague validation criteria
    - Add flags to metadata.requires_expert_review
    - _Requirements: 22.5_

  - [ ]* 8.7 Write unit tests for PlanGenerator
    - Test plan generation with few-shot examples
    - Test plan generation without few-shot examples
    - Test protocol grounding with references
    - Test materials with catalog numbers
    - Test timeline with dependencies
    - Test validation criteria generation
    - Test expert review flagging
    - _Requirements: 28.1, 28.4_

- [ ] 9. Checkpoint - Ensure all core components pass tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. SSE Stream Manager
  - [x] 10.1 Implement SSEManager class
    - Create event queue using asyncio.Queue
    - Implement emit_progress() method for progress events
    - Implement emit_error() method for error events
    - Implement emit_complete() method for completion events
    - Implement event_stream() async generator for SSE consumption
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 10.2 Write unit tests for SSEManager
    - Test event emission and consumption
    - Test multiple concurrent streams
    - Test error event handling
    - _Requirements: 28.1, 28.4_

- [x] 11. LangGraph Pipeline Implementation
  - [x] 11.1 Define PipelineState TypedDict
    - Include fields: hypothesis, user_id, validation_result, domain, novelty_assessment, experiment_plan, error, current_stage, progress_events
    - _Requirements: 5.4_

  - [x] 11.2 Implement AIPipeline class with LangGraph
    - Create __init__ with HypothesisValidator, LiteratureQCEngine, PlanGenerator, SSEManager
    - Implement _build_graph() method creating StateGraph with 3 stages
    - Add nodes: validate_hypothesis, assess_literature, generate_plan, handle_error
    - Define explicit conditional edges between stages
    - Set entry point to validate_hypothesis
    - Compile graph
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 11.3 Implement pipeline stage nodes
    - Implement _validate_hypothesis_node() emitting progress at 33%
    - Implement _assess_literature_node() emitting progress at 66%
    - Implement _generate_plan_node() emitting progress at 100%
    - Implement _handle_error_node() emitting error events
    - _Requirements: 5.1, 4.2, 4.3_

  - [x] 11.4 Implement conditional edge functions
    - Implement _should_continue_after_validation()
    - Implement _should_continue_after_qc()
    - Implement _should_complete()
    - _Requirements: 5.2, 5.3_

  - [x] 11.5 Implement execute() method with LangSmith tracing
    - Create initial PipelineState
    - Execute graph with ainvoke() and LangSmith config
    - Include run_name, tags, and metadata for tracing
    - Return final state
    - _Requirements: 5.5, 5.6, 19.4, 19.5_

  - [ ]* 11.6 Write integration tests for LangGraph pipeline
    - Test end-to-end pipeline execution with valid hypothesis
    - Test pipeline error handling at each stage
    - Test LangSmith trace generation
    - _Requirements: 28.2, 28.4_

- [x] 12. API Endpoints Implementation
  - [x] 12.1 Implement POST /api/v1/plans/generate endpoint
    - Accept GeneratePlanRequest with hypothesis and user_id
    - Validate JWT authentication
    - Check rate limit (10 requests/minute per user)
    - Create SSEManager and AIPipeline instances
    - Execute pipeline in background task
    - Stream progress events via EventSourceResponse
    - Store completed plan in database
    - Emit complete event with plan_id and plan data
    - Handle errors with structured error events
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 14.1, 27.1_

  - [x] 12.2 Implement GET /api/v1/plans/{plan_id} endpoint
    - Validate JWT authentication
    - Fetch plan from database with RLS enforcement
    - Return plan with metadata and average rating
    - Handle 404 and 403 errors
    - _Requirements: 17.3_

  - [x] 12.3 Implement GET /api/v1/plans endpoint
    - Accept query parameters: status, limit, offset
    - Validate JWT authentication
    - Fetch user's plans with pagination
    - Return plans array with total count
    - _Requirements: 17.3_

  - [x] 12.4 Implement POST /api/v1/plans/{plan_id}/reviews endpoint
    - Accept ReviewSubmission with ratings and corrections
    - Validate JWT authentication
    - Verify plan exists and user has access
    - Store review in database
    - Generate embeddings for corrections asynchronously using LearningEngine
    - Return review_id, overall_rating, embeddings_generated count
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2_

  - [ ]* 12.5 Write API endpoint tests
    - Test plan generation endpoint with SSE stream
    - Test plan retrieval with authentication
    - Test plan listing with pagination
    - Test review submission with embeddings
    - Test rate limiting enforcement
    - Test authentication and authorization errors
    - _Requirements: 28.3, 28.4_

- [ ] 13. Checkpoint - Ensure backend API is functional
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Frontend Project Setup
  - [x] 14.1 Initialize Next.js 14 project with TypeScript
    - Create Next.js app with App Router
    - Configure TypeScript with strict mode
    - Install TailwindCSS and configure
    - Install shadcn/ui and initialize
    - _Requirements: 15.1, 15.4_

  - [x] 14.2 Create TypeScript type definitions
    - Define ExperimentPlan interface matching backend schema
    - Define ProgressEvent, PipelineState, AppState types
    - Define Material, Phase, Criterion, ProtocolStep interfaces
    - Create lib/types.ts file
    - _Requirements: 15.1, 25.2_

  - [x] 14.3 Create environment configuration
    - Create .env.local with NEXT_PUBLIC_API_URL, NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
    - Create lib/config.ts for environment variable access
    - _Requirements: 18.1, 18.3_

- [x] 15. Frontend Core Components
  - [x] 15.1 Create SSEProvider component
    - Implement SSE connection management with EventSource API
    - Implement connect() method with URL and onMessage callback
    - Implement disconnect() method
    - Implement exponential backoff reconnection (max 5 attempts)
    - Handle SSE error events and reconnection
    - Create useSSE() hook for consuming context
    - _Requirements: 4.6, 15.2, 15.3, 25.5_

  - [x] 15.2 Create HypothesisInput component
    - Create textarea with 5000 character limit
    - Display character count
    - Implement submit button with loading state
    - Disable input during plan generation
    - _Requirements: 1.1, 15.5_

  - [x] 15.3 Create PipelineProgress component
    - Display overall progress bar
    - Display stage indicators (validation, literature QC, plan generation)
    - Show stage status icons (pending, in_progress, complete, error)
    - Display latest progress message for each stage
    - Update in real-time from SSE events
    - _Requirements: 4.2, 4.3, 15.3, 15.5_

  - [x] 15.4 Create ExperimentPlanViewer component
    - Display plan header with hypothesis, domain, novelty classification
    - Show few-shot examples count badge
    - Display expert review flags if present
    - Create tabbed interface for protocol, materials, budget, timeline, validation
    - _Requirements: 15.6_

  - [x] 15.5 Create MaterialList component
    - Display materials table with name, catalog number, supplier, quantity, unit price, total price
    - Show verification status badges
    - Include product URL links
    - Display alternatives if available
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 15.6 Create TimelineGantt component
    - Display phases with names, durations, dates
    - Show dependencies between phases
    - Render Gantt-style visualization
    - _Requirements: 12.1, 12.2, 12.5_

  - [x] 15.7 Create ReviewPanel component
    - Create rating controls for each section (1-5 stars)
    - Create correction text inputs for each section
    - Implement submit button
    - Display submission confirmation
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 16. Frontend Pages Implementation
  - [x] 16.1 Create app/layout.tsx root layout
    - Wrap with SSEProvider
    - Include Supabase Auth provider
    - Configure TailwindCSS and fonts
    - _Requirements: 15.1, 17.5_

  - [x] 16.2 Create app/page.tsx landing page
    - Display platform overview and features
    - Include call-to-action to create new plan
    - _Requirements: 15.1_

  - [x] 16.3 Create app/(dashboard)/new-plan/page.tsx
    - Implement state management with useState (pipelineState, currentPlan, progressEvents, error)
    - Implement handleSubmit() to establish SSE connection and POST request
    - Display HypothesisInput component
    - Display PipelineProgress component when events exist
    - Display error messages if pipeline fails
    - Navigate to plan detail page on completion
    - _Requirements: 15.2, 15.3, 15.5, 25.1, 25.2, 25.3_

  - [x] 16.4 Create app/(dashboard)/plans/page.tsx
    - Fetch user's plans from API
    - Display plans list with status, domain, rating
    - Implement pagination
    - _Requirements: 15.6_

  - [x] 16.5 Create app/(dashboard)/plans/[id]/page.tsx
    - Fetch plan by ID from API
    - Display ExperimentPlanViewer component
    - Handle loading and error states
    - _Requirements: 15.6_

  - [x] 16.6 Create app/(dashboard)/plans/[id]/review/page.tsx
    - Display ExperimentPlanViewer in read-only mode
    - Display ReviewPanel component
    - Submit review to API
    - Navigate back to plan detail on success
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 16.7 Write frontend component tests
    - Test HypothesisInput character limit and submission
    - Test PipelineProgress updates from events
    - Test SSEProvider connection and reconnection
    - Test ExperimentPlanViewer rendering
    - Test ReviewPanel submission
    - _Requirements: 28.5, 28.4_

- [x] 17. Authentication Implementation
  - [x] 17.1 Create Supabase client for frontend
    - Initialize Supabase client with URL and anon key
    - Create lib/supabase.ts
    - _Requirements: 17.1, 17.5_

  - [x] 17.2 Create authentication pages
    - Create app/(auth)/login/page.tsx with email/password form
    - Create app/(auth)/signup/page.tsx with registration form
    - Implement OAuth providers (Google, GitHub)
    - _Requirements: 17.6_

  - [x] 17.3 Implement authentication middleware
    - Create middleware.ts to check authentication on protected routes
    - Redirect unauthenticated users to login
    - _Requirements: 17.5_

  - [x] 17.4 Create API client with JWT token
    - Create lib/api-client.ts with fetch wrapper
    - Include Authorization header with JWT token
    - Handle 401 errors with redirect to login
    - _Requirements: 17.4_

- [x] 18. Error Handling and User Experience
  - [x] 18.1 Implement structured error responses
    - Create error response format with error_code, message, details, timestamp, request_id
    - Handle validation errors (HTTP 400)
    - Handle authentication errors (HTTP 401)
    - Handle authorization errors (HTTP 403)
    - Handle not found errors (HTTP 404)
    - Handle rate limit errors (HTTP 429)
    - Handle server errors (HTTP 500, 503)
    - _Requirements: 16.1, 16.2, 16.3, 16.4_

  - [x] 18.2 Implement circuit breaker pattern
    - Create circuit breaker for external API calls
    - Open circuit after 3 consecutive failures
    - Implement 30-second cooldown period
    - _Requirements: 16.2_

  - [x] 18.3 Implement frontend error boundaries
    - Create error boundary component for React
    - Display user-friendly error messages
    - Log errors to console
    - _Requirements: 16.4_

  - [x] 18.4 Add loading states and skeletons
    - Create loading skeletons for plan viewer
    - Add loading spinners for buttons
    - Display progress indicators
    - _Requirements: 15.5_

- [x] 19. Performance Optimization
  - [x] 19.1 Implement request queuing for rate limits
    - Create request queue for OpenAI API calls
    - Implement exponential backoff for retries
    - _Requirements: 16.6, 27.5_

  - [x] 19.2 Add database query optimization
    - Create indexes on frequently queried columns
    - Optimize JSONB queries with GIN indexes
    - _Requirements: 6.3, 29.5_

  - [x] 19.3 Implement frontend code splitting
    - Use dynamic imports for large components
    - Lazy load plan viewer components
    - _Requirements: 29.6_

  - [x] 19.4 Add caching for static data
    - Cache domain taxonomy
    - Cache supplier catalog data
    - _Requirements: 29.1, 29.2, 29.3_

- [x] 20. Deployment Configuration
  - [x] 20.1 Create Vercel configuration
    - Create vercel.json with build settings
    - Configure environment variables
    - Set up regions and function timeouts
    - _Requirements: 18.1, 18.2, 18.5_

  - [x] 20.2 Create Render.com configuration
    - Create render.yaml with service definition
    - Configure environment variables
    - Set up health check path
    - Enable auto-deploy from GitHub
    - _Requirements: 18.2, 18.3, 18.4, 18.5_

  - [x] 20.3 Create database migration scripts
    - Create migration runner script
    - Document migration process
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5_

  - [x] 20.4 Configure monitoring and alerting
    - Set up uptime monitoring for /health endpoint
    - Configure error rate alerts (> 5% over 5 minutes)
    - Set up LangSmith dashboard for pipeline metrics
    - _Requirements: 30.1, 30.2, 30.3, 30.4, 30.5_

- [x] 21. Documentation
  - [x] 21.1 Create README.md files
    - Create backend README with setup instructions
    - Create frontend README with setup instructions
    - Document environment variables
    - Document API endpoints
    - _Requirements: 20.3, 24.1, 24.2, 24.3, 24.4_

  - [x] 21.2 Create API documentation
    - Configure FastAPI automatic OpenAPI documentation
    - Add endpoint descriptions and examples
    - Document authentication requirements
    - Document rate limits
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6_

  - [x] 21.3 Create deployment guide
    - Document Vercel deployment steps
    - Document Render.com deployment steps
    - Document Supabase setup steps
    - Document environment variable configuration
    - _Requirements: 18.1, 18.2, 18.3_

  - [x] 21.4 Create user guide
    - Document hypothesis submission process
    - Document plan review process
    - Document supported scientific domains
    - Include example hypotheses
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5_

- [x] 22. Final Integration and Testing
  - [x] 22.1 Run end-to-end integration tests
    - Test complete flow: hypothesis submission → plan generation → review submission
    - Test SSE streaming with real pipeline execution
    - Test authentication flow
    - Test error handling scenarios
    - _Requirements: 28.2, 28.4, 29.4_

  - [x] 22.2 Perform performance benchmarking
    - Verify hypothesis validation completes within 5 seconds
    - Verify literature QC completes within 30 seconds
    - Verify plan generation completes within 60 seconds
    - Verify end-to-end pipeline completes within 90 seconds (95th percentile)
    - Verify similarity search returns within 500ms
    - _Requirements: 29.1, 29.2, 29.3, 29.4, 29.5_

  - [x] 22.3 Test with sample use cases
    - Test diagnostics hypothesis (paper-based biosensors)
    - Test gut health hypothesis (probiotic effects)
    - Test cell biology hypothesis (cryoprotectant comparison)
    - Test climate science hypothesis (CO2 fixation)
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5_

  - [x] 22.4 Verify quality thresholds
    - Verify all critical parameters specified in protocols
    - Verify catalog numbers are real and verifiable
    - Verify safety considerations included
    - Verify troubleshooting guidance included
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5_

- [x] 23. Final Checkpoint - Production Readiness
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all environment variables configured
  - Verify database migrations applied
  - Verify API documentation accessible
  - Verify monitoring and alerting configured
  - Verify deployment configurations tested

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at major milestones
- The implementation uses Python 3.12+ for backend and TypeScript for frontend
- All async operations use asyncio and httpx for concurrent execution
- LangGraph provides explicit state machine transitions for debuggability
- SSE streaming provides real-time progress updates to users
- RAG-based learning loop improves plan quality over time through few-shot examples
- All database operations enforce Row Level Security for data isolation
- Rate limiting prevents API quota exhaustion
- Circuit breakers provide graceful degradation under failure conditions
