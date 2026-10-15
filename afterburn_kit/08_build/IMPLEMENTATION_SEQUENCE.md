# Build runbook — stage gates and outputs

## Gate A — concept proof (before building millions of rows)
A1. Write one-page professional incident memo; ask whether a real security engineering director would send it.
A2. Write a sealed causal truth graph for 20 services and 8 forcing cases.
A3. Render 6 source families and verify all cases require actual cross-source reasoning.
A4. Run shortcut tournament and ablations; if not decision-sensitive, reject and redesign.
**Artifact:** `author_only/forcing_cases.csv`, causal graph, shortcut results.

## Gate B — synthetic source generation
B1. Build deterministic generator with seed, timestamps, coherent IDs, referential integrity and real-world schemas.
B2. Generate unrelated routine activity with authentic distributions, not repeated random filler.
B3. Build at least 2 held-out seeds; ensure no answer leakage.
B4. Package all source files with checksums and field dictionary.
**Artifact:** `environment/data/` with fully offline packet and manifest.

## Gate C — independent oracle and reference
C1. Implement oracle from world-state truth and a separate evidence-only solver.
C2. Compare decisions, evidence paths, response feasibility and ambiguity.
C3. Run on 3 seeds; measure runtime/memory.
**Artifact:** `solution/solve.py`, `solution/solve.sh`, author truth and tests.

## Gate D — output contract and grader
D1. Freeze the three report templates; use professional field names and reasonable enums.
D2. Implement schema/contract tests and source-grounded semantic scoring.
D3. Implement response-plan state simulator and alternate-valid-plan acceptance.
D4. Run 18 mutants, no-op, tampered evidence refs and reordered valid plans.
**Artifact:** `tests/test_outputs.py`, `tests/test.sh`, `tests/test_weights.json` if required.

## Gate E — rubric / taxonomy / format
E1. Write 30–42 focused criteria totaling 100, recommendation ≥30, IF 1–10.
E2. Build atomic requirement map; verify all prompt + worksheet instructions covered.
E3. Pairwise conflict review; one fully correct answer must satisfy all criteria.
E4. Sync taxonomy to the live form; remove unsupported TOML keys and leaked author files.
E5. Run `python tools/preflight.py candidate.zip`.
**Artifact:** root `rubrics.json`, `task_card.md`, `task.toml`, `authoring/requirement_map.csv`.

## Gate F — local build / quality / sweep preflight
F1. Test actual Docker image and shell in the target-like offline environment.
F2. Run full oracle and grader from clean extraction; record reward, CTRF, runtime.
F3. Run independent quality review: 'workplace task or ETL recipe?'.
F4. Run shortcut/ablation and cold-start strong-model trials; reject shallow task.
F5. Freeze source hashes; final zip contains only allowed task files.

## Gate G — submit and iterate
G1. Upload a single validated ZIP.
G2. Record each platform stage and verbatim feedback; do not infer stages not reached.
G3. Fix earliest failing stage and run full regression matrix.
G4. If sweep fails, inspect model trial outputs and reward geometry; do not blindly tighten literal tests.
G5. Do not claim final acceptance until the platform reports it.

## Stop conditions
- Oracle and reference disagree: stop.
- Any case requires missing evidence: stop or classify explicitly unresolved.
- An alternate valid plan fails verifier: stop.
- Rubric coverage incomplete or contradictory: stop.
- Prompt reveals exact algorithm: stop.
- Shortcuts pass at high reward: stop and redesign.
