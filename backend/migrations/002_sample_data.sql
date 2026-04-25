-- ============================================================================
-- AI Scientist Platform - Sample Data for Development
-- Migration: 002_sample_data.sql
-- Description: Inserts sample data for development and testing
-- ============================================================================

-- Sample user (Principal Investigator)
INSERT INTO users (id, email, full_name, institution, role)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'test@example.com',
  'Dr. Test Scientist',
  'MIT',
  'principal_investigator'
) ON CONFLICT (id) DO NOTHING;

-- Sample hypothesis (Diagnostics domain)
INSERT INTO hypotheses (id, user_id, hypothesis_text, domain, testable_claim, validation_status)
VALUES (
  '00000000-0000-0000-0000-000000000002',
  '00000000-0000-0000-0000-000000000001',
  'Paper-based electrochemical biosensors can detect glucose at concentrations below 1 mM with 95% accuracy',
  'diagnostics',
  'Detection accuracy >= 95% at < 1 mM glucose',
  'valid'
) ON CONFLICT (id) DO NOTHING;

-- Sample hypothesis (Gut Health domain)
INSERT INTO hypotheses (id, user_id, hypothesis_text, domain, testable_claim, validation_status)
VALUES (
  '00000000-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000001',
  'Lactobacillus rhamnosus GG supplementation for 4 weeks will reduce intestinal permeability by at least 30% compared to controls, measured by FITC-dextran assay',
  'gut_health',
  'Intestinal permeability reduction >= 30% vs controls',
  'valid'
) ON CONFLICT (id) DO NOTHING;

-- Sample hypothesis (Cell Biology domain)
INSERT INTO hypotheses (id, user_id, hypothesis_text, domain, testable_claim, validation_status)
VALUES (
  '00000000-0000-0000-0000-000000000004',
  '00000000-0000-0000-0000-000000000001',
  'Replacing DMSO with trehalose as a cryoprotectant will increase post-thaw viability of HeLa cells by at least 15 percentage points',
  'cell_biology',
  'Post-thaw viability increase >= 15 percentage points vs DMSO',
  'valid'
) ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- Sample Data Migration Complete
-- ============================================================================
