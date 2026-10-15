#!/usr/bin/env python3
"""Generate scaled packets for seeds and verify oracle/solver agreement."""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generator.render import render_packet
from generator.world import build_world
from oracle.adjudicate import build_oracle, write_oracle, write_reference_outputs
from solver.evidence_solver import solve
from verifier.grade import grade_submission


def run_seed(seed: int, scale: str = "scale") -> dict:
    work = ROOT / "work" / f"seed_{seed}_{scale}"
    if work.exists():
        shutil.rmtree(work)
    data = work / "data"
    author = work / "author_only"
    out = work / "output_solver"
    author.mkdir(parents=True)
    t0 = time.time()
    world = build_world(seed=seed, scale=scale)
    stats = render_packet(world, data)
    oracle = build_oracle(world)
    write_oracle(oracle, author / "oracle.json")
    write_reference_outputs(oracle, work / "output_reference")
    summary = solve(data, out)
    grade = grade_submission(out, author / "oracle.json", data)
    agree = set(summary["exposed"]) == set(oracle["exposed_workload_ids"])
    # package bytes
    total = sum(p.stat().st_size for p in data.rglob("*") if p.is_file())
    return {
        "seed": seed,
        "scale": scale,
        "agree": agree,
        "reward": grade.reward,
        "exposed": summary["exposed"],
        "oracle_exposed": oracle["exposed_workload_ids"],
        "stats": stats,
        "bytes": total,
        "elapsed_sec": time.time() - t0,
        "data_dir": str(data),
        "oracle_path": str(author / "oracle.json"),
    }


def main() -> int:
    results = []
    for seed in (42, 1337, 9001):
        results.append(run_seed(seed, "scale"))
    reports = ROOT / "reports"
    (reports / "scale_seeds.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    ok = all(r["agree"] and r["reward"] >= 85 for r in results)
    br = reports / "BUILD_REPORT.md"
    section = f"""

## Phase 3 — Scale (3 seeds)

| Seed | Agree | Reward | Bytes | Seconds |
|---:|:---:|---:|---:|---:|
""" + "\n".join(
        f"| {r['seed']} | {r['agree']} | {r['reward']:.1f} | {r['bytes']} | {r['elapsed_sec']:.2f} |"
        for r in results
    ) + f"""

Scale gate: **{'PASS' if ok else 'FAIL'}**
"""
    prev = br.read_text(encoding="utf-8")
    marker = "## Phase 3 — Scale"
    if marker in prev:
        prev = prev.split(marker)[0].rstrip() + "\n"
    br.write_text(prev + section, encoding="utf-8")
    print(json.dumps(results, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
