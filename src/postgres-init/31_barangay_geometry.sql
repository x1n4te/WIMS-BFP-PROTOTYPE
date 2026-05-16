-- 31_barangay_geometry.sql
-- Idempotent: YES
-- Reverses the geometry column addition from this migration.
-- The ref_barangays table retains its reference data (region/province/city mappings)
-- for validation purposes only — no polygon geometry is needed since barangay_id
-- is never supplied by AFOR import or manual regional encoder input.

DROP INDEX IF EXISTS wims.idx_ref_barangays_geometry;
ALTER TABLE wims.ref_barangays DROP COLUMN IF EXISTS geometry;