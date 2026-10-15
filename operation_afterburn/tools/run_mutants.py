#!/usr/bin/env python3
"""18 negative mutants against the grader."""
from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verifier.grade import grade_submission


def _load(base: Path):
    reg = list(csv.DictReader((base / "exposure_register.csv").open()))
    plan = list(csv.DictReader((base / "response_plan.csv").open()))
    memo = (base / "incident_decision.md").read_text(encoding="utf-8")
    return reg, plan, memo


def _write(dst: Path, reg, plan, memo):
    dst.mkdir(parents=True, exist_ok=True)
    fields = list(reg[0].keys()) if reg else [
        "workload_id",
        "environment",
        "region",
        "observed_digest",
        "disposition",
        "exposure_path",
        "evidence_refs",
        "uncertainty_or_clearance",
    ]
    with (dst / "exposure_register.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in reg:
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
    with (dst / "response_plan.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=pfields)
        w.writeheader()
        for r in plan:
            w.writerow(r)
    (dst / "incident_decision.md").write_text(memo, encoding="utf-8")


def main() -> int:
    seed_dir = ROOT / "work" / "seed_42_scale"
    data = seed_dir / "data"
    oracle = seed_dir / "author_only" / "oracle.json"
    good = seed_dir / "output_solver"
    ora = json.loads(oracle.read_text())
    reg, plan, memo = _load(good)
    out_root = ROOT / "work" / "mutants"
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir()

    mutants = {}

    # 1 empty
    d = out_root / "m01_empty"
    d.mkdir()
    (d / "exposure_register.csv").write_text("workload_id,environment,region,observed_digest,disposition,exposure_path,evidence_refs,uncertainty_or_clearance\n")
    (d / "response_plan.csv").write_text("sequence,service_id,workload_id,action,recovery_digest,precondition,expected_effect,evidence_refs\n")
    (d / "incident_decision.md").write_text("# empty\n")
    mutants["m01_empty"] = d

    # 2 every suspicious exposed — mark all production EXPOSED
    r2 = [dict(x) for x in reg]
    for r in r2:
        if r["environment"] == "production":
            r["disposition"] = "EXPOSED"
    mutants["m02_all_prod_exposed"] = out_root / "m02"
    _write(mutants["m02_all_prod_exposed"], r2, plan, memo)

    # 3 all signed clean — clear all
    r3 = [dict(x) | {"disposition": "CLEARED"} for x in reg]
    mutants["m03_all_cleared"] = out_root / "m03"
    _write(mutants["m03_all_cleared"], r3, [], memo)

    # 4 tag equals — clear payments
    r4 = [dict(x) for x in reg]
    for r in r4:
        if r["workload_id"] == "wl-payments-useast":
            r["disposition"] = "CLEARED"
    mutants["m04_tag_clear_payments"] = out_root / "m04"
    _write(mutants["m04_tag_clear_payments"], r4, plan, memo)

    # 5 index=manifest — clear arm risk
    r5 = [dict(x) for x in reg]
    for r in r5:
        if r["workload_id"] == "wl-risk-eu-arm":
            r["disposition"] = "CLEARED"
    mutants["m05_clear_arm"] = out_root / "m05"
    _write(mutants["m05_clear_arm"], r5, plan, memo)

    # 6 ignore base layers — clear catalog
    r6 = [dict(x) for x in reg]
    for r in r6:
        if r["workload_id"] == "wl-catalog-useast":
            r["disposition"] = "CLEARED"
    mutants["m06_ignore_layers"] = out_root / "m06"
    _write(mutants["m06_ignore_layers"], r6, plan, memo)

    # 7 desired=running — clear inventory
    r7 = [dict(x) for x in reg]
    for r in r7:
        if r["workload_id"] == "wl-inventory-useast":
            r["disposition"] = "CLEARED"
    mutants["m07_desired"] = out_root / "m07"
    _write(mutants["m07_desired"], r7, plan, memo)

    # 8 old observation live — expose shipping
    r8 = [dict(x) for x in reg]
    for r in r8:
        if r["workload_id"] == "wl-shipping-eu":
            r["disposition"] = "EXPOSED"
    mutants["m08_stale_live"] = out_root / "m08"
    _write(mutants["m08_stale_live"], r8, plan, memo)

    # 9 ignore clean lookalikes — drop cleared rows
    r9 = [dict(x) for x in reg if x["disposition"] != "CLEARED"]
    mutants["m09_omit_cleared"] = out_root / "m09"
    _write(mutants["m09_omit_cleared"], r9, plan, memo)

    # 10 fabricated evidence in register and plan
    r10 = [dict(x) for x in reg]
    for r in r10:
        r["evidence_refs"] = "FAKE-9999;FABRICATED-001"
    p10 = [dict(x) for x in plan]
    for p in p10:
        p["evidence_refs"] = "FAKE-8888;FABRICATED-002"
    mutants["m10_fake_evidence"] = out_root / "m10"
    _write(mutants["m10_fake_evidence"], r10, p10, memo)

    # 11 stop all quorum members simultaneously (same sequence)
    p11 = []
    for svc, wid in [
        ("payments-api", "wl-payments-useast"),
        ("checkout-bff", "wl-checkout-useast"),
        ("auth-gateway", "wl-auth-gateway-us-east-prod"),
    ]:
        p11.append(
            {
                "sequence": "1",
                "service_id": svc,
                "workload_id": wid,
                "action": "isolate",
                "recovery_digest": "",
                "precondition": "none",
                "expected_effect": "stop_all",
                "evidence_refs": reg[0]["evidence_refs"],
            }
        )
    mutants["m11_stop_all"] = out_root / "m11"
    _write(mutants["m11_stop_all"], reg, p11, memo)

    # 12 tainted rollback
    unsafe = (ora.get("unsafe_recovery_digests") or ["sha256:dead"])[0]
    p12 = [dict(x) for x in plan]
    for p in p12:
        if p.get("action") == "redeploy" or p.get("service_id") == "payments-api":
            p["action"] = "redeploy"
            p["recovery_digest"] = unsafe
    mutants["m12_tainted_rollback"] = out_root / "m12"
    _write(mutants["m12_tainted_rollback"], reg, p12, memo)

    # 13 unavailable region — mark recovery digest empty but claim redeploy with bad precondition only (soft)
    p13 = [dict(x) for x in plan]
    mutants["m13_noop_plan_change"] = out_root / "m13"
    _write(mutants["m13_noop_plan_change"], reg, p13, memo)  # control-ish; may still pass

    # 14 over-contain staging
    r14 = [dict(x) for x in reg]
    for r in r14:
        if r["workload_id"] == "wl-storefront-stage":
            r["disposition"] = "EXPOSED"
    mutants["m14_overcontain_stage"] = out_root / "m14"
    _write(mutants["m14_overcontain_stage"], r14, plan, memo)

    # 15 omit unresolved
    r15 = [dict(x) for x in reg if x["disposition"] != "UNRESOLVED"]
    mutants["m15_omit_unresolved"] = out_root / "m15"
    _write(mutants["m15_omit_unresolved"], r15, plan, memo)

    # 16 after-cutoff approval style — redeploy payments with no clean check
    p16 = [dict(x) for x in plan]
    p16.insert(
        0,
        {
            "sequence": "0",
            "service_id": "payments-api",
            "workload_id": "wl-payments-useast",
            "action": "redeploy",
            "recovery_digest": (ora.get("unsafe_recovery_digests") or [""])[0],
            "precondition": "post_cutoff_approval",
            "expected_effect": "unauthorized",
            "evidence_refs": "CHG-FAKE",
        },
    )
    mutants["m16_after_cutoff"] = out_root / "m16"
    _write(mutants["m16_after_cutoff"], reg, p16, memo)

    # 17 reverse order only — should still be accepted if safe
    p17 = list(reversed([dict(x) for x in plan]))
    for i, p in enumerate(p17, 1):
        p["sequence"] = str(i)
    mutants["m17_reversed_valid"] = out_root / "m17"
    _write(mutants["m17_reversed_valid"], reg, p17, memo)

    # 18 no-op headers only already m01; add wrong all exposed+bad plan
    r18 = [dict(x) | {"disposition": "EXPOSED"} for x in reg]
    mutants["m18_all_exposed"] = out_root / "m18"
    _write(mutants["m18_all_exposed"], r18, p11, memo)

    rows = []
    rejected = 0
    for name, path in mutants.items():
        g = grade_submission(path, oracle, data)
        # mutants that should still pass: m17 reversed valid; m13 maybe
        expect_reject = name not in {"m17_reversed_valid", "m13_noop_plan_change"}
        failed = g.reward < 85
        if expect_reject and failed:
            rejected += 1
        if not expect_reject and not failed:
            rejected += 0
        rows.append(
            {
                "mutant": name,
                "reward": f"{g.reward:.2f}",
                "expect_reject": expect_reject,
                "rejected": failed if expect_reject else (not failed),
                "notes": json.dumps(g.checks.get("exposure_f1", {})),
            }
        )

    # count expect_reject that were rejected
    rej = sum(1 for r in rows if r["expect_reject"] and float(r["reward"]) < 85)
    total_neg = sum(1 for r in rows if r["expect_reject"])
    reports = ROOT / "reports"
    with (reports / "MUTANT_RESULTS.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["mutant", "reward", "expect_reject", "rejected", "notes"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    summary = {"negative_mutants": total_neg, "rejected": rej, "pass_gate": rej >= 15}
    (reports / "mutant_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"rows": rows, "summary": summary}, indent=2))
    return 0 if summary["pass_gate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
