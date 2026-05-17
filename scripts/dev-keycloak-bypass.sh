#!/bin/bash
# =============================================================================
# dev-keycloak-bypass.sh
# =============================================================================
# Toggle Keycloak direct grant access for wims-web client.
#
# PURPOSE: Enables/disables the dev bypass endpoint (/api/dev-login) which
# relies on Keycloak direct grant (resource owner password credentials).
# The wims-web client must have directAccessGrantsEnabled=true for the bypass
# to obtain tokens with the correct audience (wims-web, matching KEYCLOAK_CLIENT_ID).
#
# WARNING: This is a DEV-ONLY artifact. Never run on production.
# Documented in: system-wiki/gaps/security-gap-register.md — DEV-BYPASS-001 CRITICAL
#
# USAGE:
#   ./dev-keycloak-bypass.sh enable    # Turn on wims-web direct access grants
#   ./dev-keycloak-bypass.sh disable   # Turn off wims-web direct access grants
#   ./dev-keycloak-bypass.sh status    # Show current state
#
# REQUIREMENTS:
#   - Docker Compose must be running (src/ directory)
#   - psql available (inside postgres container)
#   - Keycloak must be reachable
# =============================================================================

set -e

COMPOSE_DIR="$(cd "$(dirname "$0")/../src" && pwd)"
export COMPOSE_DIR

log() { echo "[$(date '+%H:%M:%S')] $1"; }

enable() {
    log "Enabling directAccessGrantsEnabled for wims-web..."
    docker compose -f "$COMPOSE_DIR/docker-compose.yml" exec -T postgres psql -U keycloak -d keycloak -c \
        "UPDATE client SET direct_access_grants_enabled = TRUE WHERE client_id = 'wims-web';" 2>/dev/null
    docker compose -f "$COMPOSE_DIR/docker-compose.yml" restart keycloak 2>/dev/null
    log "Done. Waiting for Keycloak to be ready..."
    sleep 15
    log "wims-web directAccessGrantsEnabled = $(get_status)"
}

disable() {
    log "Disabling directAccessGrantsEnabled for wims-web..."
    docker compose -f "$COMPOSE_DIR/docker-compose.yml" exec -T postgres psql -U keycloak -d keycloak -c \
        "UPDATE client SET direct_access_grants_enabled = FALSE WHERE client_id = 'wims-web';" 2>/dev/null
    docker compose -f "$COMPOSE_DIR/docker-compose.yml" restart keycloak 2>/dev/null
    log "Done. Waiting for Keycloak to be ready..."
    sleep 15
    log "wims-web directAccessGrantsEnabled = $(get_status)"
}

get_status() {
    docker compose -f "$COMPOSE_DIR/docker-compose.yml" exec -T postgres psql -U keycloak -d keycloak -t -c \
        "SELECT direct_access_grants_enabled FROM client WHERE client_id = 'wims-web';" 2>/dev/null | tr -d ' '
}

status() {
    local val=$(get_status)
    if [[ "$val" == "t" ]]; then
        echo "ENABLED — wims-web can use direct grant (password auth)"
    elif [[ "$val" == "f" ]]; then
        echo "DISABLED — wims-web direct grant is off"
    else
        echo "UNKNOWN — could not read state (Keycloak may be down)"
    fi
}

case "${1:-}" in
    enable)  enable ;;
    disable) disable ;;
    status)  status ;;
    *)
        echo "Usage: $0 {enable|disable|status}"
        echo ""
        echo "  enable   — enable wims-web directAccessGrantsEnabled (required for /api/dev-login)"
        echo "  disable  — disable wims-web directAccessGrantsEnabled"
        echo "  status   — show current state"
        exit 1
        ;;
esac