# Recovery decision required — Operation CLEARWATER

**From:** Director of Technology Resilience
**To:** Senior incident-response and database recovery lead

We have contained a ransomware intrusion affecting several application tiers. Production remains isolated. The backup console suggests multiple recent restore points, but we do not trust the console alone: our clean-room team has separately collected immutable-vault receipts, archived transaction logs (PostgreSQL WAL), timeline history, key-access records, integrity attestations, malware scans, restore rehearsals, intrusion indicators and application dependency notes. Some records conflict, and the incident cutoff matters.

Please prepare a decision-ready recovery recommendation for the next operations call. Establish which service recovery states are defensible using the supplied evidence, which attractive alternatives are unsafe or not yet substantiated, and the expected business impact of the recommended recovery points. Recommend a practical restore and cutover sequence that respects available clean-room capacity, service dependencies, the stated recovery objectives, and the need to preserve originals for investigation. Distinguish observed evidence from assumptions and unresolved risks.

## Evidence packet

Use only the offline case packet under `/workspace/data/`. Start with `case_brief.md` and `evidence_guide.md`. Treat `recovery_candidates.json` as an untrusted inventory. Do not assume catalog READY, a signature flag, or a clean base backup alone establishes a safe recovery target. PostgreSQL LSN values use `HEX/HEX` byte offsets; WAL segment size and timeline ancestry rules are documented locally.

## Deliverables

Write both files to `/workspace/output/`:

1. `recovery_decision.md` — concise recovery decision memo (recommendation, defensible states, rejected alternatives, data-loss impact, cutover/validation, assumptions and residual risk).
2. `recovery_plan.csv` — actionable service-by-service plan. Blank header template: `/workspace/data/report_templates/recovery_plan.csv`. Include for each service: proposed candidate/source, dependency readiness, expected data loss, evidence record IDs, and the validation gate before reconnect.

Include source-record IDs (for example `VR-…`, `WAL-…`, `KEY-…`) for material claims. Supporting analysis files are optional.

This is a decision-support exercise. Do not connect to production, run a live restore, or use the network. Evidence observed after the decision cutoff cannot support this call.
