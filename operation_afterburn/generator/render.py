"""Render sealed world into agent-visible source packet (no truth labels)."""
from __future__ import annotations

import csv
import gzip
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from .ids import digest, h, record_id, short_id, stable_shuffle

UTC = timezone.utc


def _write_jsonl_gz(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")
            n += 1
    return n


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def render_packet(world: dict[str, Any], out_dir: str | Path) -> dict[str, Any]:
    """Write solver-visible packet. Returns manifest stats. Never writes dispositions."""
    root = Path(out_dir)
    if root.exists():
        # clean selective
        pass
    seed = str(world["seed"])
    inc = world["incident"]
    noise = world.get("background_noise_factor", 1)

    # Docs
    _write_text(
        root / "incident_notice.md",
        f"""# Incident notice — suspected build-runner compromise

**Incident ID:** {inc['incident_id']}  
**Confirmed:** {inc['confirmed_at']}  
**Investigation cutoff:** {inc['cutoff']}  
**Board decision deadline:** {inc['board_deadline']}

## Confirmed facts
Security engineering confirmed that the ephemeral build-runner environment used by pool `{inc['compromised_pool']}` was compromised between **{inc['window_start']}** and **{inc['window_end']}**. Runner identity of primary concern: `{inc['compromised_runner']}`.

CI dashboards continue to show successful builds and authenticated attestations. Treat attestation authenticity and builder trustworthiness as separate questions.

## Ask
By the cutoff, determine which production workloads materially run code affected by the compromised build path, which apparent matches are not material exposures, and which response sequence reduces risk without violating availability commitments.

This packet is offline and complete. Do not use the network or perform live changes.
""",
    )

    _write_text(
        root / "incident_response_standard.md",
        """# Northline release-governance incident response standard (excerpt)

## Authority
1. Material production exposure requires evidence of affected immutable artifact identity **and** evidence that the workload was running in a production environment at the investigation cutoff.
2. A valid attestation authenticates a statement about a subject digest and builder identity. It does not by itself prove the builder environment was trustworthy during the compromise window.
3. Registry tags are mutable pointers. Prefer content digests and platform-specific manifests when reconciling runtime identity.
4. Desired rollout state is not proof of runtime materialization. Prefer admission outcomes and runtime observations with event times at or before the cutoff.
5. Emergency change records are usable only when their **effective** time is at or before the cutoff. Recording time alone is not authority.
6. Containment and redeploy actions must preserve disclosed quorum and regional health constraints at every intermediate step.
7. Rollback targets must be free of affected build output and available in the regions where they will be applied.
8. When evidence is insufficient to choose between exposure and clearance, record the finding as unresolved and name the observation that would resolve it.
""",
    )

    _write_text(
        root / "service_recovery_commitments.md",
        """# Service recovery commitments

## Edge checkout quorum
Services `auth-gateway`, `checkout-bff`, and `payments-api` form group `edge-checkout`. During incident response, at least **two regions** must remain healthy for each member. Do not stop or quarantine all healthy regional replicas of these services in a single step.

## Regional notes
- `us-east` and `eu-west` are primary failover pair.
- `ap-south` may be capacity-constrained; confirm region health before relying on it for recovery.

## Change windows
Emergency containment that preserves quorum is pre-authorized under the standing containment approval. Redeploys require a service-specific approval that is effective by the investigation cutoff.
""",
    )

    _write_text(
        root / "telemetry_dictionary.md",
        """# Telemetry dictionary (supported fields)

## Timing
- `time` / `event_time`: when the fact occurred operationally.
- `recorded_time`: when the telemetry system ingested the record. May be after the event.
- Investigation decisions use event/effective times at or before the cutoff unless a document says otherwise.

## Identity
- `invocation_id`: CI build invocation.
- `digest` / `manifest_digest` / `image_id`: content digests (`sha256:...`).
- `index_digest`: OCI image index digest; selects platform manifests and is not interchangeable with a platform manifest digest.
- `workload_id`: stable runtime workload identity in inventory.

## Environments
Production clusters are named `*-prod`. Staging clusters are named `*-stage`. Namespace strings alone are not authoritative; reconcile with cluster/environment inventory.

## Disposition vocabulary (outputs)
`EXPOSED`, `CLEARED`, `UNRESOLVED`.

## Response actions (outputs)
`redeploy`, `quarantine`, `isolate`, `observe`, `hold`.
""",
    )

    # Templates
    tpl = root / "report_templates"
    tpl.mkdir(parents=True, exist_ok=True)
    (tpl / "exposure_register.csv").write_text(
        "workload_id,environment,region,observed_digest,disposition,exposure_path,evidence_refs,uncertainty_or_clearance\n",
        encoding="utf-8",
    )
    (tpl / "response_plan.csv").write_text(
        "sequence,service_id,workload_id,action,recovery_digest,precondition,expected_effect,evidence_refs\n",
        encoding="utf-8",
    )
    (tpl / "incident_decision.md").write_text(
        """# Incident decision — build runner compromise

## Immediate recommendation

## Material production exposure

## Cleared lookalikes and unresolved findings

## Recovery sequence and availability safeguards

## Evidence basis and limitations
""",
        encoding="utf-8",
    )

    # Build events
    ci_rows = []
    bld_rows = []
    att_rows = []
    lock_entries = []
    for i, (key, b) in enumerate(world["builds"].items(), 1):
        ci_rows.append(
            {
                "record_id": b["ci_record"],
                "time": b["time"],
                "invocation_id": b["invocation_id"],
                "service": b["service"],
                "runner_identity": b["runner"],
                "runner_pool": b["pool"],
                "source_revision": h(seed, "rev", key)[:12],
                "result": b["result"],
                "output_digest": b["artifact_digest"],
            }
        )
        bld_rows.append(
            {
                "record_id": b["builder_record"],
                "time": b["time"],
                "runner_identity": b["runner"],
                "runner_pool": b["pool"],
                "invocation_id": b["invocation_id"],
                "image_ref": "registry.internal/ci/runner:prod-v4.2.1"
                if b["pool"] == world["incident"]["compromised_pool"]
                else "registry.internal/ci/runner:shadow-v4.2.1",
            }
        )
        deps = [{"uri": f"pkg:layer/{L}", "digest": {"sha256": L.split(':', 1)[-1]}} for L in b["layers"]]
        if b.get("vendored_from"):
            parent = world["builds"][b["vendored_from"]]
            deps.append(
                {
                    "uri": f"pkg:github/northline/{parent['service']}@{parent['invocation_id']}",
                    "digest": {"sha256": parent["artifact_digest"].split(':', 1)[-1]},
                }
            )
        att_rows.append(
            {
                "record_id": b["att_record"],
                "time": b["time"],
                "envelope": {
                    "_type": "https://in-toto.io/Statement/v1",
                    "subject": [
                        {
                            "name": f"registry.internal/{b['service']}",
                            "digest": {"sha256": b["artifact_digest"].split(':', 1)[-1]},
                        }
                    ],
                    "predicateType": "https://slsa.dev/provenance/v1",
                    "predicate": {
                        "buildDefinition": {
                            "buildType": "https://northline.example/builder/v1",
                            "externalParameters": {"service": b["service"]},
                            "resolvedDependencies": deps,
                        },
                        "runDetails": {
                            "builder": {"id": b["pool"]},
                            "metadata": {
                                "invocationId": b["invocation_id"],
                                "startedOn": b["time"],
                            },
                        },
                    },
                },
                "authentication": {
                    "status": "VALID" if b["attestation_valid"] else "INVALID",
                    "note": "Internal authenticated attestation log (offline simulated verification).",
                },
            }
        )
        lock_entries.append(
            {
                "service": b["service"],
                "invocation_id": b["invocation_id"],
                "resolved": [{"name": L, "digest": L} for L in b["layers"]],
            }
        )

    # Noise CI
    for n in range(40 * noise):
        svc = world["services"][n % len(world["services"])]["service_id"]
        t = datetime(2026, 10, 13, 12, 0, tzinfo=UTC) + timedelta(minutes=n * 3)
        inv = short_id(seed, "noise", n)
        art = digest(seed, "noise-art", n)
        ci_rows.append(
            {
                "record_id": record_id(seed, "CI", 1000 + n),
                "time": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "invocation_id": inv,
                "service": svc,
                "runner_identity": f"helix-ci-shadow/slot-{(n % 7) + 1}",
                "runner_pool": "helix-ci-shadow",
                "source_revision": h(seed, "noise-rev", n)[:12],
                "result": "SUCCESS" if n % 11 else "FAILURE",
                "output_digest": art,
            }
        )

    ci_rows = stable_shuffle(seed, "ci", ci_rows)
    bld_rows = stable_shuffle(seed, "bld", bld_rows)
    att_rows = stable_shuffle(seed, "att", att_rows)

    stats = {}
    stats["ci"] = _write_jsonl_gz(root / "build" / "ci_job_events.jsonl.gz", ci_rows)
    stats["builder"] = _write_jsonl_gz(root / "build" / "builder_identity_events.jsonl.gz", bld_rows)
    stats["att"] = _write_jsonl_gz(root / "build" / "attestations.jsonl.gz", att_rows)

    # lockfiles tar-like: store as jsonl.gz for simplicity + mention in dictionary
    stats["lock"] = _write_jsonl_gz(root / "source" / "build_lockfiles.jsonl.gz", lock_entries)
    repo_hist = []
    for n, b in enumerate(world["builds"].values()):
        repo_hist.append(
            {
                "record_id": record_id(seed, "SRC", n + 1),
                "service": b["service"],
                "time": b["time"],
                "revision": h(seed, "rev", b["key"])[:12],
                "invocation_id": b["invocation_id"],
            }
        )
    stats["repo"] = _write_jsonl_gz(root / "source" / "repository_release_history.jsonl.gz", repo_hist)

    # Registry / OCI
    tag_rows = list(world["tags"])
    for n in range(30 * noise):
        tag_rows.append(
            {
                "record_id": record_id(seed, "REG", 100 + n),
                "repository": world["services"][n % 20]["service_id"],
                "tag": "canary" if n % 2 else "dev",
                "digest": digest(seed, "noise-tag", n),
                "event": "TAG_MOVED",
                "time": (datetime(2026, 10, 13, 8, 0, tzinfo=UTC) + timedelta(minutes=n * 5)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            }
        )
    oci_rows = []
    layer_rows = []
    for img in world["images"].values():
        oci_rows.append(
            {
                "record_id": img["index_record"],
                "descriptor_type": "index",
                "index_digest": img["index_digest"],
                "manifests": [
                    {
                        "platform": p,
                        "manifest_digest": meta["manifest_digest"],
                        "record_id": meta["oci_record"],
                    }
                    for p, meta in img["platforms"].items()
                ],
            }
        )
        for p, meta in img["platforms"].items():
            oci_rows.append(
                {
                    "record_id": meta["oci_record"],
                    "descriptor_type": "manifest",
                    "platform": p,
                    "manifest_digest": meta["manifest_digest"],
                    "index_digest": img["index_digest"],
                    "layers": meta["layers"],
                }
            )
            for L in meta["layers"]:
                layer_rows.append(
                    {
                        "record_id": world["layers"].get(L, {}).get("record", record_id(seed, "LAY", abs(hash(L)) % 100000)),
                        "layer_digest": L,
                        "manifest_digest": meta["manifest_digest"],
                        "media_type": "application/vnd.oci.image.layer.v1.tar",
                    }
                )
    # IMPORTANT: do not include tainted flags in layer inventory
    stats["tags"] = _write_jsonl_gz(root / "registry" / "tag_mutations.jsonl.gz", stable_shuffle(seed, "tags", tag_rows))
    stats["oci"] = _write_jsonl_gz(root / "registry" / "oci_descriptors.jsonl.gz", stable_shuffle(seed, "oci", oci_rows))
    stats["layers"] = _write_jsonl_gz(
        root / "registry" / "layer_inventory.jsonl.gz", stable_shuffle(seed, "layers", layer_rows)
    )

    # Runtime
    adm = []
    rolls = []
    runs = []
    inv_rows = []
    cutoff = datetime.fromisoformat(inc["cutoff"].replace("Z", "+00:00"))
    for i, w in enumerate(world["workloads"].values()):
        adm_time = cutoff - timedelta(hours=5, minutes=i)
        adm.append(
            {
                "record_id": record_id(seed, "ADM", i + 1),
                "time": adm_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "workload_id": w["workload_id"],
                "service_id": w["service_id"],
                "cluster": w["cluster"],
                "namespace": w["namespace"],
                "requested_digest": w["desired_digest"] if w.get("forcing_case") == "F06" else w["running_digest"],
                "decision": "ALLOW" if w["admitted"] else "DENY",
                "reason": "policy_ok" if w["admitted"] else "admission_rejected_digest",
            }
        )
        # F05: also emit DENY for tainted promo image
        if w.get("forcing_case") == "F05":
            tainted_promo = world["images"]["promo-tainted"]["platforms"]["linux/amd64"]["manifest_digest"]
            adm.append(
                {
                    "record_id": record_id(seed, "ADM", 500 + i),
                    "time": (cutoff - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "workload_id": w["workload_id"],
                    "service_id": w["service_id"],
                    "cluster": w["cluster"],
                    "namespace": w["namespace"],
                    "requested_digest": tainted_promo,
                    "decision": "DENY",
                    "reason": "admission_rejected_digest",
                }
            )
        rolls.append(
            {
                "record_id": record_id(seed, "ROL", i + 1),
                "time": (cutoff - timedelta(hours=2, minutes=i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "workload_id": w["workload_id"],
                "service_id": w["service_id"],
                "desired_digest": w["desired_digest"],
                "phase": "Progressing" if w.get("forcing_case") == "F06" else "Healthy",
            }
        )
        if w.get("observe_recorded_after_cutoff"):
            event_time = w["stop_event_time"]
            recorded = (cutoff + timedelta(minutes=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
            runs.append(
                {
                    "record_id": record_id(seed, "RUN", i + 1),
                    "event_time": event_time,
                    "recorded_time": recorded,
                    "time": recorded,  # ambiguous field; dictionary says prefer event_time
                    "cluster": w["cluster"],
                    "namespace": w["namespace"],
                    "workload_id": w["workload_id"],
                    "pod_uid": short_id(seed, "pod", w["workload_id"]),
                    "image_id": w["running_digest"],
                    "status": "Running",  # stale delayed observation
                    "note": "delayed_shipper_observation",
                }
            )
            runs.append(
                {
                    "record_id": record_id(seed, "RUN", 8000 + i),
                    "event_time": event_time,
                    "recorded_time": event_time,
                    "time": event_time,
                    "cluster": w["cluster"],
                    "namespace": w["namespace"],
                    "workload_id": w["workload_id"],
                    "pod_uid": short_id(seed, "pod", w["workload_id"]),
                    "image_id": w["running_digest"],
                    "status": "Terminated",
                    "note": "stop_confirmed",
                }
            )
        elif w.get("dual_world"):
            # admission allow but no runtime observation rows — intentional
            pass
        else:
            status = "Running" if w["running_at_cutoff"] else "Terminated"
            et = (cutoff - timedelta(minutes=15 + (i % 20))).strftime("%Y-%m-%dT%H:%M:%SZ")
            runs.append(
                {
                    "record_id": record_id(seed, "RUN", i + 1),
                    "event_time": et,
                    "recorded_time": et,
                    "time": et,
                    "cluster": w["cluster"],
                    "namespace": w["namespace"],
                    "workload_id": w["workload_id"],
                    "pod_uid": short_id(seed, "pod", w["workload_id"]),
                    "image_id": w["running_digest"],
                    "status": status,
                }
            )
        inv_rows.append(
            {
                "workload_id": w["workload_id"],
                "service_id": w["service_id"],
                "cluster": w["cluster"],
                "region": w["region"],
                "environment": w["environment"],
                "namespace": w["namespace"],
                "platform": w["platform"],
            }
        )

    # noise runtime
    for n in range(50 * noise):
        runs.append(
            {
                "record_id": record_id(seed, "RUN", 2000 + n),
                "event_time": (datetime(2026, 10, 13, 10, 0, tzinfo=UTC) + timedelta(minutes=n)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "recorded_time": (datetime(2026, 10, 13, 10, 0, tzinfo=UTC) + timedelta(minutes=n)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "time": (datetime(2026, 10, 13, 10, 0, tzinfo=UTC) + timedelta(minutes=n)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "cluster": "us-east-stage",
                "namespace": "noise",
                "workload_id": short_id(seed, "wlnoise", n),
                "pod_uid": short_id(seed, "podnoise", n),
                "image_id": digest(seed, "noise-run", n),
                "status": "Running" if n % 3 else "Terminated",
            }
        )

    stats["adm"] = _write_jsonl_gz(root / "runtime" / "admission_audit.jsonl.gz", stable_shuffle(seed, "adm", adm))
    stats["roll"] = _write_jsonl_gz(root / "runtime" / "rollout_history.jsonl.gz", stable_shuffle(seed, "roll", rolls))
    stats["run"] = _write_jsonl_gz(
        root / "runtime" / "pod_runtime_observations.jsonl.gz", stable_shuffle(seed, "run", runs)
    )
    # workload inventory as csv.gz
    inv_path = root / "runtime" / "workload_inventory.csv.gz"
    inv_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(inv_path, "wt", encoding="utf-8", newline="") as f:
        wri = csv.DictWriter(
            f,
            fieldnames=["workload_id", "service_id", "cluster", "region", "environment", "namespace", "platform"],
        )
        wri.writeheader()
        for row in inv_rows:
            wri.writerow(row)
    stats["inv"] = len(inv_rows)

    # Operations
    dep_rows = list(world["dependencies"])
    health_rows = list(world["region_health"])
    rb_rows = []
    for r in world["rollback_artifacts"]:
        rb_rows.append(
            {
                "record_id": r["record"],
                "service_id": r["service_id"],
                "label": r["label"],
                "digest": r["digest"],
                "available_regions": r["available_regions"],
                # no tainted flag
            }
        )
    chg_docs = root / "changes" / "emergency_changes"
    chg_docs.mkdir(parents=True, exist_ok=True)
    for a in world["approvals"]:
        _write_text(
            chg_docs / f"{a['record']}.md",
            f"""# Change {a['record']}

- service: {a['service_id']}
- change_type: {a['change_type']}
- recorded_time: {a['recorded_time']}
- effective_time: {a['effective_time']}
- status: {a['status']}
- restriction: {a['restriction']}

Use effective_time to determine whether this approval is in force at the investigation cutoff.
""",
        )
    handoff = root / "changes" / "oncall_handoffs"
    handoff.mkdir(parents=True, exist_ok=True)
    _write_text(
        handoff / "handoff.md",
        """# On-call handoff

Night shift confirmed admission rejects for a promo-engine candidate digest. Edge-checkout quorum remains the standing continuity constraint. Board wants a sequenced plan, not a simultaneous stop of all suspicious services.
""",
    )
    stats["dep"] = _write_jsonl_gz(root / "operations" / "dependency_graph.jsonl.gz", dep_rows)
    # region health csv.gz
    hp = root / "operations" / "region_health.csv.gz"
    with gzip.open(hp, "wt", encoding="utf-8", newline="") as f:
        wri = csv.DictWriter(f, fieldnames=["record_id", "region", "status", "notes"])
        wri.writeheader()
        for row in health_rows:
            wri.writerow(
                {
                    "record_id": row.get("record") or row.get("record_id"),
                    "region": row["region"],
                    "status": row["status"],
                    "notes": row.get("notes", ""),
                }
            )
    stats["health"] = len(health_rows)
    stats["rollback"] = _write_jsonl_gz(root / "operations" / "rollback_artifacts.jsonl.gz", rb_rows)

    # Manifest of files (sizes only — not answers)
    manifest = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            p = Path(dirpath) / fn
            rel = str(p.relative_to(root))
            manifest.append({"path": rel, "sha256": h(seed, "file", rel, p.stat().st_size)[:64], "bytes": p.stat().st_size})
    _write_text(root / "MANIFEST.json", json.dumps({"files": sorted(manifest, key=lambda x: x["path"])}, indent=2))
    stats["files"] = len(manifest)
    return stats
