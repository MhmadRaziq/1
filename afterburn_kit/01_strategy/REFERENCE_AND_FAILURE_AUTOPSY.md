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
