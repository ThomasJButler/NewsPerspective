#!/usr/bin/env bash

set -euo pipefail

readonly REPO_ROOT="/workspace"
readonly FRONTEND_DIR="$REPO_ROOT/src/frontend"
readonly OUTPUT_DIR="$REPO_ROOT/output/playwright"
readonly DATABASE_PATH="$OUTPUT_DIR/docker-news-perspective.db"

mkdir -p "$OUTPUT_DIR"

export DATABASE_URL="sqlite:///$DATABASE_PATH"
export BACKEND_ORIGIN="${BACKEND_ORIGIN:-http://localhost:8000}"

cd "$REPO_ROOT"
rm -f "$DATABASE_PATH"
python3 -m src.backend.scripts.seed_manual_integration_data

uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 &
backend_pid=$!

cleanup() {
  kill "$backend_pid" 2>/dev/null || true
  wait "$backend_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

cd "$FRONTEND_DIR"
exec npm run dev -- --hostname 0.0.0.0 --port 3000
