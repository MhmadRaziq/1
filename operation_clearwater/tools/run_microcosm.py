#!/usr/bin/env python3
"""Phase 2/3 gate: build microcosm, dual-oracle agreement, shortcuts, counterfactuals."""
from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generator.world import FORCING_CASES, apply_counterfactual, build_world, write_world
from oracle import oracle_dp, oracle_enumerate

WORK = ROOT / "work" / "microcosm"


def portfolio_key(p: dict) -> tuple:
    return tuple(sorted(p.items()))


def run_shortcuts(data_dir: Path, ref: dict) -> list[dict]:
    shortcuts = {
        "ignore_vault_receipt": {"vault_unavailable", "vault_hold_blocks_copy"},
        "ignore_digest": {"vault_digest_mismatch"},
        "ignore_key": {"key_unavailable"},
        "ignore_attestation": {"attestation_untrusted"},
        "ignore_scan": {"scan_not_current"},
        "ignore_restore_rehearsal": {"rehearsal_not_usable"},
        "ignore_wal_continuity": {"wal_chain_not_continuous"},
        "ignore_timeline_history": {"timeline_incompatible"},
        "ignore_compromise_indicator": {"compromised_replay"},
        "ignore_capacity": {"budget"},
        "ignore_schema_compatibility": {"schema"},
        "ignore_business_priority": {"priority"},
        "treat_legal_hold_as_deny": {"LEGAL_HOLD_SHORTCUT"},  # special-cased below
        "ignore_migration_coupling": {"migration"},
        "ignore_all_evidence": {
            "vault_unavailable", "vault_digest_mismatch", "key_unavailable",
            "attestation_untrusted", "scan_not_current", "rehearsal_not_usable",
            "wal_chain_not_continuous", "timeline_incompatible", "compromised_replay",
            "vault_hold_blocks_copy",
        },
        "ignore_all_constraints": {
            "vault_unavailable", "vault_digest_mismatch", "key_unavailable",
            "attestation_untrusted", "scan_not_current", "rehearsal_not_usable",
            "wal_chain_not_continuous", "timeline_incompatible", "compromised_replay",
            "vault_hold_blocks_copy", "budget", "schema", "priority", "migration",
        },
    }
    rows = []
    for name, ignore in shortcuts.items():
        if name == "treat_legal_hold_as_deny":
            # Shortcut: treat any legal_hold as restore denial (incorrect for copy-ok).
            receipts = json.loads((data_dir / "vault_receipts.json").read_text())
            original = (data_dir / "vault_receipts.json").read_text()
            for r in receipts:
                if r.get("legal_hold"):
                    r["copy_restore_allowed"] = False
            (data_dir / "vault_receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
            try:
                v = oracle_enumerate.analyze(data_dir)
            finally:
                (data_dir / "vault_receipts.json").write_text(original)
        else:
            v = oracle_enumerate.analyze(data_dir, ignore=ignore)
        if not v.get("ok"):
            rows.append({
                "shortcut": name,
                "ok": False,
                "different_services": len(ref["portfolio"]),
                "invalid_sources": "",
                "same_portfolio": False,
                "true_weighted_loss": "",
                "reference_weighted_loss": ref["weighted_loss"],
            })
            continue
        differing = sum(v["portfolio"].get(s) != ref["portfolio"].get(s) for s in ref["portfolio"])
        invalid = sum(1 for cid in v["portfolio"].values() if not ref["candidates"][cid]["valid"])
        rows.append({
            "shortcut": name,
            "ok": True,
            "different_services": differing,
            "invalid_sources": invalid,
            "same_portfolio": differing == 0,
            "true_weighted_loss": v["weighted_loss"],
            "reference_weighted_loss": ref["weighted_loss"],
        })
    return rows


def run_counterfactuals(data_dir: Path, author_dir: Path, baseline: dict) -> list[dict]:
    forcing = json.loads((author_dir / "forcing_cases.json").read_text())
    rows = []
    # Snapshot data
    snap = ROOT / "work" / "microcosm" / "_snap"
    if snap.exists():
        shutil.rmtree(snap)
    shutil.copytree(data_dir, snap)
    for fc in FORCING_CASES:
        # restore
        if data_dir.exists():
            shutil.rmtree(data_dir)
        shutil.copytree(snap, data_dir)
        summary = apply_counterfactual(data_dir, fc.case_id, forcing)
        altered = oracle_enumerate.analyze(data_dir)
        flipped = False
        detail = ""
        if not altered.get("ok"):
            flipped = True
            detail = altered.get("error", "infeasible")
        else:
            flipped = portfolio_key(altered["portfolio"]) != portfolio_key(baseline["portfolio"])
            if not flipped:
                # cutover-only cases: compare cutover string
                if fc.scored_decision == "cutover_order":
                    flipped = altered["cutover"] != baseline["cutover"]
                if fc.scored_decision == "fair_grading":
                    # budget expand should add or change alternate set
                    flipped = (
                        altered["feasible_portfolios"] != baseline["feasible_portfolios"]
                        or portfolio_key(altered["portfolio"]) != portfolio_key(baseline["portfolio"])
                        or len(altered.get("alternate_portfolios", [])) != len(baseline.get("alternate_portfolios", []))
                    )
            detail = json.dumps(altered.get("portfolio", {}))
        rows.append({
            "forcing_case": fc.case_id,
            "candidate_id": forcing[fc.case_id]["candidate_id"],
            "mode": fc.mode,
            "scored_decision": fc.scored_decision,
            "summary": summary,
            "decision_flipped": flipped,
            "detail": detail[:200],
        })
    # restore pristine
    if data_dir.exists():
        shutil.rmtree(data_dir)
    shutil.copytree(snap, data_dir)
    return rows


def main() -> int:
    if WORK.exists():
        shutil.rmtree(WORK)
    data = WORK / "data"
    author = WORK / "author_only"
    world = build_world(seed=42, scale_days=1)
    hashes = write_world(world, data, author)

    a = oracle_enumerate.analyze(data)
    b = oracle_dp.analyze(data)
    print("Oracle A ok", a.get("ok"), "portfolio", a.get("portfolio"))
    print("Oracle B ok", b.get("ok"), "portfolio", b.get("portfolio"))
    print("weighted", a.get("weighted_loss"), b.get("weighted_loss"), "effort", a.get("effort"), b.get("effort"))
    print("feasible A", a.get("feasible_portfolios"), "B beam", b.get("feasible_portfolios"))
    # Prefer the better (lower loss, then effort, then id) and require the other
    # to match that optimum — catches incomplete search on either side.
    agree = False
    ref = a
    if a.get("ok") and b.get("ok"):
        key_a = (a["weighted_loss"], a["effort"], portfolio_key(a["portfolio"]))
        key_b = (b["weighted_loss"], b["effort"], portfolio_key(b["portfolio"]))
        ref = a if key_a <= key_b else b
        other = b if ref is a else a
        agree = (
            abs(ref["weighted_loss"] - other["weighted_loss"]) < 1e-9
            and ref["effort"] == other["effort"]
            and portfolio_key(ref["portfolio"]) == portfolio_key(other["portfolio"])
        )
        # If one found a strictly better portfolio, force the other to re-check
        # by adopting the champion only when both certify the same key.
        if not agree and key_a != key_b:
            print("ORACLE_GAP champion", "A" if ref is a else "B", "loss", ref["weighted_loss"])
    print("DUAL_ORACLE_AGREE", agree)
    a = ref  # use champion as reference for shortcuts/counterfactuals

    if not a.get("ok"):
        print("FATAL: enumerate oracle failed", a.get("error"))
        # debug missing services
        for cid, v in a.get("candidates", {}).items():
            if not v["valid"]:
                pass
        by_svc = {}
        for cid, v in a.get("candidates", {}).items():
            by_svc.setdefault(v["service"], []).append((cid, v["valid"], v["reasons"]))
        for s, items in sorted(by_svc.items()):
            valids = [i for i in items if i[1]]
            print(f"  {s}: {len(valids)} valid / {len(items)}")
            if not valids:
                print("    examples", items[:3])
        return 1

    shortcuts = run_shortcuts(data, a)
    diverging = sum(1 for r in shortcuts if not r["same_portfolio"])
    print(f"SHORTCUTS {len(shortcuts)} diverging {diverging}")
    for r in shortcuts:
        print(f"  {r['shortcut']}: different={r['different_services']} same={r['same_portfolio']}")

    cf = run_counterfactuals(data, author, a)
    flips = sum(1 for r in cf if r["decision_flipped"])
    print(f"COUNTERFACTUALS {len(cf)} flipped {flips}")
    for r in cf:
        print(f"  {r['forcing_case']} {r['mode']} flipped={r['decision_flipped']} :: {r['summary']}")

    # Write reports
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    with (reports / "SHORTCUT_TOURNAMENT.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(shortcuts[0].keys()))
        w.writeheader()
        w.writerows(shortcuts)
    with (reports / "DECISION_SENSITIVITY.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cf[0].keys()))
        w.writeheader()
        w.writerows(cf)

    gate = {
        "services": 16,
        "candidates": len(a["candidates"]),
        "dual_oracle_agree": agree,
        "shortcuts_tested": len(shortcuts),
        "shortcuts_diverging": diverging,
        "forcing_cases": len(cf),
        "forcing_flipped": flips,
        "source_hashes": hashes,
        "portfolio": a["portfolio"],
        "weighted_loss": a["weighted_loss"],
        "effort": a["effort"],
        "go": agree and diverging >= 12 and flips >= 17,
    }
    (WORK / "gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    print("GATE", json.dumps(gate, indent=2))
    print("GO" if gate["go"] else "NO-GO")
    return 0 if gate["go"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
