-- ============================================================================
-- AI Scientist Platform - Complete Schema
-- INSTRUCTIONS: Paste this entire file into the Supabase SQL Editor and run it.
-- Dashboard: https://supabase.com/dashboard/project/kdzzyxihfxxcsnifcnpi/sql/new
-- ============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Users
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  institution TEXT,
  role TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Hypotheses
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

-- Experiment Plans
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

-- Reviews
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

-- Feedback Embeddings
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

-- RLS: open policies for development
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE hypotheses ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_embeddings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "allow_all_users" ON users;
CREATE POLICY "allow_all_users" ON users FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_hypotheses" ON hypotheses;
CREATE POLICY "allow_all_hypotheses" ON hypotheses FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_plans" ON experiment_plans;
CREATE POLICY "allow_all_plans" ON experiment_plans FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_reviews" ON reviews;
CREATE POLICY "allow_all_reviews" ON reviews FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_feedback" ON feedback_embeddings;
CREATE POLICY "allow_all_feedback" ON feedback_embeddings FOR ALL USING (true) WITH CHECK (true);

-- Similarity search function
CREATE OR REPLACE FUNCTION match_feedback_embeddings(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.25,
  match_count int DEFAULT 5,
  filter_domain text DEFAULT NULL
)
RETURNS TABLE (
  id uuid, correction_text text, original_issue text,
  hypothesis_domain text, rating integer, created_at timestamptz, distance float
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT fe.id, fe.correction_text, fe.original_issue,
         fe.hypothesis_domain, fe.rating, fe.created_at,
         (fe.embedding <=> query_embedding) AS distance
  FROM feedback_embeddings fe
  WHERE (filter_domain IS NULL OR fe.hypothesis_domain = filter_domain)
    AND fe.embedding IS NOT NULL
    AND (fe.embedding <=> query_embedding) < match_threshold
  ORDER BY distance ASC LIMIT match_count;
END;
$$;

-- Average rating function
CREATE OR REPLACE FUNCTION get_average_plan_rating(plan_id_param uuid)
RETURNS decimal(3,2) LANGUAGE plpgsql AS $$
DECLARE avg_rating decimal(3,2);
BEGIN
  SELECT AVG(overall_rating) INTO avg_rating FROM reviews WHERE plan_id = plan_id_param;
  RETURN COALESCE(avg_rating, 0.0);
END;
$$;

-- ============================================================================
-- Schema applied successfully
-- ============================================================================
