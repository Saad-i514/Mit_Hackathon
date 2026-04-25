# Requirements Document

## Introduction

The AI Scientist Platform is a production-grade, full-stack AI-powered experiment planning system that accepts natural-language scientific hypotheses and autonomously generates fully operational experiment plans. The system provides protocol steps grounded in real published protocols, materials with actual catalog numbers and suppliers, realistic budget estimates with current pricing, phased timelines with dependencies, and success/failure validation criteria. The platform includes a scientist review and learning loop where corrections are embedded and used to improve future experiment plans through RAG-based continuous improvement.

## Glossary

- **Platform**: The complete AI Scientist Platform system including frontend, backend, database, and AI pipeline
- **Hypothesis_Validator**: Component that validates natural-language scientific hypotheses and extracts domain information
- **Literature_QC_Engine**: Component that searches scientific literature and classifies novelty of hypotheses
- **Plan_Generator**: Component that generates structured experiment plans using GPT-4o
- **Review_System**: Component that enables scientists to review, rate, and correct generated plans
- **Learning_Engine**: Component that embeds corrections and injects them as few-shot context for future plans
- **API_Gateway**: FastAPI backend service that orchestrates the AI pipeline
- **Web_Client**: Next.js frontend application that provides the user interface
- **Vector_Store**: Supabase pgvector database for similarity search and embeddings
- **Pipeline_Graph**: LangGraph stateful AI pipeline with explicit directed graph transitions
- **SSE_Stream**: Server-Sent Events stream for real-time progress updates
- **Protocol_Repository**: External sources like protocols.io and bio-protocol.org
- **Supplier_Catalog**: Real supplier databases (Thermo Fisher, Sigma-Aldrich, etc.)
- **Experiment_Plan**: Complete structured output including protocol, materials, budget, timeline, and validation criteria
- **Novelty_Classification**: Classification result (not_found, similar_exists, or exact_match)
- **Feedback_Embedding**: Vector embedding of scientist corrections stored in Vector_Store
- **Principal_Investigator**: Target user who must trust the plan enough to order materials and start experiments

## Requirements

### Requirement 1: Hypothesis Input and Validation

**User Story:** As a Principal_Investigator, I want to submit natural-language scientific hypotheses, so that the Platform can generate actionable experiment plans.

#### Acceptance Criteria

1. WHEN a user submits a hypothesis via the Web_Client, THE API_Gateway SHALL accept text input up to 5000 characters
2. THE Hypothesis_Validator SHALL extract the scientific domain from the hypothesis text
3. WHEN the hypothesis is ambiguous or incomplete, THE Hypothesis_Validator SHALL return specific clarification questions
4. THE Hypothesis_Validator SHALL validate that the hypothesis contains a testable claim
5. WHEN validation fails, THE API_Gateway SHALL return a structured error message with improvement suggestions

### Requirement 2: Literature Quality Control

**User Story:** As a Principal_Investigator, I want the Platform to assess novelty of my hypothesis against existing literature, so that I can understand the research landscape.

#### Acceptance Criteria

1. WHEN a validated hypothesis is received, THE Literature_QC_Engine SHALL query Semantic Scholar API for relevant papers
2. THE Literature_QC_Engine SHALL query Serper Web Search API for additional scientific sources
3. THE Literature_QC_Engine SHALL classify novelty as one of: not_found, similar_exists, or exact_match
4. WHEN similar research exists, THE Literature_QC_Engine SHALL return citations with DOI and publication year
5. THE Literature_QC_Engine SHALL complete literature search within 30 seconds
6. WHEN API rate limits are exceeded, THE Literature_QC_Engine SHALL implement exponential backoff with maximum 3 retries

### Requirement 3: Experiment Plan Generation

**User Story:** As a Principal_Investigator, I want the Platform to generate complete experiment plans with real protocols and materials, so that I can start experiments immediately.

#### Acceptance Criteria

1. WHEN literature QC is complete, THE Plan_Generator SHALL generate a structured Experiment_Plan using GPT-4o
2. THE Experiment_Plan SHALL include protocol steps grounded in Protocol_Repository sources
3. THE Experiment_Plan SHALL include materials with real catalog numbers from Supplier_Catalog
4. THE Experiment_Plan SHALL include budget estimates reflecting 2024-2025 supplier pricing
5. THE Experiment_Plan SHALL include phased timeline with explicit dependencies between phases
6. THE Experiment_Plan SHALL include success and failure validation criteria
7. FOR ALL materials listed, THE Plan_Generator SHALL verify catalog numbers exist in Supplier_Catalog databases
8. WHEN a protocol step references a published protocol, THE Plan_Generator SHALL include the protocol DOI or URL

### Requirement 4: Real-Time Pipeline Progress Streaming

**User Story:** As a Principal_Investigator, I want to see real-time progress of plan generation, so that I understand what the Platform is doing.

#### Acceptance Criteria

1. WHEN the Pipeline_Graph begins execution, THE API_Gateway SHALL establish an SSE_Stream connection to the Web_Client
2. WHEN each pipeline stage completes, THE API_Gateway SHALL emit a progress event via SSE_Stream within 500ms
3. THE SSE_Stream SHALL include stage name, status, and completion percentage
4. WHEN an error occurs in any stage, THE API_Gateway SHALL emit an error event with diagnostic information
5. THE Web_Client SHALL display progress updates in real-time without page refresh
6. WHEN the SSE_Stream connection is lost, THE Web_Client SHALL attempt reconnection with exponential backoff

### Requirement 5: LangGraph Pipeline Orchestration

**User Story:** As a developer, I want the AI pipeline to use LangGraph with deterministic transitions, so that the system is maintainable and debuggable.

#### Acceptance Criteria

1. THE Pipeline_Graph SHALL implement exactly three stages: Input Validation, Literature QC, and Plan Generation
2. THE Pipeline_Graph SHALL use explicit directed graph transitions between stages
3. WHEN a stage fails, THE Pipeline_Graph SHALL transition to an error state without proceeding
4. THE Pipeline_Graph SHALL maintain state persistence across stage transitions
5. THE API_Gateway SHALL integrate LangSmith tracing for all Pipeline_Graph executions
6. FOR ALL pipeline executions, THE Pipeline_Graph SHALL log trace data to LangSmith within 2 seconds of completion

### Requirement 6: Database Schema and Vector Storage

**User Story:** As a developer, I want a robust database schema with vector search capabilities, so that the Platform can store and retrieve experiment plans and feedback embeddings.

#### Acceptance Criteria

1. THE Vector_Store SHALL implement tables for: users, hypotheses, experiment_plans, reviews, and feedback_embeddings
2. THE Vector_Store SHALL use pgvector extension for similarity search on Feedback_Embedding vectors
3. THE Vector_Store SHALL implement Row Level Security (RLS) policies for all tables
4. WHEN a Feedback_Embedding is stored, THE Vector_Store SHALL index it for similarity search within 1 second
5. THE Vector_Store SHALL support queries returning top-k similar embeddings with cosine similarity scores
6. THE Vector_Store SHALL maintain referential integrity between experiment_plans and reviews tables

### Requirement 7: Scientist Review Interface

**User Story:** As a Principal_Investigator, I want to review and correct generated experiment plans, so that the Platform learns from my expertise.

#### Acceptance Criteria

1. WHEN an Experiment_Plan is generated, THE Web_Client SHALL display a review panel with rating controls
2. THE Review_System SHALL allow scientists to rate each section: protocol, materials, budget, timeline, validation
3. THE Review_System SHALL accept free-text corrections for any plan section
4. WHEN a scientist submits a review, THE API_Gateway SHALL store the review in the Vector_Store within 2 seconds
5. THE Web_Client SHALL display review submission confirmation with timestamp
6. THE Review_System SHALL support rating scales from 1 to 5 for each section

### Requirement 8: Feedback Embedding and Storage

**User Story:** As a developer, I want scientist corrections to be embedded and stored as vectors, so that the Learning_Engine can retrieve relevant feedback for future plans.

#### Acceptance Criteria

1. WHEN a scientist submits a correction, THE Learning_Engine SHALL generate a Feedback_Embedding using OpenAI embeddings API
2. THE Learning_Engine SHALL store the Feedback_Embedding in the Vector_Store with metadata: hypothesis_domain, correction_text, timestamp, and scientist_id
3. THE Learning_Engine SHALL complete embedding generation within 3 seconds
4. WHEN embedding generation fails, THE Learning_Engine SHALL retry up to 2 times with exponential backoff
5. FOR ALL stored embeddings, THE Learning_Engine SHALL verify vector dimensionality matches OpenAI model output (1536 dimensions for text-embedding-3-small)

### Requirement 9: RAG-Based Continuous Improvement

**User Story:** As a Principal_Investigator, I want the Platform to learn from past corrections, so that future experiment plans improve over time.

#### Acceptance Criteria

1. WHEN generating a new Experiment_Plan, THE Learning_Engine SHALL query the Vector_Store for similar past corrections
2. THE Learning_Engine SHALL retrieve top-5 most similar Feedback_Embedding vectors based on hypothesis domain and content
3. WHEN relevant corrections exist, THE Plan_Generator SHALL inject them as few-shot examples in the GPT-4o prompt
4. THE Learning_Engine SHALL use cosine similarity threshold of 0.75 for relevance filtering
5. WHEN no relevant corrections exist (similarity < 0.75), THE Plan_Generator SHALL proceed without few-shot examples
6. FOR ALL plans generated with few-shot examples, THE Platform SHALL track improvement metrics compared to baseline plans

### Requirement 10: Real Catalog Numbers and Pricing

**User Story:** As a Principal_Investigator, I want all materials to have real catalog numbers and current pricing, so that I can order them immediately.

#### Acceptance Criteria

1. THE Plan_Generator SHALL include catalog numbers from Thermo Fisher Scientific, Sigma-Aldrich, or equivalent suppliers
2. THE Plan_Generator SHALL include unit prices reflecting 2024-2025 supplier pricing
3. THE Plan_Generator SHALL include supplier name and product URL for each material
4. WHEN a catalog number cannot be verified, THE Plan_Generator SHALL mark it as "pending verification" and suggest alternatives
5. THE Experiment_Plan SHALL include total budget calculation with line-item breakdown
6. THE Plan_Generator SHALL include quantity, unit, and unit price for each material

### Requirement 11: Protocol Grounding in Published Sources

**User Story:** As a Principal_Investigator, I want protocol steps to reference real published protocols, so that I can trust the methodology.

#### Acceptance Criteria

1. THE Plan_Generator SHALL ground protocol steps in Protocol_Repository sources (protocols.io, bio-protocol.org, or peer-reviewed publications)
2. WHEN a protocol step is adapted from a source, THE Plan_Generator SHALL include the source citation with DOI or URL
3. THE Plan_Generator SHALL include protocol step numbers, descriptions, duration, and critical parameters
4. WHEN multiple protocol variants exist, THE Plan_Generator SHALL select the most cited or recently published version
5. THE Experiment_Plan SHALL include a references section listing all protocol sources

### Requirement 12: Phased Timeline with Dependencies

**User Story:** As a Principal_Investigator, I want a phased timeline with explicit dependencies, so that I can schedule experiments efficiently.

#### Acceptance Criteria

1. THE Experiment_Plan SHALL include phases with names, durations, and start/end dates
2. THE Plan_Generator SHALL identify dependencies between phases (e.g., "Phase 2 requires Phase 1 completion")
3. THE Plan_Generator SHALL calculate realistic durations based on protocol complexity and material availability
4. WHEN a phase has dependencies, THE Experiment_Plan SHALL list prerequisite phases explicitly
5. THE Experiment_Plan SHALL include a Gantt-style timeline visualization data structure
6. THE Plan_Generator SHALL account for equipment availability and scientist workload in timeline estimates

### Requirement 13: Success and Failure Validation Criteria

**User Story:** As a Principal_Investigator, I want clear success and failure criteria, so that I can objectively evaluate experiment outcomes.

#### Acceptance Criteria

1. THE Experiment_Plan SHALL include quantitative success criteria with measurable thresholds
2. THE Experiment_Plan SHALL include failure criteria that indicate when to stop or pivot
3. THE Plan_Generator SHALL define validation methods for each criterion (e.g., statistical tests, measurement techniques)
4. WHEN multiple validation approaches exist, THE Plan_Generator SHALL recommend the most reliable method
5. THE Experiment_Plan SHALL include expected result ranges based on literature precedent

### Requirement 14: Asynchronous Backend Architecture

**User Story:** As a developer, I want the backend to use async/await throughout, so that the system handles concurrent requests efficiently.

#### Acceptance Criteria

1. THE API_Gateway SHALL implement all route handlers using async def functions
2. THE API_Gateway SHALL use asynchronous database clients for Vector_Store operations
3. THE API_Gateway SHALL use asynchronous HTTP clients for external API calls (Semantic Scholar, Serper, OpenAI)
4. WHEN multiple external API calls are independent, THE API_Gateway SHALL execute them concurrently using asyncio.gather
5. THE API_Gateway SHALL handle at least 50 concurrent requests without degradation

### Requirement 15: Frontend Real-Time Updates

**User Story:** As a Principal_Investigator, I want the frontend to update in real-time as the plan generates, so that I see progress immediately.

#### Acceptance Criteria

1. THE Web_Client SHALL use Next.js 14 App Router with TypeScript
2. THE Web_Client SHALL establish SSE connections using EventSource API
3. WHEN a progress event is received, THE Web_Client SHALL update the UI within 100ms
4. THE Web_Client SHALL use TailwindCSS and shadcn/ui components for consistent styling
5. THE Web_Client SHALL display loading states, progress bars, and stage indicators
6. WHEN the pipeline completes, THE Web_Client SHALL display the complete Experiment_Plan with expandable sections

### Requirement 16: Production-Grade Error Handling

**User Story:** As a developer, I want comprehensive error handling, so that the Platform degrades gracefully under failure conditions.

#### Acceptance Criteria

1. WHEN an external API fails, THE API_Gateway SHALL return a structured error response with error code and message
2. THE API_Gateway SHALL implement circuit breaker patterns for external API calls with 3 consecutive failures triggering open state
3. WHEN the Vector_Store is unavailable, THE API_Gateway SHALL return HTTP 503 with retry-after header
4. THE Web_Client SHALL display user-friendly error messages without exposing internal details
5. THE Platform SHALL log all errors to LangSmith with full context and stack traces
6. WHEN GPT-4o rate limits are exceeded, THE Plan_Generator SHALL queue requests with exponential backoff

### Requirement 17: Authentication and Authorization

**User Story:** As a Principal_Investigator, I want secure authentication, so that my experiment plans are private.

#### Acceptance Criteria

1. THE Platform SHALL implement authentication using Supabase Auth
2. THE Vector_Store SHALL enforce Row Level Security policies based on user_id
3. WHEN a user accesses an Experiment_Plan, THE Vector_Store SHALL verify ownership before returning data
4. THE API_Gateway SHALL validate JWT tokens on all protected endpoints
5. THE Web_Client SHALL redirect unauthenticated users to login page
6. THE Platform SHALL support email/password and OAuth authentication methods

### Requirement 18: Deployment Configuration

**User Story:** As a developer, I want deployment configurations for Vercel and Render.com, so that the Platform can be deployed to production.

#### Acceptance Criteria

1. THE Web_Client SHALL include vercel.json configuration for Next.js deployment
2. THE API_Gateway SHALL include render.yaml configuration for FastAPI deployment
3. THE Platform SHALL use environment variables for all API keys and credentials
4. THE deployment configuration SHALL include health check endpoints for monitoring
5. THE API_Gateway SHALL serve on port 8000 with CORS configured for Web_Client origin
6. THE Web_Client SHALL use environment variables for API_Gateway base URL

### Requirement 19: LangSmith Observability Integration

**User Story:** As a developer, I want full trace visibility in LangSmith, so that I can debug and optimize the AI pipeline.

#### Acceptance Criteria

1. THE Pipeline_Graph SHALL integrate LangSmith tracing for all LangGraph executions
2. THE API_Gateway SHALL configure LangSmith API key via environment variable
3. WHEN a pipeline execution completes, THE Platform SHALL send trace data to LangSmith within 5 seconds
4. THE LangSmith traces SHALL include: stage names, durations, input/output data, and error messages
5. THE Platform SHALL tag traces with hypothesis_id for correlation
6. THE Platform SHALL use LangSmith free tier limits (5000 traces per month)

### Requirement 20: Python Virtual Environment Setup

**User Story:** As a developer, I want a Python virtual environment with all dependencies, so that the backend runs consistently across environments.

#### Acceptance Criteria

1. THE Platform SHALL include a requirements.txt file with pinned dependency versions
2. THE requirements.txt SHALL include: fastapi, langchain, langgraph, langsmith, openai, supabase, httpx, uvicorn
3. THE Platform SHALL include setup instructions for creating a virtual environment using venv
4. THE Platform SHALL use Python 3.12 as the minimum required version
5. THE Platform SHALL include a .gitignore file excluding venv/ and __pycache__/ directories

### Requirement 21: Sample Use Case Support

**User Story:** As a Principal_Investigator, I want the Platform to handle diverse scientific domains, so that I can use it for various research areas.

#### Acceptance Criteria

1. THE Platform SHALL support diagnostics hypotheses (e.g., paper-based electrochemical biosensors)
2. THE Platform SHALL support gut health hypotheses (e.g., probiotic effects on intestinal permeability)
3. THE Platform SHALL support cell biology hypotheses (e.g., cryoprotectant comparisons)
4. THE Platform SHALL support climate science hypotheses (e.g., CO2 fixation in bioelectrochemical systems)
5. FOR ALL supported domains, THE Plan_Generator SHALL generate domain-appropriate protocols and materials
6. THE Hypothesis_Validator SHALL recognize at least 20 distinct scientific domains

### Requirement 22: Quality Threshold for Principal Investigator Trust

**User Story:** As a Principal_Investigator, I want experiment plans that meet professional standards, so that I can trust them enough to order materials and start experiments.

#### Acceptance Criteria

1. THE Experiment_Plan SHALL include all information required to begin experiments within 1 week of material delivery
2. THE Plan_Generator SHALL verify that all critical parameters (temperatures, concentrations, durations) are specified
3. THE Experiment_Plan SHALL include safety considerations and hazard warnings for dangerous materials
4. THE Plan_Generator SHALL include troubleshooting guidance for common protocol failure modes
5. WHEN the Plan_Generator cannot provide sufficient detail, THE Platform SHALL flag sections as "requires expert review"
6. THE Review_System SHALL track average scientist ratings, with target threshold of 4.0/5.0 or higher for production readiness

### Requirement 23: Database Migration and Schema Management

**User Story:** As a developer, I want database migrations for schema versioning, so that the Vector_Store schema can evolve safely.

#### Acceptance Criteria

1. THE Platform SHALL include SQL migration files for initial schema creation
2. THE migration files SHALL create tables: users, hypotheses, experiment_plans, reviews, feedback_embeddings
3. THE migration files SHALL enable pgvector extension and create vector indexes
4. THE migration files SHALL create RLS policies for all tables
5. THE Platform SHALL include rollback migrations for schema changes
6. THE migration files SHALL include sample data for development and testing

### Requirement 24: API Documentation

**User Story:** As a developer, I want comprehensive API documentation, so that I can integrate with the Platform programmatically.

#### Acceptance Criteria

1. THE API_Gateway SHALL serve OpenAPI documentation at /docs endpoint
2. THE API documentation SHALL include request/response schemas for all endpoints
3. THE API documentation SHALL include authentication requirements for protected endpoints
4. THE API documentation SHALL include example requests and responses
5. THE API_Gateway SHALL use FastAPI automatic documentation generation
6. THE API documentation SHALL include rate limiting information

### Requirement 25: Frontend State Management

**User Story:** As a developer, I want predictable state management in the frontend, so that the Web_Client handles complex UI interactions reliably.

#### Acceptance Criteria

1. THE Web_Client SHALL use React hooks (useState, useEffect, useContext) for state management
2. THE Web_Client SHALL maintain pipeline state (idle, validating, searching, generating, complete, error)
3. WHEN the user navigates away during plan generation, THE Web_Client SHALL preserve pipeline state
4. THE Web_Client SHALL implement optimistic UI updates for review submissions
5. THE Web_Client SHALL handle SSE reconnection without losing pipeline progress
6. THE Web_Client SHALL persist completed Experiment_Plan data in browser storage for offline viewing

### Requirement 26: Parser and Pretty Printer for Experiment Plans

**User Story:** As a developer, I want to parse and format experiment plans consistently, so that the Platform can validate and display plans reliably.

#### Acceptance Criteria

1. THE Platform SHALL include an Experiment_Plan_Parser that parses JSON experiment plans into structured objects
2. WHEN an invalid experiment plan is provided, THE Experiment_Plan_Parser SHALL return descriptive validation errors
3. THE Platform SHALL include an Experiment_Plan_Printer that formats structured objects back into valid JSON
4. FOR ALL valid Experiment_Plan objects, parsing then printing then parsing SHALL produce an equivalent object (round-trip property)
5. THE Experiment_Plan_Parser SHALL validate required fields: protocol, materials, budget, timeline, validation_criteria
6. THE Experiment_Plan_Printer SHALL format JSON with consistent indentation and field ordering

### Requirement 27: Rate Limiting and Quota Management

**User Story:** As a developer, I want rate limiting to prevent API quota exhaustion, so that the Platform operates within budget constraints.

#### Acceptance Criteria

1. THE API_Gateway SHALL implement rate limiting of 10 requests per minute per user for plan generation
2. WHEN rate limits are exceeded, THE API_Gateway SHALL return HTTP 429 with retry-after header
3. THE Platform SHALL track OpenAI API token usage per request
4. WHEN monthly OpenAI quota is 80% consumed, THE Platform SHALL send alert notifications
5. THE API_Gateway SHALL implement request queuing for rate-limited endpoints
6. THE Platform SHALL display remaining quota information in the Web_Client dashboard

### Requirement 28: Testing Infrastructure

**User Story:** As a developer, I want comprehensive testing infrastructure, so that the Platform maintains quality as it evolves.

#### Acceptance Criteria

1. THE Platform SHALL include unit tests for Hypothesis_Validator, Literature_QC_Engine, and Plan_Generator
2. THE Platform SHALL include integration tests for Pipeline_Graph end-to-end execution
3. THE Platform SHALL include API tests for all API_Gateway endpoints
4. THE Platform SHALL achieve minimum 80% code coverage for backend components
5. THE Platform SHALL include frontend component tests using React Testing Library
6. THE Platform SHALL include property-based tests for Experiment_Plan_Parser round-trip validation

### Requirement 29: Performance Benchmarks

**User Story:** As a developer, I want performance benchmarks, so that the Platform meets latency requirements.

#### Acceptance Criteria

1. THE Platform SHALL complete hypothesis validation within 5 seconds
2. THE Platform SHALL complete literature QC within 30 seconds
3. THE Platform SHALL complete experiment plan generation within 60 seconds
4. THE Platform SHALL complete end-to-end pipeline execution within 90 seconds for 95th percentile requests
5. THE Vector_Store SHALL return similarity search results within 500ms for queries with k=5
6. THE Web_Client SHALL achieve Lighthouse performance score of 90 or higher

### Requirement 30: Monitoring and Alerting

**User Story:** As a developer, I want monitoring and alerting, so that I can detect and respond to production issues.

#### Acceptance Criteria

1. THE API_Gateway SHALL expose /health endpoint returning service status and dependency health
2. THE Platform SHALL log errors to LangSmith with severity levels (info, warning, error, critical)
3. WHEN error rate exceeds 5% over 5 minutes, THE Platform SHALL trigger alert notifications
4. THE Platform SHALL track metrics: request count, latency percentiles, error rate, API quota usage
5. THE Platform SHALL include dashboard displaying real-time metrics
6. THE Platform SHALL implement uptime monitoring with 99% availability target
