"""
Semantic grader for Operation AFTERBURN.

Accepts feasible safe response plans (invariant simulation), not a single golden sequence.
Does not import the evidence-only solver.
"""
from __future__ import annotations

import csv
import gzip
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DISPOSITIONS = {"EXPOSED", "CLEARED", "UNRESOLVED"}
ACTIONS = {"redeploy", "quarantine", "isolate", "observe", "hold"}


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return list(csv.DictReader(path.open(encoding="utf-8")))


def _parse_ts(ts: str | None):
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


@dataclass
class GradeResult:
    reward: float
    max_reward: float
    checks: dict[str, Any]
    partial: dict[str, float]

    @property
    def normalized(self) -> float:
        return self.reward / self.max_reward if self.max_reward else 0.0

    def as_dict(self) -> dict:
        return {
            "reward": self.reward,
            "max_reward": self.max_reward,
            "normalized": self.normalized,
            "checks": self.checks,
            "partial": self.partial,
        }


def _load_record_index(data_dir: Path) -> set[str]:
    ids: set[str] = set()
    for p in data_dir.rglob("*.jsonl.gz"):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                if "record_id" in row:
                    ids.add(row["record_id"])
                if row.get("descriptor_type") == "index":
                    for m in row.get("manifests", []):
                        if m.get("record_id"):
                            ids.add(m["record_id"])
    chg = data_dir / "changes" / "emergency_changes"
    if chg.exists():
        for p in chg.glob("*.md"):
            ids.add(p.stem)
    return ids


def _simulate_plan(plan: list[dict], oracle: dict, inventory: list[dict]) -> dict[str, Any]:
    """Simulate quorum safety and recovery constraints."""
    inv = {r["workload_id"]: r for r in inventory}
    healthy: dict[str, set[str]] = {}
    for r in inventory:
        if r.get("environment") == "production":
            healthy.setdefault(r["service_id"], set()).add(r["region"])

    quorum_members = {"auth-gateway", "checkout-bff", "payments-api"}
    min_regions = oracle.get("min_healthy_regions", 2)
    unsafe_recovery = set(oracle.get("unsafe_recovery_digests") or [])
    violations = []

    # Group by sequence to catch simultaneous multi-member stops
    by_seq: dict[str, list[dict]] = {}
    for step in plan:
        by_seq.setdefault(str(step.get("sequence", "")), []).append(step)

    for seq, steps in by_seq.items():
        edge_stops = []
        for step in steps:
            action = step.get("action")
            wid = step.get("workload_id")
            svc = step.get("service_id") or (inv.get(wid, {}) or {}).get("service_id")
            region = (inv.get(wid, {}) or {}).get("region")
            if action in {"quarantine", "isolate"} and svc in quorum_members:
                edge_stops.append(svc)
                if region:
                    after = set(healthy.get(svc, set()))
                    after.discard(region)
                    healthy[svc] = after
                    if len(after) < min_regions:
                        violations.append(f"quorum_violation:{svc}:{seq}")
            if action == "redeploy":
                dig = step.get("recovery_digest") or ""
                if dig in unsafe_recovery:
                    violations.append(f"tainted_recovery:{dig}")
                if dig and dig in set(oracle.get("tainted_manifests") or []):
                    violations.append(f"tainted_recovery:{dig}")
                # redeploy restores region capacity
                if svc and region:
                    healthy.setdefault(svc, set()).add(region)
        if len(set(edge_stops)) >= 2 and not any(s.get("action") == "redeploy" for s in steps):
            violations.append(f"simultaneous_edge_stop:{seq}:{sorted(set(edge_stops))}")

    return {"ok": not violations, "violations": violations}


def grade_submission(output_dir: str | Path, oracle_path: str | Path, data_dir: str | Path) -> GradeResult:
    out = Path(output_dir)
    oracle = json.loads(Path(oracle_path).read_text(encoding="utf-8"))
    data_dir = Path(data_dir)
    record_ids = _load_record_index(data_dir)
    inventory = list(csv.DictReader(gzip.open(data_dir / "runtime" / "workload_inventory.csv.gz", "rt", encoding="utf-8")))

    checks: dict[str, Any] = {}
    partial: dict[str, float] = {}
    max_reward = 100.0
    reward = 0.0
    # citation_integrity added dynamically; keep partial sum capped later

    # Format layer (6 pts)
    files_ok = all((out / n).exists() and (out / n).stat().st_size > 0 for n in [
        "exposure_register.csv",
        "response_plan.csv",
        "incident_decision.md",
    ])
    checks["files_present"] = files_ok
    partial["format_files"] = 2.0 if files_ok else 0.0

    reg = _read_csv(out / "exposure_register.csv")
    plan = _read_csv(out / "response_plan.csv")
    memo = (out / "incident_decision.md").read_text(encoding="utf-8") if (out / "incident_decision.md").exists() else ""

    reg_fields = {
        "workload_id",
        "environment",
        "region",
        "observed_digest",
        "disposition",
        "exposure_path",
        "evidence_refs",
        "uncertainty_or_clearance",
    }
    schema_ok = bool(reg) and reg_fields.issubset(reg[0].keys())
    disp_ok = all(r.get("disposition") in DISPOSITIONS for r in reg) if reg else False
    checks["register_schema"] = schema_ok and disp_ok
    partial["format_schema"] = 2.0 if schema_ok and disp_ok else 0.0

    # evidence refs exist — score register and plan separately so one clean file cannot mask fabrication
    def cite_stats(rows):
        total = hit = 0
        for r in rows:
            refs = [x for x in re.split(r"[;|,]", r.get("evidence_refs") or "") if x.strip()]
            for ref in refs:
                total += 1
                if ref.strip() in record_ids:
                    hit += 1
        return total, hit

    reg_total, reg_hit = cite_stats(reg)
    plan_total, plan_hit = cite_stats(plan)
    cite_total = reg_total + plan_total
    cite_hit = reg_hit + plan_hit
    cite_ratio = cite_hit / max(cite_total, 1)
    reg_ratio = reg_hit / max(reg_total, 1)
    plan_ratio = plan_hit / max(plan_total, 1) if plan_total else 1.0
    checks["evidence_refs"] = {
        "total": cite_total,
        "hit": cite_hit,
        "reg_ratio": reg_ratio,
        "plan_ratio": plan_ratio,
        "ok": cite_total > 0 and cite_ratio >= 0.7 and reg_ratio >= 0.7,
    }
    partial["format_citations"] = 2.0 * cite_ratio if cite_total else 0.0
    fabricated = bool(cite_total) and (cite_ratio < 0.5 or reg_ratio < 0.5 or (plan_total > 0 and plan_ratio < 0.5))
    checks["fabricated_evidence"] = fabricated
    partial["citation_integrity"] = 0.0 if fabricated else (5.0 if cite_total else 0.0)

    # Exposure set scoring (40)
    exp_truth = set(oracle["exposed_workload_ids"])
    clr_truth = set(oracle["cleared_workload_ids"])
    unr_truth = set(oracle["unresolved_workload_ids"])
    exp_pred = {r["workload_id"] for r in reg if r.get("disposition") == "EXPOSED"}
    clr_pred = {r["workload_id"] for r in reg if r.get("disposition") == "CLEARED"}
    unr_pred = {r["workload_id"] for r in reg if r.get("disposition") == "UNRESOLVED"}

    def pr(pred: set, truth: set) -> tuple[float, float, float]:
        if not truth and not pred:
            return 1.0, 1.0, 1.0
        if not pred:
            return 0.0, 0.0, 0.0
        if not truth:
            return 0.0, 0.0, 0.0
        tp = len(pred & truth)
        prec = tp / len(pred)
        rec = tp / len(truth)
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        return prec, rec, f1

    ep, er, ef = pr(exp_pred, exp_truth)
    cp, cr, cf = pr(clr_pred, clr_truth)
    up, ur, uf = pr(unr_pred, unr_truth)
    checks["exposure_f1"] = {"precision": ep, "recall": er, "f1": ef, "pred": sorted(exp_pred), "truth": sorted(exp_truth)}
    checks["cleared_f1"] = {"precision": cp, "recall": cr, "f1": cf}
    checks["unresolved_f1"] = {"precision": up, "recall": ur, "f1": uf}
    missed_exp = len(exp_truth - exp_pred)
    false_exp = len(exp_pred - exp_truth)
    # Decision-sensitive: each missed/false exposure flips operational outcomes — penalize hard.
    partial["exposure"] = max(0.0, 24.0 * ef - 6.0 * missed_exp - 4.0 * false_exp)
    missed_clr = len(clr_truth - clr_pred)
    false_clr = len(clr_pred - clr_truth)
    # Treating a cleared lookalike as exposed (or omitting it) is a scored clearance error.
    partial["clearance"] = max(0.0, 10.0 * cf - 3.0 * false_clr - 2.0 * missed_clr)
    missed_unr = len(unr_truth - unr_pred)
    false_unr = len(unr_pred - unr_truth)
    partial["unresolved"] = max(0.0, 6.0 * uf - 4.0 * missed_unr - 3.0 * false_unr)

    # Response-plan completeness (prompt requires service, action, recovery target when applicable, sequencing)
    plan_fields = [
        "sequence",
        "service_id",
        "workload_id",
        "action",
        "precondition",
        "expected_effect",
        "evidence_refs",
    ]
    plan_issues: list[str] = []
    complete_action_rows = []
    for i, p in enumerate(plan):
        missing = [c for c in plan_fields if not str(p.get(c) or "").strip()]
        if missing:
            plan_issues.append(f"row{i}:missing:{','.join(missing)}")
            continue
        act = str(p.get("action") or "").strip()
        if act not in ACTIONS:
            plan_issues.append(f"row{i}:bad_action:{act}")
            continue
        if act == "redeploy" and not str(p.get("recovery_digest") or "").strip():
            plan_issues.append(f"row{i}:redeploy_without_recovery_digest")
            continue
        # sequence must be numeric-ish
        try:
            int(str(p.get("sequence")).strip())
        except Exception:
            plan_issues.append(f"row{i}:non_integer_sequence")
            continue
        complete_action_rows.append(p)
    checks["plan_completeness"] = {
        "ok": not plan_issues,
        "issues": plan_issues[:20],
        "complete_rows": len(complete_action_rows),
        "total_rows": len(plan),
    }
    # Only complete rows earn coverage / recovery credit.
    plan_exposed_covered = {
        p["workload_id"]
        for p in complete_action_rows
        if p.get("action") in {"redeploy", "quarantine", "isolate"}
    }
    cover = len(exp_truth & plan_exposed_covered) / len(exp_truth) if exp_truth else 1.0
    checks["plan_coverage"] = cover
    partial["plan_coverage"] = 10.0 * cover

    sim = _simulate_plan(complete_action_rows, oracle, inventory)
    checks["plan_simulation"] = sim
    partial["plan_safety"] = 10.0 if sim["ok"] else max(0.0, 10.0 - 3.0 * len(sim["violations"]))

    tainted_used = [
        p.get("recovery_digest")
        for p in complete_action_rows
        if p.get("recovery_digest")
        and p.get("recovery_digest") in set(oracle.get("unsafe_recovery_digests") or [])
    ]
    checks["tainted_recovery_used"] = tainted_used
    redeploys = [p for p in complete_action_rows if p.get("action") == "redeploy"]
    safe = set(oracle.get("safe_recovery_digests") or [])
    redeploy_ok = all(str(p.get("recovery_digest") or "") in safe for p in redeploys) if redeploys else True
    checks["redeploy_targets_safe"] = redeploy_ok
    if tainted_used or not redeploy_ok:
        partial["clean_recovery"] = 0.0
    elif plan_issues:
        # Incomplete plans cannot earn full recovery credit even if no tainted digest is present.
        partial["clean_recovery"] = 0.0
    else:
        partial["clean_recovery"] = 8.0
    # Explicit completeness score — incomplete worksheet fields fail the band.
    if not plan:
        partial["plan_fields"] = 0.0
    elif plan_issues:
        partial["plan_fields"] = 0.0
    else:
        partial["plan_fields"] = 8.0

    # memo checklist (15)
    memo_l = memo.lower()
    memo_pts = 0.0
    memo_checks = {
        "has_recommendation": "immediate recommendation" in memo_l or "quarantine" in memo_l or "redeploy" in memo_l,
        "mentions_exposure": "exposure" in memo_l,
        "mentions_clearance": "cleared" in memo_l or "lookalike" in memo_l,
        "mentions_tradeoff": "quorum" in memo_l or "availability" in memo_l or "trade" in memo_l,
        "mentions_limits": "limitation" in memo_l or "unresolved" in memo_l or "evidence" in memo_l,
        "no_live_claim": "performed live" not in memo_l and "i have executed" not in memo_l,
    }
    memo_pts = sum(2.5 for v in memo_checks.values() if v)  # max 15
    checks["memo"] = memo_checks
    partial["memo"] = min(15.0, memo_pts)

    # empty / overbroad penalties
    if not reg:
        partial = {k: 0.0 for k in partial}
    if exp_pred and len(exp_pred) > max(3 * len(exp_truth), len(exp_truth) + 8):
        partial["exposure"] *= 0.3
        checks["overbroad_exposure"] = True
    if checks.get("fabricated_evidence"):
        partial["exposure"] *= 0.4
        partial["plan_coverage"] *= 0.4
        partial["memo"] *= 0.5
    if not checks.get("plan_simulation", {}).get("ok", True):
        # ensure unsafe plans cannot sit in the pass band on exposure strength alone
        partial["plan_safety"] = min(partial.get("plan_safety", 0.0), 2.0)
    if plan_issues:
        # Hard cap: missing required plan worksheet fields cannot reach the semantic pass band.
        partial["plan_coverage"] = min(partial.get("plan_coverage", 0.0), 2.0)
        partial["plan_safety"] = min(partial.get("plan_safety", 0.0), 2.0)

    reward = sum(partial.values())
    # clamp — also enforce incomplete-plan ceiling so leaky coverage cannot pass >=85
    if plan_issues:
        reward = min(reward, 70.0)
    reward = min(max_reward, reward)
    return GradeResult(reward=reward, max_reward=max_reward, checks=checks, partial=partial)


def write_ctrf(result: GradeResult, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "results": {
            "tool": {"name": "afterburn-grader"},
            "summary": {
                "tests": 1,
                "passed": 1 if result.reward >= 85 else 0,
                "failed": 0 if result.reward >= 85 else 1,
            },
            "tests": [
                {
                    "name": "semantic_grade",
                    "status": "passed" if result.reward >= 85 else "failed",
                    "raw_status": json.dumps(result.as_dict()),
                }
            ],
        }
    }
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
