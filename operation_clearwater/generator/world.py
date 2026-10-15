"""Author-side CLEARWATER world builder.

Emits a causal incident world with 16 services, binding forcing cases FC01–FC18,
and authentic PostgreSQL LSN/timeline geometry. Private mode labels stay in
author_only and are never written to agent-visible ledgers.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from . import pitr

UTC = timezone.utc

# ---------------------------------------------------------------------------
# Service topology (16 services) — priorities and dependencies
# ---------------------------------------------------------------------------
SERVICES: list[tuple[str, int, list[str]]] = [
    ("identity", 10, []),
    ("sessions", 8, ["identity"]),
    ("payments", 10, ["identity"]),
    ("orders", 9, ["identity", "sessions"]),
    ("inventory", 8, ["orders"]),
    ("catalog", 6, ["inventory"]),
    ("customers", 7, ["identity"]),
    ("billing", 8, ["payments", "customers"]),
    ("fulfillment", 7, ["orders", "inventory"]),
    ("notifications", 4, ["customers", "orders"]),
    ("reporting", 3, ["payments", "orders"]),
    ("search", 3, ["catalog"]),
    ("fraud", 6, ["payments", "customers"]),
    ("partners", 5, ["identity", "catalog"]),
    ("warehouse", 2, ["reporting"]),
    ("auditlog", 5, ["identity"]),
]

KINDS = ("latest", "near", "stable", "branch", "archive")

# Relative recovery freshness (hours before cutoff). Lower = more recent.
KIND_AGE_HOURS = {
    "latest": 2,
    "near": 8,
    "stable": 18,
    "branch": 14,
    "archive": 36,
}

KIND_EFFORT = {
    "latest": 7,
    "near": 6,
    "stable": 4,
    "branch": 5,
    "archive": 2,
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _stable_int(text: str) -> int:
    """Process-stable integer hash (never use built-in hash())."""
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ForcingCase:
    case_id: str
    service: str
    kind: str
    mode: str
    description: str
    scored_decision: str


# Binding forcing-case placement. Modes are author-only.
FORCING_CASES: list[ForcingCase] = [
    ForcingCase("FC01", "orders", "latest", "vault_incomplete",
                "Catalog READY but vault copy still queued", "source_selection"),
    ForcingCase("FC02", "payments", "near", "digest_mismatch",
                "Immutable receipt digest differs from signed manifest", "source_selection"),
    ForcingCase("FC03", "identity", "latest", "signer_revoked",
                "Attestation signer revoked before signature time", "source_selection"),
    ForcingCase("FC04", "billing", "latest", "key_unavailable",
                "Key exists but restore grant denied at cutoff", "source_selection"),
    ForcingCase("FC05", "fulfillment", "near", "late_key_grant",
                "Key grant approved after decision cutoff", "source_selection"),
    ForcingCase("FC06", "search", "latest", "wal_gap",
                "Missing middle WAL segment despite later segment present", "pitr_target"),
    ForcingCase("FC07", "partners", "branch", "bad_timeline",
                "Base backup belongs to incompatible timeline fork", "pitr_target"),
    ForcingCase("FC08", "customers", "latest", "stale_scan",
                "Clean scan covers base but not replay target (BINDING)", "source_selection"),
    ForcingCase("FC09", "notifications", "latest", "late_rehearsal",
                "Rehearsal PASS recorded after decision cutoff (BINDING)", "source_selection"),
    ForcingCase("FC10", "payments", "latest", "compromised_replay",
                "Ransomware writes reintroduced by replay to latest target", "pitr_target"),
    ForcingCase("FC11", "orders", "near", "schema_requires_newer",
                "Restorable orders-near requires newer identity schema", "portfolio"),
    ForcingCase("FC12", "identity", "near", "high_effort",
                "Individually attractive points exceed clean-room budget", "portfolio"),
    ForcingCase("FC13", "fulfillment", "stable", "valid",
                "Cutover order must respect inventory readiness", "cutover_order"),
    ForcingCase("FC14", "search", "stable", "valid",
                "Recent low-priority point loses to older critical under budget", "portfolio"),
    ForcingCase("FC15", "inventory", "branch", "replica_fork",
                "Replica lag fork appears fresher but is independent", "pitr_target"),
    ForcingCase("FC16", "auditlog", "latest", "legal_hold_copy_ok",
                "Vault hold protects original but allows copy restore", "containment"),
    ForcingCase("FC17", "warehouse", "latest", "irreversible_migration",
                "Restore requires irreversible migration of reporting dependent", "cutover_order"),
    ForcingCase("FC18", "reporting", "stable", "valid",
                "Equal-utility alternate portfolio exists for fair grading", "fair_grading"),
]


def _mode_map() -> dict[tuple[str, str], str]:
    m = {(fc.service, fc.kind): fc.mode for fc in FORCING_CASES}
    return m


@dataclass
class WorldConfig:
    seed: int
    decision_time: datetime
    incident_cutoff: datetime
    max_restore_effort_units: int = 62
    wal_base_offset: int = 0x200000000  # 8 GiB into WAL space
    scale_days: int = 1  # multi-day observation density


@dataclass
class BuiltWorld:
    config: WorldConfig
    agent_visible: dict[str, Any]
    author_only: dict[str, Any]
    source_hashes: dict[str, str] = field(default_factory=dict)


def build_world(seed: int = 42, scale_days: int = 3) -> BuiltWorld:
    """Build a complete CLEARWATER incident world.

    ``scale_days`` controls how many days of auxiliary observations are
    emitted around the incident window (cutoff-sensitive noise that does
    not flip decisions unless it is the binding evidence).
    """
    # Deterministic clock anchored per seed but still realistic ISO stamps.
    base = datetime(2026, 9, 18, 14, 0, 0, tzinfo=UTC) + timedelta(hours=(seed % 7))
    decision = base + timedelta(days=scale_days, hours=6)
    cutoff = decision  # decision as-of incident cutoff
    cfg = WorldConfig(
        seed=seed,
        decision_time=decision,
        incident_cutoff=cutoff,
        max_restore_effort_units=68 if scale_days <= 1 else 70,
        wal_base_offset=0x200000000 + (seed % 16) * 0x10000000,
        scale_days=scale_days,
    )

    modes = _mode_map()
    # Seed-specific service permutation of non-critical default modes keeps
    # worlds meaningfully different without renaming alone.
    rng_salt = seed * 2654435761

    candidates: list[dict] = []
    vault_receipts: list[dict] = []
    wal_archive: list[dict] = []
    timeline_history: list[dict] = []
    kms_grants: list[dict] = []
    attestations: list[dict] = []
    malware_scans: list[dict] = []
    restore_rehearsals: list[dict] = []
    intrusion_indicators: list[dict] = []
    dependency_registry: list[dict] = []
    catalog_entries: list[dict] = []
    author_modes: dict[str, str] = {}
    author_forcing: dict[str, dict] = {}

    # Shared timeline geometry for the estate.
    # Timeline 1 = main production. Timeline 2 = planned repair branch.
    # Timeline 3 = lagged replica fork (independent / unsafe for some services).
    main_tl = 1
    repair_tl = 2
    replica_tl = 3
    # Global switchpoints expressed as absolute LSN offsets.
    repair_switch = cfg.wal_base_offset + 40 * pitr.XLOG_SEG_SIZE
    replica_switch = cfg.wal_base_offset + 12 * pitr.XLOG_SEG_SIZE  # early/independent

    estate_history = [
        {
            "event_id": "TLH-REPAIR",
            "child_timeline": repair_tl,
            "parent_timeline": main_tl,
            "switchpoint_lsn": pitr.format_lsn(repair_switch),
            "recorded_at": _iso(decision - timedelta(days=2)),
            "note": "Repair timeline forked from main after emergency checkpoint.",
        },
        {
            "event_id": "TLH-REPLICA",
            "child_timeline": replica_tl,
            "parent_timeline": main_tl,
            "switchpoint_lsn": pitr.format_lsn(replica_switch),
            "recorded_at": _iso(decision - timedelta(days=4)),
            "note": "Lagged replica promoted independently; not a recovery ancestor for main backups taken later.",
        },
    ]
    timeline_history.extend(estate_history)

    # Confirmed ransomware write window on payments (and unconfirmed elsewhere).
    ransom_start = decision - timedelta(hours=5)
    ransom_end = decision - timedelta(hours=1)
    for svc, prio, deps in SERVICES:
        confirmed = svc == "payments"
        intrusion_indicators.append({
            "event_id": f"IR-{svc.upper()}",
            "service": svc,
            "window_start": _iso(ransom_start if confirmed else decision - timedelta(hours=3)),
            "window_end": _iso(ransom_end if confirmed else decision - timedelta(minutes=30)),
            "indicator": "RANSOMWARE-WRITE" if confirmed else "SUSPICIOUS-IO",
            "confirmed": confirmed,
            "notes": (
                "Confirmed encrypting writes against payments primary."
                if confirmed
                else "Unconfirmed anomalous I/O; do not treat as proven contamination."
            ),
        })
        dependency_registry.append({
            "service": svc,
            "priority": prio,
            "depends_on": deps,
            "rpo_hours": 48 if prio >= 8 else 72,
            "owner_team": f"team-{svc}",
        })

    # Per-service schema epochs: identity "near/latest" want epoch 3 when valid,
    # but FC03/FC12 force identity admissible set toward epoch 2.
    for svc, prio, deps in SERVICES:
        for kind_i, kind in enumerate(KINDS):
            mode = modes.get((svc, kind), "valid")
            # Seed-varied harmless decoy: occasionally mark archive as
            # "extra_noise" which is still valid — keeps seeds distinct.
            if mode == "valid" and kind == "archive" and ((rng_salt + kind_i + _stable_int(svc)) % 5 == 0):
                mode = "valid"
            cid = f"{svc.upper()}-{kind.upper()}"
            author_modes[cid] = mode

            age_h = KIND_AGE_HOURS[kind]
            # Seed jitter on ages (±1h) without changing relative order.
            age_h += ((rng_salt >> (kind_i + 3)) + _stable_int(svc)) % 3 - 1
            recovery_time = decision - timedelta(hours=max(1, age_h))
            # LSN geometry: newer recoveries sit further along the WAL.
            hours_from_base = (recovery_time - (decision - timedelta(days=scale_days + 1))).total_seconds() / 3600.0
            target_lsn_off = cfg.wal_base_offset + int(hours_from_base * 3) * pitr.XLOG_SEG_SIZE + (_stable_int(cid) % 7) * 0x1000

            # Timeline selection by kind / mode.
            if mode == "replica_fork" or (kind == "branch" and mode == "replica_fork"):
                timeline = replica_tl
            elif kind == "branch":
                timeline = repair_tl
            else:
                timeline = main_tl

            # Base backup stop is ~3 segments before target for normal cases.
            backup_stop = target_lsn_off - 3 * pitr.XLOG_SEG_SIZE
            backup_start = backup_stop - 2 * pitr.XLOG_SEG_SIZE
            if mode == "bad_timeline":
                # Backup taken on main AFTER the repair switchpoint claimed —
                # incompatible: backup_stop > switchpoint but timeline says repair.
                timeline = repair_tl
                backup_stop = repair_switch + 5 * pitr.XLOG_SEG_SIZE
                backup_start = backup_stop - 2 * pitr.XLOG_SEG_SIZE
                target_lsn_off = backup_stop + 2 * pitr.XLOG_SEG_SIZE
                # History switchpoint is BEFORE this backup's stop on parent —
                # wait: for incompatibility we need fork_at < base_minute in proto.
                # Authentic rule: backup is on child timeline but its stop LSN is
                # before the switchpoint (impossible ancestry) OR backup claims
                # child timeline while stop LSN is on parent before fork.
                # Implement: timeline=repair, but backup_stop < repair_switch.
                backup_stop = repair_switch - 2 * pitr.XLOG_SEG_SIZE
                backup_start = backup_stop - 2 * pitr.XLOG_SEG_SIZE
                target_lsn_off = repair_switch + 3 * pitr.XLOG_SEG_SIZE

            if mode == "replica_fork":
                # Looks recent by wall clock but sits on replica timeline whose
                # switchpoint is earlier than this backup stop → ancestry fail
                # relative to wanting main-line recovery semantics. We still
                # expose it as a candidate claiming replica timeline.
                timeline = replica_tl
                backup_stop = replica_switch + 8 * pitr.XLOG_SEG_SIZE
                backup_start = backup_stop - 2 * pitr.XLOG_SEG_SIZE
                target_lsn_off = backup_stop + 4 * pitr.XLOG_SEG_SIZE
                recovery_time = decision - timedelta(hours=3)  # appears fresh

            digest = _sha(f"content:{seed}:{cid}")[:32]
            receipt_id = f"VR-{cid}"
            key_id = f"KEY-{cid}"
            att_id = f"AT-{cid}"
            scan_id = f"SC-{cid}"
            reh_id = f"RT-{cid}"
            snap_id = f"SNAP-{cid}"

            effort = KIND_EFFORT[kind]
            if mode == "high_effort":
                effort = 14  # identity-near burns budget
            if svc == "identity" and kind == "latest":
                effort = 8
            # BINDING FC16: make auditlog-latest cheap so reference selects it;
            # treating legal hold as denial must then flip to a worse point.
            if mode == "legal_hold_copy_ok":
                effort = 3
            # Inflate other auditlog kinds so latest wins on loss+effort
            if svc == "auditlog" and mode != "legal_hold_copy_ok":
                effort = KIND_EFFORT[kind] + 3
            # BINDING FC09: make notifications-latest cheap enough to fit in budget
            if mode == "late_rehearsal":
                effort = 3
            if svc == "notifications" and mode != "late_rehearsal" and kind != "archive":
                effort = KIND_EFFORT[kind] + 1
            # Defected attractive points are cheap so repairing the single
            # defect flips them into the optimum (binding counterfactuals).
            if mode in (
                "digest_mismatch", "late_key_grant", "wal_gap",
                "vault_incomplete", "key_unavailable", "compromised_replay",
                "signer_revoked", "irreversible_migration", "bad_timeline",
                "replica_fork",
            ):
                effort = 3

            # Schema epochs
            schema_epoch = 3 if kind in ("latest", "near") else 2
            if mode == "schema_requires_newer":
                schema_epoch = 3
            if svc == "identity":
                # Admissible identity points after FC03/FC12 should be epoch 2
                # for stable/branch/archive; near is high_effort (may be invalid
                # via budget); latest is signer_revoked.
                if kind in ("stable", "branch", "archive"):
                    schema_epoch = 2
                elif kind == "near":
                    schema_epoch = 3  # attractive but expensive
                else:
                    schema_epoch = 3

            # Keep schema at 2 so the forcing defect is the sole gate into the
            # optimum (compatible with identity/reporting epoch-2 baselines).
            if mode in (
                "stale_scan", "late_rehearsal", "legal_hold_copy_ok",
                "digest_mismatch", "late_key_grant", "wal_gap",
                "irreversible_migration", "vault_incomplete", "key_unavailable",
                "compromised_replay", "signer_revoked", "bad_timeline",
                "replica_fork",
            ):
                schema_epoch = 2

            requires = {d: (3 if schema_epoch == 3 else 2) for d in deps}
            # FC11: orders-near requires identity schema 3
            if mode == "schema_requires_newer":
                requires = {d: 3 for d in deps}
                schema_epoch = 3

            # Irreversible migration flag on warehouse-latest
            migration_irreversible = mode == "irreversible_migration"

            # Legal hold on auditlog-latest
            legal_hold = mode == "legal_hold_copy_ok"

            # ----- vault receipt -----
            copy_status = "QUEUED" if mode == "vault_incomplete" else "COMPLETE"
            object_digest = ("BAD" + digest[3:]) if mode == "digest_mismatch" else digest
            received_at = recovery_time + timedelta(minutes=12)
            if mode == "vault_incomplete":
                received_at = decision + timedelta(minutes=5)  # still not complete by cutoff
            vault_receipts.append({
                "event_id": receipt_id,
                "candidate_id": cid,
                "snapshot_id": snap_id,
                "object_digest": object_digest,
                "copy_status": copy_status,
                "immutable": True,
                "legal_hold": legal_hold,
                "copy_restore_allowed": True if legal_hold else True,
                "received_at": _iso(received_at),
                "custodian": "immutable-vault-audit",
            })

            # ----- WAL archive -----
            # Build continuous segments from backup_stop to target on the
            # candidate's timeline. For wal_gap, omit the middle segment.
            # For bad_timeline / replica_fork, still emit segments on the
            # claimed timeline so the failure is ancestry, not missing files.
            seg_offsets = pitr.segments_covering(backup_stop, target_lsn_off)
            if mode == "wal_gap" and len(seg_offsets) >= 3:
                # Drop the middle segment; keep first and last (late segment present).
                drop = seg_offsets[len(seg_offsets) // 2]
                seg_offsets = [o for o in seg_offsets if o != drop]

            wal_ids = []
            for i, off in enumerate(seg_offsets, start=1):
                wid = f"WAL-{cid}-{i}"
                wal_ids.append(wid)
                wal_archive.append({
                    "event_id": wid,
                    "candidate_id": cid,
                    "wal_filename": pitr.wal_filename(timeline, off),
                    "timeline_id": timeline,
                    "segment_start_lsn": pitr.format_lsn(off),
                    "segment_end_lsn": pitr.format_lsn(off + pitr.XLOG_SEG_SIZE - 1),
                    "verified_hash": True,
                    "archive_status": "COMPLETE",
                    "archived_at": _iso(recovery_time + timedelta(minutes=i)),
                })

            # Per-candidate timeline note (references estate history)
            if timeline != main_tl:
                timeline_history.append({
                    "event_id": f"TL-{cid}",
                    "candidate_id": cid,
                    "child_timeline": timeline,
                    "parent_timeline": main_tl,
                    "switchpoint_lsn": pitr.format_lsn(
                        replica_switch if timeline == replica_tl else repair_switch
                    ),
                    "recorded_at": _iso(recovery_time),
                    "note": (
                        "Replica promotion fork"
                        if timeline == replica_tl
                        else "Repair timeline membership for this backup"
                    ),
                })

            # ----- KMS -----
            grant = "DENIED" if mode == "key_unavailable" else "APPROVED"
            key_state = "DISABLED" if mode == "key_unavailable" else "ENABLED"
            grant_at = recovery_time + timedelta(minutes=3)
            if mode == "late_key_grant":
                grant = "APPROVED"
                key_state = "ENABLED"
                grant_at = decision + timedelta(hours=2)  # after cutoff
            kms_grants.append({
                "event_id": key_id,
                "candidate_id": cid,
                "key_arn": f"key:{svc}:{kind}",
                "restore_grant": grant,
                "key_state": key_state,
                "grant_effective_at": _iso(grant_at),
                "observed_at": _iso(min(grant_at, decision) if mode != "late_key_grant" else grant_at),
            })

            # ----- attestation -----
            signer_trusted = mode != "signer_revoked"
            signed_at = recovery_time + timedelta(minutes=2)
            if mode == "signer_revoked":
                # Signer revoked before signature — record both facts.
                revoked_at = signed_at - timedelta(hours=1)
            else:
                revoked_at = None
            attestations.append({
                "event_id": att_id,
                "candidate_id": cid,
                "snapshot_digest": digest,
                "signature_valid": True,
                "signer_id": f"signer-{(_stable_int(svc) + seed) % 9}",
                "signer_trusted": signer_trusted,
                "signer_revoked_at": _iso(revoked_at) if revoked_at else None,
                "signed_at": _iso(signed_at),
            })

            # ----- malware scan -----
            # BINDING FC08: customers-latest scan covers only through base, not target.
            covered_through = recovery_time
            if mode == "stale_scan":
                covered_through = recovery_time - timedelta(hours=6)
            malware_scans.append({
                "event_id": scan_id,
                "candidate_id": cid,
                "result": "CLEAN",
                "covered_through": _iso(covered_through),
                "covers_backup_stop": True,
                "covers_recovery_target": mode != "stale_scan",
                "engine": "clean-room-scanner-v4",
                "observed_at": _iso(min(decision, covered_through + timedelta(minutes=30))),
            })

            # ----- restore rehearsal -----
            # BINDING FC09: notifications-latest PASS but recorded after cutoff.
            reh_result = "PASS"
            reh_at = recovery_time + timedelta(hours=1)
            if mode == "late_rehearsal":
                reh_at = decision + timedelta(hours=3)
            if mode == "failed_rehearsal":
                reh_result = "FAIL"
            restore_rehearsals.append({
                "event_id": reh_id,
                "candidate_id": cid,
                "result": reh_result,
                "recorded_at": _iso(reh_at),
                "data_checks": "PASS" if reh_result == "PASS" else "FAIL",
                "app_smoke": "PASS" if reh_result == "PASS" else "FAIL",
                "notes": "Post-cutoff rehearsal must not support earlier decision." if mode == "late_rehearsal" else "",
            })

            # ----- catalog (untrusted inventory) -----
            catalog_entries.append({
                "candidate_id": cid,
                "service": svc,
                "kind": kind,
                "snapshot_id": snap_id,
                "catalog_state": "READY",
                "backup_start_lsn": pitr.format_lsn(backup_start),
                "backup_stop_lsn": pitr.format_lsn(backup_stop),
                "recovery_target_lsn": pitr.format_lsn(target_lsn_off),
                "recovery_target_time": _iso(recovery_time),
                "timeline_id": timeline,
                "manifest_digest": digest,
                "vault_receipt_id": receipt_id,
                "key_event_id": key_id,
                "attestation_id": att_id,
                "scan_id": scan_id,
                "rehearsal_id": reh_id,
                "wal_event_ids": wal_ids,
                "effort_units": effort,
                "schema_epoch": schema_epoch,
                "requires_schema_epoch": requires,
                "migration_irreversible": migration_irreversible,
                "snapshot_origin": "independent-vault",
                "cluster_role": "replica" if mode == "replica_fork" else "primary",
            })

            candidates.append(catalog_entries[-1])

            # Track forcing metadata for author_only
            for fc in FORCING_CASES:
                if fc.service == svc and fc.kind == kind:
                    author_forcing[fc.case_id] = {
                        "case_id": fc.case_id,
                        "candidate_id": cid,
                        "mode": mode,
                        "description": fc.description,
                        "scored_decision": fc.scored_decision,
                    }

    # Auxiliary multi-day observations (cutoff-sensitive decoys)
    aux_scans = []
    aux_grants = []
    if scale_days >= 2:
        for day in range(scale_days):
            ts = decision - timedelta(days=day + 1)
            aux_scans.append({
                "event_id": f"SC-AUX-DAY{day}",
                "candidate_id": None,
                "result": "CLEAN",
                "covered_through": _iso(ts),
                "covers_backup_stop": False,
                "covers_recovery_target": False,
                "engine": "clean-room-scanner-v4",
                "observed_at": _iso(ts + timedelta(minutes=10)),
                "notes": "Estate-wide sweep; not scoped to a recovery candidate.",
            })
            aux_grants.append({
                "event_id": f"KEY-AUX-DAY{day}",
                "candidate_id": None,
                "key_arn": "key:estate:rotation",
                "restore_grant": "APPROVED",
                "key_state": "ENABLED",
                "grant_effective_at": _iso(ts),
                "observed_at": _iso(ts),
                "notes": "Routine estate key rotation; not candidate-specific.",
            })
        malware_scans.extend(aux_scans)
        kms_grants.extend(aux_grants)

    policy = {
        "incident_id": f"CLEARWATER-{seed}",
        "incident_cutoff": _iso(cfg.incident_cutoff),
        "decision_time": _iso(cfg.decision_time),
        "max_restore_effort_units": cfg.max_restore_effort_units,
        "service_rpo_hours": {s: (48 if p >= 8 else 72) for s, p, _ in SERVICES},
        "service_priorities": {s: p for s, p, _ in SERVICES},
        "dependencies": {s: deps for s, _, deps in SERVICES},
        "clean_room": "isolated",
        "risk_appetite": (
            "No unverified restore sources. Preserve vault originals under any "
            "legal hold; restoring from an allowed immutable *copy* is permitted. "
            "Do not reconnect services that would replay confirmed ransomware writes."
        ),
        "validation_required_before_reconnect": True,
        "postgresql_notes": {
            "wal_segment_size_bytes": pitr.XLOG_SEG_SIZE,
            "lsn_format": "HEX/HEX byte offset",
            "timeline_history": "child timeline requires switchpoint ancestry from backup timeline",
            "base_backup_stop_lsn": "recovery replay begins at backup_stop_lsn",
        },
    }

    case_brief = _case_brief(cfg, policy)
    evidence_guide = _evidence_guide()

    agent_visible = {
        "case_brief.md": case_brief,
        "evidence_guide.md": evidence_guide,
        "recovery_policy.json": policy,
        "recovery_candidates.json": catalog_entries,
        "vault_receipts.json": vault_receipts,
        "wal_archive.json": wal_archive,
        "timeline_history.json": timeline_history,
        "kms_grants.json": kms_grants,
        "build_attestations.json": attestations,
        "malware_scans.json": malware_scans,
        "restore_rehearsals.json": restore_rehearsals,
        "intrusion_indicators.json": intrusion_indicators,
        "dependency_registry.json": dependency_registry,
        "report_templates/recovery_decision.md": _decision_template(),
        "report_templates/recovery_plan.csv": _plan_template(),
    }

    author_only = {
        "modes.json": author_modes,
        "forcing_cases.json": author_forcing,
        "forcing_case_list.json": [asdict(fc) for fc in FORCING_CASES],
        "config.json": {
            "seed": seed,
            "scale_days": scale_days,
            "decision_time": _iso(cfg.decision_time),
            "max_restore_effort_units": cfg.max_restore_effort_units,
            "wal_base_offset": cfg.wal_base_offset,
        },
    }

    hashes = {}
    for name, obj in agent_visible.items():
        if isinstance(obj, str):
            raw = obj.encode()
        else:
            raw = (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode()
        hashes[name] = hashlib.sha256(raw).hexdigest()

    return BuiltWorld(config=cfg, agent_visible=agent_visible, author_only=author_only, source_hashes=hashes)


def write_world(world: BuiltWorld, data_dir: Path, author_dir: Path | None = None) -> dict[str, str]:
    data_dir.mkdir(parents=True, exist_ok=True)
    for name, obj in world.agent_visible.items():
        path = data_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(obj, str):
            path.write_text(obj if obj.endswith("\n") else obj + "\n", encoding="utf-8")
        else:
            path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    (data_dir / "MANIFEST.json").write_text(
        json.dumps({"source_sha256": world.source_hashes, "seed": world.config.seed}, indent=2) + "\n",
        encoding="utf-8",
    )
    if author_dir is not None:
        author_dir.mkdir(parents=True, exist_ok=True)
        for name, obj in world.author_only.items():
            (author_dir / name).write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
        (author_dir / "DO_NOT_SHIP.md").write_text(
            "Author-only labels and forcing-case modes. Never copy into environment/.\n",
            encoding="utf-8",
        )
    return world.source_hashes


def _case_brief(cfg: WorldConfig, policy: dict) -> str:
    return f"""# Operation CLEARWATER — case brief

**Incident ID:** {policy['incident_id']}
**Decision time (as-of):** {policy['decision_time']}
**Incident cutoff:** {policy['incident_cutoff']}
**Clean-room restore budget:** {policy['max_restore_effort_units']} effort units
**Clean-room posture:** {policy['clean_room']}

## Situation
A ransomware intrusion affecting several application tiers has been contained.
Production clusters remain isolated. The backup console lists multiple READY
restore points, but the clean-room team collected independent evidence from
the immutable vault, WAL archive, timeline history, KMS grants, integrity
attestations, malware scans, restore rehearsals, intrusion indicators and the
service dependency registry. Records conflict. Evidence observed after the
decision time cannot support this call.

## What we need for the ops call
1. Which service recovery states are defensible from admissible evidence.
2. Which attractive alternatives are unsafe or not yet substantiated.
3. Expected data loss versus business priorities and RPO.
4. A restore and cutover sequence that respects clean-room capacity,
   dependency/schema compatibility, and preservation of vault originals.
5. Explicit assumptions, gaps and residual risk.

## PostgreSQL recovery notes (local)
- LSN values use PostgreSQL ``HEX/HEX`` byte-offset form.
- WAL segment size is {pitr.XLOG_SEG_SIZE} bytes (16 MiB).
- Replay begins at each candidate's ``backup_stop_lsn`` and must have a
  continuous archived segment chain through ``recovery_target_lsn`` on a
  compatible timeline (see ``timeline_history.json``).
- A catalog READY flag is not proof that an immutable vault copy completed.

## Risk appetite
{policy['risk_appetite']}
"""


def _evidence_guide() -> str:
    return """# CLEARWATER evidence guide

All records are synthetic and offline. Times are timezone-aware ISO-8601 UTC.
PostgreSQL LSNs use ``HEX/HEX`` byte offsets. WAL filenames follow the
PostgreSQL ``{timeline}{log}{seg}`` layout for 16 MiB segments.

| File | Custodian | Use |
|---|---|---|
| `recovery_candidates.json` | Backup console | Untrusted inventory of candidate restore points |
| `vault_receipts.json` | Immutable vault audit | Copy completion, digest, immutability, legal hold |
| `wal_archive.json` | Archive gateway | Segment files, timeline, LSN span, hash verification |
| `timeline_history.json` | PostgreSQL recovery | Parent/child timelines and switchpoint LSNs |
| `kms_grants.json` | Cloud security | Restore-time key state and grant effectiveness |
| `build_attestations.json` | Signing service | Manifest digest, signature, signer trust/revocation |
| `malware_scans.json` | Clean-room analysts | Coverage through a stated timestamp / target |
| `restore_rehearsals.json` | Recovery team | Rehearsal result and observation time |
| `intrusion_indicators.json` | DFIR | Confirmed or unconfirmed contamination windows |
| `dependency_registry.json` | Architecture/SRE | Priorities, RPO, activation dependencies |
| `recovery_policy.json` | Resilience director | Cutoff, budget, priorities, risk appetite |

Record IDs such as `VR-IDENTITY-STABLE` or `WAL-ORDERS-BRANCH-1` are valid
citations. A missing or post-cutoff observation is not positive evidence.
Legal hold protects originals; when `copy_restore_allowed` is true, restoring
from the immutable *copy* remains allowed.

The case owner needs an operationally safe plan. Other defensible portfolios
are acceptable when they meet safety, capacity, dependency and priority
constraints and clearly explain trade-offs.
"""


def _decision_template() -> str:
    return """# Recovery decision memo — Operation CLEARWATER

## Immediate recommendation


## Defensible recovery states


## Rejected or deferred alternatives


## Expected data loss and business impact


## Cutover sequence and validation gates


## Assumptions, evidence gaps and residual risk

"""


def _plan_template() -> str:
    return (
        "service,action,candidate_id,recovery_target_time,recovery_target_lsn,"
        "timeline_id,effort_units,expected_data_loss_hours,depends_on_ready,"
        "validation_gate,evidence_refs,notes\n"
    )


def apply_counterfactual(data_dir: Path, case_id: str, author_forcing: dict) -> str:
    """Flip the single decisive fact for ``case_id`` in place. Returns summary."""
    fc = author_forcing[case_id]
    cid = fc["candidate_id"]
    mode = fc["mode"]

    def load(name: str):
        return json.loads((data_dir / name).read_text())

    def dump(name: str, obj):
        (data_dir / name).write_text(json.dumps(obj, indent=2) + "\n")

    if mode == "vault_incomplete":
        rows = load("vault_receipts.json")
        for r in rows:
            if r["candidate_id"] == cid:
                r["copy_status"] = "COMPLETE"
                # pull received_at back before cutoff
                pol = load("recovery_policy.json")
                r["received_at"] = pol["decision_time"]
        dump("vault_receipts.json", rows)
        return f"{case_id}: vault copy completed for {cid}"

    if mode == "digest_mismatch":
        rows = load("vault_receipts.json")
        cats = {c["candidate_id"]: c for c in load("recovery_candidates.json")}
        for r in rows:
            if r["candidate_id"] == cid:
                r["object_digest"] = cats[cid]["manifest_digest"]
        dump("vault_receipts.json", rows)
        return f"{case_id}: digest aligned for {cid}"

    if mode == "signer_revoked":
        rows = load("build_attestations.json")
        for r in rows:
            if r["candidate_id"] == cid:
                r["signer_trusted"] = True
                r["signer_revoked_at"] = None
        dump("build_attestations.json", rows)
        return f"{case_id}: signer trusted for {cid}"

    if mode == "key_unavailable":
        rows = load("kms_grants.json")
        for r in rows:
            if r["candidate_id"] == cid:
                r["restore_grant"] = "APPROVED"
                r["key_state"] = "ENABLED"
        dump("kms_grants.json", rows)
        return f"{case_id}: key grant approved for {cid}"

    if mode == "late_key_grant":
        rows = load("kms_grants.json")
        pol = load("recovery_policy.json")
        for r in rows:
            if r["candidate_id"] == cid:
                r["grant_effective_at"] = pol["decision_time"]
                r["observed_at"] = pol["decision_time"]
        dump("kms_grants.json", rows)
        return f"{case_id}: key grant moved to cutoff for {cid}"

    if mode == "wal_gap":
        return _repair_wal_after_timeline_fix(data_dir, cid)

    if mode == "bad_timeline":
        hist = load("timeline_history.json")
        sw = None
        for h in hist:
            if h.get("event_id") == "TLH-REPAIR":
                sw = pitr.parse_lsn(h["switchpoint_lsn"])
        assert sw is not None
        cats_list = load("recovery_candidates.json")
        for row in cats_list:
            if row["candidate_id"] == cid:
                row["timeline_id"] = 2
                row["backup_stop_lsn"] = pitr.format_lsn(sw + pitr.XLOG_SEG_SIZE)
                row["backup_start_lsn"] = pitr.format_lsn(sw - pitr.XLOG_SEG_SIZE)
                row["recovery_target_lsn"] = pitr.format_lsn(sw + 4 * pitr.XLOG_SEG_SIZE)
        dump("recovery_candidates.json", cats_list)
        return _repair_wal_after_timeline_fix(data_dir, cid)

    if mode == "stale_scan":
        rows = load("malware_scans.json")
        cats = {c["candidate_id"]: c for c in load("recovery_candidates.json")}
        for r in rows:
            if r.get("candidate_id") == cid:
                r["covered_through"] = cats[cid]["recovery_target_time"]
                r["covers_recovery_target"] = True
        dump("malware_scans.json", rows)
        return f"{case_id}: scan coverage extended for {cid}"

    if mode == "late_rehearsal":
        rows = load("restore_rehearsals.json")
        pol = load("recovery_policy.json")
        for r in rows:
            if r.get("candidate_id") == cid:
                r["recorded_at"] = pol["decision_time"]
                r["result"] = "PASS"
                r["data_checks"] = "PASS"
                r["app_smoke"] = "PASS"
        dump("restore_rehearsals.json", rows)
        return f"{case_id}: rehearsal moved to cutoff for {cid}"

    if mode == "compromised_replay":
        rows = load("intrusion_indicators.json")
        for r in rows:
            if r["service"] == "payments":
                r["confirmed"] = False
                r["indicator"] = "SUSPICIOUS-IO"
        dump("intrusion_indicators.json", rows)
        return f"{case_id}: payments intrusion unconfirmed"

    if mode == "schema_requires_newer":
        cats_list = load("recovery_candidates.json")
        for row in cats_list:
            if row["candidate_id"] == cid:
                row["requires_schema_epoch"] = {d: 2 for d in row["requires_schema_epoch"]}
                row["schema_epoch"] = 2
        dump("recovery_candidates.json", cats_list)
        return f"{case_id}: schema requirement lowered for {cid}"

    if mode == "high_effort":
        cats_list = load("recovery_candidates.json")
        for row in cats_list:
            if row["candidate_id"] == cid:
                row["effort_units"] = 4
        dump("recovery_candidates.json", cats_list)
        return f"{case_id}: effort reduced for {cid}"

    if mode == "replica_fork":
        cats_list = load("recovery_candidates.json")
        for row in cats_list:
            if row["candidate_id"] == cid:
                row["timeline_id"] = 1
                row["cluster_role"] = "primary"
        dump("recovery_candidates.json", cats_list)
        return _repair_wal_after_timeline_fix(data_dir, cid)

    if mode == "legal_hold_copy_ok":
        # Counterfactual: disallow copy restore → should force defer/alternate
        rows = load("vault_receipts.json")
        for r in rows:
            if r["candidate_id"] == cid:
                r["copy_restore_allowed"] = False
        dump("vault_receipts.json", rows)
        return f"{case_id}: copy restore disallowed for {cid}"

    if mode == "irreversible_migration":
        cats_list = load("recovery_candidates.json")
        for row in cats_list:
            if row["candidate_id"] == cid:
                row["migration_irreversible"] = False
        dump("recovery_candidates.json", cats_list)
        return f"{case_id}: migration flag cleared for {cid}"

    if mode == "valid":
        # FC13/FC14/FC18 — flip a related constraint in policy/deps
        if case_id == "FC13":
            pol = load("recovery_policy.json")
            # Remove inventory dependency from fulfillment (should change cutover)
            pol["dependencies"]["fulfillment"] = ["orders"]
            dump("recovery_policy.json", pol)
            reg = load("dependency_registry.json")
            for r in reg:
                if r["service"] == "fulfillment":
                    r["depends_on"] = ["orders"]
            dump("dependency_registry.json", reg)
            return f"{case_id}: fulfillment no longer depends on inventory"
        if case_id == "FC14":
            pol = load("recovery_policy.json")
            pol["service_priorities"]["search"] = 10
            dump("recovery_policy.json", pol)
            return f"{case_id}: search priority raised"
        if case_id == "FC18":
            pol = load("recovery_policy.json")
            pol["max_restore_effort_units"] = pol["max_restore_effort_units"] + 20
            dump("recovery_policy.json", pol)
            return f"{case_id}: budget expanded (alternate portfolio region)"

    return f"{case_id}: no-op"


def _repair_wal_after_timeline_fix(data_dir: Path, cid: str) -> str:
    cats_list = json.loads((data_dir / "recovery_candidates.json").read_text())
    c = next(x for x in cats_list if x["candidate_id"] == cid)
    start = pitr.parse_lsn(c["backup_stop_lsn"])
    end = pitr.parse_lsn(c["recovery_target_lsn"])
    tl = c["timeline_id"]
    wals = [w for w in json.loads((data_dir / "wal_archive.json").read_text()) if w.get("candidate_id") != cid]
    new_ids = []
    for i, off in enumerate(pitr.segments_covering(start, end), start=1):
        wid = f"WAL-{cid}-{i}"
        new_ids.append(wid)
        wals.append({
            "event_id": wid,
            "candidate_id": cid,
            "wal_filename": pitr.wal_filename(tl, off),
            "timeline_id": tl,
            "segment_start_lsn": pitr.format_lsn(off),
            "segment_end_lsn": pitr.format_lsn(off + pitr.XLOG_SEG_SIZE - 1),
            "verified_hash": True,
            "archive_status": "COMPLETE",
            "archived_at": c["recovery_target_time"],
        })
    (data_dir / "wal_archive.json").write_text(json.dumps(wals, indent=2) + "\n")
    for row in cats_list:
        if row["candidate_id"] == cid:
            row["wal_event_ids"] = new_ids
    (data_dir / "recovery_candidates.json").write_text(json.dumps(cats_list, indent=2) + "\n")
    return f"timeline/WAL repaired for {cid}"
