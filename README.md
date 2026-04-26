# AI Scientist Platform

A production-grade, full-stack AI-powered experiment planning system that transforms natural-language scientific hypotheses into fully operational experiment plans using GPT-4o, LangGraph, FastAPI, Next.js 14, and Supabase.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 14)                     │
│  HypothesisInput → PipelineProgress → ExperimentPlanViewer      │
│                    SSE real-time streaming                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP + SSE
┌──────────────────────────▼──────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  POST /api/v1/plans/generate  →  LangGraph AI Pipeline          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  HypothesisValidator → LiteratureQCEngine → PlanGenerator│    │
│  │  (GPT-4o)              (Semantic Scholar   (GPT-4o +     │    │
│  │                         + Serper)           RAG)         │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Supabase (PostgreSQL + pgvector)              │
│  users, hypotheses, experiment_plans, reviews, feedback_embeddings│
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **AI Pipeline**: 3-stage LangGraph pipeline (validation → literature QC → plan generation)
- **Real-time Streaming**: SSE-based progress updates during plan generation
- **Literature QC**: Concurrent Semantic Scholar + Serper search with novelty classification
- **RAG Learning Loop**: Embeddings-based few-shot learning from expert corrections
- **Protocol Grounding**: References to protocols.io, bio-protocol.org, and publications
- **Materials & Budget**: Real catalog numbers from Thermo Fisher and Sigma-Aldrich with 2024-2025 pricing
- **Expert Review**: Automated flagging of unverified catalog numbers and missing parameters
- **Authentication**: Supabase JWT-based auth with Row Level Security
- **Monitoring**: In-process metrics with error rate and latency alerting

## Supported Scientific Domains

Molecular Biology, Cell Biology, Biochemistry, Genetics, Neuroscience, Immunology, Microbiology, Pharmacology, Biophysics, Structural Biology, Genomics, Proteomics, Metabolomics, Ecology, Evolutionary Biology, Developmental Biology, Physiology, Pathology, Bioinformatics, Synthetic Biology

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Supabase account with pgvector enabled
- OpenAI API key (GPT-4o access)
- Semantic Scholar API key
- Serper API key

### 1. Clone and configure

```bash
git clone <repository-url>
cd ai-scientist-platform
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your API keys
```

### 3. Database setup

Run migrations in your Supabase SQL editor:

```bash
# Apply schema
psql $DATABASE_URL < migrations/001_initial_schema.sql

# Apply sample data (optional)
psql $DATABASE_URL < migrations/002_sample_data.sql
```

Or use the migration runner:

```bash
python scripts/migrate.py migrate
```

### 4. Start backend

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 5. Frontend setup

```bash
cd frontend
npm install

cp .env.example .env.local
# Edit .env.local with your Supabase and API URLs
```

### 6. Start frontend

```bash
npm run dev
```

App available at: http://localhost:3000

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key with GPT-4o access | ✅ |
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | ✅ |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | ✅ |
| `SUPABASE_JWT_SECRET` | Supabase JWT secret for token validation | ✅ |
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API key | ✅ |
| `SERPER_API_KEY` | Serper web search API key | ✅ |
| `LANGCHAIN_API_KEY` | LangSmith API key for tracing | Optional |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing (`true`/`false`) | Optional |
| `CORS_ORIGINS` | Comma-separated allowed origins | Optional |

### Frontend (`frontend/.env.local`)

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | ✅ |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | ✅ |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key | ✅ |

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/health` | Health check with dependency status | No |
| `GET` | `/metrics` | Application metrics and alerts | No |
| `POST` | `/api/v1/plans/generate` | Generate experiment plan (SSE stream) | JWT |
| `GET` | `/api/v1/plans` | List user's plans (paginated) | JWT |
| `GET` | `/api/v1/plans/{id}` | Get plan by ID | JWT |
| `POST` | `/api/v1/plans/{id}/reviews` | Submit expert review | JWT |

Full interactive API docs: `http://localhost:8000/docs`

## Deployment

### Frontend → Vercel

```bash
cd frontend
vercel --prod
```

Set environment variables in Vercel dashboard.

### Backend → Railway

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Set **Root Directory** to `backend`
3. Add environment variables in Railway dashboard
4. Railway auto-deploys on every push

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for the complete step-by-step guide.

## Monitoring

- **Health check**: `GET /health` — checks database, OpenAI, Semantic Scholar, Serper
- **Metrics**: `GET /metrics` — request rates, error rates, pipeline P95 latency, active alerts
- **LangSmith**: Pipeline traces, token usage, stage durations (requires `LANGCHAIN_API_KEY`)

Alert thresholds (configurable in `backend/app/utils/monitoring.py`):
- Error rate > 5% over 5 minutes
- Pipeline P95 latency > 90 seconds
- Validation failure rate > 20%

## Project Structure

```
ai-scientist-platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI route handlers
│   │   ├── graph/           # LangGraph pipeline
│   │   ├── models/          # Pydantic request/response models
│   │   ├── prompts/         # GPT-4o system prompts
│   │   ├── services/        # External API clients and AI components
│   │   └── utils/           # Error handling, circuit breaker, monitoring
│   ├── migrations/          # SQL migration files
│   ├── scripts/             # Database migration runner
│   ├── tests/               # Unit and integration tests
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities, hooks, API client
│   └── package.json
├── render.yaml              # Render.com deployment config
└── README.md
```

## License

MIT
