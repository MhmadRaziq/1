#!/usr/bin/env python3
"""Format + semantic tests for Operation AFTERBURN (stdlib asserts only)."""
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


def _require_file(name: str) -> Path:
    path = OUT / name
    assert path.is_file() and path.stat().st_size > 0, f"missing_output:{name}"
    return path


def test_three_files_exist():
    for name in ("exposure_register.csv", "response_plan.csv", "incident_decision.md"):
        _require_file(name)


def test_register_schema_and_vocab():
    path = _require_file("exposure_register.csv")
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert rows, "empty_register"
    required = {
        "workload_id",
        "environment",
        "region",
        "observed_digest",
        "disposition",
        "exposure_path",
        "evidence_refs",
        "uncertainty_or_clearance",
    }
    assert required.issubset(rows[0].keys()), "register_schema"
    assert all(r.get("disposition") in {"EXPOSED", "CLEARED", "UNRESOLVED"} for r in rows), "disposition_vocab"


def test_semantic_grade_reference_band():
    _require_file("exposure_register.csv")
    _require_file("response_plan.csv")
    _require_file("incident_decision.md")
    tmp = HERE / "_expected_runtime.json"
    tmp.write_text(json.dumps(EXPECTED), encoding="utf-8")
    assert DATA.exists(), "missing_data_packet"
    result = grade_lib.grade_submission(OUT, tmp, DATA)
    assert result.reward >= 85.0, f"reward_below_band:{result.reward}"


def test_exposure_set_precision_recall():
    path = _require_file("exposure_register.csv")
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    pred = {r["workload_id"] for r in rows if r.get("disposition") == "EXPOSED"}
    truth = set(EXPECTED["exposed_workload_ids"])
    assert pred == truth, "exposure_set_mismatch"


def test_no_tainted_recovery():
    path = _require_file("response_plan.csv")
    plan = list(csv.DictReader(path.open(encoding="utf-8")))
    unsafe = set(EXPECTED["unsafe_recovery_digests"])
    used = [p.get("recovery_digest") for p in plan if p.get("recovery_digest") in unsafe]
    assert not used, "tainted_recovery_selected"


def test_unresolved_present():
    path = _require_file("exposure_register.csv")
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    unr = {r["workload_id"] for r in rows if r.get("disposition") == "UNRESOLVED"}
    assert set(EXPECTED["unresolved_workload_ids"]).issubset(unr), "unresolved_missing"


def test_memo_sections():
    path = _require_file("incident_decision.md")
    text = path.read_text(encoding="utf-8").lower()
    assert "immediate recommendation" in text, "memo_missing_recommendation"
    assert ("limitation" in text) or ("unresolved" in text), "memo_missing_limits"
    assert "http://" not in text and "https://" not in text, "memo_has_urls"
