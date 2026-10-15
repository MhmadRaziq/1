#!/usr/bin/env python3
"""Static preflight for a *built candidate task ZIP*, not this design kit.
Usage: python tools/preflight.py /path/to/candidate.zip
Only static checks: does NOT prove audit, licensing, correctness or sweep difficulty.
"""
from __future__ import annotations
import csv, io, json, re, sys, tomllib, zipfile
from collections import Counter
from pathlib import PurePosixPath

REQUIRED = ('instruction.md','task_card.md','task.toml','rubrics.json',
            'environment/Dockerfile','solution/solve.py','solution/solve.sh','tests/test.sh')
CATS = {'recommend','analyze','synthesize','explore','hypothesize','instruction_following'}
BANNED = ('__pycache__/', '.pytest_cache/', '.git/', 'author_only/', 'oracle.json',
          'truth_graph.json', 'forcing_case_blueprint.csv', 'shortcut_tournament_template.csv')

def run(path):
    errors=[]; warnings=[]
    def fail(msg): errors.append(msg)
    def warn(msg): warnings.append(msg)
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad: fail('ZIP CRC failure: '+bad)
        names=z.namelist(); ns=set(names)
        for n in names:
            p=PurePosixPath(n)
            if n.startswith('/') or '..' in p.parts or '\\' in n: fail('unsafe path '+n)
            if any(b in n for b in BANNED) or n.endswith(('.pyc','.db-wal','-wal','-shm','-journal')): fail('private/cache file '+n)
            if n.startswith('output/') or n.startswith('environment/data/output/'): fail('pre-filled outputs '+n)
        for n in REQUIRED:
            if n not in ns: fail('missing root file '+n)
        if any(n.startswith('submission/') or n.startswith('task/') for n in names): warn('possible parent wrapper')
        if 'task.toml' in ns:
            try:
                tom=tomllib.loads(z.read('task.toml').decode())
                if 'source' in tom.get('metadata',{}): fail('metadata.source previously rejected by platform')
                if tom.get('schema_version') != '1.1': warn('check schema_version against current platform')
                if tom.get('environment',{}).get('allow_internet') is not False: warn('environment not explicitly offline')
            except Exception as e: fail('bad task.toml: '+str(e))
        rub=[]
        if 'rubrics.json' in ns:
            try:
                rub=json.loads(z.read('rubrics.json'))
                if not isinstance(rub,list): fail('rubrics.json must be array');rub=[]
                if rub:
                    ids=[r.get('item') for r in rub]
                    if len(ids)!=len(set(map(str,ids))): fail('duplicate rubric item ID')
                    total=sum(r.get('weight',0) for r in rub)
                    if total!=100: fail(f'rubric total {total} != 100')
                    if any(not isinstance(r.get('weight'),int) or r['weight']<=0 for r in rub): fail('rubric weights must be positive integers')
                    cats=Counter()
                    for r in rub:
                        c=r.get('category');cats[c]+=r.get('weight',0)
                        if c not in CATS: warn('unrecognized rubric category '+str(c))
                        if len(r.get('criterion',''))>250: fail('criterion >250 chars: '+str(r.get('item')))
                        if not r.get('grades_output_files'): fail('criterion has no graded output: '+str(r.get('item')))
                    if cats['recommend']<30: fail('recommend points <30: '+str(cats['recommend']))
                    if not 1<=cats['instruction_following']<=10: fail('instruction_following points outside 1..10')
            except Exception as e: fail('bad rubrics.json: '+str(e))
        if 'tests/rubrics.json' in ns and 'rubrics.json' in ns:
            if json.loads(z.read('tests/rubrics.json'))!=json.loads(z.read('rubrics.json')): fail('tests/rubrics.json != root rubrics.json')
        if 'instruction.md' in ns:
            instr=z.read('instruction.md').decode('utf-8','replace')
            if 'http://' in instr or 'https://' in instr: warn('instruction contains URL; check offline/no-URLs contract')
            if re.search(r'priority order|highest numeric revision|lexicographic optimization',instr,re.I): warn('prompt may leak algorithm; professional quality review needed')
        if 'task_card.md' in ns:
            card=z.read('task_card.md').decode('utf-8','replace')
            for h in ['# Task description','# Complexity justification','## Taxonomy tags']:
                if h not in card: warn('task card missing '+h)
        covs=[n for n in names if n.endswith('requirement_map.csv') or n.endswith('requirement_coverage.csv')]
        if covs:
            for n in covs:
                rows=list(csv.DictReader(io.StringIO(z.read(n).decode('utf-8-sig'))))
                if not rows: fail('empty coverage map '+n)
                for i,row in enumerate(rows,2):
                    criterion=next((v for k,v in row.items() if 'rubric' in k.lower() or 'criterion' in k.lower()),None)
                    if criterion is not None and not criterion.strip(): fail(f'uncovered requirement in {n}:{i}')
        else: warn('no authoring requirement map found; audit coverage cannot be checked')
        for n in names:
            if n.endswith('.gz'):
                try:
                    import gzip
                    gzip.decompress(z.read(n))
                except Exception as e: fail('bad gzip '+n+': '+str(e))
    print('STATIC PREFLIGHT',path)
    print('ERRORS',len(errors),'WARNINGS',len(warnings))
    for e in errors: print('FAIL:',e)
    for w in warnings: print('WARN:',w)
    if not errors: print('PASS static shell only; private platform stages and semantic correctness unverified')
    return 1 if errors else 0

if __name__=='__main__':
    if len(sys.argv)!=2: print('Usage: python preflight.py candidate_task.zip');sys.exit(2)
    sys.exit(run(sys.argv[1]))
