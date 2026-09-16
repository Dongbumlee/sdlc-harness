#!/usr/bin/env bash
set -euo pipefail

URL="${1:?Usage: smoke-test.sh <url>}"
TIMEOUT_SECONDS="${SMOKE_TEST_TIMEOUT_SECONDS:-180}"
SLEEP_SECONDS=10

echo "Running smoke test for: ${URL}/health"
elapsed=0
while [ "$elapsed" -lt "$TIMEOUT_SECONDS" ]; do
  if curl -fsS "${URL}/health" >/dev/null; then
    echo "Smoke test passed."
    exit 0
  fi

  sleep "$SLEEP_SECONDS"
  elapsed=$((elapsed + SLEEP_SECONDS))
done

echo "Smoke test failed after ${TIMEOUT_SECONDS}s."
exit 1
