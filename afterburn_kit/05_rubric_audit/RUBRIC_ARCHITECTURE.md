# Rubric architecture and full instruction coverage

## Platform constraints observed in prior work (verify current form)
- Total positive rubric weight: 100.
- Recommendation-category points: at least 30 (previous format checks flagged below 30).
- Instruction-following points: between 1 and 10.
- Each criterion: at most 250 characters (previous failures).
- Every criterion: observable from named deliverable(s), positive, non-conflicting, and compatible with at least one fully correct submission.
- Every explicit instruction: mapped to at least one criterion; no ungraded requirements.
- `rubrics.json` and `tests/rubrics.json`, when both required, must be identical.
- Do not use `metadata.source` in `task.toml`; a previous format checker rejected it.
- Keep form taxonomy labels exactly synchronized with `task_card.md` and any authoring profile.

## Concrete proposed allocation
| Category | Points | What to assess |
|---|---:|---|
| Explore | 8 | independent material discovery and identity conflicts |
| Hypothesize | 8 | competing explanations and defensible uncertainty |
| Analyze | 31 | digest/build/runtime evidence, transitive contamination, cutoff |
| Synthesize | 14 | reconciled findings and evidence limitations |
| Recommend | 33 | safe containment, clean recovery, staged quorum-safe plan |
| Instruction following | 6 | three worksheets, evidence refs, legible memo |
| **TOTAL** | **100** | **33 recommendation, 6 instruction following** |

## Criterion construction policy
- Prefer 30–42 focused criteria with meaningful independent weight, rather than 70–90 micro-criteria.
- Each criterion has exactly one objectively verifiable assertion, one category, a weight and one or more graded output files.
- A criterion checking 'identifies all exposed services' is too broad if individual failures matter; split by *independent causal mechanisms*, not by arbitrary per-row microcredits.
- Avoid contradictory criteria: do not simultaneously demand 'exactly N outputs' and a fourth required artifact; do not reward mutually exclusive dispositions for the same case.
- Avoid answer leakage in solver-visible task card: private ground truth is author-only.
- If a criterion is contingent on one of several valid outcomes, word it to accept all such outcomes. Do not add a negative criterion that penalizes a correct alternative.
- Do not reward repeating the same list in both memo and CSV as two independent semantic findings; grade the CSV for truth and the memo for synthesis/decision rationale.

## Coverage proof
Maintain `author_only/requirement_coverage.csv`: each atomic prompt or template requirement gets an ID, output artifact and rubric IDs. **Zero empty rubric-ID rows** before submission. Include all field-level rules in provided worksheets, source-citation requirements, counts, evidence limitations and operational sequencing.

## Rubric example (illustrative, not final)
```
{"item":1,"weight":4,"criterion":"Exposure register correctly distinguishes running affected images from registry-only artifacts at cutoff.","category":"analyze","verification_type":"text","grades_output_files":["exposure_register.csv"]}
```
Use the task's actual platform rubric schema and current form labels. Do not substitute a generic rubric format without validation.

## Audit conflict scan
Build an automated compatibility table for each pair of criteria referring to the same output or entity. Check cardinality, output count, exact versus allowed alternatives, time cutoff, statuses and category weights. Manually test the resulting 100-point reference submission against **all** criteria; if any two cannot both earn credit, redesign.
