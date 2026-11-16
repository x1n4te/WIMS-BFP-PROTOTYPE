#!/bin/bash
# Shared helpers for scripts that drive the local wims-keycloak container with
# kcadm.sh. Source this file; do not execute it.
#
# Requires the caller to have set: KEYCLOAK_CONTAINER, KC_SERVER,
# KC_SERVER_INTERNAL, KC_REALM, KC_ADMIN_USER, KC_ADMIN_PASS.

# Keep docker exec path arguments Linux-style under Git Bash on Windows.
docker_exec() {
  if [ -n "${MSYSTEM:-}" ]; then
    MSYS_NO_PATHCONV=1 docker exec "$@"
  else
    docker exec "$@"
  fi
}

kcadm() { docker_exec "$KEYCLOAK_CONTAINER" /opt/keycloak/bin/kcadm.sh "$@"; }

wait_for_keycloak_healthy() {
  local elapsed=0 timeout="${1:-120}" status
  echo "Waiting for $KEYCLOAK_CONTAINER to be healthy (max ${timeout}s)..."
  while [ "$elapsed" -lt "$timeout" ]; do
    status=$(docker inspect --format='{{.State.Health.Status}}' "$KEYCLOAK_CONTAINER" 2>/dev/null || true)
    if [ "$status" = "healthy" ]; then
      echo "Keycloak is healthy."
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  echo "ERROR: Keycloak did not become healthy within ${timeout}s." >&2
  return 1
}

# Keycloak 26's KC_BOOTSTRAP_ADMIN_* creates a TEMPORARY master admin that
# cannot do a direct-grant (kcadm) login until a one-time VERIFY_PROFILE
# required action is resolved via the browser flow. Complete it here. No-op
# once the admin is already permanent.
complete_admin_bootstrap() {
  local base="$KC_SERVER" cookies headers auth_page action_url redirect1 page verify_action verifier challenge
  cookies="$(mktemp)"; headers="$(mktemp)"
  verifier="$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-43)"
  challenge="$(printf '%s' "$verifier" | openssl dgst -sha256 -binary | openssl base64 | tr '+/' '-_' | tr -d '=')"

  auth_page="$(curl -s -c "$cookies" \
    "$base/realms/master/protocol/openid-connect/auth?client_id=security-admin-console&redirect_uri=$base/admin/master/console/&response_type=code&scope=openid&code_challenge=$challenge&code_challenge_method=S256")"
  action_url="$(printf '%s' "$auth_page" | grep -oE 'action="[^"]*"' | head -1 | sed 's/action="//;s/"$//;s/&amp;/\&/g')"
  [ -n "$action_url" ] || { rm -f "$cookies" "$headers"; return 0; }

  curl -s -b "$cookies" -c "$cookies" -D "$headers" -o /dev/null \
    --data-urlencode "username=$KC_ADMIN_USER" --data-urlencode "password=$KC_ADMIN_PASS" "$action_url"
  redirect1="$(grep -i '^Location:' "$headers" | sed 's/Location: //I' | tr -d '\r')"

  if printf '%s' "$redirect1" | grep -q 'required-action.*VERIFY_PROFILE'; then
    echo "Completing one-time Keycloak admin profile setup (temporary bootstrap admin)..."
    page="$(curl -s -b "$cookies" -c "$cookies" "$redirect1")"
    verify_action="$(printf '%s' "$page" | grep -oE 'action="[^"]*"' | head -1 | sed 's/action="//;s/"$//;s/&amp;/\&/g')"
    if [ -n "$verify_action" ]; then
      curl -s -b "$cookies" -c "$cookies" -o /dev/null \
        --data-urlencode "email=admin@wimsbfp.tech" \
        --data-urlencode "firstName=System" \
        --data-urlencode "lastName=Admin" \
        "$verify_action"
    fi
  fi
  rm -f "$cookies" "$headers"
}

kc_login() {
  complete_admin_bootstrap || true
  kcadm config credentials --server "$KC_SERVER_INTERNAL" --realm master \
    --user "$KC_ADMIN_USER" --password "$KC_ADMIN_PASS"
}
