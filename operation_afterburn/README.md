# Operation AFTERBURN

Self-contained senior DFIR software-supply-chain investigation benchmark task, built from the Baby Carrot gold-standard design kit.

## Quick start (local gates)

```bash
python3 tools/run_microcosm.py
python3 tools/run_scale.py
python3 tools/run_mutants.py
python3 tools/package_candidate.py
python3 ../afterburn_kit/tools/preflight.py operation_afterburn_candidate.zip
```

## Deliverable

- `operation_afterburn_candidate.zip` — AfterQuery-style task root ZIP  
- `reports/` — BUILD_REPORT, VALIDATION_REPORT, sensitivity / shortcut / ablation / coverage CSVs  

Author-only truth lives under `work/*/author_only/` (gitignored) and is never shipped inside the candidate ZIP.

## Status

Local engineering gates: PASS.  
Platform sweeps / Docker-in-CI / cold-start model trials: see `reports/VALIDATION_REPORT.md`.
