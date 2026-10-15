#!/usr/bin/env bash
# Harbor verifier entrypoint: must always write /logs/verifier/reward.txt (and numeric reward.json).
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"

mkdir -p /logs/verifier 2>/dev/null || true
# Pre-seed a valid zero reward in case python fails to start.
printf '0\n' > /logs/verifier/reward.txt 2>/dev/null || true
printf '{"reward":0}\n' > /logs/verifier/reward.json 2>/dev/null || true

set +e
python3 "$ROOT/run_tests.py"
set +e

# Guarantee files exist and are Harbor-parseable.
if [[ ! -s /logs/verifier/reward.txt ]]; then
  printf '0\n' > /logs/verifier/reward.txt
fi
if [[ ! -s /logs/verifier/reward.json ]]; then
  printf '{"reward":0}\n' > /logs/verifier/reward.json
fi
exit 0
