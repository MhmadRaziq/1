# CLEARWATER evidence guide

All records are synthetic and offline. Times are timezone-aware ISO-8601 UTC.
PostgreSQL LSNs use ``HEX/HEX`` byte offsets. WAL filenames follow the
PostgreSQL ``{timeline}{log}{seg}`` layout for 16 MiB segments.

| File | Custodian | Use |
|---|---|---|
| `recovery_candidates.json` | Backup console | Untrusted inventory of candidate restore points |
| `vault_receipts.json` | Immutable vault audit | Copy completion, digest, immutability, legal hold |
| `wal_archive.json` | Archive gateway | Segment files, timeline, LSN span, hash verification |
| `timeline_history.json` | PostgreSQL recovery | Parent/child timelines and switchpoint LSNs |
| `kms_grants.json` | Cloud security | Restore-time key state and grant effectiveness |
| `build_attestations.json` | Signing service | Manifest digest, signature, signer trust/revocation |
| `malware_scans.json` | Clean-room analysts | Coverage through a stated timestamp / target |
| `restore_rehearsals.json` | Recovery team | Rehearsal result and observation time |
| `intrusion_indicators.json` | DFIR | Confirmed or unconfirmed contamination windows |
| `dependency_registry.json` | Architecture/SRE | Priorities, RPO, activation dependencies |
| `recovery_policy.json` | Resilience director | Cutoff, budget, priorities, risk appetite |

Record IDs such as `VR-IDENTITY-STABLE` or `WAL-ORDERS-BRANCH-1` are valid
citations. A missing or post-cutoff observation is not positive evidence.
Legal hold protects originals; when `copy_restore_allowed` is true, restoring
from the immutable *copy* remains allowed.

The case owner needs an operationally safe plan. Other defensible portfolios
are acceptable when they meet safety, capacity, dependency and priority
constraints and clearly explain trade-offs.
