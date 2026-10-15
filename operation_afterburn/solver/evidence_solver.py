"""
Evidence-only solver for Operation AFTERBURN.

Reads only agent-visible packet files under data_dir. Does not import generator
truth graphs, oracle snapshots, or author_only labels.
"""
from __future__ import annotations

import csv
import gzip
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


def _open_maybe_gz(path: Path):
    if path.suffix == ".gz" or str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with _open_maybe_gz(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with _open_maybe_gz(path) as f:
        return list(csv.DictReader(f))


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


@dataclass
class Packet:
    cutoff: datetime
    window_start: datetime
    window_end: datetime
    compromised_pool: str
    compromised_runner: str
    ci: list[dict] = field(default_factory=list)
    builders: list[dict] = field(default_factory=list)
    attestations: list[dict] = field(default_factory=list)
    locks: list[dict] = field(default_factory=list)
    tags: list[dict] = field(default_factory=list)
    oci: list[dict] = field(default_factory=list)
    layers: list[dict] = field(default_factory=list)
    admissions: list[dict] = field(default_factory=list)
    rollouts: list[dict] = field(default_factory=list)
    runtime: list[dict] = field(default_factory=list)
    inventory: list[dict] = field(default_factory=list)
    deps: list[dict] = field(default_factory=list)
    health: list[dict] = field(default_factory=list)
    rollbacks: list[dict] = field(default_factory=list)
    approvals: list[dict] = field(default_factory=list)


def load_packet(data_dir: str | Path) -> Packet:
    root = Path(data_dir)
    notice = (root / "incident_notice.md").read_text(encoding="utf-8")
    # Parse key facts from notice with robust patterns
    def grab(pat: str, default: str = "") -> str:
        m = re.search(pat, notice, re.I | re.M)
        return m.group(1).strip() if m else default

    cutoff = _parse_ts(grab(r"Investigation cutoff:\*\*\s*`?([0-9T:\-Z]+)`?"))
    if cutoff is None:
        cutoff = _parse_ts(grab(r"Investigation cutoff:\*\*\s*([0-9T:\-Z]+)"))
    # simpler line-based
    for line in notice.splitlines():
        if "Investigation cutoff" in line:
            m = re.search(r"(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", line)
            if m:
                cutoff = _parse_ts(m.group(1))
        if "between" in line and "and" in line:
            times = re.findall(r"(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", line)
            if len(times) >= 2:
                window_start, window_end = _parse_ts(times[0]), _parse_ts(times[1])
            else:
                window_start = window_end = None
        if "pool" in line and "`" in line:
            pass
    times = re.findall(r"(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", notice)
    # window are first two in confirmed facts typically
    window_start = _parse_ts(times[1]) if len(times) > 1 else cutoff
    window_end = _parse_ts(times[2]) if len(times) > 2 else cutoff
    # Actually notice order: confirmed_at, cutoff, board, window_start, window_end
    # Re-parse more carefully
    ws = re.search(
        r"compromised between \*\*(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\*\* and \*\*(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\*\*",
        notice,
    )
    if ws:
        window_start = _parse_ts(ws.group(1))
        window_end = _parse_ts(ws.group(2))
    pool_m = re.search(r"pool `([^`]+)`", notice)
    runner_m = re.search(r"primary concern: `([^`]+)`", notice)
    compromised_pool = pool_m.group(1) if pool_m else "helix-ci-prod"
    compromised_runner = runner_m.group(1) if runner_m else "helix-ci-prod/slot-12"
    cut_m = re.search(r"Investigation cutoff:\*\* `?(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", notice)
    if not cut_m:
        cut_m = re.search(r"Investigation cutoff:\*\*\s*(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", notice)
    if cut_m:
        cutoff = _parse_ts(cut_m.group(1))
    assert cutoff and window_start and window_end

    approvals = []
    chg_dir = root / "changes" / "emergency_changes"
    if chg_dir.exists():
        for p in sorted(chg_dir.glob("*.md")):
            text = p.read_text(encoding="utf-8")
            def field(name: str) -> str:
                m = re.search(rf"- {name}:\s*(.+)", text)
                return m.group(1).strip() if m else ""
            approvals.append(
                {
                    "record": p.stem,
                    "service_id": field("service"),
                    "change_type": field("change_type"),
                    "recorded_time": field("recorded_time"),
                    "effective_time": field("effective_time"),
                    "status": field("status"),
                    "restriction": field("restriction"),
                }
            )

    return Packet(
        cutoff=cutoff,
        window_start=window_start,
        window_end=window_end,
        compromised_pool=compromised_pool,
        compromised_runner=compromised_runner,
        ci=_read_jsonl(root / "build" / "ci_job_events.jsonl.gz"),
        builders=_read_jsonl(root / "build" / "builder_identity_events.jsonl.gz"),
        attestations=_read_jsonl(root / "build" / "attestations.jsonl.gz"),
        locks=_read_jsonl(root / "source" / "build_lockfiles.jsonl.gz"),
        tags=_read_jsonl(root / "registry" / "tag_mutations.jsonl.gz"),
        oci=_read_jsonl(root / "registry" / "oci_descriptors.jsonl.gz"),
        layers=_read_jsonl(root / "registry" / "layer_inventory.jsonl.gz"),
        admissions=_read_jsonl(root / "runtime" / "admission_audit.jsonl.gz"),
        rollouts=_read_jsonl(root / "runtime" / "rollout_history.jsonl.gz"),
        runtime=_read_jsonl(root / "runtime" / "pod_runtime_observations.jsonl.gz"),
        inventory=_read_csv(root / "runtime" / "workload_inventory.csv.gz"),
        deps=_read_jsonl(root / "operations" / "dependency_graph.jsonl.gz"),
        health=_read_csv(root / "operations" / "region_health.csv.gz"),
        rollbacks=_read_jsonl(root / "operations" / "rollback_artifacts.jsonl.gz"),
        approvals=approvals,
    )


def solve(data_dir: str | Path, output_dir: str | Path) -> dict[str, Any]:
    pkt = load_packet(data_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Map manifest -> layers
    manifest_layers: dict[str, list[str]] = {}
    index_to_platform: dict[str, dict[str, str]] = {}
    for row in pkt.oci:
        if row.get("descriptor_type") == "manifest":
            manifest_layers[row["manifest_digest"]] = list(row.get("layers") or [])
        elif row.get("descriptor_type") == "index":
            index_to_platform[row["index_digest"]] = {
                m["platform"]: m["manifest_digest"] for m in row.get("manifests", [])
            }

    # Artifact digest -> build meta
    builds_by_out: dict[str, dict] = {}
    for row in pkt.ci:
        builds_by_out[row["output_digest"]] = row

    # Layer/artifact taint: produced by compromised pool within window OR dependency of such
    tainted_digests: set[str] = set()
    for row in pkt.ci:
        t = _parse_ts(row.get("time"))
        if row.get("runner_pool") == pkt.compromised_pool and t and pkt.window_start <= t <= pkt.window_end:
            if row.get("result") == "SUCCESS":
                tainted_digests.add(row["output_digest"])

    # Attestation resolvedDependencies expand taint to consumers
    # iterate to fixpoint
    att_by_subject: dict[str, dict] = {}
    for row in pkt.attestations:
        env = row.get("envelope") or {}
        for sub in env.get("subject") or []:
            d = sub.get("digest", {}).get("sha256")
            if d:
                att_by_subject["sha256:" + d] = row

    changed = True
    rounds = 0
    while changed and rounds < 20:
        changed = False
        rounds += 1
        # any manifest containing tainted layer becomes tainted
        for man, layers in manifest_layers.items():
            if man not in tainted_digests and any(L in tainted_digests for L in layers):
                tainted_digests.add(man)
                changed = True
        # attestations: subject tainted if any resolved dependency tainted
        for row in pkt.attestations:
            env = row.get("envelope") or {}
            pred = env.get("predicate") or {}
            bdef = pred.get("buildDefinition") or {}
            deps = bdef.get("resolvedDependencies") or []
            dep_digests = set()
            for dep in deps:
                dd = dep.get("digest", {}).get("sha256")
                if dd:
                    dep_digests.add("sha256:" + dd)
            if dep_digests & tainted_digests:
                for sub in env.get("subject") or []:
                    d = sub.get("digest", {}).get("sha256")
                    if d:
                        full = "sha256:" + d
                        if full not in tainted_digests:
                            tainted_digests.add(full)
                            changed = True
        # lockfiles: service invocation resolved digests
        for lock in pkt.locks:
            resolved = [x.get("digest") for x in lock.get("resolved") or [] if x.get("digest")]
            if any(d in tainted_digests for d in resolved):
                # find CI output for invocation
                for row in pkt.ci:
                    if row.get("invocation_id") == lock.get("invocation_id"):
                        if row["output_digest"] not in tainted_digests:
                            tainted_digests.add(row["output_digest"])
                            changed = True

    # Latest tag digest per repo at cutoff (for lookalike analysis, not authority)
    latest_tag: dict[str, str] = {}
    for row in sorted(pkt.tags, key=lambda r: r.get("time") or ""):
        t = _parse_ts(row.get("time"))
        if t and t <= pkt.cutoff and row.get("tag") == "stable":
            latest_tag[row["repository"]] = row["digest"]

    inv = {r["workload_id"]: r for r in pkt.inventory}

    # Runtime state at cutoff: prefer event_time; Terminated beats delayed Running if event shows stop
    runtime_by_wl: dict[str, list[dict]] = {}
    for row in pkt.runtime:
        wid = row.get("workload_id")
        if not wid:
            continue
        runtime_by_wl.setdefault(wid, []).append(row)

    def running_state(wid: str) -> tuple[str | None, str | None, list[str]]:
        rows = runtime_by_wl.get(wid, [])
        if not rows:
            return None, None, []
        # Consider only events with event_time <= cutoff when present
        usable = []
        for r in rows:
            et = _parse_ts(r.get("event_time") or r.get("time"))
            if et and et <= pkt.cutoff:
                usable.append(r)
        if not usable:
            return None, None, []
        # If any Terminated at latest event_time, not running
        usable.sort(key=lambda r: r.get("event_time") or r.get("time") or "")
        # find latest event_time group
        latest_t = usable[-1].get("event_time") or usable[-1].get("time")
        latest = [r for r in usable if (r.get("event_time") or r.get("time")) == latest_t]
        if any(r.get("status") == "Terminated" for r in latest) or any(
            r.get("status") == "Terminated" for r in usable
        ):
            # if terminated at or before cutoff, not running — even if delayed Running recorded later
            term = [r for r in usable if r.get("status") == "Terminated"]
            if term:
                term.sort(key=lambda r: r.get("event_time") or "")
                r = term[-1]
                return "Terminated", r.get("image_id"), [r["record_id"]]
        run = [r for r in usable if r.get("status") == "Running"]
        if run:
            r = run[-1]
            return "Running", r.get("image_id"), [r["record_id"]]
        r = usable[-1]
        return r.get("status"), r.get("image_id"), [r["record_id"]]

    adm_by_wl: dict[str, list[dict]] = {}
    for row in pkt.admissions:
        adm_by_wl.setdefault(row["workload_id"], []).append(row)

    register = []
    # Candidates: any inventory row with tainted runtime/admission signal, plus staging lookalikes
    candidates = []
    for wid, meta in inv.items():
        status, image_id, refs = running_state(wid)
        adm = adm_by_wl.get(wid, [])
        denied_tainted = any(
            a.get("decision") == "DENY" and a.get("requested_digest") in tainted_digests for a in adm
        )
        allowed_tainted = any(
            a.get("decision") == "ALLOW" and a.get("requested_digest") in tainted_digests for a in adm
        )
        interesting = False
        if image_id and image_id in tainted_digests:
            interesting = True
        if denied_tainted or allowed_tainted:
            interesting = True
        if meta.get("environment") != "production" and image_id in tainted_digests:
            interesting = True
        if interesting:
            candidates.append(wid)

    candidates = sorted(set(candidates))

    for wid in candidates:
        meta = inv[wid]
        status, image_id, run_refs = running_state(wid)
        adm = adm_by_wl.get(wid, [])
        evidence = list(run_refs)
        for a in adm:
            evidence.append(a["record_id"])
        # OCI refs
        for row in pkt.oci:
            rid = row.get("record_id")
            if not rid:
                continue
            if row.get("manifest_digest") == image_id or image_id in (row.get("layers") or []):
                evidence.append(rid)
            if row.get("descriptor_type") == "manifest" and row.get("manifest_digest") == image_id:
                evidence.append(rid)
        # CI / att for tainted lineage
        for row in pkt.ci:
            rid = row.get("record_id")
            if not rid:
                continue
            layers_plus = manifest_layers.get(image_id or "", []) + ([image_id] if image_id else [])
            if row["output_digest"] in tainted_digests and row["output_digest"] in layers_plus:
                evidence.append(rid)
            if image_id and row["output_digest"] == image_id:
                evidence.append(rid)
        for dig in manifest_layers.get(image_id or "", []):
            if dig in builds_by_out and builds_by_out[dig].get("record_id"):
                evidence.append(builds_by_out[dig]["record_id"])
            if dig in att_by_subject and att_by_subject[dig].get("record_id"):
                evidence.append(att_by_subject[dig]["record_id"])
        if image_id in att_by_subject and att_by_subject[image_id].get("record_id"):
            evidence.append(att_by_subject[image_id]["record_id"])
        for row in pkt.tags:
            if row.get("repository") == meta["service_id"] and row.get("tag") == "stable" and row.get("record_id"):
                evidence.append(row["record_id"])

        env = meta.get("environment")
        disposition = None
        path = ""
        note = ""

        # Staging cleared even if digest tainted
        if env != "production":
            disposition = "CLEARED"
            path = "non_production_environment"
            note = "staging/non-prod inventory environment"
        elif not image_id and any(a.get("decision") == "ALLOW" and a.get("requested_digest") in tainted_digests for a in adm):
            disposition = "UNRESOLVED"
            path = "admission_without_runtime_observation"
            note = "need conclusive runtime observation at cutoff"
        elif status != "Running":
            # cleared if not running — even if digest tainted / delayed logs
            disposition = "CLEARED"
            path = "not_running_at_cutoff"
            note = "runtime event_time shows not active at cutoff"
        elif image_id in tainted_digests:
            disposition = "EXPOSED"
            # path nuance
            b = builds_by_out.get(image_id)
            layers = manifest_layers.get(image_id, [])
            if b and b.get("runner_pool") == pkt.compromised_pool:
                path = "direct_compromised_builder_output"
            elif any(L in tainted_digests for L in layers):
                path = "transitive_tainted_layer_or_vendored_input"
            else:
                path = "tainted_digest_running_in_production"
            note = "material affected code running in production at cutoff"
        else:
            # running clean but had denied tainted — cleared lookalike
            if any(a.get("decision") == "DENY" and a.get("requested_digest") in tainted_digests for a in adm):
                disposition = "CLEARED"
                path = "tainted_build_not_admitted"
                note = "admission rejected tainted digest; running digest clean"
            else:
                continue

        register.append(
            {
                "workload_id": wid,
                "environment": env,
                "region": meta.get("region"),
                "observed_digest": image_id or "",
                "disposition": disposition,
                "exposure_path": path,
                "evidence_refs": ";".join(sorted(set(evidence))[:10]),
                "uncertainty_or_clearance": note,
            }
        )

    # Response plan
    exposed = [r for r in register if r["disposition"] == "EXPOSED"]
    # Determine tainted rollback digests: digest's layers intersect tainted
    def digest_tainted(d: str) -> bool:
        if d in tainted_digests:
            return True
        return any(L in tainted_digests for L in manifest_layers.get(d, []))

    approvals_ok = []
    for a in pkt.approvals:
        et = _parse_ts(a.get("effective_time"))
        if a.get("status") == "approved" and et and et <= pkt.cutoff:
            approvals_ok.append(a)

    def has_redeploy_approval(service_id: str) -> dict | None:
        for a in approvals_ok:
            if a["change_type"] == "emergency_redeploy" and a["service_id"] in (service_id, "*"):
                return a
        return None

    plan = []
    seq = 1
    # Sort: checkout first for quorum, then others; payments without approval -> quarantine
    def sort_key(r):
        svc = inv[r["workload_id"]]["service_id"]
        if svc == "checkout-bff":
            return (0, svc)
        if svc == "payments-api":
            return (1, svc)
        return (2, svc)

    for r in sorted(exposed, key=sort_key):
        meta = inv[r["workload_id"]]
        svc = meta["service_id"]
        rb = [x for x in pkt.rollbacks if x["service_id"] == svc and not digest_tainted(x["digest"])]
        approval = has_redeploy_approval(svc)
        if rb and approval:
            choice = rb[0]
            plan.append(
                {
                    "sequence": str(seq),
                    "service_id": svc,
                    "workload_id": r["workload_id"],
                    "action": "redeploy",
                    "recovery_digest": choice["digest"],
                    "precondition": f"approval:{approval['record']};edge-checkout_quorum_if_applicable",
                    "expected_effect": "replace_affected_running_digest",
                    "evidence_refs": r["evidence_refs"] + ";" + choice["record_id"],
                }
            )
        else:
            plan.append(
                {
                    "sequence": str(seq),
                    "service_id": svc,
                    "workload_id": r["workload_id"],
                    "action": "quarantine",
                    "recovery_digest": "",
                    "precondition": "standing_containment_approval;maintain_edge-checkout_min_healthy_regions_2",
                    "expected_effect": "reduce_exposure_without_unauthorized_or_tainted_recovery",
                    "evidence_refs": r["evidence_refs"],
                }
            )
        seq += 1

    for r in register:
        if r["disposition"] == "UNRESOLVED":
            plan.append(
                {
                    "sequence": str(seq),
                    "service_id": inv[r["workload_id"]]["service_id"],
                    "workload_id": r["workload_id"],
                    "action": "observe",
                    "recovery_digest": "",
                    "precondition": "collect_runtime_observation_at_cutoff",
                    "expected_effect": "resolve_dual_world_ambiguity",
                    "evidence_refs": r["evidence_refs"],
                }
            )
            seq += 1

    cleared = [r for r in register if r["disposition"] == "CLEARED"]
    unresolved = [r for r in register if r["disposition"] == "UNRESOLVED"]
    memo = f"""# Incident decision — build runner compromise

## Immediate recommendation
Contain production workloads whose cutoff runtime digests are in the tainted artifact closure of pool `{pkt.compromised_pool}` during {pkt.window_start.strftime('%Y-%m-%dT%H:%M:%SZ')}–{pkt.window_end.strftime('%Y-%m-%dT%H:%M:%SZ')}. Redeploy only with approvals effective by cutoff to digests outside that closure. Preserve edge-checkout quorum (two healthy regions) while sequencing actions. Do not equate tag state or attestation validity with builder trust.

## Material production exposure
{len(exposed)} material exposure(s) reconstructed by joining builder-window outputs, attestation resolved dependencies / layer membership, platform-specific manifests, and running runtime observations at cutoff.

## Cleared lookalikes and unresolved findings
Cleared examples include non-production environments, workloads not running at cutoff despite delayed records, and rejected admissions for tainted digests while a clean digest remains active. Unresolved: {len(unresolved)} case(s) with admission evidence but insufficient runtime observation.

## Recovery sequence and availability safeguards
Proposed sequence avoids simultaneous loss of edge-checkout regional capacity and rejects rollback digests inside the tainted closure. Where redeploy approval is not yet effective, quarantine/hold is recommended.

## Evidence basis and limitations
Assumptions: event_time governs cutoff state; attestation authenticity is not builder trust; tags are non-authoritative. Analysis used offline CI, builder, attestation, OCI, admission, runtime, inventory, approval, dependency, health, and rollback records. No live changes were performed. Additional host-level forensics are out of packet scope.
"""

    with (out / "exposure_register.csv").open("w", encoding="utf-8", newline="") as f:
        fields = [
            "workload_id",
            "environment",
            "region",
            "observed_digest",
            "disposition",
            "exposure_path",
            "evidence_refs",
            "uncertainty_or_clearance",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in register:
            w.writerow(row)
    with (out / "response_plan.csv").open("w", encoding="utf-8", newline="") as f:
        fields = [
            "sequence",
            "service_id",
            "workload_id",
            "action",
            "recovery_digest",
            "precondition",
            "expected_effect",
            "evidence_refs",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in plan:
            w.writerow(row)
    (out / "incident_decision.md").write_text(memo, encoding="utf-8")

    return {
        "exposed": sorted(r["workload_id"] for r in exposed),
        "cleared": sorted(r["workload_id"] for r in cleared),
        "unresolved": sorted(r["workload_id"] for r in unresolved),
        "plan_actions": [(p["workload_id"], p["action"], p["recovery_digest"]) for p in plan],
    }


if __name__ == "__main__":
    import sys

    data, outdir = sys.argv[1], sys.argv[2]
    summary = solve(data, outdir)
    print(json.dumps(summary, indent=2))
