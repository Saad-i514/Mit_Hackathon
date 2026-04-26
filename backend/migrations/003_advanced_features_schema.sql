-- ============================================================================
-- AI Scientist Platform - Advanced Features Schema
-- Migration: 003_advanced_features_schema.sql
-- Description: Creates tables for advanced features (F-04, F-08, F-09, F-10, F-11, F-12, F-13, F-15, F-16, F-17)
-- ============================================================================

-- ============================================================================
-- Table: plan_versions (F-16: Plan Version History)
-- Description: Versioned snapshots of experiment plans for history tracking and restoration
-- ============================================================================
CREATE TABLE plan_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_id UUID REFERENCES experiment_plans(id) ON DELETE CASCADE,
  version_number INTEGER NOT NULL,
  plan_snapshot JSONB NOT NULL,
  change_summary TEXT,
  triggered_by TEXT CHECK (triggered_by IN ('initial_generation', 'scientist_correction', 'hypothesis_edit', 'manual_regen')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for plan_versions
CREATE UNIQUE INDEX plan_versions_unique ON plan_versions(experiment_id, version_number);
CREATE INDEX idx_plan_versions_experiment_id ON plan_versions(experiment_id);
CREATE INDEX idx_plan_versions_created_at ON plan_versions(created_at DESC);

-- RLS Policies for plan_versions
ALTER TABLE plan_versions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view plan versions for their plans"
  ON plan_versions FOR SELECT
  USING (
    experiment_id IN (
      SELECT id FROM experiment_plans WHERE user_id = auth.uid()
    )
  );

-- ============================================================================
-- Table: plan_annotations (F-15: Live Collaborative Review)
-- Description: Real-time annotations and comments for collaborative plan review
-- ============================================================================
CREATE TABLE plan_annotations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID REFERENCES experiment_plans(id) ON DELETE CASCADE,
  section TEXT NOT NULL,
  content TEXT NOT NULL,
  position_pct FLOAT,
  author_id TEXT,
  author_role TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for plan_annotations
CREATE INDEX idx_plan_annotations_plan_id ON plan_annotations(plan_id);
CREATE INDEX idx_plan_annotations_created_at ON plan_annotations(created_at DESC);

-- RLS Policies for plan_annotations
ALTER TABLE plan_annotations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view annotations for their plans"
  ON plan_annotations FOR SELECT
  USING (
    plan_id IN (
      SELECT id FROM experiment_plans WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert annotations on their plans"
  ON plan_annotations FOR INSERT
  WITH CHECK (
    plan_id IN (
      SELECT id FROM experiment_plans WHERE user_id = auth.uid()
    )
  );

-- ============================================================================
-- Table: lab_equipment (F-13: Equipment Checklist)
-- Description: Per-lab equipment inventory and availability tracking
-- ============================================================================
CREATE TABLE lab_equipment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  equipment TEXT NOT NULL,
  has_item BOOLEAN DEFAULT TRUE,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for lab_equipment
CREATE INDEX idx_lab_equipment_user_id ON lab_equipment(user_id);
CREATE INDEX idx_lab_equipment_equipment ON lab_equipment(equipment);
CREATE UNIQUE INDEX lab_equipment_unique ON lab_equipment(user_id, equipment);

-- RLS Policies for lab_equipment
ALTER TABLE lab_equipment ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own equipment"
  ON lab_equipment FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own equipment"
  ON lab_equipment FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own equipment"
  ON lab_equipment FOR UPDATE
  USING (auth.uid() = user_id);

-- ============================================================================
-- Table: clinical_trial_results (F-04: Clinical Trials Radar)
-- Description: Cached results from ClinicalTrials.gov API queries
-- ============================================================================
CREATE TABLE clinical_trial_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_id UUID REFERENCES experiment_plans(id) ON DELETE CASCADE,
  total_found INTEGER,
  studies JSONB,
  queried_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for clinical_trial_results
CREATE INDEX idx_clinical_trial_results_experiment_id ON clinical_trial_results(experiment_id);
CREATE INDEX idx_clinical_trial_results_queried_at ON clinical_trial_results(queried_at DESC);

-- RLS Policies for clinical_trial_results
ALTER TABLE clinical_trial_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view clinical trial results for their plans"
  ON clinical_trial_results FOR SELECT
  USING (
    experiment_id IN (
      SELECT id FROM experiment_plans WHERE user_id = auth.uid()
    )
  );

-- ============================================================================
-- Table: protocol_matches (F-03: Protocol Similarity Search)
-- Description: Cached results from protocols.io API queries
-- ============================================================================
CREATE TABLE protocol_matches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_id UUID REFERENCES experiment_plans(id) ON DELETE CASCADE,
  matches JSONB,
  queried_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for protocol_matches
CREATE INDEX idx_protocol_matches_experiment_id ON protocol_matches(experiment_id);
CREATE INDEX idx_protocol_matches_queried_at ON protocol_matches(queried_at DESC);

-- RLS Policies for protocol_matches
ALTER TABLE protocol_matches ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view protocol matches for their plans"
  ON protocol_matches FOR SELECT
  USING (
    experiment_id IN (
      SELECT id FROM experiment_plans WHERE user_id = auth.uid()
    )
  );

-- ============================================================================
-- Enable Realtime for Collaborative Features
-- ============================================================================
-- NOTE: These must be enabled in Supabase Dashboard:
-- 1. Go to Table Editor
-- 2. Select plan_annotations table
-- 3. Click "Enable Realtime" and select INSERT, UPDATE events
-- 4. Select scientist_reviews table (already exists)
-- 5. Click "Enable Realtime" and select INSERT, UPDATE events
-- 6. Select experiment_plans table (already exists)
-- 7. Click "Enable Realtime" and select UPDATE events

-- ============================================================================
-- Migration Complete
-- ============================================================================
-- All tables created with RLS enabled and appropriate indexes
-- Realtime must be enabled manually in Supabase Dashboard for collaborative features
