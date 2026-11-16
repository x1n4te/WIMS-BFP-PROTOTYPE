#!/bin/bash
# First-run bootstrap: create ONE SYSTEM_ADMIN account (Keycloak + wims.users).
#
# Idempotent. Run once after the stack is up, from the project root:
#   BOOTSTRAP_ADMIN_USERNAME=... BOOTSTRAP_ADMIN_EMAIL=... \
#   BOOTSTRAP_ADMIN_PASSWORD=... ./scripts/bootstrap-admin.sh
#
# Env (read from the environment, then src/.env, then src/.env.production):
#   BOOTSTRAP_ADMIN_USERNAME   required  (letters, digits, . _ @ -)
#   BOOTSTRAP_ADMIN_EMAIL      required
#   BOOTSTRAP_ADMIN_PASSWORD   required  initial password; must satisfy the realm
#                                        password policy; it is TEMPORARY
#   BOOTSTRAP_ADMIN_FIRST_NAME optional  default "System"
#   BOOTSTRAP_ADMIN_LAST_NAME  optional  default "Administrator"
#
# The account is created with the UPDATE_PASSWORD and CONFIGURE_TOTP required
# actions, so the first login forces a password change and OTP enrolment.
# If the user already exists in Keycloak its password is NOT reset; only the
# SYSTEM_ADMIN role and the wims.users row are (re)asserted.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-wims-postgres}"
KEYCLOAK_CONTAINER="${KEYCLOAK_CONTAINER:-wims-keycloak}"
KC_SERVER="${KC_SERVER:-http://localhost:8080/auth}"   # reachable from this host
KC_SERVER_INTERNAL="http://localhost:8080/auth"        # as seen inside the container
KC_REALM="bfp"

# Snapshot caller-provided values so .env files cannot override them.
_u="${BOOTSTRAP_ADMIN_USERNAME:-}"; _e="${BOOTSTRAP_ADMIN_EMAIL:-}"; _p="${BOOTSTRAP_ADMIN_PASSWORD:-}"
for f in "$PROJECT_ROOT/src/.env" "$PROJECT_ROOT/src/.env.production"; do
  if [ -f "$f" ]; then set -a; . "$f"; set +a; fi
done
BOOTSTRAP_ADMIN_USERNAME="${_u:-${BOOTSTRAP_ADMIN_USERNAME:-}}"
BOOTSTRAP_ADMIN_EMAIL="${_e:-${BOOTSTRAP_ADMIN_EMAIL:-}}"
BOOTSTRAP_ADMIN_PASSWORD="${_p:-${BOOTSTRAP_ADMIN_PASSWORD:-}}"
FIRST_NAME="${BOOTSTRAP_ADMIN_FIRST_NAME:-System}"
LAST_NAME="${BOOTSTRAP_ADMIN_LAST_NAME:-Administrator}"
KC_ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
KC_ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"

: "${BOOTSTRAP_ADMIN_USERNAME:?BOOTSTRAP_ADMIN_USERNAME is required}"
: "${BOOTSTRAP_ADMIN_EMAIL:?BOOTSTRAP_ADMIN_EMAIL is required}"
: "${BOOTSTRAP_ADMIN_PASSWORD:?BOOTSTRAP_ADMIN_PASSWORD is required}"
if ! printf '%s' "$BOOTSTRAP_ADMIN_USERNAME" | grep -qE '^[A-Za-z0-9._@-]{3,255}$'; then
  echo "ERROR: BOOTSTRAP_ADMIN_USERNAME may only contain letters, digits, . _ @ -" >&2
  exit 1
fi
if ! printf '%s' "$BOOTSTRAP_ADMIN_EMAIL" | grep -qE "^[^@[:space:]']+@[^@[:space:]']+$"; then
  echo "ERROR: BOOTSTRAP_ADMIN_EMAIL is not a valid email address" >&2
  exit 1
fi

# shellcheck source=lib/kc-common.sh
. "$SCRIPT_DIR/lib/kc-common.sh"

wait_for_keycloak_healthy 120
kc_login

UUID_RE='[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
find_user_id() {
  kcadm get users -r "$KC_REALM" -q exact=true -q username="$BOOTSTRAP_ADMIN_USERNAME" --fields id 2>/dev/null \
    | grep -oE "$UUID_RE" | head -1 || true
}

uuid="$(find_user_id)"
if [ -n "$uuid" ]; then
  echo "Keycloak user '$BOOTSTRAP_ADMIN_USERNAME' already exists ($uuid); password left unchanged."
else
  echo "Creating Keycloak user '$BOOTSTRAP_ADMIN_USERNAME'..."
  kcadm create users -r "$KC_REALM" \
    -s username="$BOOTSTRAP_ADMIN_USERNAME" -s email="$BOOTSTRAP_ADMIN_EMAIL" \
    -s firstName="$FIRST_NAME" -s lastName="$LAST_NAME" \
    -s enabled=true -s emailVerified=true \
    -s 'requiredActions=["UPDATE_PASSWORD","CONFIGURE_TOTP"]' >/dev/null
  uuid="$(find_user_id)"
  [ -n "$uuid" ] || { echo "ERROR: user was created but its id could not be read" >&2; exit 1; }
  if ! kcadm set-password -r "$KC_REALM" --username "$BOOTSTRAP_ADMIN_USERNAME" \
        --new-password "$BOOTSTRAP_ADMIN_PASSWORD" --temporary; then
    echo "ERROR: initial password rejected (realm password policy?). Removing the half-created user." >&2
    kcadm delete "users/$uuid" -r "$KC_REALM" || true
    exit 1
  fi
fi

echo "Assigning SYSTEM_ADMIN..."
kcadm add-roles -r "$KC_REALM" --uusername "$BOOTSTRAP_ADMIN_USERNAME" --rolename SYSTEM_ADMIN

echo "Syncing wims.users..."
sql="UPDATE wims.users SET keycloak_id = '$uuid'::uuid, username = '$BOOTSTRAP_ADMIN_USERNAME', role = 'SYSTEM_ADMIN', assigned_region_id = NULL, is_active = TRUE, updated_at = now() WHERE username = '$BOOTSTRAP_ADMIN_USERNAME' OR keycloak_id = '$uuid'::uuid; INSERT INTO wims.users (user_id, keycloak_id, username, role, assigned_region_id, is_active) SELECT '$uuid'::uuid, '$uuid'::uuid, '$BOOTSTRAP_ADMIN_USERNAME', 'SYSTEM_ADMIN', NULL, TRUE WHERE NOT EXISTS (SELECT 1 FROM wims.users WHERE username = '$BOOTSTRAP_ADMIN_USERNAME' OR keycloak_id = '$uuid'::uuid);"
printf '%s\n' "$sql" | docker_exec -i "$POSTGRES_CONTAINER" psql -v ON_ERROR_STOP=1 -q -U postgres -d wims

echo ""
echo "Bootstrap admin ready: $BOOTSTRAP_ADMIN_USERNAME ($uuid)"
echo "First login forces a password change and OTP enrolment."
