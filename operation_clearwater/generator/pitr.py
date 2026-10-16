"""Authentic PostgreSQL WAL / LSN / timeline helpers.

Semantics follow PostgreSQL continuous archiving and PITR documentation:
- LSN is a 64-bit byte offset formatted as ``HEX/HEX``.
- Default WAL segment size is 16 MiB (0x1000000).
- WAL file names are ``{timeline:08X}{log:08X}{seg:08X}`` where
  ``segno = lsn // XLOG_SEG_SIZE``, ``log = segno >> 8``, ``seg = segno & 0xFF``.
- Timeline history records a parent timeline and a switchpoint LSN.
- A base backup is usable for recovery starting at its stop/checkpoint LSN.
"""
from __future__ import annotations

from dataclasses import dataclass

XLOG_SEG_SIZE = 16 * 1024 * 1024  # 16 MiB — PostgreSQL default
XLOG_SEGMENTS_PER_XLOGID = 0x100  # with 16 MiB segments


def parse_lsn(lsn: str) -> int:
    hi_s, lo_s = lsn.split("/")
    return (int(hi_s, 16) << 32) | int(lo_s, 16)


def format_lsn(offset: int) -> str:
    if offset < 0:
        raise ValueError("LSN offset must be non-negative")
    return f"{offset >> 32:X}/{offset & 0xFFFFFFFF:08X}"


def segno_of(lsn_offset: int) -> int:
    return lsn_offset // XLOG_SEG_SIZE


def wal_filename(timeline_id: int, lsn_offset: int) -> str:
    """PostgreSQL XLogFileName for the segment containing ``lsn_offset``."""
    segno = segno_of(lsn_offset)
    log = segno // XLOG_SEGMENTS_PER_XLOGID
    seg = segno % XLOG_SEGMENTS_PER_XLOGID
    return f"{timeline_id:08X}{log:08X}{seg:08X}"


def segment_start(lsn_offset: int) -> int:
    return segno_of(lsn_offset) * XLOG_SEG_SIZE


def next_segment_start(lsn_offset: int) -> int:
    return segment_start(lsn_offset) + XLOG_SEG_SIZE


def segments_covering(start_lsn: int, end_lsn: int) -> list[int]:
    """Return start offsets of WAL segments needed to replay ``[start, end)``.

    PostgreSQL recovery needs every segment from the backup stop location
    through the segment containing the recovery target. If start == end,
    the stop segment alone is required (empty replay still needs the stop page).
    """
    if end_lsn < start_lsn:
        raise ValueError("end_lsn precedes start_lsn")
    first = segment_start(start_lsn)
    last = segment_start(end_lsn if end_lsn > start_lsn else start_lsn)
    out = []
    cur = first
    while cur <= last:
        out.append(cur)
        cur += XLOG_SEG_SIZE
    return out


@dataclass(frozen=True)
class TimelineSwitch:
    child_timeline: int
    parent_timeline: int
    switchpoint_lsn: int  # byte offset


def timeline_ancestry_ok(
    backup_timeline: int,
    backup_stop_lsn: int,
    target_timeline: int,
    target_lsn: int,
    history: list[TimelineSwitch],
) -> bool:
    """True iff recovery from the base backup can reach the target on the
    requested timeline given history switchpoints.

    Compatible when:
    - same timeline and target_lsn >= backup_stop_lsn, or
    - target is a descendant timeline whose switch chain reaches the backup
      timeline with each switchpoint in [backup_stop_lsn, target_lsn].
    """
    if target_lsn < backup_stop_lsn:
        return False
    if backup_timeline == target_timeline:
        return True

    by_child = {h.child_timeline: h for h in history}
    seen: set[int] = set()
    cur = target_timeline
    while cur != backup_timeline:
        if cur in seen or cur not in by_child:
            return False
        seen.add(cur)
        sw = by_child[cur]
        if not (backup_stop_lsn <= sw.switchpoint_lsn <= target_lsn):
            return False
        cur = sw.parent_timeline
    return True


def continuous_segment_chain(
    timeline_id: int,
    start_lsn: int,
    end_lsn: int,
    present_filenames: set[str],
) -> tuple[bool, list[str]]:
    """Check that every required WAL filename is present for the span."""
    needed = [wal_filename(timeline_id, off) for off in segments_covering(start_lsn, end_lsn)]
    missing = [n for n in needed if n not in present_filenames]
    return (not missing, needed)
