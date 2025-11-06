#!/usr/bin/env bash

set -euo pipefail

echo "Running FastAPI health check"
curl --fail --silent --show-error "${API_BASE_URL:-http://localhost:8000}/health" || {
  echo "Health check failed" >&2
  exit 1
}
