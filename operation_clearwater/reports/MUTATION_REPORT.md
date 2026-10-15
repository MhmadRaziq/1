# Mutation report — Operation CLEARWATER

Measured against `work/seed_42_scale` with the semantic grader in `verifier/grade.py`.

| Mutant | Reward | Expect reject | Pass |
|---|---:|---|---|
| reference | 100.0 | no | yes |
| noop | 0.0 | yes | yes |
| m01_missing_memo | 64.0 | yes | yes |
| m02_empty | 3.0 | yes | yes |
| m03_fabricated_citation | 70.0 | yes | yes |
| m04_catalog_latest | 61.0 | yes | yes |
| m05b_expensive_set | 67.0 | yes | yes |
| m06_bad_cutover | 82.0 | yes | yes |
| m07_unsafe_payments | 75.0 | yes | yes |
| m08_schema_break | 82.0 | yes | yes |
| m09_irreversible_migration | 80.0 | yes | yes |
| m10_unnecessary_hold_denial | 83.0 | soft alternate | yes |
| m11_wal_gap_search | 75.0 | yes | yes |
| m12_stale_scan | 71.0 | yes | yes |
| m13_late_rehearsal | 75.0 | yes | yes |
| m14_alternate_valid | 100.0 | no (accept) | yes |

**Gate:** ≥10 negative mutants below the 85 band; valid alternate accepted; reference full; noop zero. **PASS** (12/12 hard negatives rejected; alternate 100).
