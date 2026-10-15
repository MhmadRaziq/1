#!/usr/bin/env python3
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
