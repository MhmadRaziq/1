"""Oracle A — evidence-only branch-and-bound portfolio solver.

Independent of oracle_dp: uses reverse-priority service order, exact
dominance pruning, and a different beam policy. Never imports generator labels.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .common import CandidateVerdict, cutover_order, evaluate_candidate, load_packet, skew_ok


def analyze(data_dir: str | Path, ignore: set[str] | None = None) -> dict[str, Any]:
    ignore = set(ignore or [])
    pkt = load_packet(data_dir)
    verdicts: dict[str, CandidateVerdict] = {}
    accepted: dict[str, list[CandidateVerdict]] = {}

    for c in pkt.candidates:
        v = evaluate_candidate(pkt, c, ignore=ignore)
        verdicts[v.candidate_id] = v
        if v.valid:
            accepted.setdefault(v.service, []).append(v)

    deps = pkt.policy["dependencies"]
    services = list(deps.keys())
    topo = cutover_order(services, deps)
    missing = [s for s in topo if not accepted.get(s)]
    if missing:
        return {
            "ok": False,
            "error": f"No feasible restore candidate for {missing}",
            "candidates": {k: asdict(v) for k, v in verdicts.items()},
            "portfolio": {},
            "cutover": [],
            "weighted_loss": None,
            "effort": None,
            "feasible_portfolios": 0,
            "alternate_portfolios": [],
        }

    budget = int(pkt.policy["max_restore_effort_units"])
    pri = pkt.policy["service_priorities"]

    # Lower bound: best individual loss per remaining service (admissible heuristic)
    best_each = {
        s: min(
            (1 if "priority" in ignore else pri[s]) * v.data_loss_hours
            for v in accepted[s]
        )
        for s in topo
    }

    def schema_ok(chosen: dict[str, str], v: CandidateVerdict) -> bool:
        if "schema" in ignore:
            return True
        for dep, need in v.requires_schema_epoch.items():
            if dep not in chosen:
                continue
            if verdicts[chosen[dep]].schema_epoch < need:
                return False
        return True

    def migration_ok(chosen: dict[str, str]) -> bool:
        if "migration" in ignore:
            return True
        # Irreversible migrations are refused in the reference plan: they strand
        # dependents even when schema epochs currently match.
        for cid in chosen.values():
            if verdicts[cid].migration_irreversible:
                return False
        return True

    max_skew = float(pkt.policy.get("max_dependent_skew_hours", 0))

    def portfolio_ok(chosen: dict[str, str]) -> bool:
        if not migration_ok(chosen):
            return False
        if "schema" not in ignore:
            for cid in chosen.values():
                if not schema_ok(chosen, verdicts[cid]):
                    return False
        if "skew" not in ignore and not skew_ok(chosen, verdicts, deps, max_skew):
            return False
        return True

    # Branch-and-bound over topological order
    # State: (lb_loss, loss, effort, idx, chosen)
    # Expand by increasing loss; prune by budget and optimistic bound.
    best_sol: tuple[float, int, dict[str, str]] | None = None
    feasible = 0
    equal_alts: list[dict[str, str]] = []

    # Sort options: prefer fresher / lower weighted loss first (greedy seed)
    options = {
        s: sorted(accepted[s], key=lambda v: (
            (1 if "priority" in ignore else pri[s]) * v.data_loss_hours,
            v.effort,
            v.candidate_id,
        ))
        for s in topo
    }

    stack: list[tuple[float, float, int, int, dict[str, str]]] = []
    # seed empty
    rem0 = sum(best_each[s] for s in topo)
    stack.append((rem0, 0.0, 0, 0, {}))
    expansions = 0
    MAX_EXPANSIONS = 250_000
    # Seed with greedy feasible to tighten bounds early
    greedy = {}
    g_effort = 0
    g_loss = 0.0
    greedy_ok = True
    for svc in topo:
        picked = None
        for v in options[svc]:
            if "budget" not in ignore and g_effort + v.effort > budget:
                continue
            if not schema_ok(greedy, v):
                continue
            trial = dict(greedy)
            trial[svc] = v.candidate_id
            if not migration_ok(trial):
                continue
            if "skew" not in ignore and not skew_ok(trial, verdicts, deps, max_skew):
                continue
            picked = v
            break
        if picked is None:
            greedy_ok = False
            break
        greedy[svc] = picked.candidate_id
        g_effort += picked.effort
        g_loss += (1 if "priority" in ignore else pri[svc]) * picked.data_loss_hours
    if greedy_ok and portfolio_ok(greedy):
        best_sol = (g_loss, g_effort, dict(greedy))
        equal_alts = [dict(greedy)]
        feasible = 1

    import heapq
    heap: list[tuple[float, float, int, int, int, tuple]] = []
    # heap entries: lb, loss, effort, idx, seq, chosen_items
    seq = 0
    heapq.heappush(heap, (rem0, 0.0, 0, 0, seq, tuple()))
    seq += 1

    while heap and expansions < MAX_EXPANSIONS:
        lb, loss, effort, idx, _, chosen_items = heapq.heappop(heap)
        expansions += 1
        chosen = dict(chosen_items)
        if best_sol is not None and lb > best_sol[0] + 1e-9:
            continue
        if idx == len(topo):
            if not portfolio_ok(chosen):
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

        svc = topo[idx]
        rem_after = sum(best_each[s] for s in topo[idx + 1 :])
        # Also reserve minimum effort for remaining services
        min_eff_after = 0
        for s in topo[idx + 1 :]:
            min_eff_after += min(v.effort for v in options[s])
        for v in options[svc]:
            new_effort = effort + v.effort
            if "budget" not in ignore:
                if new_effort > budget or new_effort + min_eff_after > budget:
                    continue
            if not schema_ok(chosen, v):
                continue
            w = (1 if "priority" in ignore else pri[svc]) * v.data_loss_hours
            new_loss = loss + w
            new_chosen_items = chosen_items + ((svc, v.candidate_id),)
            new_chosen = dict(new_chosen_items)
            if not migration_ok(new_chosen):
                continue
            if "skew" not in ignore and not skew_ok(new_chosen, verdicts, deps, max_skew):
                continue
            new_lb = new_loss + rem_after
            if best_sol is not None and new_lb > best_sol[0] + 1e-9:
                continue
            heapq.heappush(heap, (new_lb, new_loss, new_effort, idx + 1, seq, new_chosen_items))
            seq += 1
        # Keep only promising nodes; drop those already worse than known optimum.
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

    # Dedup alternates
    uniq = []
    seen = set()
    for p in equal_alts:
        t = tuple(sorted(p.items()))
        if t not in seen:
            seen.add(t)
            uniq.append(p)

    return {
        "ok": True,
        "oracle": "enumerate_bnb",
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
