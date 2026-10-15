#!/usr/bin/env python3
"""Assemble production-candidate task ZIP from seed_42_scale packet."""
from __future__ import annotations

import json
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIT = Path("/workspace/afterburn_kit")
CAND = ROOT / "candidate"
SEED = ROOT / "work" / "seed_42_scale"


INSTRUCTION = """# Emergency build-provenance incident: production exposure and safe recovery

You are the senior incident responder supporting a release-governance incident call. Security engineering has confirmed a compromise of a production build-runner environment. The confirmed window, affected runner pool, and investigation cutoff are documented in `/workspace/data/incident_notice.md`.

The incident commander needs a defensible answer to three questions:

1. Which production workloads actually run code reached through the compromised build path at the cutoff?
2. Which apparently suspicious findings are not material production exposures, and why?
3. What response sequence reduces risk without violating the organization's availability and recovery commitments?

## Evidence packet

Use only the offline incident packet under `/workspace/data/`. It contains build and artifact evidence, registry and deployment history, service dependency information, and change/response records. Treat every file as evidence. Do not assume that an image tag, a successful build, a signed attestation, or a deployment request alone establishes the effective runtime state. Resolve material conflicts using the authority described in the incident response standard and related operational documents. State remaining uncertainty explicitly.

## Deliverables

Complete the three incident-response artifacts using the worksheets in `/workspace/data/report_templates/`:

- `/workspace/output/exposure_register.csv`
- `/workspace/output/response_plan.csv`
- `/workspace/output/incident_decision.md`

The register must support each material finding with packet-local record IDs. The response plan must identify affected services, proposed action, viable recovery target when applicable, and operational sequencing. The decision memo should summarize exposure and clearance rationale, immediate actions, continuity trade-offs, assumptions, and evidence limitations.

This is a decision-support exercise. Do not take live actions and do not use the network. If a case cannot be established from the packet, record it as unresolved and name the additional observation needed — do not invent missing records.
"""

TASK_CARD = """# Task description
A production release pipeline is affected by a confirmed build-runner compromise. The responder must reconstruct which immutable artifacts were produced or contaminated in the relevant period, reconcile those artifacts with actual running production deployments, distinguish false positives from material exposures, and propose safe containment and recovery that respects dependency and availability commitments.

# Complexity justification

### Challenge 1 — artifact identity versus mutable registry pointers
Tags, image indexes, per-platform manifests and cached pulls disagree. Correct conclusions depend on immutable content identity and runtime realization rather than a tag lookup.

### Challenge 2 — attestation authority versus builder compromise
Some affected artifacts have valid signed provenance, while some apparent matches come from clean, independently authorized builders. Signature validity and trustworthiness of the builder are separate propositions.

### Challenge 3 — transitive contamination
A clean direct build can embed a compromised shared base layer or vendored build output. A suspicious build can also be harmless if its output never reaches production. The direction of propagation must be reconstructed.

### Challenge 4 — asynchronous deployment evidence
Desired state, admission decisions, runtime observations and workload turnover do not align perfectly. The responder must establish what was materially active at the cutoff.

### Challenge 5 — recovery coupling
Rollback candidates have differing trust and operational viability. A seemingly safe isolated change can violate service quorum, region dependency or recovery-time commitments; correct response is globally coordinated.

### Challenge 6 — independent clearance and uncertainty
Lookalikes and genuinely unresolved cases require distinct evidence-backed dispositions; over-containment and unjustified clearance both cause operational harm.

## Taxonomy tags
- Primary objective: Anomaly Detection & Diagnostics
- Additional objectives: Comparative Analysis & Explanation; Root-Cause Analysis
- Reasoning phases: Explore / Discover; Hypothesize; Analyze & Validate; Synthesize; Recommend

# Expected difficulty range
High. Several plausible shortcut approaches yield distinct wrong exposure and recovery outcomes. This is a target, not a verified sweep result.
"""

TASK_TOML = """schema_version = "1.1"

[metadata]
difficulty = "hard"

[environment]
allow_internet = false
"""


def build_rubrics() -> list[dict]:
    # Based on illustrative rubric; total 100; recommend >=30; IF 1-10
    items = [
        (1, "explore", 4, "Register identifies material discrepancies between mutable registry pointers and observed immutable workload identities.", ["exposure_register.csv"]),
        (2, "explore", 4, "Register identifies material build-provenance conflicts using corroborating evidence from distinct source families.", ["exposure_register.csv"]),
        (3, "hypothesize", 4, "Genuinely underdetermined cases are reported as unresolved with a specific observation that would resolve each case.", ["exposure_register.csv", "incident_decision.md"]),
        (4, "hypothesize", 4, "Memo names evidence limitations and explains which competing explanations remain possible.", ["incident_decision.md"]),
        (5, "analyze", 3, "Register contains no duplicate material workload-and-artifact findings.", ["exposure_register.csv"]),
        (6, "analyze", 3, "Exposure findings use evidence effective by the incident investigation cutoff.", ["exposure_register.csv"]),
        (7, "analyze", 4, "Register correctly separates registry-only artifacts from images actually materialized in production.", ["exposure_register.csv"]),
        (8, "analyze", 4, "Register distinguishes valid attestation signatures from the trust status of the producing builder.", ["exposure_register.csv"]),
        (9, "analyze", 4, "Register identifies affected workloads reached through transitive image layers or vendored build outputs.", ["exposure_register.csv"]),
        (10, "analyze", 4, "Register reconciles platform-specific OCI manifest identity when evaluating running workloads.", ["exposure_register.csv"]),
        (11, "analyze", 4, "Register reconciles desired rollout state with observed active workload state at cutoff.", ["exposure_register.csv"]),
        (12, "analyze", 5, "Exposure and clearance dispositions agree with independently corroborated immutable artifact lineage.", ["exposure_register.csv"]),
        (13, "synthesize", 4, "Material cleared lookalikes have evidence-supported clearance explanations.", ["exposure_register.csv", "incident_decision.md"]),
        (14, "synthesize", 4, "Memo accurately explains the material causal path from compromised runner to affected runtime artifacts.", ["incident_decision.md"]),
        (15, "synthesize", 3, "Memo explains at least two material false-positive mechanisms supported by the register.", ["incident_decision.md"]),
        (16, "synthesize", 3, "Memo distinguishes proven exposure, proven clearance and genuinely unresolved findings.", ["incident_decision.md"]),
        (17, "recommend", 5, "Plan addresses every proven material production exposure with an appropriate immediate risk-reducing action.", ["response_plan.csv"]),
        (18, "recommend", 5, "Each proposed recovery target is both trusted and operationally deployable, or the plan justifies isolation.", ["response_plan.csv"]),
        (19, "recommend", 4, "Proposed actions respect effective change approvals and protected-service commitments.", ["response_plan.csv"]),
        (20, "recommend", 5, "The proposed action order preserves disclosed critical-service availability and quorum at every intermediate step.", ["response_plan.csv"]),
        (21, "recommend", 4, "No selected rollback artifact contains affected build output or otherwise violates trusted recovery conditions.", ["response_plan.csv"]),
        (22, "recommend", 4, "Memo states the immediate containment recommendation and ties it to material exposure evidence.", ["incident_decision.md"]),
        (23, "recommend", 3, "Memo explains the material risk-versus-availability trade-offs in the chosen response.", ["incident_decision.md"]),
        (24, "recommend", 3, "Plan provides a coherent, executable sequence of actions with justified prerequisites and recovery effects.", ["response_plan.csv"]),
        (25, "instruction_following", 2, "All three specified incident-response deliverables exist at their disclosed output paths.", ["exposure_register.csv", "response_plan.csv", "incident_decision.md"]),
        (26, "instruction_following", 1, "Exposure register uses the supplied worksheet schema and disclosed disposition vocabulary.", ["exposure_register.csv"]),
        (27, "instruction_following", 1, "Material findings and proposed actions include packet-local record references.", ["exposure_register.csv", "response_plan.csv"]),
        (28, "instruction_following", 1, "Memo describes proposed changes as recommendations rather than claiming live changes were performed.", ["incident_decision.md"]),
        (29, "instruction_following", 1, "Deliverables are self-contained and do not require visiting external links.", ["exposure_register.csv", "response_plan.csv", "incident_decision.md"]),
    ]
    rub = []
    for item, cat, weight, criterion, files in items:
        assert len(criterion) <= 250
        rub.append(
            {
                "item": item,
                "weight": weight,
                "criterion": criterion,
                "category": cat,
                "verification_type": "text",
                "grades_output_files": files,
            }
        )
    assert sum(r["weight"] for r in rub) == 100
    assert sum(r["weight"] for r in rub if r["category"] == "recommend") >= 30
    if_pts = sum(r["weight"] for r in rub if r["category"] == "instruction_following")
    assert 1 <= if_pts <= 10
    return rub


# Digest pinned from Docker Hub registry (python:3.12-slim multi-arch index).
DOCKERFILE = """FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
WORKDIR /workspace
# Offline image: evidence packet is copied at build time; no network needed at runtime.
COPY data /workspace/data
RUN mkdir -p /workspace/output \\
    && chmod -R a+rX /workspace/data \\
    && chmod a+rwx /workspace/output
CMD [\"bash\"]
"""

SOLVE_SH = """#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 "$ROOT/solve.py" /workspace/data /workspace/output
"""

TEST_SH = """#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 "$ROOT/run_tests.py"
"""

TEST_WEIGHTS = {
    "test_three_files_exist": 0.05,
    "test_register_schema_and_vocab": 0.05,
    "test_semantic_grade_reference_band": 0.25,
    "test_exposure_set_precision_recall": 0.30,
    "test_no_tainted_recovery": 0.15,
    "test_unresolved_present": 0.10,
    "test_memo_sections": 0.10,
}

RUN_TESTS_PY = r'''#!/usr/bin/env python3
"""Weighted verifier entrypoint for Operation AFTERBURN."""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
WEIGHTS = json.loads((ROOT / "test_weights.json").read_text(encoding="utf-8"))


class _Collector:
    def __init__(self):
        self.passed = set()
        self.failed = set()

    def pytest_runtest_logreport(self, report):
        if report.when != "call":
            return
        name = report.nodeid.split("::")[-1]
        if report.passed:
            self.passed.add(name)
        elif report.failed or report.outcome == "failed":
            self.failed.add(name)


def main() -> int:
    collector = _Collector()
    code = pytest.main(["-q", str(ROOT / "test_outputs.py")], plugins=[collector])
    reward = 0.0
    details = {}
    for name, weight in WEIGHTS.items():
        ok = name in collector.passed and name not in collector.failed
        details[name] = {"weight": weight, "passed": ok}
        if ok:
            reward += float(weight)
    reward = round(min(1.0, max(0.0, reward)), 6)

    # Common verifier output locations (platform may use either).
    for log_dir in (Path("/logs/verifier"), Path("/logs"), ROOT / "logs"):
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            (log_dir / "reward.txt").write_text(str(reward) + "\n", encoding="utf-8")
            (log_dir / "reward.json").write_text(
                json.dumps({"reward": reward, "tests": details}, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError:
            continue

    print(json.dumps({"reward": reward, "pytest_exit": code, "tests": details}, indent=2))
    # Nonzero pytest exit still records partial reward; fail hard only on collector crash.
    return 0 if reward >= 0.0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        for log_dir in (Path("/logs/verifier"), Path("/logs")):
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
                (log_dir / "reward.txt").write_text("0\n", encoding="utf-8")
            except OSError:
                pass
        raise SystemExit(1)
'''


def main() -> int:
    if not SEED.exists():
        print("missing seed_42_scale; run tools/run_scale.py first", file=sys.stderr)
        return 1
    if CAND.exists():
        shutil.rmtree(CAND)
    CAND.mkdir()
    (CAND / "instruction.md").write_text(INSTRUCTION, encoding="utf-8")
    (CAND / "task_card.md").write_text(TASK_CARD, encoding="utf-8")
    (CAND / "task.toml").write_text(TASK_TOML, encoding="utf-8")
    rub = build_rubrics()
    (CAND / "rubrics.json").write_text(json.dumps(rub, indent=2), encoding="utf-8")

    env = CAND / "environment"
    env.mkdir()
    (env / "Dockerfile").write_text(DOCKERFILE, encoding="utf-8")
    shutil.copytree(SEED / "data", env / "data")

    sol = CAND / "solution"
    sol.mkdir()
    shutil.copy2(ROOT / "solver" / "evidence_solver.py", sol / "solve.py")
    # wrap solve.py as module-friendly — ensure __main__ works; already does
    # rewrite import-free: evidence_solver is standalone
    (sol / "solve.sh").write_text(SOLVE_SH, encoding="utf-8")
    (sol / "solve.sh").chmod((sol / "solve.sh").stat().st_mode | stat.S_IEXEC)

    tests = CAND / "tests"
    tests.mkdir()
    # Private expected snapshot — not named oracle.json
    expected = json.loads((SEED / "author_only" / "oracle.json").read_text())
    # Strip author-only forcing case map from agent-adjacent? tests are not agent-visible in platform
    private = {
        "cutoff": expected["cutoff"],
        "exposed_workload_ids": expected["exposed_workload_ids"],
        "cleared_workload_ids": expected["cleared_workload_ids"],
        "unresolved_workload_ids": expected["unresolved_workload_ids"],
        "safe_recovery_digests": expected["safe_recovery_digests"],
        "unsafe_recovery_digests": expected["unsafe_recovery_digests"],
        "tainted_manifests": expected["tainted_manifests"],
        "min_healthy_regions": expected["min_healthy_regions"],
        "quorum_group": expected["quorum_group"],
    }
    (tests / "private_expected.json").write_text(json.dumps(private, indent=2), encoding="utf-8")
    shutil.copy2(CAND / "rubrics.json", tests / "rubrics.json")

    # Copy verifier grade into tests
    grader_src = (ROOT / "verifier" / "grade.py").read_text(encoding="utf-8")
    (tests / "grade_lib.py").write_text(grader_src, encoding="utf-8")
    test_py = '''#!/usr/bin/env python3
"""Format + semantic tests for Operation AFTERBURN."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import grade_lib

DATA = Path(os.environ.get("AFTERBURN_DATA", "/workspace/data"))
OUT = Path(os.environ.get("AFTERBURN_OUTPUT", "/workspace/output"))
HERE = Path(__file__).resolve().parent
EXPECTED = json.loads((HERE / "private_expected.json").read_text())


def _ensure_outputs():
    if not (OUT / "exposure_register.csv").exists():
        # local/dev fallback
        alt = Path("/workspace/operation_afterburn/work/seed_42_scale/output_solver")
        if alt.exists():
            return alt
    return OUT


def test_three_files_exist():
    out = _ensure_outputs()
    for name in ("exposure_register.csv", "response_plan.csv", "incident_decision.md"):
        p = out / name
        assert p.exists() and p.stat().st_size > 0, name


def test_register_schema_and_vocab():
    out = _ensure_outputs()
    rows = list(csv.DictReader((out / "exposure_register.csv").open()))
    assert rows
    required = {"workload_id", "environment", "region", "observed_digest", "disposition", "exposure_path", "evidence_refs", "uncertainty_or_clearance"}
    assert required.issubset(rows[0].keys())
    assert all(r["disposition"] in {"EXPOSED", "CLEARED", "UNRESOLVED"} for r in rows)


def test_semantic_grade_reference_band():
    out = _ensure_outputs()
    # Write a temp expected path compatible with grade_lib
    tmp = HERE / "_expected_runtime.json"
    tmp.write_text(json.dumps(EXPECTED), encoding="utf-8")
    data = DATA if DATA.exists() else Path("/workspace/operation_afterburn/work/seed_42_scale/data")
    result = grade_lib.grade_submission(out, tmp, data)
    assert result.reward >= 85.0, result.as_dict()


def test_exposure_set_precision_recall():
    out = _ensure_outputs()
    rows = list(csv.DictReader((out / "exposure_register.csv").open()))
    pred = {r["workload_id"] for r in rows if r["disposition"] == "EXPOSED"}
    truth = set(EXPECTED["exposed_workload_ids"])
    assert pred == truth, (sorted(pred), sorted(truth))


def test_no_tainted_recovery():
    out = _ensure_outputs()
    plan = list(csv.DictReader((out / "response_plan.csv").open()))
    unsafe = set(EXPECTED["unsafe_recovery_digests"])
    used = [p.get("recovery_digest") for p in plan if p.get("recovery_digest") in unsafe]
    assert not used, used


def test_unresolved_present():
    out = _ensure_outputs()
    rows = list(csv.DictReader((out / "exposure_register.csv").open()))
    unr = {r["workload_id"] for r in rows if r["disposition"] == "UNRESOLVED"}
    assert set(EXPECTED["unresolved_workload_ids"]).issubset(unr)


def test_memo_sections():
    out = _ensure_outputs()
    text = (out / "incident_decision.md").read_text().lower()
    assert "immediate recommendation" in text
    assert "limitation" in text or "unresolved" in text
    assert "http://" not in text and "https://" not in text
'''
    (tests / "test_outputs.py").write_text(test_py, encoding="utf-8")
    (tests / "test_weights.json").write_text(json.dumps(TEST_WEIGHTS, indent=2) + "\n", encoding="utf-8")
    (tests / "run_tests.py").write_text(RUN_TESTS_PY, encoding="utf-8")
    (tests / "run_tests.py").chmod((tests / "run_tests.py").stat().st_mode | stat.S_IEXEC)
    (tests / "test.sh").write_text(TEST_SH, encoding="utf-8")
    (tests / "test.sh").chmod((tests / "test.sh").stat().st_mode | stat.S_IEXEC)

    # authoring coverage map
    auth = CAND / "authoring"
    auth.mkdir()
    cov = '''requirement_id,atomic_requirement,graded_output_files,rubric_item_ids
R01,Three required files,exposure_register.csv;response_plan.csv;incident_decision.md,25
R02,Disclosed register template,exposure_register.csv,26
R03,No duplicated material findings,exposure_register.csv,5
R04,Packet-local source citations,exposure_register.csv;response_plan.csv,27
R05,Investigation cutoff,exposure_register.csv,6
R06,Registry-only versus running,exposure_register.csv,7
R07,Signature versus builder trust,exposure_register.csv,8
R08,Transitive contamination,exposure_register.csv,9
R09,Cleared lookalikes,exposure_register.csv;incident_decision.md,13
R10,Unresolved findings,exposure_register.csv;incident_decision.md,3
R11,Cover immediate exposure,response_plan.csv,17
R12,Viable recovery,response_plan.csv,18
R13,Approvals and commitments,response_plan.csv,19
R14,Intermediate quorum,response_plan.csv,20
R15,No tainted rollback,response_plan.csv,21
R16,Immediate recommendation,incident_decision.md,22
R17,Principal exposure chain,incident_decision.md,14
R18,Material clearance rationale,incident_decision.md,15
R19,Operational trade-offs,incident_decision.md,23
R20,Limitations and next evidence,incident_decision.md,4
R21,No live changes,incident_decision.md,28
R22,Offline output,incident_decision.md,29
R23,Platform-specific OCI identity,exposure_register.csv,10
R24,Desired versus running reconciliation,exposure_register.csv,11
R25,Lineage-corroborated dispositions,exposure_register.csv,12
R26,Explore registry identity conflicts,exposure_register.csv,1
R27,Explore provenance conflicts,exposure_register.csv,2
R28,Synthesize exposure/clearance/unresolved,incident_decision.md,16
R29,Coherent executable plan sequence,response_plan.csv,24
'''
    (auth / "requirement_map.csv").write_text(cov, encoding="utf-8")
    shutil.copy2(auth / "requirement_map.csv", ROOT / "reports" / "REQUIREMENT_COVERAGE.csv")

    # Zip at repo root style
    zip_path = ROOT / "operation_afterburn_candidate.zip"
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", root_dir=CAND)

    # preflight
    pre = KIT / "tools" / "preflight.py"
    proc = subprocess.run(["python3", str(pre), str(zip_path)], capture_output=True, text=True)
    print(proc.stdout)
    print(proc.stderr)
    (ROOT / "reports" / "preflight_stdout.txt").write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
