#!/usr/bin/env python3
"""Stdlib-only Harbor-compatible verifier.

Always writes:
  /logs/verifier/reward.txt   -> single number
  /logs/verifier/reward.json  -> numeric metrics only (Harbor prefers this)
"""
from __future__ import annotations

import importlib.util
import json
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_DIR = Path("/logs/verifier")


def write_rewards(reward: float, metrics: dict[str, float]) -> None:
    reward = float(min(1.0, max(0.0, reward)))
    # Harbor docs: reward.txt = single number; reward.json = labeled numeric metrics.
    # If both exist, Harbor prefers reward.json — keep it numeric-only.
    numeric = {"reward": reward}
    for k, v in metrics.items():
        numeric[str(k)] = float(v)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        (LOG_DIR / "reward.txt").write_text(f"{reward}\n", encoding="utf-8")
        (LOG_DIR / "reward.json").write_text(json.dumps(numeric) + "\n", encoding="utf-8")
    except OSError:
        # Last-ditch: still try plain txt in /logs
        try:
            Path("/logs").mkdir(parents=True, exist_ok=True)
            Path("/logs/reward.txt").write_text(f"{reward}\n", encoding="utf-8")
        except OSError:
            pass


def load_weights() -> dict[str, float]:
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
    write_rewards(0.0, {"reward": 0.0})
    weights = load_weights()
    mod = load_tests_module()
    metrics: dict[str, float] = {}
    reward = 0.0
    for name, weight in weights.items():
        fn = getattr(mod, name, None)
        ok = False
        if callable(fn):
            try:
                fn()
                ok = True
            except Exception:
                ok = False
        earned = float(weight) if ok else 0.0
        metrics[name] = earned
        reward += earned
    write_rewards(reward, metrics)
    # Keep stdout minimal — do not emit nested error objects.
    print(reward)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        write_rewards(0.0, {"reward": 0.0})
        print(0.0)
        raise SystemExit(0)
