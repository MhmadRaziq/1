# Operation AFTERBURN — BUILD_REPORT

**Status:** Local production-candidate gates PASS (platform sweeps NOT run).  
**Date (UTC):** 2026-10-15  
**Branch:** `cursor/operation-afterburn-a10e`  
**Credential-hop reference:** Not present in workspace; structural facts from `afterburn_kit/reference/REFERENCE_PACKAGE_FACTS.md` only.

---

## Phase 1 — Plan

See world model, source families, challenge ledger and resource budget as originally planned (Northline Commerce / helix-ci-prod / 20 services / 12 forcing cases). No large data generated in this phase.

---

## Phase 2 — Microcosm (seed=42) — PASS

**Command:** `python3 tools/run_microcosm.py`

| Check | Required | Observed |
|---|---:|---:|
| Forcing cases | ≥8 | 13 |
| Families | ≥4 | 16 |
| Shortcut divergences | ≥10 | 15 |
| Distinct wrong outcomes | ≥5 | 12 |
| Material ablations | ≥3 | 5 |
| Action-changing ablations | ≥2 | 5 |
| Oracle/solver exposure agree | yes | yes |
| Leakage hits in packet | 0 | 0 |
| Evidence-only solver reward | ≥85 | 90.57 |

Artifacts: `DECISION_SENSITIVITY.csv`, `SHORTCUT_TOURNAMENT.csv`, `ABLATION_RESULTS.csv`.

Highest shortcut reward observed: **82.57** (`stop_all_immediately` / `ignore_quorum`) — below pass band.  
`all_signed_clean` → 54.0; `tag_equals_digest` → 29.5; `ignore_base_layers` → 44.0; `previous_green_rollback` → 74.57.

---


## Phase 3 — Scale (3 seeds)

| Seed | Agree | Reward | Bytes | Seconds |
|---:|:---:|---:|---:|---:|
| 42 | True | 90.6 | 122601 | 0.06 |
| 1337 | True | 90.6 | 123034 | 0.05 |
| 9001 | True | 90.6 | 123406 | 0.05 |

Scale gate: **PASS**
