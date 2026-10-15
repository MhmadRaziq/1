# Pre-sweep hardness protocol: measure, do not guess

## Stage 0 — independent solvability
- Author builds causal truth; separate engineer/model solves only from agent-visible data.
- Independently reconcile all scored cases; freeze seed and truth snapshot.
- All ambiguity is either resolved by evidence or scored as acceptable uncertainty.

## Stage 1 — decision-sensitive forcing proof
At least **8** independently causal cases spanning **4** capability families. At least 4 must flip an operational action; at least 2 must flip clearance; at least 2 must flip recovery feasibility/sequence. For each: correct path, shortcut path, evidence IDs, changed output, changed action, rubric points affected. If the shortcut yields the same scored outcome, the case does **not** count.

## Stage 2 — shortcut tournament
Implement 12–16 cheap solvers and measure full output/reward, not only qualitative difference. Mandatory shortcuts:
1. all signed artifacts clean;
2. all builds from runner tainted even when never deployed;
3. tag equals digest;
4. latest registry tag wins at cutoff;
5. OCI index digest equals platform manifest;
6. ignore base layers;
7. ignore vendored dependencies;
8. desired deployment equals running;
9. last observed pod remains active forever;
10. any build with suspicious dependency is affected;
11. rollback to latest previously green build;
12. stop all affected services immediately;
13. ignore service quorum;
14. ignore change approvals;
15. ignore after-cutoff timing;
16. ignore one entire evidence family.

Target: ≥10 shortcuts give wrong scored results; ≥5 distinct wrong final response decisions; no simple shortcut earns a passing sweep reward. This is an engineering acceptance target, not an AfterQuery guarantee.

## Stage 3 — ablation
Remove one family at a time: builder, source/lockfile, registry, runtime, change records, operations. At least 3 ablations must change a scored decision; at least 2 must alter the actual intervention set/sequence. If not, that family may be decoration.

## Stage 4 — compression challenge
Give an independent agent 10 minutes to identify the smallest solver representation. If a simple 10–15 column per-service table can be populated directly from one or two files, reject the concept. Hardness should require discovering the relevant artifacts, reconstructing authority and linking runtime to build materials.

## Stage 5 — independent strong-model trial
Run at least 3 independent cold starts without author-only information. Record per-criterion reward, time, solver traces, mistakes and cost. Use held-out seeds. Avoid designing around a single model's weakness; do not leak oracle through the prompt or test artifacts.

## Stage 6 — mutation regression
Mutate both the input evidence and the answer. If you flip a causal source fact, the oracle and the expected action should change. If you flip a cosmetic timestamp or unrelated event, the answer should remain stable. This metamorphic test detects fake complexity.

## Quantitative release gate
- Reference solution 100/100 on three seeds.
- 0 missing rubric coverage, 0 incompatible criterion pairs.
- No-op reward near zero; ≥15/18 negative mutants rejected.
- ≥8 forcing cases, ≥4 families, ≥10 shortcut failures, ≥5 distinct wrong outcomes.
- ≥3 material ablations, ≥2 affecting response action.
- No one input file is a compact answer index.
- Strong-model dry runs are genuinely below the target band on the *same rubric*, while competent independent humans/agents can solve the task with adequate time.

If a strong model again scores ~0.99, **change the evidence geometry and causal couplings**. Do not just add 100k more noise records or increase output formatting demands.
