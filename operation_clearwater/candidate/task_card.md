# Task description
A resilience director needs an evidence-supported restoration recommendation after a contained ransomware intrusion. Backup catalog claims, immutable vault receipts, PostgreSQL WAL/timeline history, KMS grants, attestations, malware scans and restore rehearsals disagree. The recovery lead must select safe restore points and sequence dependent services under constrained clean-room capacity without reintroducing compromised state.

# Complexity justification

### Challenge 1 — catalog READY versus vault completion
Console status can claim READY while the immutable copy is still queued or digest-mismatched.

### Challenge 2 — attestation trust versus signature presence
A cryptographically valid signature may still be untrusted if the signer was revoked before signing.

### Challenge 3 — WAL continuity and timeline ancestry
PITR requires continuous archived WAL from backup stop LSN through the recovery target on a compatible timeline; late segments do not repair a missing middle segment, and replica forks are not substitutes for primary ancestry.

### Challenge 4 — time-bounded evidence
Key grants and rehearsals observed after the decision cutoff cannot support the call; scan coverage must reach the replay target.

### Challenge 5 — capacity, schema and migration coupling
Individually best points can exceed clean-room effort, require newer provider schema epochs, or impose irreversible migrations that strand dependents.

### Challenge 6 — proportional recovery under uncertainty
Legal hold protects originals but may still allow copy restore; unconfirmed indicators are not proven contamination; equal-utility portfolios must be graded fairly.

## Taxonomy tags
- Primary objective: Anomaly Detection & Diagnostics
- Additional objectives: Comparative Analysis & Explanation
- Reasoning phases: Explore / Discover; Hypothesize; Analyze & Validate; Synthesize

# Expected difficulty range
High. Shortcut policies that trust a single evidence family produce different unsafe portfolios. This is a design target, not a verified platform sweep result.
