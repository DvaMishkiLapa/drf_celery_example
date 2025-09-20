#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC1091
source "@common@"

PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
STATE_ROOT="${STATE_ROOT:-$PROJECT_ROOT/@state_dir@}"

mode="${1:-}"; shift || true

usage() {
  local code=${1:-1}
  cat >&2 <<'USAGE'
Usage:
  runtime stack [process-compose args...]
  runtime init-db [env-file]
USAGE
  exit "$code"
}

if [ -z "$mode" ]; then
  usage 1
fi

export PC_CONFIG_FILES="@process_compose_config@"

case "$mode" in
  stack)
    if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
      usage 0
    fi

    ENV_FILE="$PROJECT_ROOT/env.list"
    if [ ! -f "$ENV_FILE" ]; then
      echo "env.list not found at $ENV_FILE" >&2
      exit 1
    fi

    load_env_file "$ENV_FILE"
    normalize_local_hosts

    if [ -z "${NIX_DAPHNE_PORT:-}" ]; then
      export NIX_DAPHNE_PORT="@web_port_default@"
    fi

    export PROJECT_ROOT
    export STATE_ROOT
    mkdir -p "$STATE_ROOT"

    if [ -n "${CELERY_BEAT_SCHEDULE_FILENAME:-}" ]; then
      if [[ "$CELERY_BEAT_SCHEDULE_FILENAME" == /data/* ]]; then
        CELERY_BEAT_SCHEDULE_FILENAME="$STATE_ROOT/${CELERY_BEAT_SCHEDULE_FILENAME#/data/}"
      fi
      mkdir -p "$(dirname "$CELERY_BEAT_SCHEDULE_FILENAME")"
      export CELERY_BEAT_SCHEDULE_FILENAME
    fi

    ensure_python_env

    export PYTHONPATH="$PROJECT_ROOT/app:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

    export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-app.settings}"

    export PC_ENV_FILES="$ENV_FILE"

    if [ "${1:-}" = "down" ]; then
      shift || true
      unset PC_ENV_FILES
      exec process-compose down "$@"
    fi

    exec process-compose "$@"
    ;;

  init-db)
    if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
      usage 0
    fi

    ENV_FILE="${1:-$PROJECT_ROOT/env.list}"
    if [ "$#" -gt 0 ]; then
      shift
    fi

    if [ ! -f "$ENV_FILE" ]; then
      echo "env file not found: $ENV_FILE" >&2
      exit 1
    fi

    load_env_file "$ENV_FILE"
    normalize_local_hosts

    if [ -z "${NIX_DAPHNE_PORT:-}" ]; then
      export NIX_DAPHNE_PORT="@web_port_default@"
    fi

    export PROJECT_ROOT
    export STATE_ROOT
    mkdir -p "$STATE_ROOT"

    if [ -n "${CELERY_BEAT_SCHEDULE_FILENAME:-}" ]; then
      if [[ "$CELERY_BEAT_SCHEDULE_FILENAME" == /data/* ]]; then
        CELERY_BEAT_SCHEDULE_FILENAME="$STATE_ROOT/${CELERY_BEAT_SCHEDULE_FILENAME#/data/}"
      fi
      mkdir -p "$(dirname "$CELERY_BEAT_SCHEDULE_FILENAME")"
      export CELERY_BEAT_SCHEDULE_FILENAME
    fi

    ensure_python_env

    export PYTHONPATH="$PROJECT_ROOT/app:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

    echo "[init-db] Waiting for PostgreSQL to become ready on port @postgres_port@"
    until pg_isready -h 127.0.0.1 -p @postgres_port@ >/dev/null 2>&1; do
      sleep 1
    done

    export PGPASSWORD="$POSTGRES_PASSWORD"
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

    echo "[init-db] Running Django migrations"
    python app/manage.py migrate "$@"
    ;;

  *)
    usage 1
    ;;

esac
