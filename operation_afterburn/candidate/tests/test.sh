#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
write_zero() {
  mkdir -p /logs/verifier /logs 2>/dev/null || true
  printf '0\n' > /logs/verifier/reward.txt 2>/dev/null || true
  printf '0\n' > /logs/reward.txt 2>/dev/null || true
}
write_zero
set +e
python3 "$ROOT/run_tests.py"
rc=$?
# If runner somehow failed before writing, keep the zero reward.
if [[ ! -f /logs/verifier/reward.txt && ! -f /logs/reward.txt ]]; then
  write_zero
fi
exit 0
