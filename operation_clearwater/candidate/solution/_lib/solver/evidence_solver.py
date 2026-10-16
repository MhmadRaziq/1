"""Reference evidence-only solver — wraps oracle_enumerate and writes deliverables."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

# Allow running from solution/ inside the packaged task
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from ref_oracle import oracle_enumerate  # packaged solution path
except ImportError:  # pragma: no cover - local authoring tree
    from oracle import oracle_enumerate


def solve(data_dir: str | Path, output_dir: str | Path) -> dict:
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = oracle_enumerate.analyze(data_dir)
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "solver failed"))

    cats = {c["candidate_id"]: c for c in json.loads((data_dir / "recovery_candidates.json").read_text())}
    policy = json.loads((data_dir / "recovery_policy.json").read_text())
    portfolio = result["portfolio"]
    cutover = result["cutover"]

    # recovery_plan.csv
    plan_path = output_dir / "recovery_plan.csv"
    fields = [
        "service", "action", "candidate_id", "recovery_target_time", "recovery_target_lsn",
        "timeline_id", "effort_units", "expected_data_loss_hours", "depends_on_ready",
        "validation_gate", "evidence_refs", "notes",
    ]
    with plan_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for svc in cutover:
            cid = portfolio[svc]
            c = cats[cid]
            v = result["candidates"][cid]
            deps = policy["dependencies"].get(svc, [])
            refs = [
                c.get("vault_receipt_id"), c.get("attestation_id"), c.get("key_event_id"),
                c.get("scan_id"), c.get("rehearsal_id"),
            ] + list(c.get("wal_event_ids") or [])
            w.writerow({
                "service": svc,
                "action": "restore_copy",
                "candidate_id": cid,
                "recovery_target_time": c["recovery_target_time"],
                "recovery_target_lsn": c["recovery_target_lsn"],
                "timeline_id": c["timeline_id"],
                "effort_units": c["effort_units"],
                "expected_data_loss_hours": round(v["data_loss_hours"], 2),
                "depends_on_ready": ";".join(deps),
                "validation_gate": result["validation_gates"][svc],
                "evidence_refs": ";".join(x for x in refs if x),
                "notes": "Preserve vault originals; restore from immutable copy in clean room.",
            })

    # Identify material rejects for the memo
    rejects = []
    for c in cats.values():
        v = result["candidates"][c["candidate_id"]]
        if not v["valid"] and c["kind"] in ("latest", "near", "branch"):
            rejects.append((c, v))

    memo = []
    memo.append("# Recovery decision memo — Operation CLEARWATER\n")
    memo.append("## Immediate recommendation\n")
    memo.append(
        "Restore the evidence-supported portfolio below in clean-room isolation, "
        "preserving vault originals (including any legal hold). Do not reconnect a "
        "service until its validation gate passes. Catalog READY alone is not proof "
        "of recoverability.\n"
    )
    memo.append("## Defensible recovery states\n")
    for svc in cutover:
        cid = portfolio[svc]
        c = cats[cid]
        v = result["candidates"][cid]
        memo.append(
            f"- **{svc}** → `{cid}` (target {c['recovery_target_time']}, LSN "
            f"{c['recovery_target_lsn']}, timeline {c['timeline_id']}, "
            f"~{v['data_loss_hours']:.1f}h loss). Evidence: "
            f"{c['vault_receipt_id']}, {c['attestation_id']}, {c['key_event_id']}, "
            f"{c['scan_id']}, {c['rehearsal_id']}.\n"
        )
    memo.append("\n## Rejected or deferred alternatives\n")
    for c, v in rejects[:12]:
        memo.append(
            f"- `{c['candidate_id']}` rejected: {', '.join(v['reasons'])} "
            f"(citations: {', '.join(v['evidence_ids'][:3]) or 'n/a'}).\n"
        )
    memo.append("\n## Expected data loss and business impact\n")
    memo.append(
        f"Priority-weighted data-loss objective for the recommended portfolio is "
        f"{result['weighted_loss']:.1f} with total clean-room effort "
        f"{result['effort']} / {policy['max_restore_effort_units']} units. "
        f"Higher-priority services (identity, payments, orders) were preferred over "
        f"uniform freshness when capacity forced a trade-off.\n"
    )
    memo.append("\n## Cutover sequence and validation gates\n")
    memo.append(
        "Activation order (dependency-respecting): "
        + " → ".join(cutover)
        + ".\n"
    )
    memo.append(
        "Each service must pass checksum, application smoke tests, and reinfection "
        "indicator review before reconnect. Do not reverse-migrate irreversible "
        "schema changes onto dependents.\n"
    )
    memo.append("\n## Assumptions, evidence gaps and residual risk\n")
    memo.append(
        "- Assumptions: agent-visible ledgers are complete as of decision_time; "
        "unconfirmed intrusion indicators are not treated as proven contamination.\n"
        "- Gaps: post-cutoff rehearsals and grants are ignored by policy; some "
        "attractive latest points remain unsubstantiated.\n"
        "- Residual risk: ransomware may have left undetected writes outside the "
        "confirmed payments window; keep originals under legal hold for forensics.\n"
    )
    memo.append(
        "\nDeliverables rely solely on the offline case packet under `/workspace/data/`.\n"
    )
    (output_dir / "recovery_decision.md").write_text("".join(memo), encoding="utf-8")

    # Optional analysis json for verifier convenience (not required by prompt)
    (output_dir / "solver_portfolio.json").write_text(
        json.dumps({
            "portfolio": portfolio,
            "cutover": cutover,
            "weighted_loss": result["weighted_loss"],
            "effort": result["effort"],
            "alternate_portfolios": result.get("alternate_portfolios", []),
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    data = sys.argv[1] if len(sys.argv) > 1 else "/workspace/data"
    out = sys.argv[2] if len(sys.argv) > 2 else "/workspace/output"
    r = solve(data, out)
    print(json.dumps({"portfolio": r["portfolio"], "loss": r["weighted_loss"], "effort": r["effort"]}, indent=2))
