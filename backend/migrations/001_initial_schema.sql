-- ============================================================================
-- AI Scientist Platform - Initial Database Schema
-- Migration: 001_initial_schema.sql
-- Description: Creates all tables, indexes, RLS policies, and functions
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- Table: users
-- Description: User accounts with authentication and profile information
-- ============================================================================
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  institution TEXT,
  role TEXT CHECK (role IN ('principal_investigator', 'postdoc', 'grad_student', 'admin')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- RLS Policies for users
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  USING (auth.uid() = id);

-- ============================================================================
-- Table: hypotheses
-- Description: Scientific hypotheses submitted by users
-- ============================================================================
CREATE TABLE hypotheses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  hypothesis_text TEXT NOT NULL CHECK (char_length(hypothesis_text) <= 5000),
  domain TEXT NOT NULL,
  testable_claim TEXT,
  validation_status TEXT CHECK (validation_status IN ('valid', 'invalid', 'needs_clarification')),
  clarification_questions JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for hypotheses
CREATE INDEX idx_hypotheses_user_id ON hypotheses(user_id);
CREATE INDEX idx_hypotheses_domain ON hypotheses(domain);
CREATE INDEX idx_hypotheses_created_at ON hypotheses(created_at DESC);

-- RLS Policies for hypotheses
ALTER TABLE hypotheses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own hypotheses"
  ON hypotheses FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own hypotheses"
  ON hypotheses FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- Table: experiment_plans
-- Description: Generated experiment plans with complete plan data
-- ============================================================================
CREATE TABLE experiment_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  hypothesis_id UUID REFERENCES hypotheses(id) ON DELETE CASCADE,
  
  -- Plan content (JSONB for flexibility)
  plan_data JSONB NOT NULL,
  
  -- Metadata
  novelty_classification TEXT CHECK (novelty_classification IN ('not_found', 'similar_exists', 'exact_match')),
  model_version TEXT DEFAULT 'gpt-4o',
  few_shot_examples_used INTEGER DEFAULT 0,
  requires_expert_review TEXT[],
  
  -- Timestamps
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Status
  status TEXT CHECK (status IN ('draft', 'under_review', 'approved', 'in_progress', 'completed')) DEFAULT 'draft'
);

-- Indexes for experiment_plans
CREATE INDEX idx_plans_user_id ON experiment_plans(user_id);
CREATE INDEX idx_plans_hypothesis_id ON experiment_plans(hypothesis_id);
CREATE INDEX idx_plans_status ON experiment_plans(status);
CREATE INDEX idx_plans_generated_at ON experiment_plans(generated_at DESC);

-- GIN index for JSONB queries
CREATE INDEX idx_plans_data_gin ON experiment_plans USING GIN (plan_data);

-- RLS Policies for experiment_plans
ALTER TABLE experiment_plans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own plans"
  ON experiment_plans FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own plans"
  ON experiment_plans FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own plans"
  ON experiment_plans FOR UPDATE
  USING (auth.uid() = user_id);

-- ============================================================================
-- Table: reviews
-- Description: Scientist reviews and ratings for experiment plans
-- ============================================================================
CREATE TABLE reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID REFERENCES experiment_plans(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  
  -- Ratings (1-5 scale)
  protocol_rating INTEGER CHECK (protocol_rating BETWEEN 1 AND 5),
  materials_rating INTEGER CHECK (materials_rating BETWEEN 1 AND 5),
  budget_rating INTEGER CHECK (budget_rating BETWEEN 1 AND 5),
  timeline_rating INTEGER CHECK (timeline_rating BETWEEN 1 AND 5),
  validation_rating INTEGER CHECK (validation_rating BETWEEN 1 AND 5),
  overall_rating DECIMAL(3,2) GENERATED ALWAYS AS (
    (protocol_rating + materials_rating + budget_rating + timeline_rating + validation_rating) / 5.0
  ) STORED,
  
  -- Corrections (JSONB for structured feedback)
  corrections JSONB,
  
  -- Timestamps
  submitted_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Constraint: One review per user per plan
  UNIQUE(plan_id, user_id)
);

-- Indexes for reviews
CREATE INDEX idx_reviews_plan_id ON reviews(plan_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);
CREATE INDEX idx_reviews_overall_rating ON reviews(overall_rating DESC);
CREATE INDEX idx_reviews_submitted_at ON reviews(submitted_at DESC);

-- RLS Policies for reviews
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view reviews of own plans"
  ON reviews FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM experiment_plans
      WHERE experiment_plans.id = reviews.plan_id
      AND experiment_plans.user_id = auth.uid()
    )
    OR auth.uid() = user_id
  );

CREATE POLICY "Users can insert own reviews"
  ON reviews FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- Table: feedback_embeddings
-- Description: Vector embeddings of scientist corrections for RAG
-- ============================================================================
CREATE TABLE feedback_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  review_id UUID REFERENCES reviews(id) ON DELETE CASCADE,
  plan_id UUID REFERENCES experiment_plans(id) ON DELETE CASCADE,
  scientist_id UUID REFERENCES users(id) ON DELETE CASCADE,
  
  -- Correction content
  correction_text TEXT NOT NULL,
  original_issue TEXT,
  
  -- Vector embedding (1536 dimensions for text-embedding-3-small)
  embedding vector(1536) NOT NULL,
  
  -- Metadata
  hypothesis_domain TEXT NOT NULL,
  rating INTEGER CHECK (rating BETWEEN 1 AND 5),
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity index (HNSW for fast approximate nearest neighbor search)
CREATE INDEX idx_feedback_embeddings_vector 
  ON feedback_embeddings 
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Regular indexes
CREATE INDEX idx_feedback_embeddings_domain ON feedback_embeddings(hypothesis_domain);
CREATE INDEX idx_feedback_embeddings_rating ON feedback_embeddings(rating DESC);
CREATE INDEX idx_feedback_embeddings_created_at ON feedback_embeddings(created_at DESC);

-- RLS Policies for feedback_embeddings
ALTER TABLE feedback_embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view feedback embeddings"
  ON feedback_embeddings FOR SELECT
  USING (true);  -- Read-only for all authenticated users (for RAG)

CREATE POLICY "Users can insert own feedback embeddings"
  ON feedback_embeddings FOR INSERT
  WITH CHECK (auth.uid() = scientist_id);

-- ============================================================================
-- Database Functions
-- ============================================================================

-- Function: match_feedback_embeddings
-- Description: Similarity search for feedback embeddings using cosine distance
CREATE OR REPLACE FUNCTION match_feedback_embeddings(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.25,  -- Cosine distance threshold (1 - 0.75 similarity)
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
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    feedback_embeddings.id,
    feedback_embeddings.correction_text,
    feedback_embeddings.original_issue,
    feedback_embeddings.hypothesis_domain,
    feedback_embeddings.rating,
    feedback_embeddings.created_at,
    (feedback_embeddings.embedding <=> query_embedding) AS distance
  FROM feedback_embeddings
  WHERE 
    (filter_domain IS NULL OR feedback_embeddings.hypothesis_domain = filter_domain)
    AND (feedback_embeddings.embedding <=> query_embedding) < match_threshold
  ORDER BY distance ASC
  LIMIT match_count;
END;
$$;

-- Function: get_average_plan_rating
-- Description: Calculate average rating for an experiment plan
CREATE OR REPLACE FUNCTION get_average_plan_rating(plan_uuid uuid)
RETURNS decimal(3,2)
LANGUAGE plpgsql
AS $$
DECLARE
  avg_rating decimal(3,2);
BEGIN
  SELECT AVG(overall_rating) INTO avg_rating
  FROM reviews
  WHERE plan_id = plan_uuid;
  
  RETURN COALESCE(avg_rating, 0.0);
END;
$$;

-- ============================================================================
-- Triggers for updated_at timestamps
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger for experiment_plans table
CREATE TRIGGER update_experiment_plans_updated_at BEFORE UPDATE ON experiment_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Migration Complete
-- ============================================================================
