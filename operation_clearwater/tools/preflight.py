#!/usr/bin/env python3
"""Static preflight for CLEARWATER candidate ZIP."""
from __future__ import annotations

import json
import tomllib
import zipfile
from pathlib import Path

FORBIDDEN_NAMES = {
    "author_only", "modes.json", "forcing_cases.json", "oracle.json",
    "truth_graph.json", "DO_NOT_SHIP.md",
}
ALLOWED_TOML_TOP = {"schema_version", "task", "metadata", "agent", "environment", "verifier", "solution"}
ALLOWED_META = {"difficulty", "category", "tags", "author_name", "author_email", "author_organization"}


def check_zip(path: Path) -> list[str]:
    errors = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        for n in names:
            low = n.lower()
            for bad in FORBIDDEN_NAMES:
                if bad.lower() in low and "report_templates" not in low:
                    # allow nothing from author_only
                    if bad in ("author_only", "modes.json", "forcing_cases.json", "DO_NOT_SHIP.md"):
                        errors.append(f"forbidden path in zip: {n}")
        required = [
            "instruction.md", "task.toml", "task_card.md", "rubrics.json",
            "environment/Dockerfile", "solution/solve.sh", "tests/test.sh",
        ]
        for r in required:
            if r not in names and not any(n.endswith(r) for n in names):
                # flat zip root
                if r not in names:
                    errors.append(f"missing {r}")
        # task.toml keys
        raw = z.read("task.toml")
        data = tomllib.loads(raw.decode())
        for k in data:
            if k not in ALLOWED_TOML_TOP:
                errors.append(f"unknown task.toml key: {k}")
        if "source" in data.get("metadata", {}):
            errors.append("metadata.source is historically rejected")
        if data.get("environment", {}).get("allow_internet") not in (False, None):
            errors.append("allow_internet must be false/absent")
        # rubrics
        rub = json.loads(z.read("rubrics.json"))
        total = sum(r["weight"] for r in rub)
        if total != 100:
            errors.append(f"rubric total {total} != 100")
        rec = sum(r["weight"] for r in rub if r["category"] == "recommend")
        if rec < 30:
            errors.append(f"recommend points {rec} < 30")
        iff = sum(r["weight"] for r in rub if r["category"] == "instruction_following")
        if not (1 <= iff <= 10):
            errors.append(f"instruction_following points {iff} out of 1-10")
        for r in rub:
            if len(r["criterion"]) > 250:
                errors.append(f"criterion {r['item']} len {len(r['criterion'])} > 250")
        # no URLs in instruction
        instr = z.read("instruction.md").decode()
        if "http://" in instr or "https://" in instr:
            errors.append("instruction.md contains URLs")
        # environment must not contain answer keys
        for n in names:
            if n.startswith("environment/") and any(x in n for x in ("expected", "answer", "oracle.json", "modes.json")):
                errors.append(f"answer-like file in environment: {n}")
        # Format rejects grader modules that re-run / duplicate the solution oracle.
        sol_files = {n: z.read(n) for n in names if n.startswith("solution/_lib/")}
        for n in names:
            if not n.startswith("tests/"):
                continue
            if "/oracle" in n or n.endswith("oracle_dp.py") or n.endswith("oracle_enumerate.py"):
                errors.append(f"tests must not ship solver/oracle modules: {n}")
            body = z.read(n)
            for sn, sb in sol_files.items():
                if n.rsplit("/", 1)[-1] != sn.rsplit("/", 1)[-1]:
                    continue
                if not n.endswith(".py") or not sn.endswith(".py"):
                    continue
                # crude similarity: shared line ratio
                ta = set(body.decode("utf-8", errors="ignore").splitlines())
                tb = set(sb.decode("utf-8", errors="ignore").splitlines())
                if not ta or not tb:
                    continue
                overlap = len(ta & tb) / max(len(ta), len(tb))
                if overlap >= 0.90:
                    errors.append(f"tests module too similar to solution ({overlap:.0%}): {n} ~ {sn}")
    return errors


def main() -> int:
    import sys
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "operation_clearwater_candidate.zip")
    errs = check_zip(path)
    if errs:
        print("PREFLIGHT FAIL")
        for e in errs:
            print(" -", e)
        return 1
    print("PREFLIGHT PASS", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
