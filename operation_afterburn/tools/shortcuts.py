"""Cheap shortcut solvers for tournament measurement."""
from __future__ import annotations

import csv
import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _read_csv(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_outputs(out: Path, register: list[dict], plan: list[dict], memo: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    fields = [
        "workload_id",
        "environment",
        "region",
        "observed_digest",
        "disposition",
        "exposure_path",
        "evidence_refs",
        "uncertainty_or_clearance",
    ]
    with (out / "exposure_register.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in register:
            w.writerow(r)
    pfields = [
        "sequence",
        "service_id",
        "workload_id",
        "action",
        "recovery_digest",
        "precondition",
        "expected_effect",
        "evidence_refs",
    ]
    with (out / "response_plan.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pfields)
        w.writeheader()
        for i, r in enumerate(plan, 1):
            row = dict(r)
            row.setdefault("sequence", str(i))
            w.writerow(row)
    (out / "incident_decision.md").write_text(memo, encoding="utf-8")


def _base_memo(title: str) -> str:
    return f"""# Incident decision — build runner compromise

## Immediate recommendation
{title}

## Material production exposure
Shortcut analysis.

## Cleared lookalikes and unresolved findings
Shortcut analysis.

## Recovery sequence and availability safeguards
See plan.

## Evidence basis and limitations
Offline packet only; no live changes.
"""


def _inv(data: Path):
    return _read_csv(data / "runtime" / "workload_inventory.csv.gz")


def _runtime(data: Path):
    return _read_jsonl(data / "runtime" / "pod_runtime_observations.jsonl.gz")


def _ci(data: Path):
    return _read_jsonl(data / "build" / "ci_job_events.jsonl.gz")


def _att(data: Path):
    return _read_jsonl(data / "build" / "attestations.jsonl.gz")


def _tags(data: Path):
    return _read_jsonl(data / "registry" / "tag_mutations.jsonl.gz")


def _oci(data: Path):
    return _read_jsonl(data / "registry" / "oci_descriptors.jsonl.gz")


def _rollbacks(data: Path):
    return _read_jsonl(data / "operations" / "rollback_artifacts.jsonl.gz")


def _notice_pool(data: Path) -> str:
    text = (data / "incident_notice.md").read_text(encoding="utf-8")
    m = re.search(r"pool `([^`]+)`", text)
    return m.group(1) if m else "helix-ci-prod"


def shortcut_all_signed_clean(data: Path, out: Path) -> None:
    # clear everything with VALID attestation subject matching runtime
    att = _att(data)
    valid_subjects = set()
    for row in att:
        if row.get("authentication", {}).get("status") == "VALID":
            for sub in row.get("envelope", {}).get("subject", []):
                d = sub.get("digest", {}).get("sha256")
                if d:
                    valid_subjects.add("sha256:" + d)
    reg = []
    for r in _runtime(data):
        if r.get("status") != "Running":
            continue
        wid = r["workload_id"]
        inv = {x["workload_id"]: x for x in _inv(data)}
        if wid not in inv:
            continue
        dig = r.get("image_id")
        disp = "CLEARED" if dig in valid_subjects else "EXPOSED"
        reg.append(
            {
                "workload_id": wid,
                "environment": inv[wid]["environment"],
                "region": inv[wid]["region"],
                "observed_digest": dig,
                "disposition": disp,
                "exposure_path": "signature_shortcut",
                "evidence_refs": r["record_id"],
                "uncertainty_or_clearance": "valid signature assumed clean",
            }
        )
    plan = []
    for i, r in enumerate([x for x in reg if x["disposition"] == "EXPOSED"], 1):
        plan.append(
            {
                "sequence": str(i),
                "service_id": "unknown",
                "workload_id": r["workload_id"],
                "action": "quarantine",
                "recovery_digest": "",
                "precondition": "none",
                "expected_effect": "stop",
                "evidence_refs": r["evidence_refs"],
            }
        )
    _write_outputs(out, reg, plan, _base_memo("Shortcut: all signed clean"))


def shortcut_all_runner_builds_tainted(data: Path, out: Path) -> None:
    pool = _notice_pool(data)
    tainted_out = {r["output_digest"] for r in _ci(data) if r.get("runner_pool") == pool}
    inv = {x["workload_id"]: x for x in _inv(data)}
    reg = []
    for r in _runtime(data):
        wid = r.get("workload_id")
        if wid not in inv or r.get("status") != "Running":
            continue
        dig = r.get("image_id")
        # also mark if any build from pool for that service exists — over-contain
        svc = inv[wid]["service_id"]
        svc_tainted_build = any(c.get("service") == svc and c.get("runner_pool") == pool for c in _ci(data))
        disp = "EXPOSED" if (dig in tainted_out or svc_tainted_build) else "CLEARED"
        reg.append(
            {
                "workload_id": wid,
                "environment": inv[wid]["environment"],
                "region": inv[wid]["region"],
                "observed_digest": dig,
                "disposition": disp,
                "exposure_path": "runner_build_shortcut",
                "evidence_refs": r["record_id"],
                "uncertainty_or_clearance": "any pool build => exposed",
            }
        )
    plan = [
        {
            "sequence": str(i),
            "service_id": inv[r["workload_id"]]["service_id"],
            "workload_id": r["workload_id"],
            "action": "isolate",
            "recovery_digest": "",
            "precondition": "none",
            "expected_effect": "stop",
            "evidence_refs": r["evidence_refs"],
        }
        for i, r in enumerate([x for x in reg if x["disposition"] == "EXPOSED"], 1)
    ]
    _write_outputs(out, reg, plan, _base_memo("Shortcut: all runner builds tainted"))


def shortcut_tag_equals_digest(data: Path, out: Path) -> None:
    tags = {}
    for row in sorted(_tags(data), key=lambda r: r.get("time") or ""):
        if row.get("tag") == "stable":
            tags[row["repository"]] = row["digest"]
    # map index to first manifest
    index_map = {}
    for row in _oci(data):
        if row.get("descriptor_type") == "index":
            mans = row.get("manifests") or []
            if mans:
                index_map[row["index_digest"]] = mans[0]["manifest_digest"]
    inv = {x["workload_id"]: x for x in _inv(data)}
    reg = []
    for wid, meta in inv.items():
        if meta["environment"] != "production":
            continue
        tag_d = tags.get(meta["service_id"])
        obs = index_map.get(tag_d, tag_d) if tag_d else ""
        # compare to runtime
        runs = [r for r in _runtime(data) if r.get("workload_id") == wid and r.get("status") == "Running"]
        actual = runs[-1]["image_id"] if runs else ""
        # shortcut trusts tag
        disp = "CLEARED"  # assumes tag points to whatever is "current" and treats as authority
        if tag_d and actual and index_map.get(tag_d, tag_d) != actual:
            # still cleared because tag says clean current
            disp = "CLEARED"
        elif actual:
            disp = "EXPOSED" if False else "CLEARED"
        reg.append(
            {
                "workload_id": wid,
                "environment": meta["environment"],
                "region": meta["region"],
                "observed_digest": obs or actual,
                "disposition": disp,
                "exposure_path": "tag_authority",
                "evidence_refs": "REG-TAG",
                "uncertainty_or_clearance": "tag used as digest",
            }
        )
    # Force payments cleared wrongly if present
    _write_outputs(out, reg, [], _base_memo("Shortcut: tag equals digest"))


def shortcut_index_equals_manifest(data: Path, out: Path) -> None:
    # Treat all platforms under an index as same disposition based on amd64 only
    index_amd = {}
    for row in _oci(data):
        if row.get("descriptor_type") == "index":
            for m in row.get("manifests", []):
                if m["platform"] == "linux/amd64":
                    index_amd[row["index_digest"]] = m["manifest_digest"]
    man_to_index = {}
    for row in _oci(data):
        if row.get("descriptor_type") == "manifest":
            man_to_index[row["manifest_digest"]] = row.get("index_digest")
    pool = _notice_pool(data)
    tainted = {r["output_digest"] for r in _ci(data) if r.get("runner_pool") == pool}
    inv = {x["workload_id"]: x for x in _inv(data)}
    reg = []
    for r in _runtime(data):
        wid = r.get("workload_id")
        if wid not in inv or r.get("status") != "Running":
            continue
        img = r.get("image_id")
        idx = man_to_index.get(img)
        amd = index_amd.get(idx, img)
        # use amd taint for all platforms
        layers = []
        for row in _oci(data):
            if row.get("manifest_digest") == amd:
                layers = row.get("layers") or []
        disp = "EXPOSED" if amd in tainted or any(L in tainted for L in layers) else "CLEARED"
        # This wrongly clears arm tainted when amd clean
        reg.append(
            {
                "workload_id": wid,
                "environment": inv[wid]["environment"],
                "region": inv[wid]["region"],
                "observed_digest": img,
                "disposition": disp if inv[wid]["environment"] == "production" else "CLEARED",
                "exposure_path": "index_as_manifest",
                "evidence_refs": r["record_id"],
                "uncertainty_or_clearance": "amd64 governs index",
            }
        )
    plan = [
        {
            "sequence": str(i),
            "service_id": inv[r["workload_id"]]["service_id"],
            "workload_id": r["workload_id"],
            "action": "quarantine",
            "recovery_digest": "",
            "precondition": "none",
            "expected_effect": "stop",
            "evidence_refs": r["evidence_refs"],
        }
        for i, r in enumerate([x for x in reg if x["disposition"] == "EXPOSED"], 1)
    ]
    _write_outputs(out, reg, plan, _base_memo("Shortcut: index equals manifest"))


def shortcut_ignore_base_layers(data: Path, out: Path) -> None:
    pool = _notice_pool(data)
    direct = {r["output_digest"] for r in _ci(data) if r.get("runner_pool") == pool}
    inv = {x["workload_id"]: x for x in _inv(data)}
    reg = []
    for r in _runtime(data):
        wid = r.get("workload_id")
        if wid not in inv or r.get("status") != "Running":
            continue
        dig = r.get("image_id")
        disp = "EXPOSED" if dig in direct and inv[wid]["environment"] == "production" else "CLEARED"
        reg.append(
            {
                "workload_id": wid,
                "environment": inv[wid]["environment"],
                "region": inv[wid]["region"],
                "observed_digest": dig,
                "disposition": disp,
                "exposure_path": "direct_only",
                "evidence_refs": r["record_id"],
                "uncertainty_or_clearance": "ignored layers",
            }
        )
    plan = [
        {
            "sequence": str(i),
            "service_id": inv[r["workload_id"]]["service_id"],
            "workload_id": r["workload_id"],
            "action": "redeploy",
            "recovery_digest": "",
            "precondition": "none",
            "expected_effect": "fix",
            "evidence_refs": r["evidence_refs"],
        }
        for i, r in enumerate([x for x in reg if x["disposition"] == "EXPOSED"], 1)
    ]
    _write_outputs(out, reg, plan, _base_memo("Shortcut: ignore base layers"))


def shortcut_desired_equals_running(data: Path, out: Path) -> None:
    rolls = {r["workload_id"]: r for r in _read_jsonl(data / "runtime" / "rollout_history.jsonl.gz")}
    pool = _notice_pool(data)
    tainted = {r["output_digest"] for r in _ci(data) if r.get("runner_pool") == pool}
    # expand layers lightly
    for row in _oci(data):
        if row.get("descriptor_type") == "manifest" and any(L in tainted for L in row.get("layers") or []):
            tainted.add(row["manifest_digest"])
    inv = {x["workload_id"]: x for x in _inv(data)}
    reg = []
    for wid, meta in inv.items():
        desired = rolls.get(wid, {}).get("desired_digest")
        disp = "EXPOSED" if desired in tainted and meta["environment"] == "production" else "CLEARED"
        reg.append(
            {
                "workload_id": wid,
                "environment": meta["environment"],
                "region": meta["region"],
                "observed_digest": desired or "",
                "disposition": disp,
                "exposure_path": "desired_state",
                "evidence_refs": rolls.get(wid, {}).get("record_id", "ROL"),
                "uncertainty_or_clearance": "desired used as running",
            }
        )
    plan = [
        {
            "sequence": str(i),
            "service_id": inv[r["workload_id"]]["service_id"],
            "workload_id": r["workload_id"],
            "action": "quarantine",
            "recovery_digest": "",
            "precondition": "none",
            "expected_effect": "stop",
            "evidence_refs": r["evidence_refs"],
        }
        for i, r in enumerate([x for x in reg if x["disposition"] == "EXPOSED"], 1)
    ]
    _write_outputs(out, reg, plan, _base_memo("Shortcut: desired equals running"))


def shortcut_latest_log_live(data: Path, out: Path) -> None:
    # ignore event_time; use recorded_time / time latest Running
    inv = {x["workload_id"]: x for x in _inv(data)}
    pool = _notice_pool(data)
    tainted = {r["output_digest"] for r in _ci(data) if r.get("runner_pool") == pool}
    for row in _oci(data):
        if row.get("descriptor_type") == "manifest" and any(L in tainted for L in row.get("layers") or []):
            tainted.add(row["manifest_digest"])
    latest = {}
    for r in sorted(_runtime(data), key=lambda x: x.get("recorded_time") or x.get("time") or ""):
        latest[r["workload_id"]] = r
    reg = []
    for wid, r in latest.items():
        if wid not in inv:
            continue
        dig = r.get("image_id")
        running = r.get("status") == "Running"
        disp = "EXPOSED" if running and dig in tainted and inv[wid]["environment"] == "production" else "CLEARED"
        reg.append(
            {
                "workload_id": wid,
                "environment": inv[wid]["environment"],
                "region": inv[wid]["region"],
                "observed_digest": dig,
                "disposition": disp,
                "exposure_path": "latest_log",
                "evidence_refs": r["record_id"],
                "uncertainty_or_clearance": "recorded_time authority",
            }
        )
    plan = [
        {
            "sequence": str(i),
            "service_id": inv[r["workload_id"]]["service_id"],
            "workload_id": r["workload_id"],
            "action": "isolate",
            "recovery_digest": "",
            "precondition": "none",
            "expected_effect": "stop",
            "evidence_refs": r["evidence_refs"],
        }
        for i, r in enumerate([x for x in reg if x["disposition"] == "EXPOSED"], 1)
    ]
    _write_outputs(out, reg, plan, _base_memo("Shortcut: latest log is live"))


def shortcut_previous_green(data: Path, out: Path) -> None:
    # Mark running tainted roughly via pool outputs+layers, then rollback to previous-green label always
    from solver.evidence_solver import solve

    tmp = out.parent / "_tmp_ref_for_prevgreen"
    solve(data, tmp)
    reg = list(csv.DictReader((tmp / "exposure_register.csv").open()))
    # corrupt plan
    plan = []
    rbs = _rollbacks(data)
    for i, r in enumerate([x for x in reg if x["disposition"] == "EXPOSED"], 1):
        inv = {x["workload_id"]: x for x in _inv(data)}
        svc = inv[r["workload_id"]]["service_id"]
        prev = next((x for x in rbs if x["service_id"] == svc and x.get("label") == "previous-green"), None)
        if not prev:
            prev = next((x for x in rbs if x["service_id"] == svc), None)
        plan.append(
            {
                "sequence": str(i),
                "service_id": svc,
                "workload_id": r["workload_id"],
                "action": "redeploy",
                "recovery_digest": (prev or {}).get("digest", ""),
                "precondition": "none",
                "expected_effect": "rollback",
                "evidence_refs": r["evidence_refs"],
            }
        )
    _write_outputs(out, reg, plan, _base_memo("Shortcut: previous green rollback"))


def shortcut_stop_all(data: Path, out: Path) -> None:
    from solver.evidence_solver import solve

    tmp = out.parent / "_tmp_ref_for_stopall"
    solve(data, tmp)
    reg = list(csv.DictReader((tmp / "exposure_register.csv").open()))
    inv = {x["workload_id"]: x for x in _inv(data)}
    plan = []
    for i, r in enumerate([x for x in reg if x["disposition"] == "EXPOSED"], 1):
        plan.append(
            {
                "sequence": "1",  # same sequence — simultaneous
                "service_id": inv[r["workload_id"]]["service_id"],
                "workload_id": r["workload_id"],
                "action": "isolate",
                "recovery_digest": "",
                "precondition": "none",
                "expected_effect": "stop_all",
                "evidence_refs": r["evidence_refs"],
            }
        )
    _write_outputs(out, reg, plan, _base_memo("Shortcut: stop all immediately"))


def shortcut_ignore_quorum(data: Path, out: Path) -> None:
    shortcut_stop_all(data, out)


def shortcut_ignore_approvals(data: Path, out: Path) -> None:
    from solver.evidence_solver import solve

    tmp = out.parent / "_tmp_ref_for_approvals"
    solve(data, tmp)
    reg = list(csv.DictReader((tmp / "exposure_register.csv").open()))
    inv = {x["workload_id"]: x for x in _inv(data)}
    rbs = _rollbacks(data)
    plan = []
    for i, r in enumerate([x for x in reg if x["disposition"] == "EXPOSED"], 1):
        svc = inv[r["workload_id"]]["service_id"]
        rb = next((x for x in rbs if x["service_id"] == svc), None)
        plan.append(
            {
                "sequence": str(i),
                "service_id": svc,
                "workload_id": r["workload_id"],
                "action": "redeploy",
                "recovery_digest": (rb or {}).get("digest", ""),
                "precondition": "ignored_approvals",
                "expected_effect": "redeploy",
                "evidence_refs": r["evidence_refs"],
            }
        )
    _write_outputs(out, reg, plan, _base_memo("Shortcut: ignore approvals"))


def shortcut_ignore_timing(data: Path, out: Path) -> None:
    # treat all Running records including after cutoff recorded_time
    shortcut_latest_log_live(data, out)


def shortcut_ignore_runtime_family(data: Path, out: Path) -> None:
    # use only CI: any service with compromised pool build is exposed
    pool = _notice_pool(data)
    bad_services = {r["service"] for r in _ci(data) if r.get("runner_pool") == pool}
    inv = _inv(data)
    reg = []
    for meta in inv:
        disp = "EXPOSED" if meta["service_id"] in bad_services and meta["environment"] == "production" else "CLEARED"
        reg.append(
            {
                "workload_id": meta["workload_id"],
                "environment": meta["environment"],
                "region": meta["region"],
                "observed_digest": "",
                "disposition": disp,
                "exposure_path": "ci_only",
                "evidence_refs": "CI",
                "uncertainty_or_clearance": "ignored runtime",
            }
        )
    plan = [
        {
            "sequence": str(i),
            "service_id": r["workload_id"],
            "workload_id": r["workload_id"],
            "action": "isolate",
            "recovery_digest": "",
            "precondition": "none",
            "expected_effect": "stop",
            "evidence_refs": "CI",
        }
        for i, r in enumerate([x for x in reg if x["disposition"] == "EXPOSED"], 1)
    ]
    _write_outputs(out, reg, plan, _base_memo("Shortcut: ignore runtime family"))


def shortcut_namespace_prod(data: Path, out: Path) -> None:
    from solver.evidence_solver import solve

    tmp = out.parent / "_tmp_ref_for_ns"
    solve(data, tmp)
    reg = list(csv.DictReader((tmp / "exposure_register.csv").open()))
    inv = {x["workload_id"]: x for x in _inv(data)}
    # flip staging with 'prod' in namespace to EXPOSED
    for r in reg:
        ns = inv.get(r["workload_id"], {}).get("namespace", "")
        if "prod" in ns and r["disposition"] == "CLEARED":
            r["disposition"] = "EXPOSED"
            r["exposure_path"] = "namespace_string"
    plan = [
        {
            "sequence": str(i),
            "service_id": inv[r["workload_id"]]["service_id"],
            "workload_id": r["workload_id"],
            "action": "isolate",
            "recovery_digest": "",
            "precondition": "none",
            "expected_effect": "stop",
            "evidence_refs": r["evidence_refs"],
        }
        for i, r in enumerate([x for x in reg if x["disposition"] == "EXPOSED"], 1)
    ]
    _write_outputs(out, reg, plan, _base_memo("Shortcut: namespace string prod"))


def shortcut_assume_admission_success(data: Path, out: Path) -> None:
    from solver.evidence_solver import solve

    tmp = out.parent / "_tmp_ref_for_adm"
    solve(data, tmp)
    reg = list(csv.DictReader((tmp / "exposure_register.csv").open()))
    for r in reg:
        if r["disposition"] == "UNRESOLVED":
            r["disposition"] = "EXPOSED"
            r["uncertainty_or_clearance"] = "assumed running"
    inv = {x["workload_id"]: x for x in _inv(data)}
    plan = [
        {
            "sequence": str(i),
            "service_id": inv[r["workload_id"]]["service_id"],
            "workload_id": r["workload_id"],
            "action": "isolate",
            "recovery_digest": "",
            "precondition": "none",
            "expected_effect": "stop",
            "evidence_refs": r["evidence_refs"],
        }
        for i, r in enumerate([x for x in reg if x["disposition"] == "EXPOSED"], 1)
    ]
    _write_outputs(out, reg, plan, _base_memo("Shortcut: assume admission success"))


SHORTCUTS: dict[str, Callable[[Path, Path], None]] = {
    "all_signed_clean": shortcut_all_signed_clean,
    "all_runner_builds_tainted": shortcut_all_runner_builds_tainted,
    "tag_equals_digest": shortcut_tag_equals_digest,
    "index_equals_manifest": shortcut_index_equals_manifest,
    "ignore_base_layers": shortcut_ignore_base_layers,
    "desired_equals_running": shortcut_desired_equals_running,
    "latest_log_is_live": shortcut_latest_log_live,
    "previous_green_rollback": shortcut_previous_green,
    "stop_all_immediately": shortcut_stop_all,
    "ignore_quorum": shortcut_ignore_quorum,
    "ignore_approvals": shortcut_ignore_approvals,
    "ignore_timing": shortcut_ignore_timing,
    "ignore_runtime_family": shortcut_ignore_runtime_family,
    "namespace_string_prod": shortcut_namespace_prod,
    "assume_admission_success": shortcut_assume_admission_success,
}
