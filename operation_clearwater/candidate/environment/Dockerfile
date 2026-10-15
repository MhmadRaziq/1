# Agent environment for Operation CLEARWATER (offline).
FROM python:3.12-slim@sha256:09f7da3bc104798d0afb40bc08d23ab2da20a76130cec1f2ef170848f5d85217

WORKDIR /workspace

COPY data/ /workspace/data/

RUN mkdir -p /workspace/output \
 && python3 -c "import json,pathlib;\
root=pathlib.Path('/workspace/data');\
assert (root/'case_brief.md').read_text().strip();\
assert (root/'evidence_guide.md').read_text().strip();\
assert json.load(open(root/'recovery_policy.json'))['decision_time'];\
assert len(json.load(open(root/'recovery_candidates.json')))>=16;\
assert len(json.load(open(root/'wal_archive.json')))>=16;\
print('CLEARWATER inputs readable')"
