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
