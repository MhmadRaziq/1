"""Produce sealed expected outputs from world truth (author-only)."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _evidence_for_workload(world: dict[str, Any], w: dict[str, Any]) -> list[str]:
    refs = []
    # CI / attestation for matching image layers
    for b in world["builds"].values():
        img = world["images"].get(w["image_key"])
        if not img:
            continue
        layers = img["platforms"][w["platform"]]["layers"]
        if b["artifact_digest"] in layers or set(b["layers"]) & set(layers) or b["key"] in (
            w["image_key"],
            w.get("desired_image_key"),
        ):
            refs.extend([b["ci_record"], b["att_record"], b["builder_record"]])
    img = world["images"][w["image_key"]]
    refs.append(img["platforms"][w["platform"]]["oci_record"])
    refs.append(img["index_record"])
    for t in world["tags"]:
        if t["repository"] == w["service_id"]:
            refs.append(t["record"])
    # runtime / admission approximate by synthetic deterministic IDs — solver cites real packet IDs
    return sorted(set(refs))[:8]


def build_oracle(world: dict[str, Any]) -> dict[str, Any]:
    register = []
    for w in sorted(world["workloads"].values(), key=lambda x: x["workload_id"]):
        # Only material review rows: forcing cases + exposed + unresolved + notable cleared lookalikes
        if not (w.get("forcing_case") or w["disposition"] == "EXPOSED"):
            # include a sample of cleared background? Keep focused: forcing + all exposed + unresolved
            continue
        register.append(
            {
                "workload_id": w["workload_id"],
                "environment": w["environment"],
                "region": w["region"],
                "observed_digest": w["running_digest"],
                "disposition": w["disposition"],
                "exposure_path": w.get("exposure_path") or "",
                "evidence_refs": ";".join(_evidence_for_workload(world, w)),
                "uncertainty_or_clearance": {
                    "EXPOSED": "material affected code running in production at cutoff",
                    "CLEARED": w.get("exposure_path") or "lookalike cleared by governing identity/runtime",
                    "UNRESOLVED": "need conclusive runtime observation at cutoff",
                }[w["disposition"]],
            }
        )

    # Ensure F05 cleared promo and F07 shipping and F14 staging included
    for wid in ["wl-promo-useast", "wl-shipping-eu", "wl-storefront-stage", "wl-risk-us-amd", "wl-partner-apsouth"]:
        if wid in world["workloads"] and not any(r["workload_id"] == wid for r in register):
            w = world["workloads"][wid]
            register.append(
                {
                    "workload_id": w["workload_id"],
                    "environment": w["environment"],
                    "region": w["region"],
                    "observed_digest": w["running_digest"],
                    "disposition": w["disposition"],
                    "exposure_path": w.get("exposure_path") or "",
                    "evidence_refs": ";".join(_evidence_for_workload(world, w)),
                    "uncertainty_or_clearance": w.get("exposure_path") or w["disposition"],
                }
            )

    exposed = [r for r in register if r["disposition"] == "EXPOSED"]
    # Build feasible response plan
    plan = []
    seq = 1
    # First: ensure quorum — redeploy checkout before touching multiple edge members
    # payments has post-cutoff redeploy approval — at cutoff only quarantine/hold, not redeploy
    actions = []
    for r in exposed:
        w = world["workloads"][r["workload_id"]]
        svc = w["service_id"]
        safe = next(
            (x for x in world["rollback_artifacts"] if x["service_id"] == svc and not x["tainted"]),
            None,
        )
        approval = next(
            (
                a
                for a in world["approvals"]
                if a["usable_at_cutoff"] and a["service_id"] in (svc, "*") and a["change_type"] == "emergency_redeploy"
            ),
            None,
        )
        if svc == "payments-api" and not approval:
            actions.append(
                {
                    "service_id": svc,
                    "workload_id": w["workload_id"],
                    "action": "quarantine",
                    "recovery_digest": "",
                    "precondition": "standing_containment_approval;edge-checkout_quorum",
                    "expected_effect": "reduce_exposure_without_unauthorized_redeploy",
                    "evidence_refs": r["evidence_refs"],
                    "priority": 2,
                }
            )
        elif safe and approval:
            # risk-scoring: avoid unavailable eu if needed — use us-east
            actions.append(
                {
                    "service_id": svc,
                    "workload_id": w["workload_id"],
                    "action": "redeploy",
                    "recovery_digest": safe["digest"],
                    "precondition": f"approval:{approval['record']};regions:{','.join(safe['available_regions'])}",
                    "expected_effect": "replace_affected_running_digest",
                    "evidence_refs": r["evidence_refs"] + ";" + safe["record"],
                    "priority": 1 if svc == "checkout-bff" else 3,
                }
            )
        else:
            actions.append(
                {
                    "service_id": svc,
                    "workload_id": w["workload_id"],
                    "action": "quarantine",
                    "recovery_digest": "",
                    "precondition": "standing_containment_approval",
                    "expected_effect": "isolate_until_clean_recovery_available",
                    "evidence_refs": r["evidence_refs"],
                    "priority": 3,
                }
            )
    actions.sort(key=lambda a: (a["priority"], a["service_id"]))
    for a in actions:
        plan.append(
            {
                "sequence": str(seq),
                "service_id": a["service_id"],
                "workload_id": a["workload_id"],
                "action": a["action"],
                "recovery_digest": a["recovery_digest"],
                "precondition": a["precondition"],
                "expected_effect": a["expected_effect"],
                "evidence_refs": a["evidence_refs"],
            }
        )
        seq += 1

    # observe unresolved
    for r in register:
        if r["disposition"] == "UNRESOLVED":
            plan.append(
                {
                    "sequence": str(seq),
                    "service_id": world["workloads"][r["workload_id"]]["service_id"],
                    "workload_id": r["workload_id"],
                    "action": "observe",
                    "recovery_digest": "",
                    "precondition": "collect_runtime_observation_at_cutoff",
                    "expected_effect": "resolve_dual_world_ambiguity",
                    "evidence_refs": r["evidence_refs"],
                }
            )
            seq += 1

    memo = f"""# Incident decision — build runner compromise

## Immediate recommendation
Quarantine or redeploy workloads with corroborated production execution of digests reached from the compromised runner path. Preserve edge-checkout quorum (two healthy regions) at every step. Do not treat tag `stable` or valid attestations as clearance. Do not use previous-green rollback digests that still embed affected layers. Hold unauthorized redeploys until approvals are effective.

## Material production exposure
Exposed workloads include those whose platform-specific running digests materially include compromised-runner outputs (direct, base-layer, or vendored), with independent admission and runtime evidence at cutoff. Cross-check OCI platform manifests; amd64 and arm64 under one index are not interchangeable.

## Cleared lookalikes and unresolved findings
Cleared cases include registry-tag drift versus running digest, rejected admissions, stopped workloads with delayed observations, staging namespace lookalikes, and clean platform children of mixed indexes. Unresolved: admission without conclusive runtime observation — collect a cutoff-bounded runtime record before binary disposition.

## Recovery sequence and availability safeguards
Sequence redeploys so edge-checkout members are not simultaneously removed from multiple regions. Prefer last-known-clean digests with verified layer provenance and regional availability. Payments-api redeploy approval is not effective at cutoff; use containment until authority applies.

## Evidence basis and limitations
Findings rely on CI/builder identity, attestations, OCI descriptors, admission, runtime event times, approvals, dependencies, and rollback inventory in the offline packet. Packet does not include host memory forensics; unresolved cases require additional runtime collection.
"""

    safe_digests = {r["digest"] for r in world["rollback_artifacts"] if not r["tainted"]}
    unsafe_digests = {r["digest"] for r in world["rollback_artifacts"] if r["tainted"]}
    tainted_layers = {d for d, meta in world["layers"].items() if meta.get("tainted")}
    tainted_manifests = set()
    for img in world["images"].values():
        for p in img["platforms"].values():
            if any(L in tainted_layers for L in p["layers"]):
                tainted_manifests.add(p["manifest_digest"])

    oracle = {
        "seed": world["seed"],
        "cutoff": world["incident"]["cutoff"],
        "compromised_pool": world["incident"]["compromised_pool"],
        "register": register,
        "plan": plan,
        "memo": memo,
        "exposed_workload_ids": sorted([r["workload_id"] for r in register if r["disposition"] == "EXPOSED"]),
        "cleared_workload_ids": sorted([r["workload_id"] for r in register if r["disposition"] == "CLEARED"]),
        "unresolved_workload_ids": sorted([r["workload_id"] for r in register if r["disposition"] == "UNRESOLVED"]),
        "safe_recovery_digests": sorted(safe_digests),
        "unsafe_recovery_digests": sorted(unsafe_digests),
        "tainted_manifests": sorted(tainted_manifests),
        "forcing_cases": world["forcing_cases"],
        "quorum_group": "edge-checkout",
        "min_healthy_regions": 2,
    }
    return oracle


def write_oracle(oracle: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(oracle, indent=2), encoding="utf-8")


def write_reference_outputs(oracle: dict[str, Any], out_dir: str | Path) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "exposure_register.csv").open("w", encoding="utf-8", newline="") as f:
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
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in oracle["register"]:
            w.writerow(row)
    with (out / "response_plan.csv").open("w", encoding="utf-8", newline="") as f:
        fields = [
            "sequence",
            "service_id",
            "workload_id",
            "action",
            "recovery_digest",
            "precondition",
            "expected_effect",
            "evidence_refs",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in oracle["plan"]:
            w.writerow(row)
    (out / "incident_decision.md").write_text(oracle["memo"], encoding="utf-8")
