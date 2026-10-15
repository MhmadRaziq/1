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
