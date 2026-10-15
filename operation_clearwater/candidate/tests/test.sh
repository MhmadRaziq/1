#!/usr/bin/env bash
set -uo pipefail
export OUTPUT_DIR="${OUTPUT_DIR:-/workspace/output}"
export CLEARWATER_DATA="${CLEARWATER_DATA:-/workspace/data}"
export VERIFIER_LOG_DIR="${VERIFIER_LOG_DIR:-/logs/verifier}"
mkdir -p "$VERIFIER_LOG_DIR"
python3 "$(dirname "$0")/ctrf_runner.py"
