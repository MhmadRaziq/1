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
