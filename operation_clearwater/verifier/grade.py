"""Output-only semantic grader for Operation CLEARWATER.

Checks submitted memo/plan against the offline evidence packet and a frozen
``private_expected.json`` reference. Does **not** import or re-run the
reference solver / oracle packages (Format requires grader independence).
"""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

ID_RE = re.compile(r"\b(?:VR|WAL|KEY|AT|SC|RT|IR|TL|TLH)-[A-Z0-9\-]+\b")
SEG = 16 * 1024 * 1024


class GradeResult:
    def __init__(self, reward: float, checks: dict[str, bool], detail: dict[str, Any]):
        self.reward = reward
        self.checks = checks
        self.detail = detail

    def as_dict(self) -> dict:
        return {"reward": self.reward, "checks": self.checks, "detail": self.detail}


def _ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _lsn(text: str) -> int:
    hi, lo = text.split("/")
    return (int(hi, 16) << 32) | int(lo, 16)


def _wal_name(timeline: int, offset: int) -> str:
    log = offset // (SEG * 256)
    seg = (offset // SEG) % 256
    return f"{timeline:08X}{log:08X}{seg:08X}"


def _needed_wal(start: int, end: int, timeline: int) -> set[str]:
    names: set[str] = set()
    off = (start // SEG) * SEG
    while off <= end:
        names.add(_wal_name(timeline, off))
        off += SEG
    return names


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _index_by_candidate(rows: list[dict]) -> dict[str, dict]:
    return {r["candidate_id"]: r for r in rows if r.get("candidate_id")}


def _load_plan(path: Path) -> list[dict]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".csv":
        return list(csv.DictReader(text.splitlines()))
    rows: list[dict] = []
    lines = [ln for ln in text.splitlines() if "|" in ln]
    if len(lines) >= 2:
        headers = [h.strip() for h in lines[0].strip("|").split("|")]
        for ln in lines[2:]:
            cols = [c.strip() for c in ln.strip("|").split("|")]
            if len(cols) == len(headers):
                rows.append(dict(zip(headers, cols)))
    return rows


def _collect_ids(*texts: str) -> set[str]:
    found: set[str] = set()
    for t in texts:
        found.update(ID_RE.findall(t or ""))
    return found


def _load_expected(data_dir: Path, expected: dict | None) -> dict:
    if expected is not None:
        return expected
    # Packaged tests keep the frozen answer beside grade_lib.py
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / "private_expected.json",  # tests/_lib/verifier -> tests/
        here.parents[2] / "private_expected.json",
        Path(__file__).resolve().parents[2] / "candidate" / "tests" / "private_expected.json",
        data_dir.parent.parent / "tests" / "private_expected.json",
    ]
    for path in candidates:
        if path.is_file():
            return _load_json(path)
    return {}


def _hours_since(cutoff: datetime, recovery: datetime | None) -> float:
    if recovery is None:
        return 999.0
    return (cutoff - recovery).total_seconds() / 3600.0


def _candidate_fail_reasons(
    cand: dict,
    *,
    policy: dict,
    receipts: dict[str, dict],
    keys: dict[str, dict],
    attest: dict[str, dict],
    scans: dict[str, dict],
    rehearsals: dict[str, dict],
    wal_by_id: dict[str, dict],
    timelines: list[dict],
    indicators: dict[str, dict],
    decision: datetime,
) -> tuple[list[str], float]:
    """Return (reject_reasons, data_loss_hours). Structured differently from the solver."""
    fails: list[str] = []
    cid = cand["candidate_id"]
    receipt = receipts.get(cid)
    key = keys.get(cid)
    attestation = attest.get(cid)
    scan = scans.get(cid)
    rehearsal = rehearsals.get(cid)
    target_time = _ts(cand.get("recovery_target_time"))
    loss_h = _hours_since(decision, target_time)

    # Vault receipt gates
    if receipt is None:
        fails.append("vault_unavailable")
    else:
        arrived = _ts(receipt.get("received_at"))
        if receipt.get("copy_status") != "COMPLETE" or not receipt.get("immutable"):
            fails.append("vault_unavailable")
        if arrived and arrived > decision:
            fails.append("vault_unavailable")
        if receipt.get("legal_hold") and receipt.get("copy_restore_allowed") is False:
            fails.append("vault_hold_blocks_copy")
        if receipt.get("object_digest") != cand.get("manifest_digest"):
            fails.append("vault_digest_mismatch")

    # Key / attestation / scan / rehearsal gates (separate blocks)
    if key is None:
        fails.append("key_unavailable")
    else:
        grant_at = _ts(key.get("grant_effective_at"))
        if key.get("restore_grant") != "APPROVED" or key.get("key_state") != "ENABLED":
            fails.append("key_unavailable")
        if grant_at and grant_at > decision:
            fails.append("key_unavailable")

    if attestation is None:
        fails.append("attestation_untrusted")
    else:
        if not attestation.get("signature_valid") or not attestation.get("signer_trusted"):
            fails.append("attestation_untrusted")
        if attestation.get("snapshot_digest") != cand.get("manifest_digest"):
            fails.append("attestation_untrusted")
        revoked = _ts(attestation.get("signer_revoked_at"))
        signed = _ts(attestation.get("signed_at"))
        if revoked and signed and revoked <= signed:
            fails.append("attestation_untrusted")

    if scan is None:
        fails.append("scan_not_current")
    else:
        covered = _ts(scan.get("covered_through"))
        if scan.get("result") != "CLEAN":
            fails.append("scan_not_current")
        elif (covered and target_time and covered < target_time) or scan.get("covers_recovery_target") is False:
            fails.append("scan_not_current")

    if rehearsal is None:
        fails.append("rehearsal_not_usable")
    else:
        recorded = _ts(rehearsal.get("recorded_at"))
        if rehearsal.get("result") != "PASS" or rehearsal.get("data_checks") != "PASS":
            fails.append("rehearsal_not_usable")
        if recorded and recorded > decision:
            fails.append("rehearsal_not_usable")

    # WAL continuity
    stop = _lsn(cand["backup_stop_lsn"])
    target = _lsn(cand["recovery_target_lsn"])
    tl = int(cand["timeline_id"])
    need = _needed_wal(stop, target, tl)
    have: set[str] = set()
    for wid in cand.get("wal_event_ids") or []:
        row = wal_by_id.get(wid)
        if not row:
            continue
        if row.get("archive_status") != "COMPLETE" or not row.get("verified_hash"):
            continue
        if int(row.get("timeline_id", -1)) != tl:
            continue
        have.add(row["wal_filename"])
    if need - have:
        fails.append("wal_chain_not_continuous")

    # Timeline / replica rules
    if tl != 1:
        child_rows = [h for h in timelines if int(h.get("child_timeline", -1)) == tl]
        ok = False
        for h in child_rows:
            sp = _lsn(h["switchpoint_lsn"])
            if int(h["parent_timeline"]) == 1 and stop >= sp and target >= stop:
                ok = True
                break
        if not ok:
            fails.append("timeline_incompatible")
    if cand.get("cluster_role") == "replica":
        fails.append("timeline_incompatible")

    # Intrusion windows
    tip = indicators.get(cand["service"])
    if tip and target_time:
        w0, w1 = _ts(tip.get("window_start")), _ts(tip.get("window_end"))
        if w0 and w1 and w0 <= target_time <= w1:
            if tip.get("confirmed") and tip.get("indicator") == "RANSOMWARE-WRITE":
                fails.append("compromised_replay")
            elif (
                policy.get("block_held_targets_inside_open_indicator_windows")
                and receipt
                and receipt.get("legal_hold")
            ):
                fails.append("open_indicator_window")

    rpo = policy["service_rpo_hours"].get(cand["service"], 72)
    if loss_h > rpo:
        fails.append("rpo_exceeded")

    # Deduplicate while preserving order
    seen: set[str] = set()
    uniq = []
    for reason in fails:
        if reason not in seen:
            seen.add(reason)
            uniq.append(reason)
    return uniq, loss_h


def _skew_violation(
    portfolio: dict[str, str],
    cats: dict[str, dict],
    deps: dict[str, list[str]],
    max_hours: float,
) -> bool:
    for svc, cid in portfolio.items():
        child_t = _ts(cats[cid].get("recovery_target_time"))
        if child_t is None:
            continue
        for dep in deps.get(svc, []):
            parent_cid = portfolio.get(dep)
            if not parent_cid or parent_cid not in cats:
                continue
            parent_t = _ts(cats[parent_cid].get("recovery_target_time"))
            if parent_t is None:
                continue
            ahead = (child_t - parent_t).total_seconds() / 3600.0
            if ahead > max_hours + 1e-9:
                return True
    return False


def grade_submission(output_dir: Path, data_dir: Path, expected: dict | None = None) -> GradeResult:
    output_dir = Path(output_dir)
    data_dir = Path(data_dir)
    checks: dict[str, bool] = {}
    detail: dict[str, Any] = {}

    memo_path = output_dir / "recovery_decision.md"
    plan_path = output_dir / "recovery_plan.csv"
    if not plan_path.exists():
        alt = output_dir / "recovery_plan.md"
        if alt.exists():
            plan_path = alt

    checks["memo_exists"] = memo_path.exists() and memo_path.stat().st_size > 40
    checks["plan_exists"] = plan_path.exists() and plan_path.stat().st_size > 40
    memo = memo_path.read_text(encoding="utf-8") if checks["memo_exists"] else ""
    plan_rows = _load_plan(plan_path) if checks["plan_exists"] else []

    policy = _load_json(data_dir / "recovery_policy.json")
    candidates = _load_json(data_dir / "recovery_candidates.json")
    cats = {c["candidate_id"]: c for c in candidates}
    decision = _ts(policy["decision_time"])
    assert decision is not None

    receipts = _index_by_candidate(_load_json(data_dir / "vault_receipts.json"))
    keys = _index_by_candidate(_load_json(data_dir / "kms_grants.json"))
    attest = _index_by_candidate(_load_json(data_dir / "build_attestations.json"))
    scans = _index_by_candidate(_load_json(data_dir / "malware_scans.json"))
    rehearsals = _index_by_candidate(_load_json(data_dir / "restore_rehearsals.json"))
    wal_rows = _load_json(data_dir / "wal_archive.json")
    wal_by_id = {r["event_id"]: r for r in wal_rows if r.get("event_id")}
    timelines = _load_json(data_dir / "timeline_history.json")
    indicators = {r["service"]: r for r in _load_json(data_dir / "intrusion_indicators.json")}

    known_ids: set[str] = set()
    for name in (
        "vault_receipts.json",
        "wal_archive.json",
        "kms_grants.json",
        "build_attestations.json",
        "malware_scans.json",
        "restore_rehearsals.json",
        "intrusion_indicators.json",
        "timeline_history.json",
    ):
        for row in _load_json(data_dir / name):
            if row.get("event_id"):
                known_ids.add(row["event_id"])

    ref = _load_expected(data_dir, expected)

    portfolio: dict[str, str] = {}
    for row in plan_rows:
        svc = (row.get("service") or "").strip()
        cid = (row.get("candidate_id") or row.get("source") or "").strip()
        action = (row.get("action") or "restore").strip().lower()
        if svc and cid and "defer" not in action:
            portfolio[svc] = cid

    services = sorted(policy["dependencies"])
    checks["plan_covers_services"] = all(s in portfolio for s in services) if portfolio else False

    unsafe: list[str] = []
    loss_by_cid: dict[str, float] = {}
    for svc, cid in portfolio.items():
        if cid not in cats:
            unsafe.append(f"unknown:{cid}")
            continue
        reasons, loss_h = _candidate_fail_reasons(
            cats[cid],
            policy=policy,
            receipts=receipts,
            keys=keys,
            attest=attest,
            scans=scans,
            rehearsals=rehearsals,
            wal_by_id=wal_by_id,
            timelines=timelines,
            indicators=indicators,
            decision=decision,
        )
        loss_by_cid[cid] = loss_h
        if reasons:
            unsafe.append(f"{cid}:{','.join(reasons)}")
    checks["no_unsafe_sources"] = bool(portfolio) and not unsafe and checks["plan_covers_services"]
    detail["unsafe"] = unsafe

    effort = sum(int(cats[cid]["effort_units"]) for cid in portfolio.values() if cid in cats)
    checks["within_budget"] = (
        bool(portfolio)
        and checks["plan_covers_services"]
        and effort <= int(policy["max_restore_effort_units"])
    )
    detail["effort"] = effort

    schema_bad: list[str] = []
    if checks["plan_covers_services"]:
        for svc, cid in portfolio.items():
            c = cats.get(cid)
            if not c:
                continue
            for dep, need in (c.get("requires_schema_epoch") or {}).items():
                parent = portfolio.get(dep)
                if parent and cats[parent]["schema_epoch"] < need:
                    schema_bad.append(f"{svc}->{dep}")
    checks["schema_compatible"] = bool(portfolio) and checks["plan_covers_services"] and not schema_bad
    detail["schema_bad"] = schema_bad

    mig_bad = any(cats[cid].get("migration_irreversible") for cid in portfolio.values() if cid in cats)
    checks["no_irreversible_migration"] = bool(portfolio) and checks["plan_covers_services"] and not mig_bad

    skew_bad = False
    if checks["plan_covers_services"] and portfolio:
        skew_bad = _skew_violation(
            portfolio,
            cats,
            policy["dependencies"],
            float(policy.get("max_dependent_skew_hours", 0)),
        )
    checks["skew_compatible"] = bool(portfolio) and checks["plan_covers_services"] and not skew_bad

    deps = policy["dependencies"]
    order = [r.get("service", "").strip() for r in plan_rows if r.get("service")]
    order = [s for s in order if s in portfolio]
    cutover_ok = True
    if order:
        idx = {s: i for i, s in enumerate(order)}
        for s in order:
            for d in deps.get(s, []):
                if d in idx and idx[d] > idx[s]:
                    cutover_ok = False
    checks["cutover_feasible"] = cutover_ok and bool(order)

    cited = _collect_ids(memo, plan_path.read_text(encoding="utf-8") if plan_path.exists() else "")
    fabricated = sorted(i for i in cited if i not in known_ids)
    checks["citations_resolvable"] = bool(memo) and len(cited) >= 8 and not fabricated
    checks["no_fabricated_citations"] = bool(memo) and not fabricated
    detail["cited"] = len(cited)
    detail["fabricated"] = fabricated[:10]

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

    loss = None
    if checks["plan_covers_services"] and checks["no_unsafe_sources"]:
        loss = 0.0
        for svc, cid in portfolio.items():
            loss += policy["service_priorities"][svc] * loss_by_cid[cid]
    detail["weighted_loss"] = loss
    detail["ref_loss"] = ref.get("weighted_loss")
    if loss is not None and ref.get("weighted_loss") is not None:
        checks["near_optimal_loss"] = loss <= float(ref["weighted_loss"]) * 1.05 + 1e-6
    else:
        checks["near_optimal_loss"] = False

    checks["matches_reference_portfolio"] = bool(ref.get("portfolio")) and portfolio == ref.get("portfolio")

    # Accept alternate portfolios listed in the frozen expected file
    alts = ref.get("alternate_portfolios") or []
    if not checks["matches_reference_portfolio"] and portfolio in alts:
        checks["matches_reference_portfolio"] = True

    weights = {
        "memo_exists": 3,
        "plan_exists": 3,
        "plan_covers_services": 4,
        "no_unsafe_sources": 12,
        "within_budget": 4,
        "schema_compatible": 4,
        "no_irreversible_migration": 6,
        "skew_compatible": 8,
        "cutover_feasible": 6,
        "citations_resolvable": 5,
        "no_fabricated_citations": 7,
        "memo_mentions_vault_vs_catalog": 4,
        "memo_mentions_uncertainty": 3,
        "memo_mentions_data_loss": 4,
        "memo_mentions_rejected": 4,
        "no_external_urls": 2,
        "preserves_originals": 4,
        "validation_gates_present": 4,
        "near_optimal_loss": 8,
        "matches_reference_portfolio": 5,
    }
    assert sum(weights.values()) == 100
    earned = sum(w for k, w in weights.items() if checks.get(k))
    reward = float(earned)
    if fabricated or not checks.get("memo_exists") or not checks.get("plan_exists"):
        reward = min(reward, 70.0)
    if unsafe or mig_bad:
        reward = min(reward, 80.0)
    if skew_bad:
        reward = min(reward, 78.0)
    if schema_bad:
        reward = min(reward, 82.0)
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
