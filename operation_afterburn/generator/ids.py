"""Deterministic synthetic identifiers and digests."""
from __future__ import annotations

import hashlib
import struct
from typing import Iterable


def h(seed: str, *parts: object) -> str:
    m = hashlib.sha256()
    m.update(seed.encode())
    for p in parts:
        m.update(b"\0")
        m.update(str(p).encode())
    return m.hexdigest()


def digest(seed: str, *parts: object) -> str:
    return "sha256:" + h(seed, "digest", *parts)


def short_id(seed: str, prefix: str, *parts: object) -> str:
    return f"{prefix}-{h(seed, prefix, *parts)[:10]}"


def record_id(seed: str, family: str, seq: int) -> str:
    return f"{family}-{h(seed, family, seq)[:8].upper()}"


def pick(seed: str, key: str, options: Iterable[object]):
    opts = list(options)
    if not opts:
        raise ValueError("empty options")
    idx = int(h(seed, "pick", key), 16) % len(opts)
    return opts[idx]


def jitter_seconds(seed: str, key: str, lo: int, hi: int) -> int:
    span = hi - lo + 1
    return lo + (int(h(seed, "jitter", key), 16) % span)


def stable_shuffle(seed: str, key: str, items: list) -> list:
    decorated = [(h(seed, "shuffle", key, i, x), x) for i, x in enumerate(items)]
    decorated.sort(key=lambda t: t[0])
    return [x for _, x in decorated]
