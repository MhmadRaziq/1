#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import traceback
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
LOG_DIR = Path(__import__("os").environ.get("VERIFIER_LOG_DIR", "/logs/verifier"))


def load_module():
    spec = importlib.util.spec_from_file_location("test_outputs", TESTS_DIR / "test_outputs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module()
    weights = {row["test_name"]: row for row in json.loads((TESTS_DIR / "test_weights.json").read_text())}
    names = sorted(n for n in dir(module) if n.startswith("test_") and callable(getattr(module, n)))
    results, earned, possible = [], 0, 0
    for name in names:
        weight = int(weights.get(name, {}).get("weight", 1))
        if weight > 0:
            possible += weight
        try:
            getattr(module, name)()
            status, message = "passed", ""
            earned += weight
        except Exception:
            status = "failed"
            message = traceback.format_exc(limit=3).strip().splitlines()[-1]
        results.append({
            "name": name, "status": status, "duration": 0,
            "message": message, "extra": {"weight": weight},
        })
        print(f"{status.upper():6} [{weight:+3d}] {name}" + (f"  -- {message}" if message else ""))
    passed = sum(1 for r in results if r["status"] == "passed")
    reward = max(0.0, min(1.0, earned / possible)) if possible else 0.0
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "ctrf.json").write_text(json.dumps({
        "reportFormat": "CTRF", "specVersion": "0.0.0",
        "results": {
            "tool": {"name": "operation-clearwater-verifier"},
            "summary": {
                "tests": len(results), "passed": passed, "failed": len(results) - passed,
                "pending": 0, "skipped": 0, "other": 0, "start": 0, "stop": 0,
            },
            "tests": results,
        },
    }, indent=2) + "\n")
    (LOG_DIR / "reward.json").write_text(json.dumps({"reward": round(reward, 6)}) + "\n")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
