-- 24_replaced_status_action_label.sql
-- 1. Expands fire_incidents verification_status CHECK to include 'REPLACED'.
-- 2. Adds action_label VARCHAR(80) column to incident_verification_history.
-- Idempotent: YES (DO $$ guards).
--
-- ⚠️  Stop and ask before running in production: the CHECK drop-and-recreate
--     takes a brief ACCESS EXCLUSIVE lock on fire_incidents.

BEGIN;

-- -----------------------------------------------------------------------
-- 1. Expand verification_status CHECK to include REPLACED
-- -----------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM   pg_constraint c
        JOIN   pg_namespace  n ON n.oid = c.connamespace
        WHERE  n.nspname  = 'wims'
          AND  c.conname  = 'fire_incidents_verification_status_check'
          AND  pg_get_constraintdef(c.oid) NOT LIKE '%REPLACED%'
    ) THEN
        ALTER TABLE wims.fire_incidents
            DROP CONSTRAINT fire_incidents_verification_status_check;
        ALTER TABLE wims.fire_incidents
            ADD CONSTRAINT fire_incidents_verification_status_check
            CHECK (verification_status IN (
                'DRAFT', 'PENDING', 'PENDING_VALIDATION',
                'VERIFIED', 'REJECTED', 'REPLACED'
            ));
        RAISE NOTICE 'Rebuilt fire_incidents_verification_status_check with REPLACED.';
    ELSE
        RAISE NOTICE 'fire_incidents_verification_status_check already includes REPLACED; skipped.';
    END IF;
END $$;

-- -----------------------------------------------------------------------
-- 2. Add action_label to incident_verification_history
-- -----------------------------------------------------------------------
ALTER TABLE wims.incident_verification_history
    ADD COLUMN IF NOT EXISTS action_label VARCHAR(80);

COMMIT;
