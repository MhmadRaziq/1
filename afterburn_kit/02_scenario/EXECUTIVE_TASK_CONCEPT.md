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
