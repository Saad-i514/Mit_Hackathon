# AI Scientist Platform

> **From hypothesis to lab-ready protocol in under 90 seconds.**
>
> Most AI science tools give you a wall of text and call it a protocol. We give you something a scientist can actually run on Monday morning.

A production-grade, full-stack AI-powered experiment planning system that transforms natural-language scientific hypotheses into fully operational experiment plans — complete with real catalog numbers, Gantt timelines, safety assessments, power analysis, and literature novelty scoring.

**Stack:** GPT-4o · LangGraph · FastAPI · Next.js 14 · Supabase · pgvector · LangSmith

---

## Table of Contents

- [Live Demo](#live-demo)
- [What It Does](#what-it-does)
- [Architecture](#architecture)
- [AI Pipeline](#ai-pipeline)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Testing](#testing)
- [Contributing](#contributing)

---

## Live Demo

| Service | URL |
|---------|-----|
| Frontend | Deploy to Vercel (see [Deployment](#deployment)) |
| Backend API | Deploy to Railway (see [Deployment](#deployment)) |
| API Docs | `https://your-backend.railway.app/docs` |

---

## What It Does

A scientist types a hypothesis like:

> *"DMSO at 10% v/v will provide superior cryoprotection compared to glycerol for HeLa cell cryopreservation, resulting in ≥85% post-thaw viability measured by trypan blue exclusion after 6 months at -80°C."*

Within 90 seconds, the platform returns:

| Output | Details |
|--------|---------|
| **Protocol** | Step-by-step procedure grounded in protocols.io and peer-reviewed sources, with critical parameters and troubleshooting |
| **Materials & Budget** | Real catalog numbers (Thermo Fisher, Sigma-Aldrich, ATCC) with 2024–2025 pricing and PubChem enrichment |
| **Timeline** | Gantt chart with phase dependencies and real ISO dates |
| **Validation Criteria** | Quantitative success/failure thresholds with measurement techniques |
| **Literature QC** | Novelty classification against 6 databases (Semantic Scholar, PubMed, OpenAlex, Europe PMC, bioRxiv, Serper) |
| **Safety Assessment** | BSL level, GHS hazard codes, PPE requirements, waste disposal, regulatory approvals (IACUC/IRB) |
| **Power Analysis** | Sample size calculation with effect size, alpha, and power |
| **Protocol Variants** | Budget / Standard / Premium tiers with cost and timeline tradeoffs |
| **Clinical Trials** | Related ClinicalTrials.gov studies |
| **Grant Methods** | NIH / NSF / ERC-formatted Methods section |
| **Lab Notebook** | Pre-filled electronic lab notebook template |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Frontend  (Next.js 14 · Vercel)                  │
│                                                                      │
│  Login ──► New Plan ──► SSE Stream ──► Plan Viewer                  │
│                          (real-time)    Protocol · Materials         │
│                                         Timeline · Validation        │
│                                         Safety · Grant · Notebook    │
└────────────────────────────┬─────────────────────────────────────────┘
                             │  HTTPS + Server-Sent Events
┌────────────────────────────▼─────────────────────────────────────────┐
│                     Backend  (FastAPI · Railway)                     │
│                                                                      │
│  POST /api/v1/plans/generate                                         │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              LangGraph AI Pipeline                          │    │
│  │                                                             │    │
│  │  [1] HypothesisValidator  ──►  [2] ClinicalTrialsClient    │    │
│  │       (GPT-4o)                      (ClinicalTrials.gov)   │    │
│  │           │                               │                │    │
│  │           ▼                               ▼                │    │
│  │  [3] LiteratureQCEngine  ──►  [4] PlanGenerator            │    │
│  │       6 databases               (GPT-4o + RAG)             │    │
│  │       novelty scoring           + SafetyAssessor           │    │
│  │                                 + ReproducibilityScorer    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  GET  /api/v1/plans/{id}   ·   POST /api/v1/plans/{id}/reviews      │
│  POST /api/v1/plans/{id}/grant-methods                               │
│  POST /api/v1/plans/{id}/notebook                                    │
│  GET  /api/v1/plans/{id}/versions                                    │
│  PUT  /api/v1/plans/equipment/{name}                                 │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│              Supabase  (PostgreSQL + pgvector + Auth)                │
│                                                                      │
│  experiment_plans  ·  hypotheses  ·  reviews                        │
│  feedback_embeddings (vector 1536d)  ·  plan_versions               │
│  lab_equipment  ·  plan_annotations                                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## AI Pipeline

The pipeline is a **LangGraph state machine** with 4 sequential nodes:

```
validate_hypothesis
        │
        ▼ (valid?)
assess_clinical_trials   ← non-blocking, always continues
        │
        ▼
assess_literature        ← 6 concurrent database searches
        │
        ▼ (novelty classified?)
generate_plan            ← GPT-4o + RAG + PubChem + Safety
        │
        ▼
     [END]
```

Each node emits **Server-Sent Events** so the frontend shows live progress. The entire pipeline runs in a background `asyncio.Task` while the SSE stream is consumed by the client.

### Stage Details

| Stage | Duration | What Happens |
|-------|----------|-------------|
| **Hypothesis Validation** | ~5s | GPT-4o extracts domain, testable claim, clarification questions. Optional auto-refinement if quality score < 70. |
| **Clinical Trials** | ~3s | Searches ClinicalTrials.gov for overlapping studies. Non-blocking — pipeline continues on failure. |
| **Literature QC** | ~20–30s | Concurrent search across Semantic Scholar, PubMed, OpenAlex, Europe PMC, bioRxiv, Serper. GPT-4o classifies novelty as `not_found` / `similar_exists` / `exact_match`. |
| **Plan Generation** | ~40–60s | GPT-4o generates structured JSON plan. RAG queries `feedback_embeddings` for expert corrections. PubChem enriches materials. Safety assessor classifies BSL level. Reproducibility scorer evaluates protocol quality. |

---

## Features

### Core
- ✅ **3-stage LangGraph pipeline** with conditional edges and error recovery
- ✅ **Real-time SSE streaming** — live progress for each pipeline stage
- ✅ **RAG learning loop** — expert review corrections stored as pgvector embeddings, retrieved as few-shot examples for future plans
- ✅ **Literature novelty scoring** across 6 databases with GPT-4o classification
- ✅ **PubChem enrichment** — molecular weight, CAS numbers, GHS hazard codes
- ✅ **Protocol grounding** — steps reference protocols.io and peer-reviewed publications
- ✅ **Real catalog numbers** — verified against Thermo Fisher, Sigma-Aldrich, ATCC

### Advanced Features
- ✅ **Safety assessment** — BSL level, IACUC/IRB/IBC flags, PPE, waste disposal
- ✅ **Power analysis** — sample size calculator with t-test/ANOVA/chi-squared support
- ✅ **Protocol variants** — Budget / Standard / Premium tiers
- ✅ **Protocol flowchart** — interactive React Flow diagram with mouse repulsion
- ✅ **Gantt timeline** — Frappe Gantt chart with computed ISO dates
- ✅ **Version history** — plan snapshots with restore capability
- ✅ **Collaborative review** — real-time annotations via Supabase Realtime
- ✅ **Equipment checklist** — lab equipment availability tracking
- ✅ **Grant Methods generator** — NIH / NSF / ERC formatted output
- ✅ **Lab notebook export** — pre-filled ELN template (PDF)
- ✅ **Export suite** — PDF, CSV, iCal, DOCX
- ✅ **Clinical trials badge** — related ClinicalTrials.gov studies

### Infrastructure
- ✅ **JWT authentication** via Supabase Auth (token validated server-side)
- ✅ **Row Level Security** — users can only access their own plans
- ✅ **Rate limiting** — 10 req/min for plan generation, 60 req/min for other endpoints
- ✅ **Circuit breaker** — external API failure isolation
- ✅ **LangSmith tracing** — full pipeline observability
- ✅ **In-process metrics** — error rate, latency P95, alert thresholds
- ✅ **Request ID middleware** — every request gets a UUID for tracing

---

## Tech Stack

### Backend
| Package | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.115.0 | REST API framework |
| LangGraph | 0.2.35 | AI pipeline orchestration |
| LangChain | 0.3.7 | LLM abstractions |
| OpenAI | 1.54.0 | GPT-4o + embeddings |
| LangSmith | 0.1.147 | Pipeline observability |
| Supabase | 2.9.0 | Database + Auth client |
| sse-starlette | 2.1.3 | Server-Sent Events |
| slowapi | 0.1.9 | Rate limiting |
| httpx | 0.27.2 | Async HTTP client |
| pydantic | 2.9.2 | Data validation |
| python-docx | 1.2.0 | DOCX export |
| reportlab | 4.2.5 | PDF generation |

### Frontend
| Package | Version | Purpose |
|---------|---------|---------|
| Next.js | 14.2.15 | React framework (App Router) |
| React | 18.3.1 | UI library |
| @xyflow/react | 12.3.0 | Protocol flowchart |
| frappe-gantt | 0.6.1 | Gantt timeline |
| framer-motion | 11.18.2 | Animations |
| @supabase/ssr | 0.10.2 | Supabase SSR client |
| Tailwind CSS | 3.4.13 | Styling |
| Radix UI | various | Accessible components |
| sonner | 2.0.7 | Toast notifications |
| jsPDF | 2.5.1 | PDF export |
| lucide-react | 0.453.0 | Icons |

### Infrastructure
| Service | Purpose |
|---------|---------|
| Supabase | PostgreSQL + pgvector + Auth + Realtime |
| Railway | Backend hosting (auto-deploy from GitHub) |
| Vercel | Frontend hosting (auto-deploy from GitHub) |
| LangSmith | LLM pipeline tracing and evaluation |

---

## Project Structure

```
MIT_HACK5/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── health.py          # GET /health, GET /metrics
│   │   │       └── plans.py           # All plan endpoints
│   │   ├── graph/
│   │   │   ├── ai_pipeline.py         # LangGraph state machine
│   │   │   └── pipeline_state.py      # TypedDict state definition
│   │   ├── models/
│   │   │   ├── requests.py            # Pydantic request models
│   │   │   └── responses.py           # Pydantic response models
│   │   ├── prompts/
│   │   │   └── plan_generator_system.txt  # GPT-4o system prompt
│   │   ├── services/
│   │   │   ├── clinical_trials.py     # ClinicalTrials.gov client
│   │   │   ├── grant_methods.py       # Grant Methods generator
│   │   │   ├── hypothesis_refiner.py  # Auto-refinement
│   │   │   ├── hypothesis_validator.py # GPT-4o validation
│   │   │   ├── langsmith.py           # LangSmith logger
│   │   │   ├── learning_engine.py     # RAG + pgvector
│   │   │   ├── literature_qc.py       # 6-database search
│   │   │   ├── notebook_generator.py  # ELN template
│   │   │   ├── openai_client.py       # OpenAI wrapper
│   │   │   ├── plan_generator.py      # GPT-4o plan generation
│   │   │   ├── protocols_io.py        # protocols.io client
│   │   │   ├── pubchem.py             # PubChem enrichment
│   │   │   ├── reproducibility_scorer.py # Protocol quality
│   │   │   ├── safety_assessor.py     # BSL + GHS assessment
│   │   │   ├── semantic_scholar.py    # Semantic Scholar client
│   │   │   ├── serper.py              # Serper web search
│   │   │   └── sse_manager.py         # SSE event queue
│   │   ├── utils/
│   │   │   ├── circuit_breaker.py     # External API isolation
│   │   │   ├── errors.py              # Structured error handling
│   │   │   └── monitoring.py          # In-process metrics
│   │   ├── auth.py                    # Supabase JWT validation
│   │   ├── config.py                  # Pydantic settings
│   │   ├── database.py                # Supabase client
│   │   └── main.py                    # FastAPI app + middleware
│   ├── migrations/
│   │   ├── 001_initial_schema.sql     # Core tables + pgvector
│   │   ├── 002_sample_data.sql        # Sample data
│   │   ├── 003_advanced_features_schema.sql  # Advanced tables
│   │   ├── 004_fix_lab_equipment_fk.sql
│   │   └── APPLY_IN_SUPABASE.sql      # Combined migration
│   ├── tests/
│   │   ├── unit/                      # Unit tests (41 tests)
│   │   └── integration/               # Integration tests
│   ├── .env.example
│   ├── Procfile                       # Railway start command
│   ├── railway.json                   # Railway config
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── (auth)/login/page.tsx      # Login page (particle animation)
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx             # Dashboard layout + nav
│   │   │   ├── new-plan/page.tsx      # Hypothesis input + SSE stream
│   │   │   └── plans/
│   │   │       ├── page.tsx           # Plan list
│   │   │       └── [id]/page.tsx      # Plan detail (all tabs)
│   │   └── auth/callback/route.ts     # Supabase OAuth callback
│   ├── components/
│   │   ├── plan-viewer/
│   │   │   ├── clinical-trials-badge.tsx
│   │   │   ├── collaborative-review.tsx
│   │   │   ├── equipment-checklist.tsx
│   │   │   ├── export-suite.tsx
│   │   │   ├── gantt-timeline.tsx
│   │   │   ├── grant-methods.tsx
│   │   │   ├── notebook-export.tsx
│   │   │   ├── power-calculator.tsx
│   │   │   ├── protocol-flowchart.tsx
│   │   │   ├── safety-tab.tsx
│   │   │   ├── variant-selector.tsx
│   │   │   └── version-history.tsx
│   │   └── ui/                        # Radix UI components
│   ├── lib/
│   │   ├── api-client.ts              # Authenticated API client
│   │   ├── config.ts                  # Env config + API endpoints
│   │   ├── hooks/use-sse.ts           # SSE React hook
│   │   ├── supabase.ts                # Supabase browser client
│   │   └── types.ts                   # TypeScript interfaces
│   ├── .env.example
│   └── package.json
│
├── docs/
│   ├── DEPLOYMENT.md                  # Full deployment guide
│   └── USER_GUIDE.md
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Supabase project with pgvector enabled
- OpenAI API key (GPT-4o access required)
- Semantic Scholar API key (free at [semanticscholar.org](https://www.semanticscholar.org/product/api))
- Serper API key (free tier at [serper.dev](https://serper.dev))

### 1. Clone

```bash
git clone https://github.com/Saad-i514/Mit_Hackathon.git
cd Mit_Hackathon
```

### 2. Database setup (Supabase)

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Enable the `vector` extension: **Database → Extensions → vector**
3. Open the SQL editor and run `backend/migrations/APPLY_IN_SUPABASE.sql`

### 3. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# Fill in your keys (see Environment Variables section)

uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs  
Health check: http://localhost:8000/health

### 4. Frontend

```bash
cd frontend
npm install

cp .env.example .env.local
# Fill in your keys

npm run dev
```

App: http://localhost:3000

---

## Environment Variables

### Backend — `backend/.env`

```env
# ── Required ──────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret

SERPER_API_KEY=your-serper-key
SEMANTIC_SCHOLAR_API_KEY=your-ss-key

# ── Optional ──────────────────────────────────────────────────────────
PROTOCOLS_IO_TOKEN=           # Leave blank if unused
LANGCHAIN_API_KEY=ls__...     # LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ai-scientist-platform
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

APP_ENV=development
CORS_ORIGINS=http://localhost:3000
```

### Frontend — `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

### Where to get each key

| Key | Source |
|-----|--------|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `SUPABASE_URL` + keys | Supabase → Project Settings → API |
| `SUPABASE_JWT_SECRET` | Supabase → Project Settings → API → JWT Settings |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev) → Dashboard |
| `SEMANTIC_SCHOLAR_API_KEY` | [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api) |
| `LANGCHAIN_API_KEY` | [smith.langchain.com](https://smith.langchain.com) → Settings → API Keys |

---

## API Reference

### Authentication
All plan endpoints require `Authorization: Bearer <supabase-jwt>` header.

### Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/health` | Health check — database, OpenAI, Semantic Scholar, Serper | No |
| `GET` | `/metrics` | Request rates, error rates, P95 latency, active alerts | No |
| `POST` | `/api/v1/plans/generate` | Generate plan — returns SSE stream | ✅ |
| `GET` | `/api/v1/plans` | List plans (paginated, filterable by status) | ✅ |
| `GET` | `/api/v1/plans/{id}` | Get plan by ID | ✅ |
| `POST` | `/api/v1/plans/{id}/reviews` | Submit expert review (triggers embedding generation) | ✅ |
| `POST` | `/api/v1/plans/{id}/grant-methods` | Generate grant Methods section | ✅ |
| `POST` | `/api/v1/plans/{id}/notebook` | Generate lab notebook template | ✅ |
| `GET` | `/api/v1/plans/{id}/versions` | Get version history | ✅ |
| `POST` | `/api/v1/plans/{id}/restore/{version}` | Restore a previous version | ✅ |
| `PUT` | `/api/v1/plans/equipment/{name}` | Update equipment availability | ✅ |

### SSE Event Format

Plan generation streams events in this format:

```json
{
  "event_type": "progress",
  "timestamp": "2025-01-01T00:00:00",
  "data": {
    "stage": "literature_qc",
    "progress_percent": 55,
    "message": "Searching scientific literature..."
  }
}
```

Event types: `stage_start` · `progress` · `stage_complete` · `error` · `complete`

---

## Database Schema

### Core Tables

```sql
experiment_plans   -- Generated plans (JSONB plan_data)
hypotheses         -- User hypotheses
reviews            -- Expert ratings (1-5) + corrections
feedback_embeddings -- vector(1536) for RAG
```

### Advanced Tables (migration 003)

```sql
plan_versions      -- Snapshot history
plan_annotations   -- Collaborative review comments
lab_equipment      -- Per-user equipment availability
```

### Key Functions

```sql
match_feedback_embeddings(query_embedding, threshold, count, domain)
-- Cosine similarity search for RAG

get_average_plan_rating(plan_uuid)
-- Aggregate review ratings
```

---

## Deployment

### Backend → Railway

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
2. Select this repo → set **Root Directory** to `backend`
3. Add all backend environment variables in **Variables** tab
4. Railway uses `backend/railway.json` and `backend/Procfile` automatically
5. Get your URL from **Settings → Domains**

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New Project**
2. Import this repo → set **Root Directory** to `frontend`
3. Add frontend environment variables (`NEXT_PUBLIC_API_URL` = your Railway URL)
4. Deploy

### Post-deployment

Update `CORS_ORIGINS` in Railway to include your Vercel domain:
```
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

Update Supabase redirect URLs:
- **Authentication → URL Configuration → Redirect URLs**: add `https://your-app.vercel.app/auth/callback`
- **Site URL**: `https://your-app.vercel.app`

Full guide: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## Monitoring

### Health Check
```bash
curl https://your-backend.railway.app/health
```
Returns status of: database · OpenAI · Semantic Scholar · Serper

### Metrics
```bash
curl https://your-backend.railway.app/metrics
```
Returns: request rates · error rates · pipeline P95 latency · active alerts

### Alert Thresholds (configurable in `backend/app/utils/monitoring.py`)
- Error rate > 5% over 5 minutes
- Pipeline P95 latency > 90 seconds
- Validation failure rate > 20%

### LangSmith
Set `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` to enable full pipeline tracing at [smith.langchain.com](https://smith.langchain.com).

---

## Testing

```bash
cd backend

# Run all unit tests
venv\Scripts\python.exe -m pytest tests/unit/ -v

# Run with coverage
venv\Scripts\python.exe -m pytest tests/unit/ --cov=app --cov-report=term-missing

# Run integration tests (requires live Supabase + API keys)
venv\Scripts\python.exe -m pytest tests/integration/ -v
```

**41 unit tests** covering:
- Hypothesis validator (9 tests)
- Metrics collector (22 tests)
- System prompt quality thresholds (10 tests)

---

## Supported Scientific Domains

Molecular Biology · Cell Biology · Biochemistry · Genetics · Neuroscience · Immunology · Microbiology · Pharmacology · Biophysics · Structural Biology · Genomics · Proteomics · Metabolomics · Ecology · Evolutionary Biology · Developmental Biology · Physiology · Pathology · Bioinformatics · Synthetic Biology

---

## License

MIT — see [LICENSE](LICENSE) for details.
