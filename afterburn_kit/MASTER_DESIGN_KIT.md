# Baby Carrot — Complete Master Design Kit

> Design blueprint only, not a completed submission.

<!-- README_START_HERE.md -->

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


---

<!-- 01_strategy/REFERENCE_AND_FAILURE_AUTOPSY.md -->

# Reference-based design: what to keep and what to reject

## Evidence actually inspected
The local reference archive `enterprise-credential-hop-containment.zip` contains a seed, four large compressed telemetry sources (authentication, process, network flow, DNS), a containment standard, a telemetry dictionary, a four-artifact output contract, a 35-item/100-point rubric, a reference solver and pytest tests. Its task card describes 28 accepted credential hops, 17 host isolations, 13 credential resets and six cleared historical lookalikes. Those are **author claims in the reference package**, not independently verified private sweep results.

### Reuse the underlying structure
- Start from a confirmed event rather than a vague request to hunt everything.
- Require cross-source corroboration; absence of one kind of evidence must not automatically prove innocence.
- Include historically routine lookalikes that are materially different from campaign activity.
- Reward the operational decision and independent evidence findings, not only format.
- Use a local, self-contained evidence packet; no solver network egress.
- Provide a reference solver and tests as part of the author submission, but not to the agent.

### Do NOT reproduce weaknesses from later task attempts
- **V19 audit:** conflicting criteria (28 vs 60) and an ungraded revision-reversal requirement.
- **V20 sweeps:** stronger model scored 0.99 on all four trials. Data volume and added checks did not create meaningful hardness.
- **V21 coverage:** six instructions uncovered by the rubric, including citations, coverage status, point computation, table schema and recommendation counts.
- **V21 Quality:** algorithm prescribed as six gates; exactly nine CSVs; explicit join/revision recipe; explicit lexicographic optimization. These made the task feel like a synthetic ETL benchmark rather than a professional handoff.
- **V22 risk:** more realistic prompt, but inherited evidence geometry; no proof of sweep hardness.
- **Q1 forensic autopsy:** semantic-index sidecars and candidate-level normalizations let a strong agent compress the entire task into a small deterministic table. Some planted cases did not change decisions under shortcuts.

## Design constraints derived from the record
1. A professional document establishes obligations and source authority; the prompt states the business question, not the algorithm.
2. Don't disclose an anomaly register, expected exposure list, forcing cases, or normalized per-service truth in the agent-visible packet.
3. Source diversity must be causal: remove a major source, and the decision changes.
4. The strongest traps must have **two defensible-looking paths that yield different decisions**, with evidence resolving which is right.
5. A signed provenance document is not the same as a trustworthy builder; an image tag is not an immutable deployed digest; a deployment declaration is not a proof of runtime materialization.
6. Rubric points should not reward the same underlying mistake multiple times as if independent.
7. Use a **realistic three-artifact handoff** rather than nine artificial output files. If CSV schemas are required for grading, frame them as supplied SOC templates.
8. Write an explicit author-only truth specification; a different implementation of the oracle must reproduce the same decisions.

## Novelty claim discipline
We cannot know what any frontier model was trained on, nor promise a particular score. Novelty here means freshly generated organization-specific evidence, causal relationships and operational constraints; not secret keywords, tricks, obscure encodings or benchmark contamination.


---

<!-- 02_scenario/EXECUTIVE_TASK_CONCEPT.md -->

# Scenario: Operation AFTERBURN — supply-chain compromise exposure and recovery

## Authentic business request
At 09:20 UTC, the security engineering team confirms that an ephemeral build runner image used by the production release pipeline was compromised between 02:10 and 04:05 UTC. The CI dashboard still shows green builds and valid attestations. An emergency board must decide by 10:00 UTC which production workloads require immediate containment, which apparent exposures can be cleared, and which recovery changes can be deployed without breaking critical customer-facing services.

The organization operates several business units across three clusters, multiple CPU architectures and separate production/staging tenants. Release tags are mutable, deployment status is asynchronous, image indices can select different architecture manifests, and some builds include shared base layers or vendored dependencies. A valid attestation proves a statement was made and authenticated; it does not prove the build environment was uncompromised.

## What the incident commander must decide
A. **Exposure:** Which running production workload instances were materially affected by the compromised build path before the cutoff? Which candidates are cleared and why?
B. **Trust boundary:** Which artifact identities, runner attestations, base layers and build outputs should be distrusted? Which signed artifacts are nevertheless outside scope?
C. **Action:** Which workloads need immediate stop/quarantine/redeploy, which can safely continue, and what exact trusted rollback or clean rebuild path exists?
D. **Safety:** What action order preserves the defined business continuity constraints and does not use a rollback artifact with hidden contamination?
E. **Uncertainty:** Which plausible cases cannot be established from the available evidence, and what next collection would resolve them? Do not turn uncertainty into fabricated certainty.

## Professional outputs
1. `exposure_register.csv` — existing security team's finding register; one row per material reviewed workload / artifact relationship, with supporting record references and disposition.
2. `response_plan.csv` — existing change-management response worksheet; actionable interventions, dependency/sequence, trusted recovery target and evidence.
3. `incident_decision.md` — executive incident memo with evidence, cleared lookalikes, trade-offs, risks and limits.

Output templates are provided under `templates/`. The task prompt refers to the templates instead of reproducing nine pages of schema minutiae.

## Explicit scope limits
- Entirely offline, self-contained. No cloud API calls, no registry pulls, no external websites.
- The analyst does not need to prove arbitrary malware behavior. The compromised runner's **taint mechanism** and relevant build window are supplied by a confirmed incident record.
- Material exposure is determined from build inputs, immutable artifact identity, deployment realization and in-scope production workloads, not from mere possession of a matching tag.
- Ambiguous cases must have explicit acceptable dispositions and independent tests, not hidden arbitrary truth.
- Emergency response constraints are provided in change-management records and service dependency docs; do not demand live actions.

## Distinctive hard challenge
Two images have the same release tag but different immutable digests; one is compromised and one is safe. Another has a valid signature but was built by the compromised runner. A third was built cleanly but embeds an affected shared layer. A fourth was exposed in registry but never materialized into production. A fifth appears to be a safe rollback, but a regional replica still resolves its old digest. A sixth can only be stopped after a healthy quorum is restored elsewhere. These are *examples for authors only*; in the final solver packet they must emerge from the records, not be narrated as clues.

## Fairness
Every scored disposition must be grounded in at least two independent evidence families. Each safety constraint must be disclosed in ordinary operational records. A professional should be able to defend the answer from the packet without guessing what the benchmark writer intended.


---

<!-- 02_scenario/SOLVER_PROMPT_DRAFT.md -->

# Emergency build-provenance incident: production exposure and safe recovery

You are the senior incident responder supporting a release-governance incident call. Security engineering has confirmed a compromise of a production build-runner environment; the incident seed and investigation cutoff are in `/workspace/data/incident_notice.md`.

The incident commander needs a defensible answer to three questions: what production code was actually exposed to the compromised build path, which apparently suspicious findings are not material production exposures, and what response sequence reduces risk without violating the organization's availability and recovery commitments.

Use the offline incident packet under `/workspace/data/`. It includes build and artifact evidence, registry and deployment history, service dependency information, and the organization's response/change records. Treat these as evidence; do not assume that an image tag, a successful build, a signed attestation, or a deployment request alone establishes the effective runtime state. Resolve material conflicts and explain remaining uncertainty.

Complete the three incident-response artifacts using the supplied worksheets in `/workspace/data/report_templates/`:

- `/workspace/output/exposure_register.csv`
- `/workspace/output/response_plan.csv`
- `/workspace/output/incident_decision.md`

The register must support each material finding with packet-local record IDs. The response plan must identify affected services, proposed action, viable recovery target and operational sequencing. The decision memo should summarize the exposure and clearance rationale, immediate actions, continuity trade-offs, assumptions and evidence limitations. Do not take live actions or use the network.

This is a decision-support exercise, not an instruction to run production changes. State any unresolved case as unresolved and recommend the additional evidence needed; do not invent missing records.

[AUTHOR NOTE: Remove this line before submission. Exact fields and acceptable enums are in provided report_templates; no answer IDs, algorithms, forcing-case names or expected counts may appear in the solver prompt.]


---

<!-- 02_scenario/TASK_CARD_DRAFT.md -->

# Task description
A production release pipeline is affected by a confirmed build-runner compromise. The responder must reconstruct which immutable artifacts were produced or contaminated in the relevant period, reconcile those artifacts with actual running production deployments, distinguish false positives from material exposures, and propose safe containment and recovery that respects dependency and availability commitments.

# Complexity justification

### Challenge 1 — artifact identity versus mutable registry pointers
Tags, image indexes, per-platform manifests and cached pulls disagree. Correct conclusions depend on immutable content identity and runtime realization rather than a tag lookup.

### Challenge 2 — attestation authority versus builder compromise
Some affected artifacts have valid signed provenance, while some apparent matches come from clean, independently authorized builders. Signature validity and trustworthiness of the builder are separate propositions.

### Challenge 3 — transitive contamination
A clean direct build can embed a compromised shared base layer or vendored build output. A suspicious build can also be harmless if its output never reaches production. The direction of propagation must be reconstructed.

### Challenge 4 — asynchronous deployment evidence
Desired state, admission decisions, runtime observations and workload turnover do not align perfectly. The responder must establish what was materially active at the cutoff.

### Challenge 5 — recovery coupling
Rollback candidates have differing trust and operational viability. A seemingly safe isolated change can violate service quorum, region dependency or recovery-time commitments; correct response is globally coordinated.

### Challenge 6 — independent clearance and uncertainty
Lookalikes and genuinely unresolved cases require distinct evidence-backed dispositions; over-containment and unjustified clearance both cause operational harm.

# Taxonomy tags
- Primary objective: Anomaly Detection & Diagnostics
- Additional objectives: Comparative Analysis & Explanation; Root-Cause Analysis
- Reasoning phases: Explore / Discover; Hypothesize; Analyze & Validate; Synthesize; Recommend

# Expected difficulty range
High. Several plausible shortcut approaches yield distinct wrong exposure and recovery outcomes. This is a target, not a verified sweep result.

# Private ground truth
[AUTHOR ONLY: populate from the independently generated oracle after the dataset is frozen. Never disclose the exact affected set or forcing-case map in the solver-visible packet.]


---

<!-- 03_data_architecture/SOURCE_PACKET_AND_PROVENANCE.md -->

# Evidence architecture — actual packet design

## Solver-visible directory (suggested)
```
/workspace/data/
  incident_notice.md
  incident_response_standard.md
  service_recovery_commitments.md
  telemetry_dictionary.md
  report_templates/
    exposure_register.csv
    response_plan.csv
    incident_decision.md
  changes/
    release_approvals/*.md
    emergency_changes/*.md
    oncall_handoffs/*.md
  source/
    build_lockfiles.tar.gz
    repository_release_history.jsonl.gz
  build/
    ci_job_events.jsonl.gz
    builder_identity_events.jsonl.gz
    attestations.jsonl.gz
  registry/
    tag_mutations.jsonl.gz
    oci_descriptors.jsonl.gz
    layer_inventory.jsonl.gz
  runtime/
    admission_audit.jsonl.gz
    rollout_history.jsonl.gz
    pod_runtime_observations.jsonl.gz
    workload_inventory.csv.gz
  operations/
    dependency_graph.jsonl.gz
    region_health.csv.gz
    rollback_artifacts.jsonl.gz
```

## Roles and necessary cross-source facts
| Family | Carries | Why it is indispensable |
|---|---|---|
| Incident notice + builder identity | compromised window, affected trust domain, investigation cutoff | Defines exposure origin; neither timestamps nor signatures alone determine taint. |
| CI job + source lockfiles | build invocation, resolved inputs, inherited build outputs | Reveals indirect materialization and clean lookalikes. |
| in-toto/SLSA-style attestations | authenticated claim about subject digest and builder identity | Distinguishes signed statements from trusted execution. |
| OCI descriptors + registry mutations | immutable digest, platform index, tag movement, layer ancestry | Prevents false tag equality and cross-architecture conflation. |
| Admission + rollout + runtime | desired versus observed state, image digest actually run, terminated vs live | Decides real production exposure. |
| Change approvals + incident SOP | emergency authority, superseded changes, protected services | Establishes which actions are permissible at the cutoff. |
| Dependencies + health + recovery artifacts | quorum, regional failover, trusted rollback availability | Makes remediation a coupled decision, not a per-service greedy choice. |

## Critical representation decisions
- Use actual JSONL and OCI-like descriptor structures, but bound the supported feature subset in the *data dictionary*. Never fabricate fields that conflict with a named standard.
- Preserve subject digests and builder identities. If using synthetic signatures, either implement real verification with a bundled public key and fixed offline library, or clearly label the record as an authenticated simulated internal log; do not pretend a string field proves cryptographic validity.
- A signed attestation can still describe a compromised build. A registry tag is a mutable pointer. An OCI image index selects a platform-specific manifest; do not treat the index digest as interchangeable with a platform manifest digest.
- Reconcile `event_time`, `recorded_time`, `effective_time` and observation timestamps only where the operational documents make those distinctions meaningful; avoid a generic 'latest numeric revision wins' rule.
- The same business service can appear under multiple namespaces/aliases; identity mappings must be inferred from deployment and inventory evidence, not exposed as a tiny target-indexed join table.
- Avoid leaking answer-like labels such as `is_compromised`, `expected_action`, `material_case`, `trap_id`, `review_target`, `golden_class` or `attack_flag`.
- Decoys should be natural operational noise: routine rollouts, retries, cache revalidation, canary deployment, failed admissions, nonproduction builds, old approvals, benign tag reuse, multiple CPU architectures.

## Scale and operational budget
**Pilot first:** 20–50 services; 100–300 workload identities; 20–80k CI events; 80–250k registry/deploy events; 20–100k runtime observations; 200–800 attestation subjects; 30–60 professional change documents. Pilot can be tens of MB compressed.

**Scale only after forcing-case and ablation proofs:** 100–250 services, 0.5–2M total events and a few hundred MB compressed, as long as a 4 CPU / 8 GB / 2-hour offline environment can solve it. Do not inflate size solely for appearance. Stream `.jsonl.gz` rather than loading every file into RAM.

## Deterministic construction
1. Generate a clean organization world and realistic background events.
2. Generate compromise origin and *causal* contamination edges.
3. Generate deployment/running state independently from desired-state history.
4. Generate valid but misleading evidence from normal business processes.
5. Generate approvals, rollback options and dependency constraints from a separate operational model.
6. Render source formats and inject record IDs.
7. Independently recompute the true exposure, clearance, uncertain set and feasible response plan.
8. Shuffle IDs/order, randomize harmless timestamps, and re-run all invariants for three seeds.

## Licensing and source discipline
Use newly generated organization identities, logs and configurations; do not paste proprietary corporate records. The publicly published SLSA/in-toto/OCI formats can guide structure; copying source datasets or standards text requires checking their respective licenses and attribution. Keep an author-only provenance ledger. Do not include internet URLs in the agent's requested outputs; schema URI strings in actual attestation records are not network dependencies.


---

<!-- 03_data_architecture/CAUSAL_TRUTH_MODEL.md -->

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


---

<!-- 04_oracle_verifier/ORACLE_AND_GRADER_SPEC.md -->

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


---

<!-- 04_oracle_verifier/FAIRNESS_AND_ALTERNATIVES.md -->

# Fairness proof before task submission

For each scored conclusion, answer all of these:
1. What evidence actually proves it? Give source filenames and record IDs in the author ledger.
2. Could another competent responder reach a different but defensible answer from the supplied evidence? If yes, score both or add resolving evidence.
3. Does the rubric criterion demand an exact word/row order beyond a disclosed export contract? If yes, relax it.
4. Does a later source contradict an earlier one? Which source has governing authority and why? Does the solver packet reveal that authority in a professional document?
5. Does a plan need a particular sequence, or merely any safe feasible sequence? Prefer invariant-based simulation.
6. Does the evidence support a factual claim about runtime execution, or only a deployment request? Grade accordingly.
7. Could the task be solved by inspecting a small single file? If yes, redesign.
8. Is the necessary source present, readable, and within runtime budget? Test clean extraction and the actual environment.

### Dual-world ambiguity check
For every `UNRESOLVED` case, construct two plausible world states consistent with all visible evidence. If one world is ruled out, it is not genuinely unresolved. For every binary `EXPOSED` or `CLEARED` case, ensure no competing consistent world exists that flips the result.

### Correctness under changed seed
Randomize organization identifiers, record ordering, harmless timestamps, benign workload count, and architecture distribution. Reference solver and verifier must still agree. This prevents accidental hard-coded case ID dependence.


---

<!-- 05_rubric_audit/RUBRIC_ARCHITECTURE.md -->

# Rubric architecture and full instruction coverage

## Platform constraints observed in prior work (verify current form)
- Total positive rubric weight: 100.
- Recommendation-category points: at least 30 (previous format checks flagged below 30).
- Instruction-following points: between 1 and 10.
- Each criterion: at most 250 characters (previous failures).
- Every criterion: observable from named deliverable(s), positive, non-conflicting, and compatible with at least one fully correct submission.
- Every explicit instruction: mapped to at least one criterion; no ungraded requirements.
- `rubrics.json` and `tests/rubrics.json`, when both required, must be identical.
- Do not use `metadata.source` in `task.toml`; a previous format checker rejected it.
- Keep form taxonomy labels exactly synchronized with `task_card.md` and any authoring profile.

## Concrete proposed allocation
| Category | Points | What to assess |
|---|---:|---|
| Explore | 8 | independent material discovery and identity conflicts |
| Hypothesize | 8 | competing explanations and defensible uncertainty |
| Analyze | 31 | digest/build/runtime evidence, transitive contamination, cutoff |
| Synthesize | 14 | reconciled findings and evidence limitations |
| Recommend | 33 | safe containment, clean recovery, staged quorum-safe plan |
| Instruction following | 6 | three worksheets, evidence refs, legible memo |
| **TOTAL** | **100** | **33 recommendation, 6 instruction following** |

## Criterion construction policy
- Prefer 30–42 focused criteria with meaningful independent weight, rather than 70–90 micro-criteria.
- Each criterion has exactly one objectively verifiable assertion, one category, a weight and one or more graded output files.
- A criterion checking 'identifies all exposed services' is too broad if individual failures matter; split by *independent causal mechanisms*, not by arbitrary per-row microcredits.
- Avoid contradictory criteria: do not simultaneously demand 'exactly N outputs' and a fourth required artifact; do not reward mutually exclusive dispositions for the same case.
- Avoid answer leakage in solver-visible task card: private ground truth is author-only.
- If a criterion is contingent on one of several valid outcomes, word it to accept all such outcomes. Do not add a negative criterion that penalizes a correct alternative.
- Do not reward repeating the same list in both memo and CSV as two independent semantic findings; grade the CSV for truth and the memo for synthesis/decision rationale.

## Coverage proof
Maintain `author_only/requirement_coverage.csv`: each atomic prompt or template requirement gets an ID, output artifact and rubric IDs. **Zero empty rubric-ID rows** before submission. Include all field-level rules in provided worksheets, source-citation requirements, counts, evidence limitations and operational sequencing.

## Rubric example (illustrative, not final)
```
{"item":1,"weight":4,"criterion":"Exposure register correctly distinguishes running affected images from registry-only artifacts at cutoff.","category":"analyze","verification_type":"text","grades_output_files":["exposure_register.csv"]}
```
Use the task's actual platform rubric schema and current form labels. Do not substitute a generic rubric format without validation.

## Audit conflict scan
Build an automated compatibility table for each pair of criteria referring to the same output or entity. Check cardinality, output count, exact versus allowed alternatives, time cutoff, statuses and category weights. Manually test the resulting 100-point reference submission against **all** criteria; if any two cannot both earn credit, redesign.


---

<!-- 05_rubric_audit/REQUIREMENT_INVENTORY.md -->

# Atomic requirements to map to rubric

The final instruction, output worksheet and governing incident SOP must be parsed into atomic requirements. Suggested inventory:

- R01 exactly three named artifacts delivered at expected paths.
- R02 exposure register uses disclosed worksheet columns and accepted disposition labels.
- R03 each material production workload finding is represented without duplicates.
- R04 each material finding is backed by packet-local source record IDs.
- R05 incident cutoff respected.
- R06 distinguish registry-only presence from runtime execution.
- R07 distinguish attestation authenticity from compromised builder trust.
- R08 include transitive contamination when actually materialized.
- R09 clear materially suspicious non-exposures with evidence.
- R10 report genuinely unresolved cases without invented certainty.
- R11 response plan covers immediate exposed services.
- R12 response actions include operationally viable recovery target or justified isolation.
- R13 plan respects change approvals and protected service commitments.
- R14 response ordering maintains quorum/availability at each intermediate step.
- R15 no tainted or unavailable rollback target is selected.
- R16 incident memo gives an explicit immediate recommendation.
- R17 memo explains the principal exposure chain.
- R18 memo explains at least two material clearance rationales.
- R19 memo explains trade-offs and operational risk.
- R20 memo states evidence limitations and next collection needs.
- R21 no live changes or network activity are attempted.
- R22 no external URL dependency or link is required in outputs.

These are **starting** requirements; compare with the final actual prompt and template cells. If the final prompt adds any instruction, add a coverage row before submission.


---

<!-- 06_quality_format/QUALITY_AND_FORMAT_GATES.md -->

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


---

<!-- 06_quality_format/RESEARCH_SOURCES_AND_LICENSE.md -->

# Author research sources and provenance ledger

These are **author-side references**, not network resources for the agent. Consult the current primary specifications when generating authentic record structures. Do not paste large portions of copyrighted documents into the task packet.

1. **SLSA Build Provenance v1**: fields and trust assumptions of `buildDefinition`, `runDetails`, `builder.id`, `resolvedDependencies`. Official spec: https://slsa.dev/spec/v1.0/provenance
2. **in-toto Attestation Framework**: Statement/Predicate/Envelope/Bundle and digest-bound subjects. Official spec: https://github.com/in-toto/attestation
3. **OCI Image Manifest and Image Index**: content-addressed manifests, layer descriptors, architecture selection. Official spec: https://specs.opencontainers.org/image-spec/
4. **SPDX / CycloneDX**: package/component SBOM semantics. Prefer the format your generator can implement faithfully, not both merely for variety.
5. **Kubernetes audit events and workload status**: event/request versus observed runtime; read official Kubernetes audit and pod lifecycle documentation.
6. **NIST SP 800-61 Rev.3 (April 2025)**: response governance and risk-based incident decision-making. Official: https://csrc.nist.gov/pubs/sp/800/61/r3/final
7. **User's reference task**: `enterprise-credential-hop-containment.zip` in this workspace, for architecture only.

## Licensing checklist
- Every external dataset: original URL, copyright holder, exact license version, permitted modifications, attribution text, redistribution restrictions, and SHA-256 of original.
- Every external document excerpt: quotation size and redistribution permissions.
- Every synthetic file: note that identities and records were generated; verify no copied production identifiers or secrets.
- If real open-source repo history is included, check license and potential private/personal data in commits.
- Put attribution in the appropriate agent-visible `NOTICE.md` only when required; keep the full provenance ledger author-only.

## Standards accuracy
Use real schema URIs where required by an actual standard. Network-style URIs inside structured attestation data are identifiers, not a request to browse. Never create a test that rejects valid standard-compliant schema URIs while claiming the packet follows that standard. The **no URL** restriction, if imposed, should apply to solver output content, not blindly to standard-conformant source records.


---

<!-- 07_red_team/HARDNESS_PROTOCOL.md -->

# Pre-sweep hardness protocol: measure, do not guess

## Stage 0 — independent solvability
- Author builds causal truth; separate engineer/model solves only from agent-visible data.
- Independently reconcile all scored cases; freeze seed and truth snapshot.
- All ambiguity is either resolved by evidence or scored as acceptable uncertainty.

## Stage 1 — decision-sensitive forcing proof
At least **8** independently causal cases spanning **4** capability families. At least 4 must flip an operational action; at least 2 must flip clearance; at least 2 must flip recovery feasibility/sequence. For each: correct path, shortcut path, evidence IDs, changed output, changed action, rubric points affected. If the shortcut yields the same scored outcome, the case does **not** count.

## Stage 2 — shortcut tournament
Implement 12–16 cheap solvers and measure full output/reward, not only qualitative difference. Mandatory shortcuts:
1. all signed artifacts clean;
2. all builds from runner tainted even when never deployed;
3. tag equals digest;
4. latest registry tag wins at cutoff;
5. OCI index digest equals platform manifest;
6. ignore base layers;
7. ignore vendored dependencies;
8. desired deployment equals running;
9. last observed pod remains active forever;
10. any build with suspicious dependency is affected;
11. rollback to latest previously green build;
12. stop all affected services immediately;
13. ignore service quorum;
14. ignore change approvals;
15. ignore after-cutoff timing;
16. ignore one entire evidence family.

Target: ≥10 shortcuts give wrong scored results; ≥5 distinct wrong final response decisions; no simple shortcut earns a passing sweep reward. This is an engineering acceptance target, not an AfterQuery guarantee.

## Stage 3 — ablation
Remove one family at a time: builder, source/lockfile, registry, runtime, change records, operations. At least 3 ablations must change a scored decision; at least 2 must alter the actual intervention set/sequence. If not, that family may be decoration.

## Stage 4 — compression challenge
Give an independent agent 10 minutes to identify the smallest solver representation. If a simple 10–15 column per-service table can be populated directly from one or two files, reject the concept. Hardness should require discovering the relevant artifacts, reconstructing authority and linking runtime to build materials.

## Stage 5 — independent strong-model trial
Run at least 3 independent cold starts without author-only information. Record per-criterion reward, time, solver traces, mistakes and cost. Use held-out seeds. Avoid designing around a single model's weakness; do not leak oracle through the prompt or test artifacts.

## Stage 6 — mutation regression
Mutate both the input evidence and the answer. If you flip a causal source fact, the oracle and the expected action should change. If you flip a cosmetic timestamp or unrelated event, the answer should remain stable. This metamorphic test detects fake complexity.

## Quantitative release gate
- Reference solution 100/100 on three seeds.
- 0 missing rubric coverage, 0 incompatible criterion pairs.
- No-op reward near zero; ≥15/18 negative mutants rejected.
- ≥8 forcing cases, ≥4 families, ≥10 shortcut failures, ≥5 distinct wrong outcomes.
- ≥3 material ablations, ≥2 affecting response action.
- No one input file is a compact answer index.
- Strong-model dry runs are genuinely below the target band on the *same rubric*, while competent independent humans/agents can solve the task with adequate time.

If a strong model again scores ~0.99, **change the evidence geometry and causal couplings**. Do not just add 100k more noise records or increase output formatting demands.


---

<!-- 08_build/IMPLEMENTATION_SEQUENCE.md -->

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


---

<!-- 08_build/CURSOR_MASTER_BUILD_PROMPT.md -->

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


---

<!-- BUILD_STATUS_AND_NEXT_ACTION.md -->

# What has and has not been built

## Completed in this kit
- Inspected the user's actual credential-hop reference task structure.
- Selected a new, technically distinct security incident with authentic source formats.
- Designed causal graph, source packet, 16 forcing-case blueprints and 22 atomic requirement mappings.
- Created realistic three-artifact prompt draft and output worksheets.
- Documented independent oracle, verifier, rubric, quality, audit, licensing, ablation and sweep strategy.
- Included runnable ZIP static preflight and design-kit integrity checks.

## Not completed — do not imply otherwise
- Full synthetic production dataset, including millions of telemetry records.
- Independent oracle and evidence-only reference solver.
- Executable semantic verifier or valid alternate-plan simulator.
- Platform-ready `rubrics.json`, `task.toml`, Docker image or submission ZIP.
- Independent cold-start model sweeps, private AfterQuery audit, similarity/licensing verdict.

## Next action
Use `08_build/CURSOR_MASTER_BUILD_PROMPT.md` in Cursor/ChatGPT Work to implement the microcosm **before** large-data generation. The first engineering checkpoint is a measured 8-case forcing proof and a shortcut/ablation report. Only then scale and build a candidate submission.
