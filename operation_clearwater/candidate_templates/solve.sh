#!/usr/bin/env bash
set -euo pipefail
export DATA_DIR="${DATA_DIR:-/workspace/data}"
export OUTPUT_DIR="${OUTPUT_DIR:-/workspace/output}"
mkdir -p "$OUTPUT_DIR"
python3 "$(dirname "$0")/solve.py"
