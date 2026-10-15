"""Oracle B — independent ready-set priority branch-and-bound.

Unlike oracle_enumerate (fixed dependency topo expansion), this oracle expands
the highest-priority *ready* service at each node. Same objective and
feasibility; different search order. Evidence-only.
"""
from __future__ import annotations

import heapq
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .common import cutover_order, evaluate_candidate, load_packet, skew_ok


def analyze(data_dir: str | Path, ignore: set[str] | None = None) -> dict[str, Any]:
    ignore = set(ignore or [])
    pkt = load_packet(data_dir)

    verdicts = {}
    by_service: dict[str, list] = {}
    for c in pkt.candidates:
        v = evaluate_candidate(pkt, c, ignore=ignore)
        verdicts[v.candidate_id] = v
        if v.valid:
            by_service.setdefault(v.service, []).append(v)

    deps = pkt.policy["dependencies"]
    services = list(deps.keys())
    topo = cutover_order(services, deps)
    missing = [s for s in topo if not by_service.get(s)]
    if missing:
        return {
            "ok": False,
            "error": f"No feasible restore candidate for {missing}",
            "candidates": {k: asdict(v) for k, v in verdicts.items()},
            "portfolio": {},
            "cutover": topo,
            "weighted_loss": None,
            "effort": None,
            "feasible_portfolios": 0,
            "alternate_portfolios": [],
        }

    budget = int(pkt.policy["max_restore_effort_units"])
    pri = pkt.policy["service_priorities"]
    options = {
        s: sorted(
            by_service[s],
            key=lambda v: (
                (1 if "priority" in ignore else pri[s]) * v.data_loss_hours,
                v.effort,
                v.candidate_id,
            ),
        )
        for s in services
    }
    best_each = {
        s: min((1 if "priority" in ignore else pri[s]) * v.data_loss_hours for v in options[s])
        for s in services
    }
    min_eff = {s: min(v.effort for v in options[s]) for s in services}

    def schema_ok(chosen: dict, v) -> bool:
        if "schema" in ignore:
            return True
        for dep, need in v.requires_schema_epoch.items():
            if dep in chosen and verdicts[chosen[dep]].schema_epoch < need:
                return False
        return True

    def migration_ok(chosen: dict) -> bool:
        if "migration" in ignore:
            return True
        for cid in chosen.values():
            if verdicts[cid].migration_irreversible:
                return False
        return True

    max_skew = float(pkt.policy.get("max_dependent_skew_hours", 0))

    def portfolio_constraints_ok(chosen: dict) -> bool:
        if not migration_ok(chosen):
            return False
        if "skew" not in ignore and not skew_ok(chosen, verdicts, deps, max_skew):
            return False
        return True

    def ready_services(chosen: dict) -> list[str]:
        rem = [s for s in services if s not in chosen]
        ready = [s for s in rem if all(d in chosen for d in deps.get(s, []))]
        # Highest priority first — distinct from enumerate's alphabetical topo
        ready.sort(key=lambda s: (-pri[s], s))
        return ready

    best_sol = None
    equal_alts: list[dict] = []
    feasible = 0
    expansions = 0
    MAX_EXP = 250_000

    # Greedy seed along priority-ready order
    chosen = {}
    g_loss = 0.0
    g_eff = 0
    ok = True
    while len(chosen) < len(services):
        ready = ready_services(chosen)
        if not ready:
            ok = False
            break
        svc = ready[0]
        picked = None
        for v in options[svc]:
            if "budget" not in ignore and g_eff + v.effort + sum(
                min_eff[s] for s in services if s not in chosen and s != svc
            ) > budget:
                continue
            if not schema_ok(chosen, v):
                continue
            trial = dict(chosen)
            trial[svc] = v.candidate_id
            if not portfolio_constraints_ok(trial):
                continue
            picked = v
            break
        if picked is None:
            ok = False
            break
        chosen[svc] = picked.candidate_id
        g_eff += picked.effort
        g_loss += (1 if "priority" in ignore else pri[svc]) * picked.data_loss_hours
    if ok and portfolio_constraints_ok(chosen):
        # also full schema
        schema_fine = True
        if "schema" not in ignore:
            for cid in chosen.values():
                if not schema_ok(chosen, verdicts[cid]):
                    schema_fine = False
                    break
        if schema_fine:
            best_sol = (g_loss, g_eff, dict(chosen))
            equal_alts = [dict(chosen)]
            feasible = 1

    # Heap state: lb, loss, effort, seq, frozenset chosen items
    seq = 0
    heap: list[tuple] = []
    rem_all = sum(best_each.values())
    heapq.heappush(heap, (rem_all, 0.0, 0, seq, tuple()))
    seq += 1

    while heap and expansions < MAX_EXP:
        lb, loss, effort, _, items = heapq.heappop(heap)
        expansions += 1
        chosen = dict(items)
        if best_sol is not None and lb > best_sol[0] + 1e-9:
            continue
        if len(chosen) == len(services):
            if not portfolio_constraints_ok(chosen):
                continue
            if "schema" not in ignore:
                if any(not schema_ok(chosen, verdicts[cid]) for cid in chosen.values()):
                    continue
            feasible += 1
            id_tuple = tuple(sorted(chosen.items()))
            cand = (loss, effort, id_tuple)
            if best_sol is None or cand < (best_sol[0], best_sol[1], tuple(sorted(best_sol[2].items()))):
                best_sol = (loss, effort, dict(chosen))
                equal_alts = [dict(chosen)]
            elif abs(loss - best_sol[0]) < 1e-9 and effort == best_sol[1]:
                equal_alts.append(dict(chosen))
            continue

        ready = ready_services(chosen)
        if not ready:
            continue
        # Expand ALL ready services (not only the top) to keep completeness,
        # but order children by priority service first for better bounds.
        # To limit branching, expand only the single highest-priority ready
        # service — this remains complete because every service becomes ready
        # eventually when deps are filled.
        svc = ready[0]
        rem_services = [s for s in services if s not in chosen and s != svc]
        rem_loss = sum(best_each[s] for s in rem_services)
        rem_eff = sum(min_eff[s] for s in rem_services)
        for v in options[svc]:
            new_effort = effort + v.effort
            if "budget" not in ignore and (new_effort > budget or new_effort + rem_eff > budget):
                continue
            if not schema_ok(chosen, v):
                continue
            new_items = items + ((svc, v.candidate_id),)
            new_chosen = dict(new_items)
            if not portfolio_constraints_ok(new_chosen):
                continue
            w = (1 if "priority" in ignore else pri[svc]) * v.data_loss_hours
            new_loss = loss + w
            new_lb = new_loss + rem_loss
            if best_sol is not None and new_lb > best_sol[0] + 1e-9:
                continue
            heapq.heappush(heap, (new_lb, new_loss, new_effort, seq, new_items))
            seq += 1
        if len(heap) > 12000 and best_sol is not None:
            heap = [h for h in heap if h[0] <= best_sol[0] + 1e-9]
            heapq.heapify(heap)
            if len(heap) > 8000:
                heap = heapq.nsmallest(8000, heap)
                heapq.heapify(heap)

    if best_sol is None:
        return {
            "ok": False,
            "error": "No globally feasible restore portfolio",
            "candidates": {k: asdict(v) for k, v in verdicts.items()},
            "portfolio": {},
            "cutover": topo,
            "weighted_loss": None,
            "effort": None,
            "feasible_portfolios": 0,
            "alternate_portfolios": [],
        }

    uniq = []
    seen = set()
    for p in equal_alts:
        t = tuple(sorted(p.items()))
        if t not in seen:
            seen.add(t)
            uniq.append(p)

    return {
        "ok": True,
        "oracle": "ready_set_bnb",
        "candidates": {k: asdict(v) for k, v in verdicts.items()},
        "portfolio": best_sol[2],
        "cutover": topo,
        "weighted_loss": best_sol[0],
        "effort": best_sol[1],
        "feasible_portfolios": feasible,
        "alternate_portfolios": uniq[:8],
        "expansions": expansions,
        "validation_gates": {
            s: "checksum + app smoke + no reinfection indicators before reconnect"
            for s in services
        },
    }


if __name__ == "__main__":
    import json
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "work/microcosm/data"
    print(json.dumps({k: v for k, v in analyze(path).items() if k != "candidates"}, indent=2))
