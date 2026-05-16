-- 31_barangay_geometry.sql
-- Dependencies: 02_ref_geography.sql
-- Idempotent: YES
-- Adds geometry column to ref_barangays for reverse-geocoding incidents to barangay.
-- A GiST index is created for fast ST_Contains lookups.
--
-- NOTE: Barangay polygon data must be loaded separately after this migration.
-- Until polygons are loaded, reverse-geocoding gracefully skips and incidents
-- keep barangay_id unset unless supplied explicitly.
BEGIN;

ALTER TABLE wims.ref_barangays
    ADD COLUMN IF NOT EXISTS geometry GEOGRAPHY(POLYGON, 4326);

CREATE INDEX IF NOT EXISTS idx_ref_barangays_geometry
    ON wims.ref_barangays USING GIST (geometry);

COMMIT;
