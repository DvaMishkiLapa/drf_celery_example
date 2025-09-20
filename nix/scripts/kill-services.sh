#!/usr/bin/env bash
set -euo pipefail

processes_soft=(
  "daphne"
  "redis-server"
  "postgres-server"
  "app-server"
  "worker-server"
  "beat-server"
)

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

if pgrep -x "process-compose" > /dev/null 2>&1; then
  echo -e "${RED}Killing process-compose (SIGKILL)...${NC}"
  killall -9 process-compose || true
  echo -e "${GREEN}✔ process-compose stopped${NC}"
else
  echo -e "${GREEN}✔ process-compose not running${NC}"
fi

# Остальные (мягко)
for proc in "${processes_soft[@]}"; do
  if pgrep -x "$proc" > /dev/null 2>&1; then
    echo -e "${RED}Killing $proc...${NC}"
    pkill -x "$proc"
    echo -e "${GREEN}✔ $proc stopped${NC}"
  else
    echo -e "${GREEN}✔ $proc not running${NC}"
  fi
done
