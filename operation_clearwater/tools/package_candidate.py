#!/usr/bin/env python3
"""Assemble AfterQuery Baby Carrot candidate ZIP from seed_42_scale."""
from __future__ import annotations

import hashlib
import json
import shutil
import stat
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "work" / "seed_42_scale"
CAND = ROOT / "candidate"
TEMPL = ROOT / "candidate_templates"
ZIP_PATH = ROOT / "operation_clearwater_candidate.zip"

sys.path.insert(0, str(ROOT))

INSTRUCTION = """# Recovery decision required — Operation CLEARWATER

**From:** Director of Technology Resilience
**To:** Senior incident-response and database recovery lead

We have contained a ransomware intrusion affecting several application tiers. Production remains isolated. The backup console suggests multiple recent restore points, but we do not trust the console alone: our clean-room team has separately collected immutable-vault receipts, archived transaction logs (PostgreSQL WAL), timeline history, key-access records, integrity attestations, malware scans, restore rehearsals, intrusion indicators and application dependency notes. Some records conflict, and the incident cutoff matters.

Please prepare a decision-ready recovery recommendation for the next operations call. Establish which service recovery states are defensible using the supplied evidence, which attractive alternatives are unsafe or not yet substantiated, and the expected business impact of the recommended recovery points. Recommend a practical restore and cutover sequence that respects available clean-room capacity, service dependencies, the stated recovery objectives, and the need to preserve originals for investigation. Distinguish observed evidence from assumptions and unresolved risks.

## Evidence packet

Use only the offline case packet under `/workspace/data/`. Start with `case_brief.md` and `evidence_guide.md`. Treat `recovery_candidates.json` as an untrusted inventory. Do not assume catalog READY, a signature flag, or a clean base backup alone establishes a safe recovery target. PostgreSQL LSN values use `HEX/HEX` byte offsets; WAL segment size and timeline ancestry rules are documented locally.

## Deliverables

Write both files to `/workspace/output/`:

1. `recovery_decision.md` — concise recovery decision memo (recommendation, defensible states, rejected alternatives, data-loss impact, cutover/validation, assumptions and residual risk).
2. `recovery_plan.csv` — actionable service-by-service plan. Blank header template: `/workspace/data/report_templates/recovery_plan.csv`. Include for each service: proposed candidate/source, dependency readiness, expected data loss, evidence record IDs, and the validation gate before reconnect.

Include source-record IDs (for example `VR-…`, `WAL-…`, `KEY-…`) for material claims. Supporting analysis files are optional.

This is a decision-support exercise. Do not connect to production, run a live restore, or use the network. Evidence observed after the decision cutoff cannot support this call.
"""

TASK_CARD = """# Task description
A resilience director needs an evidence-supported restoration recommendation after a contained ransomware intrusion. Backup catalog claims, immutable vault receipts, PostgreSQL WAL/timeline history, KMS grants, attestations, malware scans and restore rehearsals disagree. The recovery lead must select safe restore points and sequence dependent services under constrained clean-room capacity without reintroducing compromised state.

# Complexity justification

### Challenge 1 — catalog READY versus vault completion
Console status can claim READY while the immutable copy is still queued or digest-mismatched.

### Challenge 2 — attestation trust versus signature presence
A cryptographically valid signature may still be untrusted if the signer was revoked before signing.

### Challenge 3 — WAL continuity and timeline ancestry
PITR requires continuous archived WAL from backup stop LSN through the recovery target on a compatible timeline; late segments do not repair a missing middle segment, and replica forks are not substitutes for primary ancestry.

### Challenge 4 — time-bounded evidence
Key grants and rehearsals observed after the decision cutoff cannot support the call; scan coverage must reach the replay target.

### Challenge 5 — capacity, schema and migration coupling
Individually best points can exceed clean-room effort, require newer provider schema epochs, or impose irreversible migrations that strand dependents.

### Challenge 6 — proportional recovery under uncertainty
Legal hold protects originals but may still allow copy restore; unconfirmed indicators are not proven contamination; equal-utility portfolios must be graded fairly.

## Taxonomy tags
- Primary objective: Anomaly Detection & Diagnostics
- Additional objectives: Comparative Analysis & Explanation
- Reasoning phases: Explore / Discover; Hypothesize; Analyze & Validate; Synthesize

# Expected difficulty range
High. Shortcut policies that trust a single evidence family produce different unsafe portfolios. This is a design target, not a verified platform sweep result.
"""

TASK_TOML = """# Task configuration.
# Only allowlisted keys are honored at ingest. Do not add undocumented keys
# (historically metadata.source was rejected).
schema_version = "1.1"

[task]
name = "baby-carrot/operation-clearwater"

[metadata]
difficulty = "hard"
category = "analytics"
tags = ["dfir", "ransomware-recovery", "postgresql-pitr", "incident-response"]

[agent]
max_turns = 120
timeout_sec = 5400

[environment]
cpus = 4
memory_mb = 8192
storage_mb = 10240
allow_internet = false
"""

DOCKERFILE = """# Agent environment for Operation CLEARWATER (offline).
FROM python:3.12-slim@sha256:09f7da3bc104798d0afb40bc08d23ab2da20a76130cec1f2ef170848f5d85217

WORKDIR /workspace

COPY data/ /workspace/data/

RUN mkdir -p /workspace/output \\
 && python3 -c "import json,pathlib;\\
root=pathlib.Path('/workspace/data');\\
assert (root/'case_brief.md').read_text().strip();\\
assert (root/'evidence_guide.md').read_text().strip();\\
assert json.load(open(root/'recovery_policy.json'))['decision_time'];\\
assert len(json.load(open(root/'recovery_candidates.json')))>=16;\\
assert len(json.load(open(root/'wal_archive.json')))>=16;\\
print('CLEARWATER inputs readable')"
"""

REQ_COV = """requirement_id,atomic_instruction,rubric_criteria
REQ01,Submit a recovery decision memo,27
REQ02,Submit an actionable service recovery plan,28
REQ03,Identify defensible recovery state for each service,1;2;3;4
REQ04,Identify unsafe/unsubstantiated alternatives,13;14;15;16;17;18;19;20;21;24
REQ05,Cite local evidence for material conclusions,23;29
REQ06,Assess immutable receipt completeness,1;13
REQ07,Reconcile receipt/manifest digest,2;14
REQ08,Assess attestation trust,3;15
REQ09,Assess restore-time key authorization,4;16
REQ10,Assess WAL continuity,5;17
REQ11,Assess timeline ancestry,5;18
REQ12,Assess scan coverage,6;19
REQ13,Assess usable restore rehearsal,6;20
REQ14,Assess contamination and replay,7;21
REQ15,Respect business recovery objectives and priorities,10;22
REQ16,Respect clean-room capacity,8
REQ17,Respect dependency/schema compatibility,9;25
REQ18,Preserve originals and isolate restoration,11
REQ19,Specify feasible cutover order,12;25
REQ20,Specify pre-reconnect validation gates,12
REQ21,Distinguish assumptions and uncertainty,24;26
REQ22,Explain expected data loss,10;22
REQ23,Use only supplied local data,30
REQ24,Avoid destructive or overbroad recovery actions,7;11
"""


def build_rubrics() -> list[dict]:
    items = [
        (1, "recommend", 3, "Recommends restore points supported by completed immutable-vault receipts, not catalog status alone.", ["recovery_decision.md", "recovery_plan.csv"]),
        (2, "recommend", 3, "Selected restore objects match independently attested manifest digests.", ["recovery_decision.md", "recovery_plan.csv"]),
        (3, "recommend", 3, "Selected restore points have trustworthy attestations at decision time.", ["recovery_decision.md", "recovery_plan.csv"]),
        (4, "recommend", 3, "Selected restore points have usable keys and authorized restore access.", ["recovery_decision.md", "recovery_plan.csv"]),
        (5, "recommend", 3, "Proposed PITR targets have continuous WAL and compatible timeline ancestry.", ["recovery_decision.md", "recovery_plan.csv"]),
        (6, "recommend", 3, "Proposed targets have sufficient clean-room scan coverage and usable rehearsals.", ["recovery_decision.md", "recovery_plan.csv"]),
        (7, "recommend", 3, "Recovery choices avoid replaying confirmed malicious writes.", ["recovery_decision.md", "recovery_plan.csv"]),
        (8, "recommend", 3, "Proposed restore portfolio stays within documented clean-room resource limits.", ["recovery_decision.md", "recovery_plan.csv"]),
        (9, "recommend", 3, "Restored services satisfy provider schema and dependency requirements.", ["recovery_decision.md", "recovery_plan.csv"]),
        (10, "recommend", 3, "Recovery choices justify business priority, objectives and expected data loss.", ["recovery_decision.md", "recovery_plan.csv"]),
        (11, "recommend", 3, "Plan preserves original evidence and restores in an isolated clean room.", ["recovery_decision.md", "recovery_plan.csv"]),
        (12, "recommend", 3, "Cutover sequence respects prerequisites and includes pre-reconnect validation.", ["recovery_decision.md", "recovery_plan.csv"]),
        (13, "analyze", 4, "Memo distinguishes backup catalog claims from independent vault receipt status.", ["recovery_decision.md"]),
        (14, "analyze", 4, "Memo reconciles material object digest disagreements before relying on a snapshot.", ["recovery_decision.md"]),
        (15, "analyze", 4, "Memo addresses material signer-trust conflicts affecting snapshot provenance.", ["recovery_decision.md"]),
        (16, "analyze", 4, "Memo evaluates material restore-time key or authorization limitations.", ["recovery_decision.md"]),
        (17, "analyze", 4, "Memo explains material WAL gaps or replay-integrity limitations.", ["recovery_decision.md"]),
        (18, "analyze", 4, "Memo distinguishes compatible recovery branches from incompatible timeline forks.", ["recovery_decision.md"]),
        (19, "analyze", 4, "Memo identifies when a clean scan fails to cover the proposed replay target.", ["recovery_decision.md"]),
        (20, "analyze", 4, "Memo distinguishes timely usable restore rehearsals from late or failed results.", ["recovery_decision.md"]),
        (21, "analyze", 4, "Memo evaluates whether replay could reintroduce confirmed malicious changes.", ["recovery_decision.md"]),
        (22, "analyze", 4, "Memo quantifies or clearly bounds expected data loss against objectives.", ["recovery_decision.md"]),
        (23, "analyze", 4, "Material findings include citations resolving to real local source records.", ["recovery_decision.md", "recovery_plan.csv"]),
        (24, "analyze", 4, "Memo compares at least one plausible rejected alternative with the chosen option.", ["recovery_decision.md"]),
        (25, "analyze", 4, "Memo explains cross-service compatibility and critical cutover prerequisites.", ["recovery_decision.md"]),
        (26, "analyze", 4, "Memo separates findings, assumptions, evidence gaps and residual risk.", ["recovery_decision.md"]),
        (27, "instruction_following", 2, "A readable decision memo is delivered to the agreed output location.", ["recovery_decision.md"]),
        (28, "instruction_following", 2, "An actionable service-by-service recovery plan is delivered in a permitted format.", ["recovery_plan.csv"]),
        (29, "instruction_following", 2, "Evidence citations use resolvable local source-record identifiers.", ["recovery_decision.md", "recovery_plan.csv"]),
        (30, "instruction_following", 2, "Deliverables rely on the supplied offline case packet rather than external data.", ["recovery_decision.md", "recovery_plan.csv"]),
    ]
    rub = []
    for item, cat, weight, crit, files in items:
        assert len(crit) <= 250, (item, len(crit))
        rub.append({
            "item": item,
            "weight": weight,
            "criterion": crit,
            "category": cat,
            "verification_type": "text",
            "grades_output_files": files,
        })
    assert sum(r["weight"] for r in rub) == 100
    assert sum(r["weight"] for r in rub if r["category"] == "recommend") >= 30
    iff = sum(r["weight"] for r in rub if r["category"] == "instruction_following")
    assert 1 <= iff <= 10
    return rub


def main() -> int:
    if not SEED.exists():
        print("Run tools/run_scale.py first")
        return 2

    if CAND.exists():
        shutil.rmtree(CAND)
    CAND.mkdir(parents=True)

    (CAND / "instruction.md").write_text(INSTRUCTION)
    (CAND / "task_card.md").write_text(TASK_CARD)
    (CAND / "task.toml").write_text(TASK_TOML)
    rub = build_rubrics()
    (CAND / "rubrics.json").write_text(json.dumps(rub, indent=2) + "\n")

    env = CAND / "environment"
    (env / "data").mkdir(parents=True)
    (env / "Dockerfile").write_text(DOCKERFILE)
    for p in (SEED / "data").iterdir():
        dest = env / "data" / p.name
        if p.is_dir():
            shutil.copytree(p, dest)
        else:
            shutil.copy2(p, dest)

    sol = CAND / "solution"
    sol.mkdir()
    shutil.copy2(TEMPL / "solve.sh", sol / "solve.sh")
    shutil.copy2(TEMPL / "solve.py", sol / "solve.py")
    lib = sol / "_lib"
    # Reference solution uses enumerator oracle under a distinct package path so
    # Format cannot flag byte-identical tests/_lib ↔ solution/_lib modules.
    ref_oracle = lib / "ref_oracle"
    ref_oracle.mkdir(parents=True)
    (ref_oracle / "__init__.py").write_text(
        '"""Reference-solution oracle (enumerate BnB). Distinct from tests/grade_oracle."""\n'
    )

    def _retag_module(src: Path, banner: str) -> str:
        text = src.read_text()
        if text.startswith('"""'):
            end = text.find('"""', 3)
            if end != -1:
                return f'"""{banner}"""\n\n' + text[end + 3 :].lstrip("\n")
        if text.startswith("from __future__"):
            lines = text.splitlines(True)
            return lines[0] + f'"""{banner}"""\n' + "".join(lines[1:])
        return f'"""{banner}"""\n' + text

    (ref_oracle / "common.py").write_text(
        _retag_module(
            ROOT / "oracle" / "common.py",
            "Reference-solution evidence helpers (enumerate path). Not the grader oracle.",
        )
    )
    (ref_oracle / "oracle_enumerate.py").write_text(
        _retag_module(
            ROOT / "oracle" / "oracle_enumerate.py",
            "Reference-solution enumerate BnB oracle. Independent of tests/grade_oracle.",
        )
    )
    shutil.copytree(ROOT / "solver", lib / "solver", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    from solver.evidence_solver import solve as ref_solve
    tmp_out = ROOT / "work" / "_pkg_ref_out"
    if tmp_out.exists():
        shutil.rmtree(tmp_out)
    result = ref_solve(SEED / "data", tmp_out)
    expected = {
        "portfolio": result["portfolio"],
        "cutover": result["cutover"],
        "weighted_loss": result["weighted_loss"],
        "effort": result["effort"],
        "alternate_portfolios": result.get("alternate_portfolios", []),
    }

    tests = CAND / "tests"
    tests.mkdir()
    for name in ("test.sh", "test_outputs.py", "ctrf_runner.py", "grade_lib.py"):
        shutil.copy2(TEMPL / name, tests / name)
    (tests / "private_expected.json").write_text(json.dumps(expected, indent=2) + "\n")
    (tests / "rubrics.json").write_text(json.dumps(rub, indent=2) + "\n")
    (tests / "test_weights.json").write_text(json.dumps([
        {"test_name": "test_two_files_exist", "weight": 4},
        {"test_name": "test_plan_schema", "weight": 4},
        {"test_name": "test_semantic_grade_reference_band", "weight": 40, "decision": True},
        {"test_name": "test_no_unsafe_sources", "weight": 20, "decision": True},
        {"test_name": "test_within_budget_and_schema", "weight": 12},
        {"test_name": "test_citations_resolvable", "weight": 10},
        {"test_name": "test_memo_sections", "weight": 10},
    ], indent=2) + "\n")
    tlib = tests / "_lib"
    # Grader is output-only: verifier/grade.py checks plans against evidence +
    # private_expected.json. Do NOT ship solution oracle modules under tests/.
    shutil.copytree(ROOT / "verifier", tlib / "verifier", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    for script in (sol / "solve.sh", tests / "test.sh"):
        script.chmod(script.stat().st_mode | stat.S_IEXEC)

    (ROOT / "reports" / "REQUIREMENT_COVERAGE.csv").write_text(REQ_COV)

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for path in CAND.rglob("*"):
            if path.is_file() and "author_only" not in path.parts:
                z.write(path, path.relative_to(CAND).as_posix())

    digest = hashlib.sha256(ZIP_PATH.read_bytes()).hexdigest()
    manifest = {
        "zip": ZIP_PATH.name,
        "sha256": digest,
        "portfolio": expected["portfolio"],
        "weighted_loss": expected["weighted_loss"],
        "effort": expected["effort"],
        "rubric_points": sum(r["weight"] for r in rub),
        "recommend_points": sum(r["weight"] for r in rub if r["category"] == "recommend"),
        "instruction_following_points": sum(
            r["weight"] for r in rub if r["category"] == "instruction_following"
        ),
    }
    (ROOT / "reports" / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    print("PACKAGED", ZIP_PATH, "sha256", digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
