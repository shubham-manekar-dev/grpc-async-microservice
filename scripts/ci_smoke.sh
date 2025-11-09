#!/usr/bin/env bash
set -euo pipefail

APP_MODULE=${APP_MODULE:-backend.app.main:app}
API_HOST=${API_HOST:-127.0.0.1}
API_PORT=${API_PORT:-8000}
API_BASE_URL=${API_BASE_URL:-"http://${API_HOST}:${API_PORT}"}

# Ensure optional integrations don't block the smoke probe
export CARE_PLAN_GRPC_TARGET=${CARE_PLAN_GRPC_TARGET:-disabled}
export DATABASE_URL=${DATABASE_URL:-sqlite:///./ci-smoke.db}
export KAFKA_ENABLED=${KAFKA_ENABLED:-false}
export REDIS_URL=${REDIS_URL:-memory://}
export MONGO_URL=${MONGO_URL:-memory://}
export GEN_AI_PROVIDER=${GEN_AI_PROVIDER:-heuristic}

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT

python -m uvicorn "$APP_MODULE" --host "$API_HOST" --port "$API_PORT" --log-level warning &
SERVER_PID=$!

# Give the server a moment to start
health_url="${API_BASE_URL%/}/health"

for attempt in $(seq 1 30); do
  if curl --fail --silent "$health_url" >/dev/null 2>&1; then
    break
  fi
  sleep 1
  if [[ $attempt -eq 30 ]]; then
    echo "Service did not become healthy in time" >&2
    exit 1
  fi
done

echo "FastAPI health endpoint responded successfully"
