# Oracle, solution and verifier engineering

## Separate the three implementations
1. **Generator** creates causal world-state, source records, and a sealed truth graph. The graph is not exposed to the solver.
2. **Reference solver** consumes only the same agent-visible source packet and reconstructs findings; never reads the sealed truth graph. If it cannot, the task is not ready.
3. **Verifier** reads submitted outputs plus a private oracle snapshot or independently generated expectations. It must not import the reference solver, share its normalization functions, or rely on a solver-visible answer index.

## Ground-truth invariants
- Every exposed runtime instance has a taint path to the compromised runner or its contaminated output AND independent proof of production execution at cutoff.
- Every cleared finding has a genuine apparent exposure trigger plus a decisive clearance record; do not invent trivial false positives.
- Every unresolved case is provably underdetermined by the supplied packet, with at least two compatible world states yielding different exposure outcomes.
- Every recovery target has independently verified clean provenance and is deployable under the stated platform/region constraints.
- Every response plan preserves declared critical-service quorum at each step, not only in the final state.
- Every cited evidence ID exists in the appropriate source and supports the claimed relationship, not merely a filename token.
- Seed and cutoff facts are internally consistent across notices, events and operational decisions.

## Grader design
**Layer A — format (nonsemantic, low weight):** exact three files, readable CSV, disclosed worksheet headers, allowed disposition/action vocabulary, valid Markdown, no output URLs if specified.

**Layer B — source-backed facts (main score):** exposure and clearance precision/recall, material taint paths, trust claims, running state, disputed findings, cited evidence support. Use sets keyed by stable workload identity + cutoff + artifact digest, not arbitrary row order.

**Layer C — operational decisions (main score):** necessary interventions covered, safe alternatives accepted, response sequence simulates to healthy intermediate states, no use of tainted rollback, no unauthorized change.

**Layer D — executive synthesis:** material limitations, reasons for clearance, risk/availability trade-offs, clear prioritization. Check objectively named facts and evidence, not exact prose strings.

## Objective semantic checks
- `exposure_register.csv`: compare normalized `(workload, artifact, disposition)` sets against oracle; exact string matching only for disclosed stable identifiers, not explanations. Permit a defensible `UNRESOLVED` where the oracle marks it acceptable.
- Evidence: resolve each submitted record ID in a compact private record index constructed by the verifier from raw sources; check source family and relevant object/time. Merely matching an ID regex is insufficient.
- `response_plan.csv`: simulate proposed actions in declared order; check preconditions, affected workload coverage, clean recovery, and quorum after **every** step. Accept any feasible safe plan within disclosed business constraints.
- Memo: evaluate a bounded checklist of factual claims, with robust patterns or structured cross-checks, not literal paragraphs. Avoid unverifiable rubric claims about 'professional quality'.

## Reward geometry
Prefer granular partial credit over all-or-nothing reward. A 0/1 local reward is useful for a strict gate but is a poor instrument for understanding model sweep performance. If the platform requires binary test rewards, keep a meaningful graded rubric and ensure each test is nontrivial. Do not double-count the same semantic error across many criteria.

## Example scoring distribution (100 positive points)
- Discovery of material source/identity conflicts: 12
- Causal exposure reconstruction: 24
- Clearance and uncertainty adjudication: 15
- Recovery feasibility and change sequencing: 10
- Operational recommendation: 33
- Instruction following and evidence integrity: 6
**This is a conceptual split, not a category assignment.** For an actual 100-point category allocation with recommendation ≥30 and instruction following ≤10, use `05_rubric_audit/RUBRIC_ARCHITECTURE.md`.

## Negative tests / mutation suite
1. Empty files or only headers.
2. Every suspicious image marked exposed.
3. Every validly signed build marked clean.
4. Treat tag equality as digest equality.
5. Treat OCI index digest as architecture-specific manifest digest.
6. Ignore base-layer propagation.
7. Treat desired rollout as running state.
8. Treat an old observation as active at cutoff.
9. Ignore clean lookalikes.
10. Invent evidence references that have valid-looking syntax.
11. Stop all exposed workloads simultaneously, violating quorum.
12. Select a tainted rollback image.
13. Select an unavailable regional replica.
14. Over-contain a protected service despite a safe narrower action.
15. Omit unresolved cases.
16. Use after-cutoff approvals as if in force.
17. Reverse action order while preserving final state.
18. Copy an oracle-like answer from a solver-visible sidecar (this must be impossible).

## Adversarial acceptance
For each mutant record the violated invariant, affected rubric/test and measured reward. No-op must not earn meaningful credit. A correct alternate plan must not fail because its sequence differs from the author's preferred plan. Re-run mutations across three data seeds.

## Test contamination prevention
Never ship `author_only/`, `oracle.json`, `truth_graph.json`, generated reference outputs or challenge ledgers in `environment/data`. If the platform expects `solution/` and `tests/` at ZIP root, keep them in the author package's designated locations and confirm the agent environment cannot read them.
