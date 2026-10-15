#!/usr/bin/env python3
"""Check design-kit integrity; not a candidate submission validator."""
from pathlib import Path
import csv,json,sys
root=Path(__file__).resolve().parents[1]
required=['README_START_HERE.md','02_scenario/SOLVER_PROMPT_DRAFT.md','03_data_architecture/CAUSAL_TRUTH_MODEL.md','04_oracle_verifier/ORACLE_AND_GRADER_SPEC.md','05_rubric_audit/RUBRIC_ARCHITECTURE.md','06_quality_format/QUALITY_AND_FORMAT_GATES.md','07_red_team/HARDNESS_PROTOCOL.md','08_build/CURSOR_MASTER_BUILD_PROMPT.md','tools/preflight.py','author_only/forcing_case_blueprint.csv']
missing=[x for x in required if not (root/x).is_file()]
with (root/'author_only/forcing_case_blueprint.csv').open() as f: cases=list(csv.DictReader(f))
with (root/'author_only/requirement_coverage_blueprint.csv').open() as f: cov=list(csv.DictReader(f))
assert not missing,missing
assert len(cases)>=12,len(cases)
assert len({x['case_id'] for x in cases})==len(cases)
assert len(cov)>=20
assert all(x['planned_criterion_ids'].strip() for x in cov)
assert len({x['requirement_id'] for x in cov})==len(cov)
assert json.loads((root/'templates/record_shapes.json').read_text())
rub=json.loads((root/'author_only/illustrative_rubric_NOT_FOR_SUBMISSION.json').read_text())
assert sum(x['weight'] for x in rub)==100
assert sum(x['weight'] for x in rub if x['category']=='recommend')>=30
assert 1<=sum(x['weight'] for x in rub if x['category']=='instruction_following')<=10
ids={x['design_id'] for x in rub}
assert all(all(i in ids for i in x['planned_criterion_ids'].split(';')) for x in cov)
assert all(len(x['criterion'])<=250 for x in rub)
print('PASS kit integrity:',len(required),'required files;',len(cases),'challenge blueprints;',len(cov),'coverage blueprint rows')
