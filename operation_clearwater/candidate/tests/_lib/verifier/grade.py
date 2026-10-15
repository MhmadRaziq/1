"""Semantic grader — accepts valid alternate portfolios; rejects unsafe plans."""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# When packaged inside candidate/tests, oracle may live beside grade_lib.
import sys

_ROOT_CANDIDATES = [
    Path(__file__).resolve().parents[1],
    Path(__file__).resolve().parents[2],
]
for _r in _ROOT_CANDIDATES:
    if (_r / "oracle").is_dir() and str(_r) not in sys.path:
        sys.path.insert(0, str(_r))

from oracle.common import evaluate_candidate, load_packet, cutover_order  # noqa: E402
from oracle import oracle_enumerate  # noqa: E402


ID_RE = re.compile(r"\b(?:VR|WAL|KEY|AT|SC|RT|IR|TL|TLH)-[A-Z0-9\-]+\b")


@dataclass
class GradeResult:
    reward: float
    checks: dict[str, bool] = field(default_factory=dict)
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"reward": self.reward, "checks": self.checks, "detail": self.detail}


def _load_plan(path: Path) -> list[dict]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".csv":
        return list(csv.DictReader(text.splitlines()))
    # Markdown table fallback
    rows = []
    lines = [ln for ln in text.splitlines() if "|" in ln]
    if len(lines) >= 2:
        headers = [h.strip() for h in lines[0].strip("|").split("|")]
        for ln in lines[2:]:
            cols = [c.strip() for c in ln.strip("|").split("|")]
            if len(cols) == len(headers):
                rows.append(dict(zip(headers, cols)))
    return rows


def _collect_ids(*texts: str) -> set[str]:
    found = set()
    for t in texts:
        found.update(ID_RE.findall(t or ""))
    return found


def grade_submission(output_dir: Path, data_dir: Path, expected: dict | None = None) -> GradeResult:
    output_dir = Path(output_dir)
    data_dir = Path(data_dir)
    checks: dict[str, bool] = {}
    detail: dict[str, Any] = {}

    memo_path = output_dir / "recovery_decision.md"
    plan_path = output_dir / "recovery_plan.csv"
    # Allow markdown plan as alternate filename
    if not plan_path.exists():
        alt = output_dir / "recovery_plan.md"
        plan_path = alt if alt.exists() else plan_path

    checks["memo_exists"] = memo_path.exists() and memo_path.stat().st_size > 40
    checks["plan_exists"] = plan_path.exists() and plan_path.stat().st_size > 40
    memo = memo_path.read_text(encoding="utf-8") if checks["memo_exists"] else ""
    plan_rows = _load_plan(plan_path) if checks["plan_exists"] else []

    ref = oracle_enumerate.analyze(data_dir)
    pkt = load_packet(data_dir)
    cats = {c["candidate_id"]: c for c in pkt.candidates}
    known_ids = set()
    for name in (
        "vault_receipts.json", "wal_archive.json", "kms_grants.json",
        "build_attestations.json", "malware_scans.json", "restore_rehearsals.json",
        "intrusion_indicators.json", "timeline_history.json",
    ):
        for row in json.loads((data_dir / name).read_text()):
            if row.get("event_id"):
                known_ids.add(row["event_id"])

    # Parse portfolio from plan
    portfolio = {}
    for row in plan_rows:
        svc = (row.get("service") or "").strip()
        cid = (row.get("candidate_id") or row.get("source") or "").strip()
        action = (row.get("action") or "restore").strip().lower()
        if svc and cid and "defer" not in action:
            portfolio[svc] = cid

    services = sorted(pkt.policy["dependencies"])
    checks["plan_covers_services"] = all(s in portfolio for s in services) if portfolio else False

    # Safety: every selected candidate must be admissible. Empty portfolios fail.
    unsafe = []
    for svc, cid in portfolio.items():
        if cid not in cats:
            unsafe.append(f"unknown:{cid}")
            continue
        v = evaluate_candidate(pkt, cats[cid])
        if not v.valid:
            unsafe.append(f"{cid}:{','.join(v.reasons)}")
    checks["no_unsafe_sources"] = bool(portfolio) and not unsafe and checks["plan_covers_services"]
    detail["unsafe"] = unsafe

    # Capacity
    effort = sum(int(cats[cid]["effort_units"]) for cid in portfolio.values() if cid in cats)
    checks["within_budget"] = (
        bool(portfolio)
        and checks["plan_covers_services"]
        and effort <= int(pkt.policy["max_restore_effort_units"])
    )
    detail["effort"] = effort

    # Schema
    schema_bad = []
    if checks["plan_covers_services"]:
        for svc, cid in portfolio.items():
            c = cats.get(cid)
            if not c:
                continue
            for dep, need in (c.get("requires_schema_epoch") or {}).items():
                if portfolio.get(dep) and cats[portfolio[dep]]["schema_epoch"] < need:
                    schema_bad.append(f"{svc}->{dep}")
    checks["schema_compatible"] = bool(portfolio) and checks["plan_covers_services"] and not schema_bad
    detail["schema_bad"] = schema_bad

    # Migration
    mig_bad = any(cats[cid].get("migration_irreversible") for cid in portfolio.values() if cid in cats)
    checks["no_irreversible_migration"] = bool(portfolio) and checks["plan_covers_services"] and not mig_bad

    # Cutover order
    deps = pkt.policy["dependencies"]
    order = [r.get("service", "").strip() for r in plan_rows if r.get("service")]
    order = [s for s in order if s in portfolio]
    cutover_ok = True
    if order:
        seen = set()
        for s in order:
            if any(d not in seen for d in deps.get(s, []) if d in portfolio):
                # allow if dependency appears earlier — check
                pass
            seen.add(s)
        # verify topological: for each service, all deps appear before it
        idx = {s: i for i, s in enumerate(order)}
        for s in order:
            for d in deps.get(s, []):
                if d in idx and idx[d] > idx[s]:
                    cutover_ok = False
    checks["cutover_feasible"] = cutover_ok and bool(order)

    # Citations
    cited = _collect_ids(memo, plan_path.read_text(encoding="utf-8") if plan_path.exists() else "")
    fabricated = sorted(i for i in cited if i not in known_ids)
    checks["citations_resolvable"] = bool(memo) and len(cited) >= 8 and not fabricated
    checks["no_fabricated_citations"] = bool(memo) and not fabricated
    detail["cited"] = len(cited)
    detail["fabricated"] = fabricated[:10]

    # Memo quality signals (require a real memo)
    low = memo.lower()
    checks["memo_mentions_vault_vs_catalog"] = bool(memo) and (
        ("vault" in low or "receipt" in low) and ("catalog" in low or "console" in low)
    )
    checks["memo_mentions_uncertainty"] = bool(memo) and any(
        k in low for k in ("assumption", "residual", "gap", "uncertain", "unresolved")
    )
    checks["memo_mentions_data_loss"] = bool(memo) and ("loss" in low or "rpo" in low)
    checks["memo_mentions_rejected"] = bool(memo) and (
        "reject" in low or "unsafe" in low or "defer" in low
    )
    checks["no_external_urls"] = bool(memo) and "http://" not in low and "https://" not in low
    checks["preserves_originals"] = bool(memo) and any(
        k in low for k in ("original", "legal hold", "clean room", "clean-room", "isolat")
    )
    checks["validation_gates_present"] = bool(plan_rows) and (
        any(
            "validation" in (r.get("validation_gate") or "").lower()
            or "smoke" in (r.get("validation_gate") or "").lower()
            or "checksum" in (r.get("validation_gate") or "").lower()
            for r in plan_rows
        )
        or "validation" in low
    )

    # Near-optimal portfolio: accept if weighted loss within 5% of reference
    # and all safety checks pass
    loss = None
    if checks["plan_covers_services"] and checks["no_unsafe_sources"]:
        loss = 0.0
        for svc, cid in portfolio.items():
            v = evaluate_candidate(pkt, cats[cid])
            loss += pkt.policy["service_priorities"][svc] * v.data_loss_hours
    detail["weighted_loss"] = loss
    detail["ref_loss"] = ref.get("weighted_loss")
    if loss is not None and ref.get("weighted_loss"):
        checks["near_optimal_loss"] = loss <= ref["weighted_loss"] * 1.05 + 1e-6
    else:
        checks["near_optimal_loss"] = False

    # Exact reference match (bonus path, not required)
    checks["matches_reference_portfolio"] = portfolio == ref.get("portfolio")

    # Scoring weights (sum of positive = 100)
    weights = {
        "memo_exists": 3,
        "plan_exists": 3,
        "plan_covers_services": 5,
        "no_unsafe_sources": 12,
        "within_budget": 5,
        "schema_compatible": 5,
        "no_irreversible_migration": 8,
        "cutover_feasible": 8,
        "citations_resolvable": 6,
        "no_fabricated_citations": 8,
        "memo_mentions_vault_vs_catalog": 4,
        "memo_mentions_uncertainty": 3,
        "memo_mentions_data_loss": 4,
        "memo_mentions_rejected": 4,
        "no_external_urls": 2,
        "preserves_originals": 4,
        "validation_gates_present": 4,
        "near_optimal_loss": 8,
        "matches_reference_portfolio": 4,
    }
    assert sum(weights.values()) == 100
    earned = sum(w for k, w in weights.items() if checks.get(k))
    reward = float(earned)
    # Hard floors: fabricated citations or empty deliverables cannot pass
    if fabricated or not checks.get("memo_exists") or not checks.get("plan_exists"):
        reward = min(reward, 70.0)
    if unsafe or mig_bad:
        reward = min(reward, 80.0)
    if not checks.get("cutover_feasible"):
        reward = min(reward, 82.0)
    detail["weights"] = weights
    detail["portfolio"] = portfolio
    return GradeResult(reward=reward, checks=checks, detail=detail)


if __name__ == "__main__":
    import sys
    out = Path(sys.argv[1])
    data = Path(sys.argv[2])
    print(json.dumps(grade_submission(out, data).as_dict(), indent=2))
