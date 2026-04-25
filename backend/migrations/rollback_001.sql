-- ============================================================================
-- AI Scientist Platform - Rollback Initial Schema
-- Migration: rollback_001.sql
-- Description: Drops all tables, functions, and extensions in reverse order
-- ============================================================================

-- Drop triggers
DROP TRIGGER IF EXISTS update_experiment_plans_updated_at ON experiment_plans;
DROP TRIGGER IF EXISTS update_users_updated_at ON users;

-- Drop trigger function
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop database functions
DROP FUNCTION IF EXISTS get_average_plan_rating(uuid);
DROP FUNCTION IF EXISTS match_feedback_embeddings(vector(1536), float, int, text);

-- Drop tables in reverse order (respecting foreign key dependencies)
DROP TABLE IF EXISTS feedback_embeddings CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS experiment_plans CASCADE;
DROP TABLE IF EXISTS hypotheses CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop extensions
DROP EXTENSION IF EXISTS vector;
DROP EXTENSION IF EXISTS "uuid-ossp";

-- ============================================================================
-- Rollback Complete
-- ============================================================================
