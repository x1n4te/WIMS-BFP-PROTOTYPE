-- 03_users.sql
-- Dependencies: 01_extensions_roles.sql (schema + roles exist)
-- Idempotent: YES

BEGIN;

CREATE TABLE IF NOT EXISTS wims.users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  keycloak_id UUID NOT NULL UNIQUE,
  username VARCHAR NOT NULL UNIQUE,
  role VARCHAR NOT NULL,
  assigned_region_id INTEGER REFERENCES wims.ref_regions(region_id),
  contact_number    VARCHAR(20),
  is_active BOOLEAN DEFAULT TRUE,
  mfa_enabled BOOLEAN DEFAULT FALSE,
  last_login TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT users_role_check CHECK (
    role IN (
      'CIVILIAN_REPORTER',
      'REGIONAL_ENCODER',
      'NATIONAL_VALIDATOR',
      'NATIONAL_ANALYST',
      'SYSTEM_ADMIN'
    )
  )
);

-- Bootstrap inserts (safe for re-runs via ON CONFLICT)
-- Suricata EVE ingestion service account
INSERT INTO wims.users (user_id, keycloak_id, username, role, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    '00000000-0000-0000-0000-000000000000'::uuid,
    'svc_suricata',
    'NATIONAL_ANALYST',
    TRUE
)
ON CONFLICT (user_id) DO NOTHING;

-- Background task service account (SYSTEM_ADMIN role, cross-table access for Celery tasks)
INSERT INTO wims.users (user_id, keycloak_id, username, role, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000002'::uuid,
    '00000000-0000-0000-0000-000000000002'::uuid,
    'svc_task',
    'SYSTEM_ADMIN',
    TRUE
)
ON CONFLICT (user_id) DO NOTHING;

COMMIT;
