# Emergency build-provenance incident: production exposure and safe recovery

You are the senior incident responder supporting a release-governance incident call. Security engineering has confirmed a compromise of a production build-runner environment. The confirmed window, affected runner pool, and investigation cutoff are documented in `/workspace/data/incident_notice.md`.

The incident commander needs a defensible answer to three questions:

1. Which production workloads actually run code reached through the compromised build path at the cutoff?
2. Which apparently suspicious findings are not material production exposures, and why?
3. What response sequence reduces risk without violating the organization's availability and recovery commitments?

## Evidence packet

Use only the offline incident packet under `/workspace/data/`. It contains build and artifact evidence, registry and deployment history, service dependency information, and change/response records. Treat every file as evidence. Do not assume that an image tag, a successful build, a signed attestation, or a deployment request alone establishes the effective runtime state. Resolve material conflicts using the authority described in the incident response standard and related operational documents. State remaining uncertainty explicitly.

## Deliverables

Complete the three incident-response artifacts using the worksheets in `/workspace/data/report_templates/`:

- `/workspace/output/exposure_register.csv`
- `/workspace/output/response_plan.csv`
- `/workspace/output/incident_decision.md`

The register must support each material finding with packet-local record IDs. The response plan must identify affected services, proposed action, viable recovery target when applicable, and operational sequencing. The decision memo should summarize exposure and clearance rationale, immediate actions, continuity trade-offs, assumptions, and evidence limitations.

This is a decision-support exercise. Do not take live actions and do not use the network. If a case cannot be established from the packet, record it as unresolved and name the additional observation needed — do not invent missing records.
