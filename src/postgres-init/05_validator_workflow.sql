-- =============================================================================
-- Migration: 05_validator_workflow.sql
-- Purpose  : Implements the encoder → validator review workflow.
--
-- Changes
-- -------
--   1. Normalize wims.users role constraint to include NATIONAL_VALIDATOR
--      (was stored as 'VALIDATOR' in seed; application code expects 'NATIONAL_VALIDATOR').
--   2. Migrate any existing VALIDATOR rows to NATIONAL_VALIDATOR.
--   3. Ensure validator test user has an assigned_region_id (defaults to region 1).
--   4. Align fire_incidents verification_status CHECK to include PENDING_VALIDATION.
--   5. Create wims.incident_verification_history (audit trail).
--   6. Create RLS UPDATE policy: NATIONAL_VALIDATOR may only update incidents
--      in their assigned region.
--
-- Idempotent: safe to re-run.
-- Run via:
--   docker compose exec postgres psql -U postgres -d wims \
--     -f /docker-entrypoint-initdb.d/05_validator_workflow.sql
--   OR from project root:
--   docker compose exec -T postgres psql -U postgres -d wims \
--     < src/postgres-init/05_validator_workflow.sql
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Normalize wims.users role CHECK constraint
--    The seed script used 'VALIDATOR'; application code uses 'NATIONAL_VALIDATOR'.
--    We drop and recreate the constraint to include both during the transition
--    window, then normalise existing data, then tighten if desired.
-- ---------------------------------------------------------------------------

DO $$
BEGIN
    -- Drop old constraint if it does not already include NATIONAL_VALIDATOR
    IF EXISTS (
        SELECT 1
        FROM   pg_constraint c
        JOIN   pg_namespace  n ON n.oid = c.connamespace
        WHERE  n.nspname = 'wims'
          AND  c.conname  = 'users_role_check'
          AND  pg_get_constraintdef(c.oid) NOT LIKE '%NATIONAL_VALIDATOR%'
    ) THEN
        ALTER TABLE wims.users DROP CONSTRAINT users_role_check;
        RAISE NOTICE 'Dropped old users_role_check (did not contain NATIONAL_VALIDATOR).';
    END IF;

    -- Re-add with full authoritative set (idempotent: only if absent)
    IF NOT EXISTS (
        SELECT 1
        FROM   pg_constraint c
        JOIN   pg_namespace  n ON n.oid = c.connamespace
        WHERE  n.nspname = 'wims'
          AND  c.conname  = 'users_role_check'
    ) THEN
        ALTER TABLE wims.users
            ADD CONSTRAINT users_role_check
            CHECK (role IN (
                'CIVILIAN_REPORTER',
                'REGIONAL_ENCODER',
                'VALIDATOR',            -- legacy seed value; kept for backwards compat
                'NATIONAL_VALIDATOR',   -- authoritative application value
                'NATIONAL_ANALYST',
                'ANALYST',              -- legacy alias
                'SYSTEM_ADMIN'
            ));
        RAISE NOTICE 'Created new users_role_check including NATIONAL_VALIDATOR.';
    END IF;
END $$;


-- ---------------------------------------------------------------------------
-- 2. Migrate existing VALIDATOR rows → NATIONAL_VALIDATOR
-- ---------------------------------------------------------------------------

UPDATE wims.users
SET    role       = 'NATIONAL_VALIDATOR',
       updated_at = now()
WHERE  role = 'VALIDATOR';

-- Log how many rows were touched (visible in psql output)
DO $$
DECLARE
    n INT;
BEGIN
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE 'Migrated % user row(s) from VALIDATOR → NATIONAL_VALIDATOR.', n;
END $$;


-- ---------------------------------------------------------------------------
-- 3. Ensure validator_test and encoder_test users have assigned_region_id
--    (seed-dev-users.sh leaves it NULL; our dependency requires a value).
--    Defaults to region_id = 1.  Skip if user does not exist yet.
-- ---------------------------------------------------------------------------

UPDATE wims.users
SET    assigned_region_id = COALESCE(assigned_region_id, 1),
       updated_at         = now()
WHERE  username IN ('validator_test', 'encoder_test')
  AND  assigned_region_id IS NULL;


-- ---------------------------------------------------------------------------
-- 4. Align fire_incidents verification_status CHECK
--    DB must allow PENDING_VALIDATION (used by public DMZ route since day 1).
-- ---------------------------------------------------------------------------

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM   pg_constraint c
        JOIN   pg_namespace  n ON n.oid = c.connamespace
        WHERE  n.nspname = 'wims'
          AND  c.conname  = 'fire_incidents_verification_status_check'
          AND  pg_get_constraintdef(c.oid) NOT LIKE '%PENDING_VALIDATION%'
    ) THEN
        ALTER TABLE wims.fire_incidents
            DROP CONSTRAINT fire_incidents_verification_status_check;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM   pg_constraint c
        JOIN   pg_namespace  n ON n.oid = c.connamespace
        WHERE  n.nspname = 'wims'
          AND  c.conname  = 'fire_incidents_verification_status_check'
    ) THEN
        ALTER TABLE wims.fire_incidents
            ADD CONSTRAINT fire_incidents_verification_status_check
            CHECK (verification_status IN (
                'DRAFT',
                'PENDING',
                'PENDING_VALIDATION',
                'VERIFIED',
                'REJECTED'
            ));
    END IF;
END $$;


-- ---------------------------------------------------------------------------
-- 5. Create incident verification history table
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS wims.incident_verification_history (
    ivh_id              BIGSERIAL PRIMARY KEY,
    incident_id         INTEGER REFERENCES wims.fire_incidents(incident_id) ON DELETE CASCADE,
    action              VARCHAR(32) NOT NULL,
    previous_status     VARCHAR(32),
    new_status          VARCHAR(32),
    comments            TEXT,
    action_by_user_id   UUID REFERENCES wims.users(user_id) ON DELETE RESTRICT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- ---------------------------------------------------------------------------
-- 6. Add RLS policy for validators
-- ---------------------------------------------------------------------------

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM   pg_policies p
        WHERE  p.schemaname = 'wims'
          AND  p.tablename  = 'fire_incidents'
          AND  p.policyname = 'fire_incidents_validator_update'
    ) THEN
        CREATE POLICY fire_incidents_validator_update
            ON wims.fire_incidents
            FOR UPDATE
            USING (
                EXISTS (
                    SELECT 1
                    FROM wims.users u
                    WHERE u.user_id = current_setting('wims.current_user_id', true)::uuid
                      AND u.role = 'NATIONAL_VALIDATOR'
                      AND u.assigned_region_id = wims.fire_incidents.region_id
                )
            )
            WITH CHECK (
                EXISTS (
                    SELECT 1
                    FROM wims.users u
                    WHERE u.user_id = current_setting('wims.current_user_id', true)::uuid
                      AND u.role = 'NATIONAL_VALIDATOR'
                      AND u.assigned_region_id = wims.fire_incidents.region_id
                )
            );
    END IF;
END $$;

COMMIT;