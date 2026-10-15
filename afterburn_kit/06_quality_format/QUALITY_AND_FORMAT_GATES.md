# Quality + Format + Audit — explicit failure-prevention guide

## Format (run before any expensive build/sweep)
- Root contains `instruction.md`, `task_card.md`, `task.toml`, `rubrics.json`, `environment/`, `solution/`, `tests/`; **no parent wrapper**.
- Environment builds offline and copies complete source packet to the intended paths; no external data dependencies.
- `task.toml` uses current supported keys only. Avoid rejected `metadata.source`; put provenance in `authoring/source_provenance.md` or other allowed field only if platform schema permits.
- Rubric weights total 100, positive, recommendation >=30, instruction following 1..10, criterion <=250 characters; no duplicate rubric IDs.
- Any `tests/rubrics.json` matches root `rubrics.json` exactly.
- Tests generate expected CTRF/reward files in the correct path; missing verifier or pytest crash must not be mistaken for solver failure.
- `solution/solve.sh` works with exact expected invocation and permissions; solver never accesses `author_only/`.
- No hidden symlinks, path traversal, absolute paths, caches, outputs, `.git/`, accidental `.db-wal` or journal files.
- All `*.gz` files decompress; manifest sizes/checksums match.

## Quality — real workplace, no algorithm giveaway
- Task prompt reads as an incident commander handoff, not a benchmark's ETL specification.
- Do not enumerate 'six logic gates', hard-coded rule order, exact data joins, expected counts or optimization algorithm.
- Three familiar artifacts with existing worksheet templates are preferable to nine invented files.
- Policy documents state authority and business constraints, not a solved decision tree.
- A professional must make judgments about contradictory evidence and safe sequencing.
- No artificial anomaly-index files such as `known_traps.csv`, `reconciliation_cases.csv` or `answer_keys.json` in agent-visible data.
- No arbitrary requirements to cite exactly one source when several valid corroborations exist.
- Include operationally meaningful, not random, uncertainty; explicitly allow `UNRESOLVED` where appropriate.
- Task card taxonomy matches user form exactly. Previous observed values: primary `Anomaly Detection & Diagnostics`, additional `Comparative Analysis & Explanation` and possibly `Root-Cause Analysis`; phases `Explore / Discover`, `Hypothesize`, `Analyze & Validate`, `Synthesize`, `Recommend`. **Do not assume these values are always selectable**; reconcile against the live form before submission.

## Audit — full and compatible rubric
- For every imperative in the prompt and report templates, at least one criterion checks it.
- For every criterion, a correct answer can earn it alongside every other criterion.
- Tests only assert disclosed output contracts; semantic assertions accept every correct solution and do not silently require one hidden formatting choice.
- No tests that always pass, compare only the file to itself, or verify superficial presence while claiming semantic correctness.
- All evidence references are verified against actual supplied records, with contextual support.
- Negative mutants fail for the intended reason; reference passes in clean container on three seeds.

## Similarity and licensing
- Use newly synthesized incident, identifiers, workloads, records, documents and forcing geometry.
- Reusing the general task structure is fine; avoid copying source task prose and source data into new task.
- Keep source/attribution ledger for any external samples and spec excerpts. No unlicensed corporate logs.
- Validate all third-party datasets and licenses against platform's actual submission policy; a license label is not proof.

## Expected stage order (not guaranteed)
Format → Quality → Similarity/Licensing → Audit → Model Sweeps → final review. The platform may order them differently; verify the actual UI. Fix the earliest failure first, but preserve regression tests for earlier stages.

## Common false confidence
- 'Reference passes' ≠ 'sweep is hard'.
- 'A lot of data' ≠ 'a lot of reasoning'.
- '10 mutation tests fail' ≠ 'frontier models will fail'.
- 'Valid signature' ≠ 'trusted builder'.
- 'No-op gets 0' ≠ 'grader discriminates between near-correct and wrong'.
- 'More constraints' ≠ 'higher quality'; overspecification may itself fail Quality.
