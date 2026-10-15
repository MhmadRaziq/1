# Strong-model cold trials — Operation CLEARWATER

**Protocol:** Four independent agents received only `/tmp/clearwater_cold/instruction.md` and `/tmp/clearwater_cold/data/` (agent-visible packet). No oracle, author_only labels, generator modes, or reference portfolio were provided. Deliverables graded with `verifier/grade.py` against the same packet.

| Trial | Model | Status | Reward | Notes |
|---|---|---|---:|---|
| A | claude-sonnet-5-5-high | PENDING | — | background agent bc-2143f407… |
| B | gpt-5.6-sol-high | PENDING | — | background agent bc-c6fc7b05… |
| C | claude-opus-5-5-high | PENDING | — | background agent bc-78384a22… |
| D | composer-2.5 | PENDING | — | background agent bc-554e1b77… |

Results will be filled when trials complete. Per design kit: if mean reward remains ~0.99, redesign causal interactions rather than adding prompt friction.

**This section is not a platform Model Sweep.**
