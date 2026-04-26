-- ============================================================================
-- Migration: 004_fix_lab_equipment_fk.sql
-- Description: Fix lab_equipment FK to reference auth.users instead of public.users
-- ============================================================================

-- Drop the existing FK constraint and recreate pointing to auth.users
ALTER TABLE lab_equipment DROP CONSTRAINT IF EXISTS lab_equipment_user_id_fkey;
ALTER TABLE lab_equipment ADD CONSTRAINT lab_equipment_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
