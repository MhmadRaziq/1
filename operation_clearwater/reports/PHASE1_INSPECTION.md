# Phase 1 — Inspection, flaws, causal world model

## Prototype measured results
Command: `python3 tools/build_microcosm.py && python3 tools/evidence_solver.py && python3 tools/shortcut_tournament.py` (kit)

| Metric | Value |
|---|---|
| Services | 8 |
| Candidates | 40 |
| Source records | 377 |
| Shortcuts diverging | **12 / 14** |
| Nondifferentiating | `ignore_scan`, `ignore_restore_rehearsal` |

## Flaws fixed in full build
1. Binding stale-scan / late-rehearsal candidates (schema-compatible, budget-cheap) so those shortcuts flip the portfolio.
2. Replaced minute/ordinal WAL with PostgreSQL 16 MiB LSN filenames, backup_stop_lsn, timeline switchpoints.
3. Implemented FC01–FC18 with one-fact counterfactual flips (18/18).
4. Dual independent oracles (topo BnB vs ready-set priority BnB) agree on 3 seeds.
5. Scaled to 16 services, multi-day auxiliary observations, reproducible SHA-256 source hashes.

**Phase 1 gate: GO.**
