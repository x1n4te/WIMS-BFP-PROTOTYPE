#!/bin/sh
# CLIENT ONLY. Runs once, on first boot of an empty data volume, after every *.sql file
# (the zz_ prefix sorts last). The shared SQL files create the keycloak and wims_app_user
# roles with fixed development passwords; replace them with the generated ones from .env.
set -eu
: "${KC_DB_PASSWORD:?KC_DB_PASSWORD is required}"
: "${WIMS_APP_DB_PASSWORD:?WIMS_APP_DB_PASSWORD is required}"
# Generated passwords are alphanumeric only (setup-secrets.ps1), so plain quoting is safe.
case "$KC_DB_PASSWORD$WIMS_APP_DB_PASSWORD" in
  *[!A-Za-z0-9]*) echo "passwords must be alphanumeric" >&2; exit 1 ;;
esac
psql -v ON_ERROR_STOP=1 -U postgres -d wims <<SQL
ALTER ROLE keycloak PASSWORD '${KC_DB_PASSWORD}';
ALTER ROLE wims_app_user PASSWORD '${WIMS_APP_DB_PASSWORD}';
SQL
echo "client init: database role passwords set"
