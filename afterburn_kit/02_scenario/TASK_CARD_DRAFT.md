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
