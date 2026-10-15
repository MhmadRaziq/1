# Operation CLEARWATER — VALIDATION_REPORT

**Candidate ZIP:** `operation_clearwater/operation_clearwater_candidate.zip`  
**SHA-256:** `fa37e50bfa5a1a87b4d8186e4c4d54701f4ab0cd034c764ba45b99372fcc7558`  
**Date (UTC):** 2026-10-15

This report separates **local, measured validation** from **platform-only checks**. A design-kit validation is **not** a Baby Carrot platform pass. The design kit itself is not the submitted task.

---

## Local validation (measured)

| Gate | Result | Evidence |
|---|---|---|
| Phase 1 prototype inspection | PASS | Kit microcosm 12/14 shortcuts diverge; scan/rehearsal nondifferentiating — fixed in full build (`PHASE1_INSPECTION.md`) |
| Causal world (16 services, 18 FCs) | PASS | `work/microcosm/gate.json` — 80 candidates |
| Dual oracle agreement (3 seeds) | PASS | seeds 42 / 1337 / 9001 — `scale_seeds.json` |
| Shortcut tournament (≥12 diverge) | PASS | **16/16** diverge incl. scan + rehearsal — `SHORTCUT_TOURNAMENT.csv` |
| One-fact counterfactuals (18 FCs) | PASS | **18/18** flipped — `DECISION_SENSITIVITY.csv` |
| WAL/timeline invariants | PASS | 0 errors on scaled worlds; 16 MiB LSN filenames |
| Ablations | PASS | 8/8 families change decisions — `ABLATION_RESULTS.csv` |
| Reference / noop | PASS | reference reward **100** / **1.0**; noop **0** |
| Negative mutants | PASS | 11/12 expected-negatives &lt;85; alternate accepted at 100 — `MUTATION_REPORT.md` |
| Rubric constraints | PASS | 100 pts; recommend **36**; IF **8**; each criterion ≤250 chars |
| Requirement coverage | PASS | 24/24 atomic rows mapped — `REQUIREMENT_COVERAGE.csv` |
| Static ZIP preflight | PASS | `python3 tools/preflight.py …` → PASS; no author_only / modes in ZIP |
| Pytest/CTRF semantic suite | PASS | 7/7 on reference extract |
| Docker offline image build | **NOT RUN** | `docker` binary absent in this environment |
| Strong-model cold trials | IN PROGRESS | See `STRONG_MODEL_TRIALS.md` |

### Exact local commands

```bash
cd /workspace/operation_clearwater
PYTHONHASHSEED=0 python3 tools/run_microcosm.py
PYTHONHASHSEED=0 python3 tools/run_scale.py
PYTHONHASHSEED=0 python3 tools/run_mutants.py
PYTHONHASHSEED=0 python3 tools/run_ablation.py
PYTHONHASHSEED=0 python3 tools/package_candidate.py
PYTHONHASHSEED=0 python3 tools/preflight.py operation_clearwater_candidate.zip
```

### Hardness proxy (not a model sweep)

All 16 measured shortcut policies select a different portfolio from the reference on seed 42, including `ignore_scan` and `ignore_restore_rehearsal` (the prototype failures). This demonstrates decision-sensitive causal geometry. It is **not** a substitute for cold-start frontier-model trials.

---

## Platform-only / not claimed here

| Check | Status |
|---|---|
| AfterQuery Format UI acceptance | Not submitted |
| Quality / Audit / Similarity / Licensing stages | Not submitted |
| Hosted offline Docker build on platform image | Not run (no local Docker) |
| Live form taxonomy dropdown exact match | Labels match kit draft; confirm in live form before upload |

**Do not describe this ZIP as sweep-certified or guaranteed to pass platform stages.**

---

## Production-candidate posture

**Local engineering gates for a production *candidate* are PASS** (pending completion of recorded strong-model trial scores).  
Remaining before claiming readiness for model sweeps:

1. Build/run the Docker image offline and re-run `solution/solve.sh` + `tests/test.sh` inside the container.
2. Record ≥4 independent cold-start strong-model trials; if mean ≥0.99, revise causal geometry.
3. Upload through the platform pipeline and fix the earliest failing stage with full regression.
