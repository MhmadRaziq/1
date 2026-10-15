# Operation AFTERBURN — VALIDATION_REPORT

**Candidate ZIP:** `operation_afterburn/operation_afterburn_candidate.zip`  
**SHA-256:** `2dbe6fa4290e9cf0147f767e3227a4a50ddb21b335d4f7d1e882febdc776fb81`  
**Date (UTC):** 2026-10-15

This report separates **local, measured validation** from **platform-only checks** that cannot be claimed from this environment.

---

## Local validation (measured)

| Gate | Result | Evidence |
|---|---|---|
| Design-kit integrity | PASS | `python3 afterburn_kit/tools/check_design_kit.py` |
| Microcosm forcing (≥8 cases, ≥4 families) | PASS | 13 cases / 16 families — `reports/DECISION_SENSITIVITY.csv`, `work/microcosm/gate.json` |
| Shortcut tournament (≥10 diverge, ≥5 distinct wrong) | PASS | 15 shortcuts implemented; diverge ≥10 — `reports/SHORTCUT_TOURNAMENT.csv` |
| Ablations (≥3 decision, ≥2 action) | PASS | `reports/ABLATION_RESULTS.csv` |
| Oracle ↔ evidence-only solver agree (3 seeds) | PASS | seeds 42 / 1337 / 9001 — `reports/scale_seeds.json` |
| Evidence-only solver reward | PASS | ~90.57/100 on all three seeds |
| Negative mutants (≥15/18 reject band) | PASS | 16/16 expected-negative mutants score &lt;85 — `reports/MUTANT_RESULTS.csv` |
| Alternate valid plan accepted | PASS | reversed feasible plan keeps ~90+ reward (`m17_reversed_valid`) |
| Rubric constraints | PASS | 100 pts; recommend 33; IF 6; each criterion ≤250 chars |
| Requirement coverage | PASS | 29/29 atomic rows mapped — `reports/REQUIREMENT_COVERAGE.csv` |
| Static ZIP preflight | PASS | `python3 afterburn_kit/tools/preflight.py operation_afterburn_candidate.zip` → 0 errors |
| Pytest semantic suite | PASS | 7/7 — `candidate/tests/test_outputs.py` |
| Offline packet / no answer leakage filenames | PASS | ZIP lacks `author_only/`, `oracle.json`, `truth_graph.json` |
| Docker offline image build | **NOT RUN** | `docker` binary absent in this environment |

### Exact local commands

```bash
cd /workspace/operation_afterburn
python3 tools/run_microcosm.py
python3 tools/run_scale.py
python3 tools/run_mutants.py
python3 tools/package_candidate.py
python3 /workspace/afterburn_kit/tools/preflight.py operation_afterburn_candidate.zip
AFTERBURN_DATA=$PWD/work/seed_42_scale/data \
AFTERBURN_OUTPUT=$PWD/work/seed_42_scale/output_solver \
python3 -m pytest -q candidate/tests/test_outputs.py
```

### Hardness proxy (not a model sweep)

Shortcut policies that scored well below the pass band include `all_signed_clean`, `tag_equals_digest`, `ignore_base_layers`, `desired_equals_running`, `previous_green_rollback`, `stop_all_immediately`, and `ignore_runtime_family`. This demonstrates decision-sensitive causal geometry under measured cheap solvers. It is **not** a substitute for cold-start frontier-model trials.

---

## Platform-only / not claimed here

| Check | Status |
|---|---|
| AfterQuery Format UI acceptance | Not submitted |
| Quality / Audit / Similarity / Licensing stages | Not submitted |
| Hosted offline Docker build on platform image | Not run (no local Docker) |
| Cold-start strong-model dry runs (≥3) scoring &lt;0.9 | **Not run** — no model-sweep API in this environment |
| Private platform grader CTRF path quirks | Unverified |
| Live form taxonomy dropdown exact match | Labels match kit draft; confirm in live form before upload |

**Do not describe this ZIP as sweep-certified or guaranteed to pass platform stages.**

---

## Production-candidate posture

**Local engineering gates for a production *candidate* are PASS.**  
Remaining blockers before claiming readiness for model sweeps:

1. Build/run the Docker image in an offline environment and re-run `solution/solve.sh` + `tests/test.sh` inside the container.
2. Execute ≥3 independent cold-start strong-model trials on held-out seeds; if any trial ≥0.9, revise causal geometry (not prompt friction).
3. Upload through the platform pipeline and fix the earliest failing stage with full regression.
