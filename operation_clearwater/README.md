# Operation CLEARWATER

Self-contained AfterQuery Baby Carrot task: ransomware clean-room restore-point
selection under divergent PostgreSQL timelines, unreliable backup catalogs,
key-grant state, immutable vault evidence and cross-service cutover constraints.

## Quick start (local gates)

```bash
cd operation_clearwater
PYTHONHASHSEED=0 python3 tools/run_microcosm.py
PYTHONHASHSEED=0 python3 tools/run_scale.py
PYTHONHASHSEED=0 python3 tools/run_mutants.py
PYTHONHASHSEED=0 python3 tools/run_ablation.py
PYTHONHASHSEED=0 python3 tools/package_candidate.py
PYTHONHASHSEED=0 python3 tools/preflight.py operation_clearwater_candidate.zip
```

## Deliverable

- `operation_clearwater_candidate.zip` — AfterQuery-style task root ZIP
- `reports/` — validation, sensitivity, shortcut, ablation, mutant, coverage artifacts

Author-only truth lives under `work/*/author_only/` (gitignored) and is never
shipped inside the candidate ZIP.

## Status

See `reports/VALIDATION_REPORT.md`. Design-kit validation is not a platform pass.
