#!/usr/bin/env python3
"""Phase 4: multi-day scaled worlds on 3 seeds; dual-oracle agreement."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generator.pitr import XLOG_SEG_SIZE, parse_lsn, segments_covering, wal_filename
from generator.world import build_world, write_world
from oracle import oracle_dp, oracle_enumerate

SEEDS = [42, 1337, 9001]


def check_wal_invariants(data_dir: Path) -> list[str]:
    errors = []
    cats = json.loads((data_dir / "recovery_candidates.json").read_text())
    wals = json.loads((data_dir / "wal_archive.json").read_text())
    by_cand: dict[str, list] = {}
    for w in wals:
        if w.get("candidate_id"):
            by_cand.setdefault(w["candidate_id"], []).append(w)
    for c in cats:
        cid = c["candidate_id"]
        start = parse_lsn(c["backup_stop_lsn"])
        end = parse_lsn(c["recovery_target_lsn"])
        if end < start:
            errors.append(f"{cid}: target before stop")
        tl = int(c["timeline_id"])
        # Filenames that exist must match declared timeline+offset
        for w in by_cand.get(cid, []):
            off = parse_lsn(w["segment_start_lsn"])
            expect = wal_filename(int(w["timeline_id"]), off)
            if w["wal_filename"] != expect:
                errors.append(f"{cid}: bad wal filename {w['wal_filename']} != {expect}")
            span = parse_lsn(w["segment_end_lsn"]) - off + 1
            if span != XLOG_SEG_SIZE:
                errors.append(f"{cid}: segment span {span} != {XLOG_SEG_SIZE}")
    return errors


def main() -> int:
    results = []
    all_ok = True
    for seed in SEEDS:
        work = ROOT / "work" / f"seed_{seed}_scale"
        if work.exists():
            shutil.rmtree(work)
        data, author = work / "data", work / "author_only"
        world = build_world(seed=seed, scale_days=3)
        hashes = write_world(world, data, author)
        inv = check_wal_invariants(data)
        a = oracle_enumerate.analyze(data)
        b = oracle_dp.analyze(data)
        agree = (
            a.get("ok")
            and b.get("ok")
            and a["portfolio"] == b["portfolio"]
            and abs(a["weighted_loss"] - b["weighted_loss"]) < 1e-9
        )
        n_cand = len(json.loads((data / "recovery_candidates.json").read_text()))
        n_wal = len(json.loads((data / "wal_archive.json").read_text()))
        n_scans = len(json.loads((data / "malware_scans.json").read_text()))
        row = {
            "seed": seed,
            "ok": bool(a.get("ok") and b.get("ok") and agree and not inv),
            "dual_agree": agree,
            "wal_invariant_errors": len(inv),
            "candidates": n_cand,
            "wal_records": n_wal,
            "scan_records": n_scans,
            "weighted_loss": a.get("weighted_loss"),
            "effort": a.get("effort"),
            "portfolio": a.get("portfolio"),
            "source_hash_count": len(hashes),
        }
        results.append(row)
        (work / "gate.json").write_text(json.dumps(row, indent=2) + "\n")
        print("SEED", seed, "agree", agree, "inv_err", len(inv), "loss", a.get("weighted_loss"), "cand", n_cand, "wal", n_wal)
        if inv:
            print("  invariants", inv[:5])
        if not row["ok"]:
            all_ok = False

    out = ROOT / "reports" / "scale_seeds.json"
    out.write_text(json.dumps(results, indent=2) + "\n")
    print("GO" if all_ok else "NO-GO")
    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
