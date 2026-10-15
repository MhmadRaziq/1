# Northline release-governance incident response standard (excerpt)

## Authority
1. Material production exposure requires evidence of affected immutable artifact identity **and** evidence that the workload was running in a production environment at the investigation cutoff.
2. A valid attestation authenticates a statement about a subject digest and builder identity. It does not by itself prove the builder environment was trustworthy during the compromise window.
3. Registry tags are mutable pointers. Prefer content digests and platform-specific manifests when reconciling runtime identity.
4. Desired rollout state is not proof of runtime materialization. Prefer admission outcomes and runtime observations with event times at or before the cutoff.
5. Emergency change records are usable only when their **effective** time is at or before the cutoff. Recording time alone is not authority.
6. Containment and redeploy actions must preserve disclosed quorum and regional health constraints at every intermediate step.
7. Rollback targets must be free of affected build output and available in the regions where they will be applied.
8. When evidence is insufficient to choose between exposure and clearance, record the finding as unresolved and name the observation that would resolve it.
