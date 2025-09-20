#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "@common@"

PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
STATE_ROOT="${STATE_ROOT:-$PROJECT_ROOT/@state_dir@}"

ENV_FILE="${1:-$PROJECT_ROOT/env.list}"
if [ -f "$ENV_FILE" ]; then
  load_env_file "$ENV_FILE"
fi
normalize_local_hosts

export PROJECT_ROOT
export STATE_ROOT
mkdir -p "$STATE_ROOT"

ensure_python_env

export PYTHONPATH="$PROJECT_ROOT/app:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

echo "[migrate] Waiting for PostgreSQL to become ready on port @postgres_port@"
until pg_isready -h 127.0.0.1 -p @postgres_port@ >/dev/null 2>&1; do
  sleep 1
done

if [ -n "${POSTGRES_PASSWORD:-}" ]; then
  export PGPASSWORD="$POSTGRES_PASSWORD"
fi

if ! psql \
  --host=127.0.0.1 \
  --port=@postgres_port@ \
  --username="$POSTGRES_USER" \
  --dbname=postgres \
  --tuples-only \
  --no-align \
  --command "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'" | grep -q 1; then
  createdb \
    --host=127.0.0.1 \
    --port=@postgres_port@ \
    --username="$POSTGRES_USER" \
    --owner="$POSTGRES_USER" \
    "$POSTGRES_DB"
fi

python app/manage.py migrate
