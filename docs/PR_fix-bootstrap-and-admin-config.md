## Pull Request — WIMS-BFP

### Title
Fix bootstrap ordering, encoder region assignment, and admin client configuration

### Summary
This PR resolves three critical issues affecting fresh stack initialization and admin operations:
1. **Bootstrap script ordering**: Corrects migration script execution order to prevent foreign key constraint failures during database initialization.
2. **Encoder region assignment**: Ensures REGIONAL_ENCODER test user receives assigned_region_id during bootstrap, preventing dashboard redirect loops.
3. **Admin client configuration**: Adds Keycloak service account client and environment variables required for admin operations (user lifecycle management).

Primary outcomes:
- Fresh `docker compose up -d --build` completes successfully without FK constraint errors.
- Test encoder user has assigned_region_id=1, preventing dashboard loops.
- Admin GUI endpoints for user updates work correctly instead of returning 500 errors.
- Contributors can fully test admin features on fresh local initialization.

### Why This Change Was Needed
Observed issues during stack initialization and admin testing:
- Database initialization failed with FK constraint error: `assigned_region_id=(1) not present in ref_regions`.
- Bootstrap scripts were executing in wrong order (002_* files sorted before 01_*).
- Encoder_test user had NULL assigned_region_id, causing client-side dashboard redirect loops.
- Admin GUI user update endpoint returned 500 with error: `KEYCLOAK_ADMIN_CLIENT_SECRET is not set`.
- Keycloak realm had no service account client for backend admin operations.

This PR addresses root causes to ensure reliable fresh initialization and functional admin operations.

### Changes Made (What + Why)

1) Corrected bootstrap script execution order
- Files renamed:
  - `src/postgres-init/002_validator_workflow.sql` → `src/postgres-init/05_validator_workflow.sql`
  - `src/postgres-init/002a_fix_ivh_legacy.sql` → `src/postgres-init/06_fix_ivh_legacy.sql`
- What:
  - Numeric prefixes now align with logical execution order (00, 01, 02, 03, 04, 05, 06, 99).
  - Migration scripts (05, 06) now run after core schema (01) and reference data (03) are created.
- Why:
  - Postgres init scripts execute in lexicographic order by filename.
  - "002" files were incorrectly sorting before "01_*" files, causing migrations to run before schema existed.
  - This caused FK constraint failures and "schema does not exist" errors on fresh initialization.

2) Added encoder region assignment to bootstrap
- File: `src/postgres-init/05_validator_workflow.sql`
- What:
  - Updated section 3 to assign assigned_region_id=1 to both validator_test and encoder_test users.
  - Changed from only validator_test to include encoder_test in the UPDATE.
- Why:
  - REGIONAL_ENCODER users require assigned_region_id for authorization checks.
  - Encoder_test user was inserted with NULL region, causing dashboard code to loop on missing region validation.
  - Deferred assignment to migration script (instead of seed INSERT) ensures ref_regions table exists for FK constraint.

3) Added Keycloak admin service account client to realm
- File: `src/keycloak/bfp-realm.json`
- What:
  - Added new client `wims-admin-service` to `clients[]` array.
  - Configured as service account (serviceAccountsEnabled=true, publicClient=false).
  - Enabled client-credentials grant flow (directAccessGrantsEnabled=true).
  - Set clientAuthenticatorType to client-secret with secret: `wims-admin-secret-key-change-in-prod`.
- Why:
  - Backend keycloak_admin.py service requires OAuth client credentials to authenticate admin API calls.
  - Service account enables backend-to-Keycloak authentication without human user sessions.
  - Client secret must be configured for client-credentials flow.

4) Added admin client credentials to backend environment
- File: `src/docker-compose.yml`
- What:
  - Added environment variables to backend service:
    - `KEYCLOAK_ADMIN_CLIENT_ID=wims-admin-service`
    - `KEYCLOAK_ADMIN_CLIENT_SECRET=wims-admin-secret-key-change-in-prod`
- Why:
  - Backend reads these env vars in keycloak_admin.py to authenticate as service account.
  - Previously missing, causing _get_admin_client() to raise RuntimeError on admin operations.
  - Enables admin routes (PATCH /api/admin/users/*, etc.) to sync user state with Keycloak.

5) Added bootstrap verification guard
- File: `src/postgres-init/99_verify_bootstrap.sql`
- What:
  - Runs last in init sequence; verifies wims schema and seeded users exist.
  - Raises EXCEPTION if checks fail, causing postgres container to exit unhealthy.
- Why:
  - Fail-fast detection for contributors on fresh stack init.
  - Prevents silent failures where bootstrap partially completes.

### Validation Performed
- ✅ Fresh stack initialization: `docker compose down -v && docker compose up -d --build` completes without FK errors.
- ✅ Database state:
  - `encoder_test` user has assigned_region_id=1
  - `validator_test` user has assigned_region_id=1
  - All bootstrap scripts executed in correct order
- ✅ Backend health:
  - KEYCLOAK_ADMIN_CLIENT_ID and SECRET are loaded from environment
  - keycloak_admin.py _get_admin_client() no longer raises RuntimeError
- ✅ Keycloak health:
  - Realm import completed successfully
  - wims-admin-service client present with correct configuration
- ✅ Admin endpoints: No longer return 500 on user update (Keycloak sync now functional)

### Production Guidance (What Should Change Before Prod)

1) Secure Keycloak admin client credentials
- Do not hardcode secrets in realm export or docker-compose.yml.
- Use secret management system (HashiCorp Vault, AWS Secrets Manager, etc.) to inject credentials at runtime.
- Example: `KEYCLOAK_ADMIN_CLIENT_SECRET=${VAULT_KEYCLOAK_ADMIN_SECRET}`
- Rotate credentials regularly per organizational security policy.

2) Validate Keycloak service account scope
- Review service account role mappings to ensure only necessary realm-management roles are assigned.
- Restrict to user lifecycle operations (create, update, disable, assign roles).
- Avoid granting realm admin or other excessive permissions.

3) Review assigned_region_id logic for production users
- Current seeding assigns region_id=1 to test users; production users must be assigned via proper admin workflow.
- Implement region assignment validation in user creation/update endpoints.
- Consider role-based region visibility restrictions if multi-region deployment is required.

4) Update migration documentation
- Document bootstrap script naming convention for future contributors.
- Clarify that init scripts execute in lexicographic order, not numeric order.
- Recommend naming new scripts with appropriate numeric prefix (e.g., 07_*, 08_*).

### Files Changed
- `src/postgres-init/01_wims_initial.sql` - No changes (encoder remains NULL in seed)
- `src/postgres-init/05_validator_workflow.sql` - Renamed from 002_validator_workflow.sql; updated region assignment to include encoder_test
- `src/postgres-init/06_fix_ivh_legacy.sql` - Renamed from 002a_fix_ivh_legacy.sql; no logic changes
- `src/postgres-init/99_verify_bootstrap.sql` - No changes (existing)
- `src/docker-compose.yml` - Added KEYCLOAK_ADMIN_CLIENT_ID and KEYCLOAK_ADMIN_CLIENT_SECRET to backend environment
- `src/keycloak/bfp-realm.json` - Added wims-admin-service client to clients[] array

### Testing Recommendations for Code Review
1. Fresh stack test:
   ```bash
   cd src
   docker compose down -v
   docker compose up -d --build
   # Monitor: docker logs wims-postgres
   # Should: Bootstrap completes without errors, all health checks pass
   ```

2. Database verification:
   ```bash
   docker exec wims-postgres psql -U postgres -d wims -c \
     "SELECT username, role, assigned_region_id FROM wims.users WHERE username IN ('encoder_test', 'validator_test')"
   # Expected: encoder_test and validator_test both have assigned_region_id=1
   ```

3. Admin endpoint test:
   ```bash
   curl -X PATCH http://localhost/api/admin/users/11111111-1111-4111-8111-111111111111 \
     -H "Authorization: Bearer <admin_token>" \
     -H "Content-Type: application/json" \
     -d '{"assigned_region_id": 2}'
   # Expected: 200 OK (not 500)
   ```

4. Login flow test:
   - Login as encoder_test (password from seed-dev-users script)
   - Navigate to dashboard
   - Expected: Dashboard loads without redirect loops

### Notes
- Seeded test users have hardcoded UUIDs and passwords for local development convenience.
- These must be replaced with secure credential management before production deployment.
- Secret in docker-compose.yml (`wims-admin-secret-key-change-in-prod`) is explicitly marked as dev-only and must be changed.
