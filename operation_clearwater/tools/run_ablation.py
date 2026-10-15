#!/usr/bin/env python3
"""Ablate one evidence family at a time; record portfolio/decision changes."""
from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oracle import oracle_enumerate

SEED = ROOT / "work" / "seed_42_scale" / "data"


def main() -> int:
    base = oracle_enumerate.analyze(SEED)
    rows = []
    families = {
        "vault_receipts": "vault_receipts.json",
        "attestations": "build_attestations.json",
        "kms_grants": "kms_grants.json",
        "wal_archive": "wal_archive.json",
        "timeline_history": "timeline_history.json",
        "malware_scans": "malware_scans.json",
        "restore_rehearsals": "restore_rehearsals.json",
        "intrusion_indicators": "intrusion_indicators.json",
    }
    tmp = ROOT / "work" / "_ablation"
    for fam, fname in families.items():
        if tmp.exists():
            shutil.rmtree(tmp)
        shutil.copytree(SEED, tmp)
        # Empty the family (keep structure as empty list) — should force deferrals / infeasibility / change
        (tmp / fname).write_text("[]\n")
        alt = oracle_enumerate.analyze(tmp)
        changed = (not alt.get("ok")) or (alt.get("portfolio") != base["portfolio"])
        rows.append({
            "family": fam,
            "still_ok": bool(alt.get("ok")),
            "decision_changed": changed,
            "error": alt.get("error", ""),
            "loss": alt.get("weighted_loss", ""),
        })
        print(fam, "ok", alt.get("ok"), "changed", changed, alt.get("error", ""))
    out = ROOT / "reports" / "ABLATION_RESULTS.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    changed_n = sum(1 for r in rows if r["decision_changed"])
    print("changed_families", changed_n)
    print("GO" if changed_n >= 5 else "NO-GO")
    return 0 if changed_n >= 5 else 2


if __name__ == "__main__":
    raise SystemExit(main())
