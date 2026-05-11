-- 23_archived_at.sql
-- Adds archived_at TIMESTAMPTZ column to wims.fire_incidents.
-- Idempotent: YES (IF NOT EXISTS guard).

BEGIN;

ALTER TABLE wims.fire_incidents
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

-- Backfill: rows already archived receive a synthetic timestamp from updated_at.
UPDATE wims.fire_incidents
SET archived_at = updated_at
WHERE is_archived = TRUE AND archived_at IS NULL;

COMMIT;
