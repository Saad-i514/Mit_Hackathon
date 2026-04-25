#!/usr/bin/env python3
"""
Supabase Schema Setup Script
Applies the database schema using the Supabase REST API.

Usage:
    python scripts/setup_supabase.py

Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
"""
import os
import sys
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Use whichever key is available
KEY = SERVICE_KEY or ANON_KEY

HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# Simplified schema that works with anon key (no auth.uid() RLS)
SCHEMA_SQL = """
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  institution TEXT,
  role TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Hypotheses table
CREATE TABLE IF NOT EXISTS hypotheses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  hypothesis_text TEXT NOT NULL,
  domain TEXT NOT NULL,
  testable_claim TEXT,
  validation_status TEXT,
  clarification_questions JSONB,
  status TEXT DEFAULT 'completed',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hypotheses_user_id ON hypotheses(user_id);
CREATE INDEX IF NOT EXISTS idx_hypotheses_domain ON hypotheses(domain);

-- Experiment plans table
CREATE TABLE IF NOT EXISTS experiment_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  hypothesis_id UUID,
  plan_data JSONB NOT NULL DEFAULT '{}',
  novelty_classification TEXT,
  model_version TEXT DEFAULT 'gpt-4o',
  few_shot_examples_used INTEGER DEFAULT 0,
  requires_expert_review TEXT[],
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT DEFAULT 'generated'
);

CREATE INDEX IF NOT EXISTS idx_plans_user_id ON experiment_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_plans_generated_at ON experiment_plans(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_plans_data_gin ON experiment_plans USING GIN (plan_data);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID,
  user_id UUID,
  protocol_rating INTEGER,
  materials_rating INTEGER,
  timeline_rating INTEGER,
  validation_rating INTEGER,
  overall_rating DECIMAL(3,2),
  protocol_corrections TEXT,
  materials_corrections TEXT,
  timeline_corrections TEXT,
  validation_corrections TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reviews_plan_id ON reviews(plan_id);

-- Feedback embeddings table
CREATE TABLE IF NOT EXISTS feedback_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  review_id UUID,
  plan_id UUID,
  scientist_id UUID,
  correction_text TEXT NOT NULL,
  original_issue TEXT,
  embedding vector(1536),
  hypothesis_domain TEXT NOT NULL,
  rating INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_domain ON feedback_embeddings(hypothesis_domain);

-- RLS: allow all operations for development
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE hypotheses ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_embeddings ENABLE ROW LEVEL SECURITY;

-- Open policies for development (anon can do everything)
DO $$ BEGIN
  CREATE POLICY "allow_all_users" ON users FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE POLICY "allow_all_hypotheses" ON hypotheses FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE POLICY "allow_all_plans" ON experiment_plans FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE POLICY "allow_all_reviews" ON reviews FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE POLICY "allow_all_feedback" ON feedback_embeddings FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Similarity search function
CREATE OR REPLACE FUNCTION match_feedback_embeddings(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.25,
  match_count int DEFAULT 5,
  filter_domain text DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  correction_text text,
  original_issue text,
  hypothesis_domain text,
  rating integer,
  created_at timestamptz,
  distance float
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT
    fe.id, fe.correction_text, fe.original_issue,
    fe.hypothesis_domain, fe.rating, fe.created_at,
    (fe.embedding <=> query_embedding) AS distance
  FROM feedback_embeddings fe
  WHERE
    (filter_domain IS NULL OR fe.hypothesis_domain = filter_domain)
    AND fe.embedding IS NOT NULL
    AND (fe.embedding <=> query_embedding) < match_threshold
  ORDER BY distance ASC
  LIMIT match_count;
END;
$$;

-- Average rating function
CREATE OR REPLACE FUNCTION get_average_plan_rating(plan_id_param uuid)
RETURNS decimal(3,2)
LANGUAGE plpgsql AS $$
DECLARE avg_rating decimal(3,2);
BEGIN
  SELECT AVG(overall_rating) INTO avg_rating FROM reviews WHERE plan_id = plan_id_param;
  RETURN COALESCE(avg_rating, 0.0);
END;
$$;
"""


def apply_schema():
    """Apply schema via Supabase SQL endpoint"""
    print(f"Connecting to: {SUPABASE_URL}")
    print(f"Using key type: {'service_role' if SERVICE_KEY else 'anon'}")

    # Split into individual statements
    statements = [s.strip() for s in SCHEMA_SQL.split(';') if s.strip()]
    
    success_count = 0
    error_count = 0

    with httpx.Client(timeout=30) as client:
        for i, stmt in enumerate(statements):
            if not stmt:
                continue
            try:
                # Use the pg REST endpoint
                r = client.post(
                    f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                    headers=HEADERS,
                    json={"sql": stmt + ";"}
                )
                if r.status_code in (200, 201, 204):
                    success_count += 1
                else:
                    # Some statements may fail if already exist — that's OK
                    print(f"  Statement {i+1}: {r.status_code} - {r.text[:100]}")
                    error_count += 1
            except Exception as e:
                print(f"  Statement {i+1} error: {e}")
                error_count += 1

    print(f"\nSchema application: {success_count} succeeded, {error_count} had issues")
    return error_count == 0


def verify_tables():
    """Verify tables exist"""
    tables = ["users", "hypotheses", "experiment_plans", "reviews", "feedback_embeddings"]
    
    with httpx.Client(timeout=15) as client:
        for table in tables:
            r = client.get(
                f"{SUPABASE_URL}/rest/v1/{table}?select=id&limit=1",
                headers=HEADERS
            )
            status = "✓" if r.status_code == 200 else "✗"
            print(f"  {status} {table}: HTTP {r.status_code}")


if __name__ == "__main__":
    print("=" * 50)
    print("AI Scientist Platform - Supabase Setup")
    print("=" * 50)
    
    apply_schema()
    
    print("\nVerifying tables...")
    verify_tables()
