# Deployment Guide

This guide covers deploying the AI Scientist Platform to production using Vercel (frontend), Render.com (backend), and Supabase (database).

## Prerequisites

- GitHub account with the repository pushed
- Supabase account
- Vercel account
- Render.com account
- All required API keys (see README.md)

---

## 1. Supabase Setup

### 1.1 Create a new project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Choose a region close to your users
3. Save the database password securely

### 1.2 Enable pgvector extension

In the Supabase SQL editor, run:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
```

### 1.3 Apply database migrations

In the Supabase SQL editor, run the contents of each migration file in order:

```sql
-- Run migrations/001_initial_schema.sql
-- (paste the full contents)
```

### 1.4 Collect credentials

From your Supabase project settings:

- **Project URL**: Settings → API → Project URL
- **Anon key**: Settings → API → Project API keys → `anon public`
- **Service role key**: Settings → API → Project API keys → `service_role` (keep secret)
- **JWT secret**: Settings → API → JWT Settings → JWT Secret

---

## 2. Backend Deployment (Render.com)

### 2.1 Connect repository

1. Go to [render.com](https://render.com) and create a new account
2. Click **New** → **Blueprint**
3. Connect your GitHub repository
4. Render will detect `render.yaml` automatically

### 2.2 Configure environment variables

In the Render dashboard for the `ai-scientist-backend` service, add these secret environment variables:

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Your Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Your Supabase service role key |
| `SUPABASE_JWT_SECRET` | Your Supabase JWT secret |
| `SEMANTIC_SCHOLAR_API_KEY` | Your Semantic Scholar API key |
| `SERPER_API_KEY` | Your Serper API key |
| `LANGCHAIN_API_KEY` | Your LangSmith API key (optional) |
| `CORS_ORIGINS` | `https://your-app.vercel.app,http://localhost:3000` |

### 2.3 Deploy

Click **Deploy** in the Render dashboard. The first deploy takes 3-5 minutes.

Verify deployment:
```bash
curl https://your-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "dependencies": {
    "database": {"status": "healthy"},
    "openai": {"status": "healthy"},
    "semantic_scholar": {"status": "healthy"},
    "serper": {"status": "healthy"}
  }
}
```

### 2.4 Auto-deploy

Render auto-deploys on every push to the main branch. To disable, set `autoDeploy: false` in `render.yaml`.

---

## 3. Frontend Deployment (Vercel)

### 3.1 Import project

1. Go to [vercel.com](https://vercel.com) and create a new account
2. Click **Add New** → **Project**
3. Import your GitHub repository
4. Set **Root Directory** to `frontend`
5. Framework preset: **Next.js** (auto-detected)

### 3.2 Configure environment variables

In the Vercel project settings → Environment Variables, add:

| Key | Value | Environment |
|-----|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.onrender.com` | Production |
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL | All |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase anon key | All |

### 3.3 Deploy

Click **Deploy**. Vercel builds and deploys automatically.

### 3.4 Update CORS

After getting your Vercel URL (e.g., `https://ai-scientist-platform.vercel.app`), update the `CORS_ORIGINS` environment variable in Render to include it.

---

## 4. Post-Deployment Verification

### 4.1 Health check

```bash
curl https://your-backend.onrender.com/health
```

### 4.2 API documentation

Visit `https://your-backend.onrender.com/docs` to verify the OpenAPI docs are accessible.

### 4.3 Metrics

```bash
curl https://your-backend.onrender.com/metrics
```

### 4.4 End-to-end test

1. Open `https://your-app.vercel.app`
2. Sign up for an account
3. Submit a test hypothesis: *"Does increasing BDNF expression in hippocampal neurons improve spatial memory in aged mice?"*
4. Verify the SSE stream shows progress through all 3 stages
5. Verify the generated plan contains protocol steps, materials with catalog numbers, and a timeline

---

## 5. Monitoring Setup

### 5.1 Uptime monitoring

Set up uptime monitoring for the health endpoint using any of:
- [UptimeRobot](https://uptimerobot.com) (free tier available)
- [Better Uptime](https://betteruptime.com)
- Render's built-in health check alerts

Configure: `GET https://your-backend.onrender.com/health` every 5 minutes.

### 5.2 LangSmith dashboard

If `LANGCHAIN_API_KEY` is configured:
1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Open the `ai-scientist-platform` project
3. View pipeline traces, token usage, and stage durations

### 5.3 Application metrics

Poll `GET /metrics` to track:
- `requests.error_rate` — alert if > 5%
- `pipeline.p95_seconds` — alert if > 90s
- `validation.failure_rate` — alert if > 20%

---

## 6. Database Maintenance

### 6.1 Running new migrations

```bash
cd backend
python scripts/migrate.py migrate
```

### 6.2 Checking migration status

```bash
python scripts/migrate.py status
```

### 6.3 Rolling back

```bash
python scripts/migrate.py rollback --migration 001_initial_schema.sql
```

### 6.4 Backup

Use Supabase's built-in point-in-time recovery (available on Pro plan) or schedule manual backups via the Supabase dashboard.

---

## 7. Scaling Considerations

### Backend

- Render Starter plan handles ~100 concurrent users
- Upgrade to Standard plan for production traffic
- The SSE connections are long-lived; ensure your plan supports enough concurrent connections

### Database

- pgvector HNSW index handles similarity search efficiently up to ~1M embeddings
- Monitor `feedback_embeddings` table size; consider partitioning at 10M+ rows

### Rate Limits

- OpenAI GPT-4o: 10,000 TPM on Tier 1; upgrade as needed
- Semantic Scholar: 100 requests/second with API key
- Serper: 2,500 queries/month on free tier; upgrade for production

---

## Troubleshooting

### Backend won't start

Check Render logs for:
- Missing environment variables → add them in Render dashboard
- Import errors → check `requirements.txt` is complete

### SSE stream disconnects immediately

- Verify `CORS_ORIGINS` includes your frontend URL
- Check Render's request timeout (default 30s); SSE streams need longer — set `timeoutSeconds: 300` in render.yaml if needed

### Database connection errors

- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are correct
- Check Supabase project is not paused (free tier pauses after 1 week of inactivity)

### OpenAI rate limit errors

- The circuit breaker opens after 3 consecutive failures
- Check `GET /metrics` for `pipeline_error` count
- Verify your OpenAI API key has GPT-4o access
