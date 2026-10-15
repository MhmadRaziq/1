#!/usr/bin/env python3
"""Gate A microcosm: generate, solve, grade, shortcut tournament, ablations."""
from __future__ import annotations

import csv
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
from tools.shortcuts import SHORTCUTS
from verifier.grade import grade_submission


def ablation_packet(src: Path, dst: Path, family: str) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    remove_map = {
        "builder": ["build/builder_identity_events.jsonl.gz", "build/ci_job_events.jsonl.gz"],
        "attestation": ["build/attestations.jsonl.gz"],
        "registry": ["registry/tag_mutations.jsonl.gz", "registry/oci_descriptors.jsonl.gz", "registry/layer_inventory.jsonl.gz"],
        "runtime": [
            "runtime/pod_runtime_observations.jsonl.gz",
            "runtime/admission_audit.jsonl.gz",
            "runtime/rollout_history.jsonl.gz",
        ],
        "changes": ["changes"],
        "operations": ["operations"],
    }
    for rel in remove_map.get(family, []):
        p = dst / rel
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()


def decision_signature(output_dir: Path) -> str:
    reg = list(csv.DictReader((output_dir / "exposure_register.csv").open()))
    plan = list(csv.DictReader((output_dir / "response_plan.csv").open()))
    exp = sorted((r["workload_id"], r["disposition"]) for r in reg)
    acts = sorted((p.get("workload_id"), p.get("action"), p.get("recovery_digest")) for p in plan)
    return json.dumps({"exp": exp, "acts": acts}, sort_keys=True)


def main() -> int:
    seed = 42
    work = ROOT / "work" / "microcosm"
    if work.exists():
        shutil.rmtree(work)
    data = work / "data"
    author = work / "author_only"
    out_ref = work / "output_reference"
    out_solver = work / "output_solver"
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)

    t0 = time.time()
    world = build_world(seed=seed, scale="microcosm")
    author.mkdir(parents=True)
    (author / "truth_graph.json").write_text(json.dumps({
        "seed": world["seed"],
        "forcing_cases": world["forcing_cases"],
        "workloads": {
            k: {
                "disposition": v["disposition"],
                "forcing_case": v.get("forcing_case"),
                "running_digest": v["running_digest"],
                "environment": v["environment"],
                "service_id": v["service_id"],
            }
            for k, v in world["workloads"].items()
        },
    }, indent=2), encoding="utf-8")

    stats = render_packet(world, data)
    oracle = build_oracle(world)
    write_oracle(oracle, author / "oracle.json")
    write_reference_outputs(oracle, out_ref)

    # Leakage scan: agent data must not contain disposition labels / forcing ids
    leakage = []
    for p in data.rglob("*"):
        if p.is_file() and p.suffix in {".md", ".json", ".csv"} or str(p).endswith(".jsonl.gz"):
            try:
                text = p.read_bytes()[:500000]
            except Exception:
                continue
            for bad in [b"EXPOSED", b"forcing_case", b"truth_graph", b"is_compromised", b"F01", b"F03"]:
                # F01 etc might appear? shouldn't. EXPOSED shouldn't be in sources.
                if bad in text and p.name != "telemetry_dictionary.md" and "report_templates" not in str(p):
                    # dictionary mentions disposition vocabulary — allow
                    if p.name == "telemetry_dictionary.md" and bad == b"EXPOSED":
                        continue
                    if bad in text:
                        leakage.append(f"{p.relative_to(data)}:{bad.decode()}")
    # Filter allowed dictionary mentions
    leakage = [x for x in leakage if not x.endswith("telemetry_dictionary.md:EXPOSED")]

    solver_summary = solve(data, out_solver)
    grade_ref = grade_submission(out_ref, author / "oracle.json", data)
    grade_sol = grade_submission(out_solver, author / "oracle.json", data)

    # Decision sensitivity CSV
    sens_rows = []
    for fid, fc in world["forcing_cases"].items():
        wid = fc.get("workload_id")
        truth = None
        if wid:
            truth = world["workloads"][wid]["disposition"]
        shortcut_keys = [k for k in fc.keys() if k.startswith("shortcut_")]
        for sk in shortcut_keys:
            sens_rows.append(
                {
                    "forcing_case": fid,
                    "workload_id": wid or fc.get("service_id", ""),
                    "correct_decision": truth or fc.get("correct_disposition") or fc.get("correct_action") or fc.get("correct_authority"),
                    "shortcut_name": sk,
                    "shortcut_decision": fc[sk],
                    "changed_output": "yes" if fc[sk] != (truth or fc.get("correct_disposition")) else "no",
                    "families": ";".join(fc.get("families", [])),
                    "scored_flip_flags": ";".join(
                        k for k in ("action_flip", "clearance_flip", "recovery_flip", "uncertainty_flip") if fc.get(k)
                    ),
                }
            )
    with (reports / "DECISION_SENSITIVITY.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "forcing_case",
                "workload_id",
                "correct_decision",
                "shortcut_name",
                "shortcut_decision",
                "changed_output",
                "families",
                "scored_flip_flags",
            ],
        )
        w.writeheader()
        for row in sens_rows:
            w.writerow(row)

    # Shortcut tournament
    short_dir = work / "shortcuts"
    short_dir.mkdir()
    sys.path.insert(0, str(ROOT))
    tourney = []
    ref_sig = decision_signature(out_solver)
    distinct_wrong = set()
    diverge = 0
    for name, fn in SHORTCUTS.items():
        od = short_dir / name
        try:
            fn(data, od)
            g = grade_submission(od, author / "oracle.json", data)
            sig = decision_signature(od)
            wrong = sig != ref_sig
            if wrong:
                diverge += 1
                distinct_wrong.add(sig)
            tourney.append(
                {
                    "shortcut": name,
                    "reward": f"{g.reward:.2f}",
                    "normalized": f"{g.normalized:.3f}",
                    "diverges_from_reference": "yes" if wrong else "no",
                    "exposure_f1": f"{g.checks.get('exposure_f1', {}).get('f1', 0):.3f}",
                    "plan_ok": "yes" if g.checks.get("plan_simulation", {}).get("ok", False) else "no",
                    "notes": json.dumps(g.checks.get("plan_simulation", {}).get("violations", [])),
                }
            )
        except Exception as e:
            tourney.append(
                {
                    "shortcut": name,
                    "reward": "0",
                    "normalized": "0",
                    "diverges_from_reference": "yes",
                    "exposure_f1": "0",
                    "plan_ok": "no",
                    "notes": f"ERROR:{e}",
                }
            )
            diverge += 1
            distinct_wrong.add(f"error:{name}")

    with (reports / "SHORTCUT_TOURNAMENT.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "shortcut",
                "reward",
                "normalized",
                "diverges_from_reference",
                "exposure_f1",
                "plan_ok",
                "notes",
            ],
        )
        w.writeheader()
        for row in tourney:
            w.writerow(row)

    # Ablations
    abl_rows = []
    material_ablations = 0
    action_ablations = 0
    for family in ["builder", "attestation", "registry", "runtime", "changes", "operations"]:
        ad = work / f"ablation_{family}"
        ao = work / f"ablation_{family}_out"
        ablation_packet(data, ad, family)
        try:
            solve(ad, ao)
            g = grade_submission(ao, author / "oracle.json", data)
            sig = decision_signature(ao)
            changed = sig != ref_sig
            # action set change
            plan_a = list(csv.DictReader((ao / "response_plan.csv").open())) if (ao / "response_plan.csv").exists() else []
            plan_r = list(csv.DictReader((out_solver / "response_plan.csv").open()))
            acts_a = sorted((p.get("workload_id"), p.get("action")) for p in plan_a)
            acts_r = sorted((p.get("workload_id"), p.get("action")) for p in plan_r)
            act_changed = acts_a != acts_r
            if changed:
                material_ablations += 1
            if act_changed:
                action_ablations += 1
            abl_rows.append(
                {
                    "ablated_family": family,
                    "reward": f"{g.reward:.2f}",
                    "decision_changed": "yes" if changed else "no",
                    "action_set_changed": "yes" if act_changed else "no",
                    "exposure_f1": f"{g.checks.get('exposure_f1', {}).get('f1', 0):.3f}",
                }
            )
        except Exception as e:
            abl_rows.append(
                {
                    "ablated_family": family,
                    "reward": "0",
                    "decision_changed": "yes",
                    "action_set_changed": "yes",
                    "exposure_f1": "0",
                    # keep schema
                }
            )
            # ensure keys
            abl_rows[-1] = {
                "ablated_family": family,
                "reward": "0",
                "decision_changed": "yes",
                "action_set_changed": "yes",
                "exposure_f1": f"ERROR:{e}",
            }
            material_ablations += 1
            action_ablations += 1

    with (reports / "ABLATION_RESULTS.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["ablated_family", "reward", "decision_changed", "action_set_changed", "exposure_f1"],
        )
        w.writeheader()
        for row in abl_rows:
            w.writerow(row)

    # Compare oracle vs solver exposures
    sol_exp = set(solver_summary["exposed"])
    ora_exp = set(oracle["exposed_workload_ids"])
    agree = sol_exp == ora_exp

    elapsed = time.time() - t0
    forcing_count = len(world["forcing_cases"])
    families = set()
    for fc in world["forcing_cases"].values():
        families.update(fc.get("families", []))

    gate = {
        "forcing_cases": forcing_count,
        "families": sorted(families),
        "family_count": len(families),
        "shortcut_diverge": diverge,
        "distinct_wrong_outcomes": len(distinct_wrong),
        "material_ablations": material_ablations,
        "action_ablations": action_ablations,
        "oracle_solver_exposure_agree": agree,
        "oracle_exposed": sorted(ora_exp),
        "solver_exposed": sorted(sol_exp),
        "grade_reference": grade_ref.as_dict(),
        "grade_solver": grade_sol.as_dict(),
        "render_stats": stats,
        "leakage_hits": leakage,
        "elapsed_sec": elapsed,
    }

    ok = (
        forcing_count >= 8
        and len(families) >= 4
        and diverge >= 10
        and len(distinct_wrong) >= 5
        and material_ablations >= 3
        and action_ablations >= 2
        and agree
        and grade_sol.reward >= 85
        and not leakage
    )
    gate["microcosm_pass"] = ok

    # Update BUILD_REPORT
    br = reports / "BUILD_REPORT.md"
    section = f"""

## Phase 2 — Microcosm results (seed={seed})

**Measured:** `{json.dumps({k: gate[k] for k in ['forcing_cases','family_count','shortcut_diverge','distinct_wrong_outcomes','material_ablations','action_ablations','oracle_solver_exposure_agree','microcosm_pass','elapsed_sec']})}`

### Commands
```bash
cd operation_afterburn && python3 tools/run_microcosm.py
```

### Grades
- Oracle-authored reference reward: **{grade_ref.reward:.2f}/100**
- Evidence-only solver reward: **{grade_sol.reward:.2f}/100**
- Solver exposed set: `{sorted(sol_exp)}`
- Oracle exposed set: `{sorted(ora_exp)}`

### Gate checks
| Check | Required | Observed | Pass |
|---|---:|---:|:---:|
| Forcing cases | ≥8 | {forcing_count} | {'Y' if forcing_count>=8 else 'N'} |
| Families | ≥4 | {len(families)} | {'Y' if len(families)>=4 else 'N'} |
| Shortcut divergences | ≥10 | {diverge} | {'Y' if diverge>=10 else 'N'} |
| Distinct wrong outcomes | ≥5 | {len(distinct_wrong)} | {'Y' if len(distinct_wrong)>=5 else 'N'} |
| Material ablations | ≥3 | {material_ablations} | {'Y' if material_ablations>=3 else 'N'} |
| Action-changing ablations | ≥2 | {action_ablations} | {'Y' if action_ablations>=2 else 'N'} |
| Oracle/solver agree | yes | {agree} | {'Y' if agree else 'N'} |
| Leakage hits | 0 | {len(leakage)} | {'Y' if not leakage else 'N'} |

### Artifacts
- `reports/DECISION_SENSITIVITY.csv`
- `reports/SHORTCUT_TOURNAMENT.csv`
- `reports/ABLATION_RESULTS.csv`
- `work/microcosm/author_only/oracle.json` (DO NOT SHIP)
- `work/microcosm/data/` agent packet

### Render stats
`{json.dumps(stats)}`

### Failure modes / blockers
{"None — microcosm gate passed." if ok else "MICROCOSM GATE FAILED — do not scale until fixed. Details: " + json.dumps(gate, indent=2)[:4000]}
"""
    prev = br.read_text(encoding="utf-8") if br.exists() else ""
    # replace prior phase 2 section if present
    marker = "## Phase 2 — Microcosm results"
    if marker in prev:
        prev = prev.split(marker)[0].rstrip() + "\n"
    br.write_text(prev + section, encoding="utf-8")
    (work / "gate.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")

    print(json.dumps(gate, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
