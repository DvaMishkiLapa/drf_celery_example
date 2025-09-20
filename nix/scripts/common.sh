#!/usr/bin/env bash
set -euo pipefail

ensure_python_env() {
  local project_root="${PROJECT_ROOT:?PROJECT_ROOT must be set before ensure_python_env}"
  local state_root="${STATE_ROOT:?STATE_ROOT must be set before ensure_python_env}"
  local venv_dir="$state_root/.venv"
  local requirements_file="$project_root/requirements.txt"

  if [ ! -f "$requirements_file" ]; then
    echo "[python] requirements.txt not found at $requirements_file" >&2
    exit 1
  fi

  mkdir -p "$state_root"

  echo "[python] Installing dependencies into $venv_dir via uv"
  uv venv "$venv_dir" >/dev/null 2>&1
  uv pip install --python "$venv_dir/bin/python" --requirement "$requirements_file"

  export UV_PROJECT_ENVIRONMENT="$venv_dir"
  export PATH="$venv_dir/bin:$PATH"
}

load_env_file() {
  local file="$1"
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ""|\#*) continue ;;
    esac
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      local key="${BASH_REMATCH[1]}"
      local value="${BASH_REMATCH[2]}"
      value="${value%$'\r'}"
      value="${value%\"}"
      value="${value#\"}"
      export "$key"="$value"
    fi
  done < "$file"
}

normalize_local_hosts() {
  if [ "${POSTGRES_HOST:-}" = "postgres" ]; then
    POSTGRES_HOST=127.0.0.1
  fi
  POSTGRES_PORT="${POSTGRES_PORT:-5432}"
  export POSTGRES_HOST
  export POSTGRES_PORT
  export PGHOST="${PGHOST:-$POSTGRES_HOST}"
  export PGPORT="${PGPORT:-$POSTGRES_PORT}"

  if [ "${REDIS_HOST:-}" = "redis" ]; then
    REDIS_HOST=127.0.0.1
  fi
  export REDIS_HOST

  _rewrite_redis_url() {
    local var_name="$1"
    local value="${!var_name:-}"
    if [[ -z "$value" ]]; then
      return
    fi
    if [[ "$value" == redis://redis* ]]; then
      local suffix="${value#redis://redis}"
      if [[ "$suffix" == :* ]]; then
        export "$var_name"="redis://127.0.0.1${suffix}"
      else
        export "$var_name"="redis://127.0.0.1$suffix"
      fi
    fi
  }

  _rewrite_redis_url CELERY_BROKER_URL
  _rewrite_redis_url CELERY_RESULT_BACKEND
  _rewrite_redis_url CACHE_URL
}
