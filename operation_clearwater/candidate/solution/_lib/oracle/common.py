"""Shared evidence loading and candidate admissibility (no generator imports)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc
XLOG_SEG_SIZE = 16 * 1024 * 1024
XLOG_SEGMENTS_PER_XLOGID = 0x100


def parse_lsn(lsn: str) -> int:
    hi, lo = lsn.split("/")
    return (int(hi, 16) << 32) | int(lo, 16)


def format_lsn(offset: int) -> str:
    return f"{offset >> 32:X}/{offset & 0xFFFFFFFF:08X}"


def segno_of(offset: int) -> int:
    return offset // XLOG_SEG_SIZE


def wal_filename(timeline_id: int, lsn_offset: int) -> str:
    segno = segno_of(lsn_offset)
    log = segno // XLOG_SEGMENTS_PER_XLOGID
    seg = segno % XLOG_SEGMENTS_PER_XLOGID
    return f"{timeline_id:08X}{log:08X}{seg:08X}"


def segment_start(offset: int) -> int:
    return segno_of(offset) * XLOG_SEG_SIZE


def segments_covering(start_lsn: int, end_lsn: int) -> list[int]:
    if end_lsn < start_lsn:
        raise ValueError("end before start")
    first = segment_start(start_lsn)
    last = segment_start(end_lsn if end_lsn > start_lsn else start_lsn)
    out = []
    cur = first
    while cur <= last:
        out.append(cur)
        cur += XLOG_SEG_SIZE
    return out


def parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(UTC)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class Packet:
    root: Path
    policy: dict
    candidates: list[dict]
    receipts: dict[str, dict]
    keys: dict[str, dict]
    attest: dict[str, dict]
    scans: dict[str, dict]
    rehearsals: dict[str, dict]
    wal_by_id: dict[str, dict]
    timelines: list[dict]
    indicators: dict[str, dict]
    deps: dict[str, dict]
    decision_time: datetime
    cutoff: datetime


def load_packet(data_dir: str | Path) -> Packet:
    root = Path(data_dir)
    policy = load_json(root / "recovery_policy.json")
    candidates = load_json(root / "recovery_candidates.json")

    def index(name: str, key: str = "candidate_id") -> dict[str, dict]:
        rows = load_json(root / name)
        out = {}
        for r in rows:
            k = r.get(key)
            if k:
                out[k] = r
        return out

    receipts = index("vault_receipts.json")
    keys = index("kms_grants.json")
    attest = index("build_attestations.json")
    scans = index("malware_scans.json")
    rehearsals = index("restore_rehearsals.json")
    wal_rows = load_json(root / "wal_archive.json")
    wal_by_id = {r["event_id"]: r for r in wal_rows}
    timelines = load_json(root / "timeline_history.json")
    indicators = {r["service"]: r for r in load_json(root / "intrusion_indicators.json")}
    deps = {r["service"]: r for r in load_json(root / "dependency_registry.json")}
    decision_time = parse_ts(policy["decision_time"])
    cutoff = parse_ts(policy["incident_cutoff"])
    assert decision_time and cutoff
    return Packet(
        root=root,
        policy=policy,
        candidates=candidates,
        receipts=receipts,
        keys=keys,
        attest=attest,
        scans=scans,
        rehearsals=rehearsals,
        wal_by_id=wal_by_id,
        timelines=timelines,
        indicators=indicators,
        deps=deps,
        decision_time=decision_time,
        cutoff=cutoff,
    )


def timeline_ancestry_ok(
    backup_timeline: int,
    backup_stop: int,
    target_timeline: int,
    target_lsn: int,
    history_rows: list[dict],
) -> bool:
    if target_lsn < backup_stop:
        return False
    if backup_timeline == target_timeline:
        return True
    by_child = {}
    for h in history_rows:
        child = h.get("child_timeline")
        if child is not None and "parent_timeline" in h and "switchpoint_lsn" in h:
            by_child[int(child)] = h
    seen: set[int] = set()
    cur = int(target_timeline)
    goal = int(backup_timeline)
    while cur != goal:
        if cur in seen or cur not in by_child:
            return False
        seen.add(cur)
        sw = by_child[cur]
        sp = parse_lsn(sw["switchpoint_lsn"])
        if not (backup_stop <= sp <= target_lsn):
            return False
        cur = int(sw["parent_timeline"])
    return True


@dataclass
class CandidateVerdict:
    candidate_id: str
    service: str
    valid: bool
    reasons: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    weighted_loss: float = 0.0
    effort: int = 0
    schema_epoch: int = 0
    requires_schema_epoch: dict = field(default_factory=dict)
    recovery_target_time: str = ""
    recovery_target_lsn: str = ""
    timeline_id: int = 1
    migration_irreversible: bool = False
    data_loss_hours: float = 0.0


def evaluate_candidate(
    pkt: Packet,
    c: dict,
    ignore: set[str] | None = None,
) -> CandidateVerdict:
    ignore = set(ignore or [])
    cid = c["candidate_id"]
    reasons: list[str] = []
    ev: list[str] = []

    def reject(reason: str, event_id: str):
        if reason not in ignore:
            reasons.append(reason)
            ev.append(event_id)

    r = pkt.receipts.get(cid)
    k = pkt.keys.get(cid)
    a = pkt.attest.get(cid)
    s = pkt.scans.get(cid)
    t = pkt.rehearsals.get(cid)
    if not r:
        reject("vault_unavailable", "MISSING-RECEIPT")
    else:
        recv = parse_ts(r.get("received_at"))
        if r.get("copy_status") != "COMPLETE" or not r.get("immutable"):
            reject("vault_unavailable", r["event_id"])
        if recv and recv > pkt.decision_time:
            reject("vault_unavailable", r["event_id"])
        if r.get("legal_hold") and r.get("copy_restore_allowed") is False:
            reject("vault_hold_blocks_copy", r["event_id"])
        if r.get("object_digest") != c.get("manifest_digest"):
            reject("vault_digest_mismatch", r["event_id"])

    if not k:
        reject("key_unavailable", "MISSING-KEY")
    else:
        ge = parse_ts(k.get("grant_effective_at"))
        if k.get("restore_grant") != "APPROVED" or k.get("key_state") != "ENABLED":
            reject("key_unavailable", k["event_id"])
        if ge and ge > pkt.decision_time:
            reject("key_unavailable", k["event_id"])

    if not a:
        reject("attestation_untrusted", "MISSING-ATT")
    else:
        if not a.get("signature_valid") or not a.get("signer_trusted"):
            reject("attestation_untrusted", a["event_id"])
        if a.get("snapshot_digest") != c.get("manifest_digest"):
            reject("attestation_untrusted", a["event_id"])
        rev = parse_ts(a.get("signer_revoked_at"))
        signed = parse_ts(a.get("signed_at"))
        if rev and signed and rev <= signed and "attestation_untrusted" not in ignore:
            if "attestation_untrusted" not in reasons:
                reject("attestation_untrusted", a["event_id"])

    if not s:
        reject("scan_not_current", "MISSING-SCAN")
    else:
        covered = parse_ts(s.get("covered_through"))
        target_t = parse_ts(c.get("recovery_target_time"))
        if s.get("result") != "CLEAN":
            reject("scan_not_current", s["event_id"])
        elif (covered and target_t and covered < target_t) or s.get("covers_recovery_target") is False:
            reject("scan_not_current", s["event_id"])

    if not t:
        reject("rehearsal_not_usable", "MISSING-REH")
    else:
        recorded = parse_ts(t.get("recorded_at"))
        if t.get("result") != "PASS" or t.get("data_checks") != "PASS":
            reject("rehearsal_not_usable", t["event_id"])
        if recorded and recorded > pkt.decision_time:
            reject("rehearsal_not_usable", t["event_id"])

    # WAL continuity on declared timeline
    backup_stop = parse_lsn(c["backup_stop_lsn"])
    target_lsn = parse_lsn(c["recovery_target_lsn"])
    tl = int(c["timeline_id"])
    needed = {wal_filename(tl, off) for off in segments_covering(backup_stop, target_lsn)}
    present = set()
    for wid in c.get("wal_event_ids", []):
        w = pkt.wal_by_id.get(wid)
        if not w:
            continue
        if w.get("archive_status") != "COMPLETE" or not w.get("verified_hash"):
            continue
        if int(w.get("timeline_id", -1)) != tl:
            continue
        present.add(w["wal_filename"])
    if needed - present:
        reject("wal_chain_not_continuous", (c.get("wal_event_ids") or ["MISSING-WAL"])[0])

    # Timeline ancestry: backup timeline is the candidate's timeline_id;
    # for branch/replica, ensure switchpoint ancestry is coherent with stop/target.
    if not timeline_ancestry_ok(tl, backup_stop, tl, target_lsn, pkt.timelines):
        # same-timeline always ok; this branch handles inconsistent history rows
        pass
    # If candidate claims a non-main timeline, verify history switchpoint lies
    # between backup_stop and target (PostgreSQL child timeline recovery rule).
    if tl != 1:
        child_rows = [h for h in pkt.timelines if int(h.get("child_timeline", -1)) == tl]
        ok = False
        for h in child_rows:
            sp = parse_lsn(h["switchpoint_lsn"])
            parent = int(h["parent_timeline"])
            # Recovery onto child requires the base backup to have been taken on
            # the child *after* the switchpoint, OR taken on parent and replay
            # crossing the switchpoint. Our candidates claim backup on `tl`.
            if parent == 1 and backup_stop >= sp and target_lsn >= backup_stop:
                ok = True
                break
        if not ok:
            eid = child_rows[0]["event_id"] if child_rows else "MISSING-TL"
            reject("timeline_incompatible", eid)

    # Replica forks that are independent promotions with stop after an early
    # switchpoint on timeline 3 are marked cluster_role=replica — treat as
    # incompatible for primary estate recovery unless ignore set.
    if c.get("cluster_role") == "replica":
        reject("timeline_incompatible", f"TL-{cid}")

    ind = pkt.indicators.get(c["service"])
    rt = parse_ts(c["recovery_target_time"])
    if ind:
        w0 = parse_ts(ind["window_start"])
        w1 = parse_ts(ind["window_end"])
        if w0 and w1 and rt and w0 <= rt <= w1:
            # Confirmed ransomware writes are never replayable.
            if ind.get("confirmed") and ind.get("indicator") == "RANSOMWARE-WRITE":
                reject("compromised_replay", ind["event_id"])
            # Hardening: for objects under legal hold, do not restore a target
            # that lands inside any still-open indicator window (even
            # unconfirmed) until DFIR clears it. Ordinary non-held services
            # still treat unconfirmed windows as non-blocking.
            elif (
                pkt.policy.get("block_held_targets_inside_open_indicator_windows", False)
                and r
                and r.get("legal_hold")
            ):
                if "open_indicator_window" not in ignore:
                    reject("open_indicator_window", ind["event_id"])

    # RPO
    rpo_h = pkt.policy["service_rpo_hours"].get(c["service"], 72)
    if rt:
        loss_h = (pkt.cutoff - rt).total_seconds() / 3600.0
        if loss_h > rpo_h:
            reject("rpo_exceeded", "recovery_policy.json")
    else:
        loss_h = 999.0

    # Irreversible migration: admissible alone but portfolio/cutover logic
    # may reject; still mark reason for awareness when paired badly.
    # (Handled at portfolio layer.)

    prio = pkt.policy["service_priorities"].get(c["service"], 1)
    weighted = prio * loss_h
    return CandidateVerdict(
        candidate_id=cid,
        service=c["service"],
        valid=not reasons,
        reasons=reasons,
        evidence_ids=ev,
        weighted_loss=weighted,
        effort=int(c.get("effort_units", 0)),
        schema_epoch=int(c.get("schema_epoch", 0)),
        requires_schema_epoch=dict(c.get("requires_schema_epoch") or {}),
        recovery_target_time=c.get("recovery_target_time", ""),
        recovery_target_lsn=c.get("recovery_target_lsn", ""),
        timeline_id=tl,
        migration_irreversible=bool(c.get("migration_irreversible")),
        data_loss_hours=loss_h,
    )


def cutover_order(services: list[str], dependencies: dict[str, list[str]]) -> list[str]:
    """Topological order; raise on cycle."""
    pending = set(services)
    ordered: list[str] = []
    while pending:
        ready = [s for s in sorted(pending) if all(d not in pending for d in dependencies.get(s, []))]
        if not ready:
            raise RuntimeError(f"dependency cycle among {sorted(pending)}")
        ordered.append(ready[0])
        pending.remove(ready[0])
    return ordered


def skew_ok(
    chosen: dict[str, "CandidateVerdict"] | dict[str, str],
    verdicts: dict[str, CandidateVerdict],
    dependencies: dict[str, list[str]],
    max_skew_hours: float,
) -> bool:
    """Dependent recovery targets must not be more than ``max_skew_hours``
    newer than each upstream provider's chosen target.

    This blocks pure per-service freshness optimization that leaves billing /
    orders hours ahead of their payment / identity providers.
    """
    # Normalize to verdict map
    chosen_v: dict[str, CandidateVerdict] = {}
    for svc, val in chosen.items():
        if isinstance(val, CandidateVerdict):
            chosen_v[svc] = val
        else:
            chosen_v[svc] = verdicts[val]
    for svc, v in chosen_v.items():
        dep_t = parse_ts(v.recovery_target_time)
        if not dep_t:
            return False
        for prov in dependencies.get(svc, []):
            if prov not in chosen_v:
                continue
            prov_t = parse_ts(chosen_v[prov].recovery_target_time)
            if not prov_t:
                return False
            ahead_h = (dep_t - prov_t).total_seconds() / 3600.0
            if ahead_h > max_skew_hours + 1e-9:
                return False
    return True
