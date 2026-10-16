"""Thin wrapper: output-only grader + frozen private_expected.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "_lib"))
from verifier.grade import GradeResult, grade_submission as _grade  # noqa: E402

_EXPECTED = json.loads((HERE / "private_expected.json").read_text(encoding="utf-8"))


def grade_submission(output_dir, data_dir, expected=None):
    return _grade(output_dir, data_dir, expected if expected is not None else _EXPECTED)


__all__ = ["GradeResult", "grade_submission"]
