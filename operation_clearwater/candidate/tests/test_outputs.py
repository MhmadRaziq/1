#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import grade_lib

DATA = Path(os.environ.get("CLEARWATER_DATA", "/workspace/data"))
OUT = Path(os.environ.get("CLEARWATER_OUTPUT", os.environ.get("OUTPUT_DIR", "/workspace/output")))
HERE = Path(__file__).resolve().parent
EXPECTED = json.loads((HERE / "private_expected.json").read_text())


def test_two_files_exist():
    assert (OUT / "recovery_decision.md").exists()
    assert (OUT / "recovery_plan.csv").exists()


def test_plan_schema():
    rows = list(csv.DictReader((OUT / "recovery_plan.csv").open()))
    assert rows
    assert "service" in rows[0] and "candidate_id" in rows[0]


def test_semantic_grade_reference_band():
    result = grade_lib.grade_submission(OUT, DATA)
    assert result.reward >= 85.0, result.as_dict()


def test_no_unsafe_sources():
    result = grade_lib.grade_submission(OUT, DATA)
    assert result.checks.get("no_unsafe_sources"), result.detail.get("unsafe")


def test_within_budget_and_schema():
    result = grade_lib.grade_submission(OUT, DATA)
    assert result.checks.get("within_budget")
    assert result.checks.get("schema_compatible")


def test_citations_resolvable():
    result = grade_lib.grade_submission(OUT, DATA)
    assert result.checks.get("citations_resolvable"), result.detail.get("fabricated")


def test_memo_sections():
    text = (OUT / "recovery_decision.md").read_text().lower()
    assert "recommendation" in text or "recover" in text
    assert "http://" not in text and "https://" not in text
    assert any(k in text for k in ("assumption", "residual", "gap", "risk"))
