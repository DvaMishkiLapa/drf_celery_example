#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
STATE_ROOT="${STATE_ROOT:-$PROJECT_ROOT/@state_dir@}"
REDIS_DATA="$STATE_ROOT/redis"
mkdir -p "$REDIS_DATA"

exec redis-server \
  --dir "$REDIS_DATA" \
  --bind 127.0.0.1 \
  --port @redis_port@ \
  --save "" \
  --appendonly no
