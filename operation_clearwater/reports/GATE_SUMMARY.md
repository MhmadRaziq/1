# Gate summary

| Phase | Result | Evidence |
|---|---|---|
| 1 Inspection | GO | reports/PHASE1_INSPECTION.md |
| 2/3 Microcosm | GO | 16 svc, dual-oracle agree, **17/18** shortcuts diverge, **18/18** CF flips — reports/microcosm_gate.json, SHORTCUT_TOURNAMENT.csv, DECISION_SENSITIVITY.csv |
| 4 Scale | GO | seeds 42/1337/9001 agree, 0 WAL invariant errors — scale_seeds.json |
| 5 Workplace materials | GO | candidate/instruction.md, task_card.md, templates |
| 6 Verifier/mutants | GO | reference 100, noop 0, **12/12** negatives rejected — MUTATION_REPORT.md |
| 7 Rubric | GO | 100 pts, recommend 36, IF 8, criteria ≤250 — rubrics.json, REQUIREMENT_COVERAGE.csv |
| 8 Preflight | GO | preflight PASS; clean extract; reference 100; noop 0. Docker binary absent in this VM |
| 9 Strong-model trials | GO (hardness) | mean **72.0** (A/B/C=75, D=63) after held+open-indicator redesign — STRONG_MODEL_TRIALS.md |
| 10 Submission ZIP | GO (local) | `operation_clearwater_candidate.zip` sha256 `ebf52e2384b91fac72b69040e528d61b6f240bc767d28d23b2bc6dee2a1a0680` |

Design-kit / local engineering validation is **not** a Baby Carrot platform pass.
