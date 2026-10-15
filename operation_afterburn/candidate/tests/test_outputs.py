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

PLAN_REQUIRED = [
    "sequence",
    "service_id",
    "workload_id",
    "action",
    "precondition",
    "expected_effect",
    "evidence_refs",
]
ACTIONS = {"redeploy", "quarantine", "isolate", "observe", "hold"}


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


def test_response_plan_required_fields():
    """Reject plans that omit service/action/sequence/recovery fields required by the prompt."""
    path = _require_file("response_plan.csv")
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert rows, "empty_plan"
    assert PLAN_REQUIRED == [c for c in PLAN_REQUIRED if c in rows[0].keys()] or set(PLAN_REQUIRED).issubset(rows[0].keys()), "plan_schema"
    exposed = set(EXPECTED["exposed_workload_ids"])
    covered = set()
    for r in rows:
        for col in PLAN_REQUIRED:
            assert str(r.get(col) or "").strip(), f"missing_plan_field:{col}"
        action = str(r.get("action") or "").strip()
        assert action in ACTIONS, f"bad_action:{action}"
        int(str(r.get("sequence")).strip())
        if action == "redeploy":
            assert str(r.get("recovery_digest") or "").strip(), "redeploy_without_recovery_digest"
            assert str(r.get("recovery_digest")).strip() in set(EXPECTED["safe_recovery_digests"]), "unsafe_or_unknown_recovery"
        if action in {"redeploy", "quarantine", "isolate"}:
            covered.add(r.get("workload_id"))
    assert exposed.issubset(covered), "plan_missing_exposed_workloads"


def test_semantic_grade_reference_band():
    _require_file("exposure_register.csv")
    _require_file("response_plan.csv")
    _require_file("incident_decision.md")
    tmp = HERE / "_expected_runtime.json"
    tmp.write_text(json.dumps(EXPECTED), encoding="utf-8")
    assert DATA.exists(), "missing_data_packet"
    result = grade_lib.grade_submission(OUT, tmp, DATA)
    assert result.reward >= 85.0, f"reward_below_band:{result.reward}"
    # Incomplete plans must not reach the pass band.
    assert result.checks.get("plan_completeness", {}).get("ok") is True, "plan_incomplete"


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
    assert "assumption" in text, "memo_missing_assumptions"
    assert "http://" not in text and "https://" not in text, "memo_has_urls"
