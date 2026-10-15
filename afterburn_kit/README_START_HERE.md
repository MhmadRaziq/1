# Baby Carrot — Gold-Standard Task Design Kit v1
## Project: Compromised Build Runner / Production Exposure & Safe Recovery
**Status:** COMPLETE DESIGN KIT / IMPLEMENTATION BLUEPRINT — **NOT** a finished AfterQuery submission, and **NOT** sweep-certified.
**Benchmark intent:** A realistic senior software-supply-chain incident-response investigation with measurable evidence reconstruction, causal validation, and safe operational decisions.

### The core idea
A trusted CI runner was compromised for a bounded period. Security leadership needs to know which deployed production workloads actually contain affected build output, which alarming matches are false positives, and what minimum safe response prevents continued exposure while preserving critical availability. The answer cannot be read from an SBOM, a tag, a signature, or a single audit feed. Reconstruct actual materialization and runtime deployment from several independently plausible sources; apply the organization's signed exception/change history; then propose a sequenced response that is feasible at the cutoff.

### Why this can be harder than Enterprise credential-hop containment
The reference task had a seed, large re-keyed telemetry, corroboration, historical clearance, and containment scope. Keep those strengths. Add a multi-layer artifact graph (source/build/attestation/registry/image/platform/runtime), competing evidence authority, a difference between *suspect build*, *reachable deployed code*, and *safe rollback*, plus mutually dependent response decisions. The new difficulty is in reconstructing governing state, not in the number of rows.

### What is included
- `01_strategy/`: original reference autopsy, design constraints and reject tests.
- `02_scenario/`: professional task and hard case geometry, with a solver-facing prompt draft.
- `03_data_architecture/`: source packet, scale plan, causality, provenance, realism.
- `04_oracle_verifier/`: independent ground-truth strategy, grader contracts, mutations.
- `05_rubric_audit/`: rubric design, requirement coverage, mutually compatible criteria.
- `06_quality_format/`: exact previous platform failure prevention, taxonomy, licensing.
- `07_red_team/`: ablations, shortcut tournament, held-out evaluation, thresholds.
- `08_build/`: execution sequence, submission gating, Cursor master prompt.
- `templates/`: solver output templates and sample source record shapes.
- `tools/preflight.py`: runnable static ZIP preflight (not a substitute for platform QA).
- `author_only/`: internal forcing cases, mappings and challenge ledger templates; never ship this folder in the final task.
- `reference/`: analyzed structure of the user-provided credential-hop reference and public specification research.

### Hard boundaries
1. **No guarantee** of passing proprietary Quality, Audit, Similarity, Licensing or model sweeps; only the platform can decide.
2. The kit does **not** contain a full real evidence dataset, oracle, reference solution or production-ready verifier. Building and testing those is the next implementation phase.
3. Do not submit this ZIP to AfterQuery. Build a separate task ZIP with the prescribed root structure after all gates pass.
4. Do not copy the reference task's incident seed, synthetic identifiers, rubric answers, or data directly; it is a structural reference, not reusable truth.
5. Do not try to make the task unsolvable, intentionally ambiguous, or unfair. Target **hard but fully solvable**, with one defensible adjudication for every scored factual claim.

### Go/no-go in one line
**GO** only if (i) oracle reproduces truth on 3 independent seeds, (ii) no single file reveals the target set, (iii) ≥8 decision-sensitive forcing cases span ≥4 reasoning families, (iv) ≥3 source ablations change a scored decision, (v) ≥10 shortcuts yield ≥5 distinct wrong outcomes, (vi) local grader accepts alternate valid solutions and rejects mutants, (vii) full rubric coverage is proven, and (viii) an independent strong-model trial demonstrates real weakness rather than mere prompt friction.
