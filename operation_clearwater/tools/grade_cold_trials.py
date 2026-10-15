#!/usr/bin/env python3
"""Grade cold-trial outputs under /tmp/clearwater_cold/trial_*."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verifier.grade import grade_submission

COLD = Path("/tmp/clearwater_cold")
DATA = COLD / "data"
OUT_MD = ROOT / "reports" / "STRONG_MODEL_TRIALS.md"

TRIALS = [
    ("A", "claude-sonnet-5-5-high", "trial_a"),
    ("B", "gpt-5.6-sol-high", "trial_b"),
    ("C", "claude-opus-5-5-high", "trial_c"),
    ("D", "composer-2.5", "trial_d"),
]


def main() -> int:
    rows = []
    for tid, model, dirname in TRIALS:
        out = COLD / dirname
        if not (out / "recovery_decision.md").exists() or not (out / "recovery_plan.csv").exists():
            rows.append({"trial": tid, "model": model, "status": "MISSING", "reward": None, "checks": {}})
            continue
        g = grade_submission(out, DATA)
        rows.append({
            "trial": tid,
            "model": model,
            "status": "GRADED",
            "reward": g.reward,
            "checks": {k: v for k, v in g.checks.items() if not v},
            "portfolio": g.detail.get("portfolio"),
            "loss": g.detail.get("weighted_loss"),
        })
        print(tid, model, g.reward, "failed_checks", [k for k, v in g.checks.items() if not v][:8])

    graded = [r for r in rows if r["status"] == "GRADED"]
    mean = sum(r["reward"] for r in graded) / len(graded) if graded else None
    lines = [
        "# Strong-model cold trials — Operation CLEARWATER\n",
        "\n**Protocol:** Four independent agents received only the agent-visible instruction + `/data` packet. "
        "No oracle, author_only labels, or reference portfolio.\n\n",
        "| Trial | Model | Status | Reward | Notes |\n|---|---|---|---:|---|\n",
    ]
    for r in rows:
        notes = ""
        if r["status"] == "GRADED":
            failed = list(r["checks"].keys())[:5]
            notes = ("failed: " + ", ".join(failed)) if failed else "all graded checks passed"
            if r.get("loss") is not None:
                notes += f"; loss={r['loss']}"
        lines.append(f"| {r['trial']} | {r['model']} | {r['status']} | {r['reward'] if r['reward'] is not None else '—'} | {notes} |\n")
    lines.append(f"\n**Graded trials:** {len(graded)}/4\n")
    if mean is not None:
        lines.append(f"**Mean reward:** {mean:.2f}\n")
        if mean >= 99:
            lines.append("\n**NO-GO for hardness:** mean ~0.99 — redesign causal interactions.\n")
        elif mean >= 90:
            lines.append("\n**Caution:** mean still high; consider additional binding interactions before platform sweeps.\n")
        else:
            lines.append("\n**Hardness proxy:** mean below 0.90 on local cold trials.\n")
    lines.append("\n**This section is not a platform Model Sweep.**\n")
    OUT_MD.write_text("".join(lines))
    (ROOT / "reports" / "strong_model_trials.json").write_text(json.dumps({"rows": rows, "mean": mean}, indent=2) + "\n")
    print("mean", mean)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
