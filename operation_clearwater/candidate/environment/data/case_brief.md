# Operation CLEARWATER — case brief

**Incident ID:** CLEARWATER-42
**Decision time (as-of):** 2026-09-21T20:00:00Z
**Incident cutoff:** 2026-09-21T20:00:00Z
**Clean-room restore budget:** 70 effort units
**Clean-room posture:** isolated

## Situation
A ransomware intrusion affecting several application tiers has been contained.
Production clusters remain isolated. The backup console lists multiple READY
restore points, but the clean-room team collected independent evidence from
the immutable vault, WAL archive, timeline history, KMS grants, integrity
attestations, malware scans, restore rehearsals, intrusion indicators and the
service dependency registry. Records conflict. Evidence observed after the
decision time cannot support this call.

## What we need for the ops call
1. Which service recovery states are defensible from admissible evidence.
2. Which attractive alternatives are unsafe or not yet substantiated.
3. Expected data loss versus business priorities and RPO.
4. A restore and cutover sequence that respects clean-room capacity,
   dependency/schema compatibility, and preservation of vault originals.
5. Explicit assumptions, gaps and residual risk.

## PostgreSQL recovery notes (local)
- LSN values use PostgreSQL ``HEX/HEX`` byte-offset form.
- WAL segment size is 16777216 bytes (16 MiB).
- Replay begins at each candidate's ``backup_stop_lsn`` and must have a
  continuous archived segment chain through ``recovery_target_lsn`` on a
  compatible timeline (see ``timeline_history.json``).
- A catalog READY flag is not proof that an immutable vault copy completed.

## Risk appetite
No unverified restore sources. Preserve vault originals under any legal hold; restoring from an allowed immutable *copy* is permitted. Do not reconnect services that would replay confirmed ransomware writes.
