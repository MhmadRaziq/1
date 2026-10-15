# Operation CLEARWATER — VALIDATION_REPORT

**Candidate ZIP:** `operation_clearwater/operation_clearwater_candidate.zip`  
**SHA-256:** `ebf52e2384b91fac72b69040e528d61b6f240bc767d28d23b2bc6dee2a1a0680`  
**Date (UTC):** 2026-10-15

This report separates **local, measured validation** from **platform-only checks**. A design-kit validation is **not** a Baby Carrot platform pass. The design kit itself is not the submitted task.

---

## Local validation (measured)

| Gate | Result | Evidence |
|---|---|---|
| Phase 1 prototype inspection | PASS | Kit microcosm 12/14 shortcuts diverge; scan/rehearsal nondifferentiating — fixed in full build (`PHASE1_INSPECTION.md`) |
| Causal world (16 services, 18 FCs) | PASS | `work/microcosm/gate.json` — 80 candidates |
| Dual oracle agreement (3 seeds) | PASS | seeds 42 / 1337 / 9001 — `scale_seeds.json` |
| Shortcut tournament (≥12 diverge) | PASS | **17/18** diverge incl. scan, rehearsal, open-indicator — `SHORTCUT_TOURNAMENT.csv` |
| One-fact counterfactuals (18 FCs) | PASS | **18/18** flipped — `DECISION_SENSITIVITY.csv` |
| WAL/timeline invariants | PASS | 0 errors on scaled worlds; 16 MiB LSN filenames |
| Ablations | PASS | 8/8 families change decisions — `ABLATION_RESULTS.csv` |
| Reference / noop | PASS | reference reward **100**; noop **0** |
| Negative mutants | PASS | **12/12** expected-negatives &lt;85; alternate accepted at 100 — `MUTATION_REPORT.md` |
| Rubric constraints | PASS | 100 pts; recommend **36**; IF **8**; each criterion ≤250 chars |
| Requirement coverage | PASS | 24/24 atomic rows mapped — `REQUIREMENT_COVERAGE.csv` |
| Static ZIP preflight | PASS | `python3 tools/preflight.py` → PASS; no author_only / modes in ZIP |
| Pytest/CTRF semantic suite | PASS | on reference extract |
| Docker offline image build | **NOT RUN** | `docker` binary absent in this environment |
| Strong-model cold trials | PASS (hardness) | mean **72.0** on 4 trials after held+open-indicator redesign — `STRONG_MODEL_TRIALS.md` |

### Exact local commands

```bash
cd /workspace/operation_clearwater
PYTHONHASHSEED=0 python3 tools/run_microcosm.py
PYTHONHASHSEED=0 python3 tools/run_scale.py
PYTHONHASHSEED=0 python3 tools/run_mutants.py
PYTHONHASHSEED=0 python3 tools/run_ablation.py
PYTHONHASHSEED=0 python3 tools/package_candidate.py
PYTHONHASHSEED=0 python3 tools/preflight.py operation_clearwater_candidate.zip
PYTHONHASHSEED=0 python3 tools/grade_cold_trials.py
```

### Hardness redesign (post cold-trial)

Prior cold trials A/B/C scored **100** on the pre-redesign packet (pure min priority×loss). Redesign:

1. `block_held_targets_inside_open_indicator_windows` policy
2. `AUDITLOG-LATEST` held + recovery target inside open indicator window; schema epoch 2 so the indicator rule is the sole reject
3. Reference selects `AUDITLOG-STABLE` (held, copy-ok, outside window)
4. Ignoring open-indicator flips portfolio to `AUDITLOG-LATEST` (shortcut diverge)

Re-grade of the same cold outputs against the hardened packet: **A=75, B=75, C=75, D=63, mean=72**. All four selected the unsafe freshest held target.

### Outstanding risks

- Docker offline build not executed locally (no daemon).
- `ignore_skew` shortcut remains non-differentiating on seed 42 (17/18 still ≥12).
- Design-kit / local gates ≠ platform Format/Audit/Similarity/Sweep pass.

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

**Local engineering gates: GO.** Strong-model hardness proxy (mean 72) clears the ≥0.99 redesign trigger. Remaining before platform sweeps: hosted Docker offline build, then upload and fix earliest failing stage with full regression.
