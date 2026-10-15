"""Thin wrapper importing packaged oracle + verifier grade."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "_lib"))
from verifier.grade import GradeResult, grade_submission  # noqa: F401,E402
