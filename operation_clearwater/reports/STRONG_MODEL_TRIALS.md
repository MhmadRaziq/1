# Strong-model cold trials — Operation CLEARWATER

**Protocol:** Four independent agents received only the agent-visible instruction + `/data` packet. No oracle, author_only labels, or reference portfolio.

| Trial | Model | Status | Reward | Notes |
|---|---|---|---:|---|
| A | claude-sonnet-5-5-high | GRADED | 100.0 | all graded checks passed; loss=1495.0 |
| B | gpt-5.6-sol-high | GRADED | 100.0 | all graded checks passed; loss=1495.0 |
| C | claude-opus-5-5-high | MISSING | — |  |
| D | composer-2.5 | GRADED | 62.0 | failed: no_unsafe_sources, citations_resolvable, no_fabricated_citations, near_optimal_loss, matches_reference_portfolio |

**Graded trials:** 3/4
**Mean reward:** 87.33

**Hardness proxy:** mean below 0.90 on local cold trials.

**This section is not a platform Model Sweep.**
