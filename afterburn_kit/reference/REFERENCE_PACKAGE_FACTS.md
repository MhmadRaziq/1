# Facts inspected in the local reference archive

- Archive: `enterprise-credential-hop-containment.zip` (present in the user's workspace).
- Root: `instruction.md`, `task_card.md`, `task.toml`, `rubrics.json`, `environment/`, `solution/`, `tests/`.
- Data: compressed authentication, DNS, network flow and process event telemetry plus seed and containment standard.
- Outputs: `attack_chain.csv`, `containment_scope.csv`, `cleared_findings.csv`, `incident_brief.md`.
- Rubric: 35 positive criteria, 100 points, source-grounded containment findings.
- The task card claims a seed-linked 28-hop chain, 17 hosts to isolate, 13 credentials to reset and six cleared lookalikes. These are claims within the supplied reference and should not be represented as independent proof of private platform performance.
- Strengths: confirmed seed, corroboration, clearance, scope and independent evidence.
- Weakness to avoid in new task: reproducing a predictable deterministic graph rule or counting data volume as model difficulty.

The source ZIP is not duplicated in this kit, to avoid needless reuse and licensing/similarity issues. Read the original in the user's workspace when implementing.
