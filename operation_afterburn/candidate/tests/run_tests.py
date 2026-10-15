#!/usr/bin/env python3
"""Stdlib-only weighted verifier. Always writes /logs/verifier/reward.txt."""
from __future__ import annotations

import importlib.util
import json
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REWARD_PATHS = (
    Path("/logs/verifier/reward.txt"),
    Path("/logs/reward.txt"),
)


def write_reward(reward: float, details: dict | None = None) -> None:
    reward = round(min(1.0, max(0.0, float(reward))), 6)
    payload = json.dumps({"reward": reward, "tests": details or {}}, indent=2) + "\n"
    text = f"{reward}\n"
    for path in REWARD_PATHS:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            path.with_name("reward.json").write_text(payload, encoding="utf-8")
        except OSError:
            continue
    # Also mirror beside tests for local debugging (not relied on by platform).
    try:
        local = ROOT / "logs"
        local.mkdir(parents=True, exist_ok=True)
        (local / "reward.txt").write_text(text, encoding="utf-8")
        (local / "reward.json").write_text(payload, encoding="utf-8")
    except OSError:
        pass


def load_weights() -> dict:
    raw = json.loads((ROOT / "test_weights.json").read_text(encoding="utf-8"))
    return {str(k): float(v) for k, v in raw.items()}


def load_tests_module():
    path = ROOT / "test_outputs.py"
    spec = importlib.util.spec_from_file_location("afterburn_test_outputs", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load test_outputs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    # Guarantee a reward file exists even if later steps crash.
    write_reward(0.0, {"status": "starting"})
    weights = load_weights()
    mod = load_tests_module()
    details = {}
    reward = 0.0
    for name, weight in weights.items():
        fn = getattr(mod, name, None)
        ok = False
        err = None
        if callable(fn):
            try:
                fn()
                ok = True
            except Exception as exc:  # noqa: BLE001 - record per-test failure
                err = f"{type(exc).__name__}: {exc}"
        else:
            err = "missing_test_function"
        details[name] = {"weight": weight, "passed": ok, "error": err}
        if ok:
            reward += weight
    write_reward(reward, details)
    print(json.dumps({"reward": round(reward, 6), "tests": details}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        write_reward(0.0, {"status": "fatal", "error": "unhandled_exception"})
        raise SystemExit(0)  # still exit 0 so platform can read reward=0
