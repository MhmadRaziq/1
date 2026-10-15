#!/usr/bin/env python3
"""Format + semantic tests for Operation AFTERBURN."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import grade_lib

DATA = Path(os.environ.get("AFTERBURN_DATA", "/workspace/data"))
OUT = Path(os.environ.get("AFTERBURN_OUTPUT", "/workspace/output"))
HERE = Path(__file__).resolve().parent
EXPECTED = json.loads((HERE / "private_expected.json").read_text())


def _ensure_outputs():
    if not (OUT / "exposure_register.csv").exists():
        # local/dev fallback
        alt = Path("/workspace/operation_afterburn/work/seed_42_scale/output_solver")
        if alt.exists():
            return alt
    return OUT


def test_three_files_exist():
    out = _ensure_outputs()
    for name in ("exposure_register.csv", "response_plan.csv", "incident_decision.md"):
        p = out / name
        assert p.exists() and p.stat().st_size > 0, name


def test_register_schema_and_vocab():
    out = _ensure_outputs()
    rows = list(csv.DictReader((out / "exposure_register.csv").open()))
    assert rows
    required = {"workload_id", "environment", "region", "observed_digest", "disposition", "exposure_path", "evidence_refs", "uncertainty_or_clearance"}
    assert required.issubset(rows[0].keys())
    assert all(r["disposition"] in {"EXPOSED", "CLEARED", "UNRESOLVED"} for r in rows)


def test_semantic_grade_reference_band():
    out = _ensure_outputs()
    # Write a temp expected path compatible with grade_lib
    tmp = HERE / "_expected_runtime.json"
    tmp.write_text(json.dumps(EXPECTED), encoding="utf-8")
    data = DATA if DATA.exists() else Path("/workspace/operation_afterburn/work/seed_42_scale/data")
    result = grade_lib.grade_submission(out, tmp, data)
    assert result.reward >= 85.0, result.as_dict()


def test_exposure_set_precision_recall():
    out = _ensure_outputs()
    rows = list(csv.DictReader((out / "exposure_register.csv").open()))
    pred = {r["workload_id"] for r in rows if r["disposition"] == "EXPOSED"}
    truth = set(EXPECTED["exposed_workload_ids"])
    assert pred == truth, (sorted(pred), sorted(truth))


def test_no_tainted_recovery():
    out = _ensure_outputs()
    plan = list(csv.DictReader((out / "response_plan.csv").open()))
    unsafe = set(EXPECTED["unsafe_recovery_digests"])
    used = [p.get("recovery_digest") for p in plan if p.get("recovery_digest") in unsafe]
    assert not used, used


def test_unresolved_present():
    out = _ensure_outputs()
    rows = list(csv.DictReader((out / "exposure_register.csv").open()))
    unr = {r["workload_id"] for r in rows if r["disposition"] == "UNRESOLVED"}
    assert set(EXPECTED["unresolved_workload_ids"]).issubset(unr)


def test_memo_sections():
    out = _ensure_outputs()
    text = (out / "incident_decision.md").read_text().lower()
    assert "immediate recommendation" in text
    assert "limitation" in text or "unresolved" in text
    assert "http://" not in text and "https://" not in text
