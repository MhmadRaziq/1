#!/usr/bin/env python3
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "_lib"))
from solver.evidence_solver import solve  # noqa: E402

solve(os.environ.get("DATA_DIR", "/workspace/data"), os.environ.get("OUTPUT_DIR", "/workspace/output"))
