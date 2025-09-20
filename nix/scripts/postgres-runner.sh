#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
STATE_ROOT="${STATE_ROOT:-$PROJECT_ROOT/@state_dir@}"
PGDATA="$STATE_ROOT/postgres"
SOCKET_DIR="$STATE_ROOT/postgres-socket"

mkdir -p "$SOCKET_DIR"

if [ ! -f "$PGDATA/PG_VERSION" ]; then
  rm -rf "$PGDATA"
  mkdir -p "$PGDATA"
  echo "[postgres] Initializing data directory at $PGDATA"
  tmp_pwfile=$(mktemp)
  trap 'rm -f "$tmp_pwfile"' EXIT
  printf '%s\n' "$POSTGRES_PASSWORD" > "$tmp_pwfile"
  initdb \
    --username="$POSTGRES_USER" \
    --pwfile="$tmp_pwfile" \
    --auth-local=scram-sha-256 \
    --auth-host=scram-sha-256 \
    "$PGDATA"
  rm -f "$tmp_pwfile"

  postgres --single -D "$PGDATA" postgres <<EOSQL
CREATE DATABASE "${POSTGRES_DB}";
EOSQL
fi

export PGDATA
exec postgres \
  -D "$PGDATA" \
  -c listen_addresses=127.0.0.1 \
  -c port=@postgres_port@ \
  -c unix_socket_directories="$SOCKET_DIR"
