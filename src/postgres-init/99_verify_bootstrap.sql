-- Final bootstrap guard for fresh Postgres initialization.
-- Fails fast if the auth schema or deterministic Keycloak-linked users were not created.

\connect wims

DO $$
DECLARE
  seeded_users INTEGER;
BEGIN
  IF to_regclass('wims.users') IS NULL THEN
    RAISE EXCEPTION 'Bootstrap verification failed: wims.users table is missing';
  END IF;

  SELECT COUNT(*)
    INTO seeded_users
    FROM wims.users
   WHERE keycloak_id IN (
     '11111111-1111-4111-8111-111111111111'::uuid,
     '22222222-2222-4222-8222-222222222222'::uuid,
     '33333333-3333-4333-8333-333333333333'::uuid,
     '44444444-4444-4444-8444-444444444444'::uuid,
     '55555555-5555-4555-8555-555555555555'::uuid
   );

  IF seeded_users <> 5 THEN
    RAISE EXCEPTION
      'Bootstrap verification failed: expected 5 seeded Keycloak users, found %',
      seeded_users;
  END IF;
END $$;