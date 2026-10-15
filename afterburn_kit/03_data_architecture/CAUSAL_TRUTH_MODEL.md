# Causal model: from compromised runner to effective exposure

## Author-only truth graph
Entities: runner identity, build invocation, resolved dependency, artifact digest, OCI image index, platform manifest, layer, registry tag event, admission, rollout revision, runtime instance, service, recovery artifact, change approval, dependency/quorum requirement.

Edges: `ran_on`, `produced`, `consumed`, `includes_layer`, `tag_pointed_to_at`, `index_selects`, `requested`, `admitted`, `materialized`, `observed_running`, `superseded_by`, `approved_under`, `depends_on`, `recovers_to`.

Exposure is not one predicate applied to a flat table. It requires: confirmed taint origin; causally reachable build output/layer; effective immutable runtime identity; material production execution at the cutoff. A compromised runner that produced no deployed code is a build-integrity incident but not necessarily an exposed running workload. An observed workload whose image includes a tainted layer can be exposed even when its final build was clean.

## Independent adjudication classes
- `EXPOSED`: material affected code running in production by the cutoff, supported by at least two independent source families.
- `CLEARED`: apparent match disproved by governing immutable identity or deployment realization evidence.
- `UNRESOLVED`: conflicting/incomplete evidence prevents a defensible binary decision; requires a specific next observation.

Avoid silently equating missing logs with clean state. Define in author-only truth which cases are provable and which are intentionally indeterminate. Never grade `UNRESOLVED` as wrong if the packet genuinely lacks sufficient evidence.

## Recovery feasibility
Define a set of allowable change actions and their actual effects on service health. A feasible plan must (a) eliminate or isolate proven material exposure, (b) avoid tainted recovery targets, (c) respect critical quorum and regional failover constraints, and (d) be achievable with the available change windows/rollout slots. Multiple equally safe and feasible plans should receive credit; do not secretly enforce a single lexicographic optimizer.

For truly unique recommended choices, add operational facts that make alternatives infeasible, not hidden arbitrary tie-breaks. If several plans are feasible, evaluate invariants and risk/cost bounds rather than exact row equality.

## Two-clock discipline
At a cutoff, use facts effective by that cutoff, distinguishing delayed recording from late effect. A later record can report a historical fact, but should not retroactively grant authority unless the source's operational semantics permit it. The author must document each such choice and test both sides of the boundary.

## No oracle leakage
The solver packet cannot contain the causal truth graph, taint flags, planted-case ledger, expected recovery set, or a ready-made per-service state table. These belong under `author_only/` during construction and in the private reference solution, never in the agent's environment.
