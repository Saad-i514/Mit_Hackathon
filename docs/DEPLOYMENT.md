# Deployment Guide — Railway + Vercel + Supabase

This guide covers deploying the AI Scientist Platform using:
- **Railway** — backend FastAPI server
- **Vercel** — frontend Next.js app
- **Supabase** — PostgreSQL database + Auth

---

## 1. Supabase Setup

### 1.1 Create project

1. Go to [supabase.com](https://supabase.com) → New project
2. Choose a region close to your users
3. Save the database password

### 1.2 Enable pgvector

In the Supabase SQL editor:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
```

### 1.3 Apply migrations

Run `backend/migrations/001_initial_schema.sql` in the SQL editor.

### 1.4 Fix FK constraints (required)

Run this in the SQL editor to point FKs at `auth.users`:

```sql
ALTER TABLE hypotheses DROP CONSTRAINT IF EXISTS hypotheses_user_id_fkey;
ALTER TABLE experiment_plans DROP CONSTRAINT IF EXISTS experiment_plans_user_id_fkey;
ALTER TABLE reviews DROP CONSTRAINT IF EXISTS reviews_user_id_fkey;
ALTER TABLE feedback_embeddings DROP CONSTRAINT IF EXISTS feedback_embeddings_scientist_id_fkey;

ALTER TABLE hypotheses ADD CONSTRAINT hypotheses_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE experiment_plans ADD CONSTRAINT experiment_plans_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE experiment_plans ALTER COLUMN hypothesis_id DROP NOT NULL;
ALTER TABLE reviews ADD CONSTRAINT reviews_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE feedback_embeddings ADD CONSTRAINT feedback_embeddings_scientist_id_fkey
  FOREIGN KEY (scientist_id) REFERENCES auth.users(id) ON DELETE CASCADE;
```

### 1.5 Collect credentials

From **Project Settings → API**:
- Project URL
- `anon` public key
- `service_role` key (keep secret)
- JWT Secret (under JWT Settings)

---

## 2. Backend Deployment (Railway)

### 2.1 Create Railway project

1. Go to [railway.app](https://railway.app) → New Project
2. Click **Deploy from GitHub repo**
3. Select your repository
4. Set **Root Directory** to `backend`

Railway auto-detects Python via Nixpacks and uses `backend/Procfile` for the start command.

### 2.2 Set environment variables

In Railway dashboard → your service → **Variables**, add:

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | Your OpenAI key |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Your Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Your Supabase service role key |
| `SUPABASE_JWT_SECRET` | Your Supabase JWT secret |
| `SEMANTIC_SCHOLAR_API_KEY` | Your Semantic Scholar key |
| `SERPER_API_KEY` | Your Serper key |
| `LANGCHAIN_API_KEY` | LangSmith key (optional) |
| `LANGCHAIN_TRACING_V2` | `false` (set `true` if using LangSmith) |
| `LANGCHAIN_PROJECT` | `ai-scientist-platform` |
| `CORS_ORIGINS` | `https://your-app.vercel.app,http://localhost:3000` |
| `APP_ENV` | `production` |

### 2.3 Deploy

Click **Deploy** — Railway builds and starts the server automatically.

Get your Railway URL from the **Settings → Domains** tab (e.g. `https://ai-scientist-backend.up.railway.app`).

### 2.4 Verify

```bash
curl https://your-backend.up.railway.app/health
```

Expected:
```json
{"status": "healthy", "dependencies": {...}}
```

---

## 3. Frontend Deployment (Vercel)

### 3.1 Import project

1. Go to [vercel.com](https://vercel.com) → Add New → Project
2. Import your GitHub repository
3. Set **Root Directory** to `frontend`
4. Framework: **Next.js** (auto-detected)

### 3.2 Set environment variables

In Vercel → Project Settings → Environment Variables:

| Key | Value | Environment |
|-----|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.up.railway.app` | Production |
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase URL | All |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase anon key | All |

### 3.3 Deploy

Click **Deploy**. Vercel builds and deploys automatically.

### 3.4 Update CORS on Railway

After getting your Vercel URL, update `CORS_ORIGINS` in Railway to include it:
```
https://your-app.vercel.app,http://localhost:3000
```

---

## 4. Post-Deployment Verification

```bash
# Backend health
curl https://your-backend.up.railway.app/health

# API docs
open https://your-backend.up.railway.app/docs

# Frontend
open https://your-app.vercel.app
```

---

## 5. Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Fill in your keys
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
cp .env.example .env.local  # Fill in your keys
npm run dev
```

---

## 6. Environment Variables Reference

### Backend (Railway / `.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key (GPT-4o access) |
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anonymous key |
| `SUPABASE_SERVICE_KEY` | ✅ | Supabase service role key |
| `SUPABASE_JWT_SECRET` | ✅ | Supabase JWT secret |
| `SEMANTIC_SCHOLAR_API_KEY` | ✅ | Semantic Scholar API key |
| `SERPER_API_KEY` | ✅ | Serper web search key |
| `CORS_ORIGINS` | ✅ | Comma-separated allowed origins |
| `LANGCHAIN_API_KEY` | Optional | LangSmith tracing key |
| `LANGCHAIN_TRACING_V2` | Optional | `true` to enable LangSmith |
| `APP_ENV` | Optional | `production` or `development` |

### Frontend (Vercel / `.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend Railway URL |
| `NEXT_PUBLIC_SUPABASE_URL` | ✅ | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ | Supabase anonymous key |

---

## 7. Troubleshooting

**Backend won't start on Railway**
- Check build logs in Railway dashboard
- Ensure `backend/Procfile` exists: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Verify all required env vars are set

**401 Unauthorized errors**
- The backend validates tokens via Supabase API — ensure `SUPABASE_URL` and `SUPABASE_ANON_KEY` are correct
- Check that the frontend `NEXT_PUBLIC_API_URL` points to the Railway backend URL

**CORS errors**
- Update `CORS_ORIGINS` in Railway to include your Vercel domain
- Format: `https://your-app.vercel.app,http://localhost:3000`

**SSE stream disconnects**
- Railway has a 30s request timeout by default — SSE streams need longer
- In Railway dashboard → Service Settings → enable **TCP Proxy** or contact Railway support for streaming support
- Alternative: set `RAILWAY_DEPLOYMENT_TIMEOUT=300` in Railway env vars

**Database FK errors**
- Run the FK migration SQL from Section 1.4 in Supabase SQL editor
- The `users` table in `public` schema is separate from `auth.users` — all FKs must reference `auth.users`
