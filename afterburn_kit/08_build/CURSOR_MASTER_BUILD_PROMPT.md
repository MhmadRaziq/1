# Cursor master build prompt — copy this entire prompt into a coding agent

You are the lead security-data engineer and independent benchmark QA architect. Work in the attached Baby Carrot design-kit workspace. Your job is to implement **Operation AFTERBURN**, a completely self-contained, realistic senior DFIR software-supply-chain investigation. Read every document in the kit first, especially `README_START_HERE.md`, `03_data_architecture/CAUSAL_TRUTH_MODEL.md`, `04_oracle_verifier/ORACLE_AND_GRADER_SPEC.md`, `06_quality_format/QUALITY_AND_FORMAT_GATES.md` and `07_red_team/HARDNESS_PROTOCOL.md`.

**Non-negotiable:** Do not make the task artificially hard through obscurity, missing evidence, ambiguous rules, over-specific output formatting, hidden external dependencies, answer leakage, or brittle tests. Do not claim sweep success without actual sweep results. Design novel causal evidence relationships that remain independently solvable.

### Work in gated phases
1. **Plan:** Inspect the credential-hop reference if available, then propose the new task world model, professional prompt, source list, challenge ledger and resource budget. Do not generate large data yet.
2. **Microcosm:** Implement 20 services, 8–12 decision-sensitive forcing cases, independent evidence families, sealed oracle and source renderer. Prove ≥10 shortcuts diverge and ≥3 ablations change decisions. Report exact outputs and failure modes. Do not proceed if proof fails.
3. **Scale:** Generate realistic source packet with authentic SLSA/in-toto/OCI-style semantics, cross-architecture indices, deployment realization, and operational constraints. All synthetic; no external network at solve time.
4. **Independent reference:** Build an evidence-only solver separate from the generator/oracle. It must not import hidden truth or private labels.
5. **Verifier:** Write format tests, evidence-grounded semantic tests and a response-plan simulator accepting every feasible safe plan. Reject empty, overbroad, fabricated, time-invalid and unsafe solutions. Measure partial reward; do not merely test existence.
6. **Rubric:** 100 positive points, recommendation ≥30, instruction following 1–10, ≤250 chars/criterion. Atomic requirement coverage must be 100%. Review all pairs for conflicts. Task card taxonomy must match the submission form exactly.
7. **Quality:** Rewrite any prompt section that gives a join recipe, case IDs, expected counts, decision gates or exact optimization algorithm. Keep a genuine workplace handoff and only three natural artifacts. Avoid a semantic-index sidecar.
8. **Red team:** 18 mutants, 12–16 shortcut policies, source ablations, 3 independent seeds, cold-start strong-model dry runs. A task that a strong model solves at ≥0.9 is not ready; revise the causal geometry.
9. **Packaging:** Generate root-level task ZIP, tests, solution, Dockerfile, manifest, rubric and card. Run `tools/preflight.py`. Clean extraction, offline Docker, and full reference/verifier tests must pass.

### Output required at each phase
- A `BUILD_REPORT.md` with verified facts, commands, hashes, performance, coverage and failures.
- A `DECISION_SENSITIVITY.csv` with each forcing case's correct and shortcut decisions and changed outputs.
- A `SHORTCUT_TOURNAMENT.csv` and `ABLATION_RESULTS.csv` with measured outcomes.
- A `REQUIREMENT_COVERAGE.csv` mapping every atomic instruction to rubric criteria.
- A `VALIDATION_REPORT.md` separating local validation from platform-only checks.

### Engineering behavior
Work iteratively and test every claim. If a challenge doesn't flip a scored decision, delete or strengthen it. If a grader rejects a correct alternative, repair it. If the task is reducible to one simple query, redesign the data relationships. Never hide the expected answer in agent-visible source files. Keep all author-only truth outside the agent environment. When unsure of standard semantics, verify against official source and narrow the supported subset; don't invent an incorrect rule.

### Deliverable
Only when all local gates pass: a production candidate ZIP and validation report. Otherwise deliver the prototype, precise blockers and next engineering steps. Never describe an untested candidate as 'guaranteed to pass'.
