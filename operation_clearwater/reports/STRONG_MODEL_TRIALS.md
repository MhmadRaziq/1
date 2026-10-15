# Strong-model cold trials — Operation CLEARWATER

**Protocol:** Four independent agents received only the agent-visible instruction + `/data` packet. No oracle, author_only labels, or reference portfolio.

**Packet versions:** Trials were authored against the pre-redesign packet (where `AUDITLOG-LATEST` was admissible). Scores below are **re-grades on the hardened packet** (`block_held_targets_inside_open_indicator_windows`, held freshest auditlog trap). Pre-redesign scores were A/B/C=100, D=62 (mean 90.5) — triggering redesign.

| Trial | Model | Status | Reward | Notes |
|---|---|---|---:|---|
| A | claude-sonnet-5-5-high | GRADED | 75.0 | selected AUDITLOG-LATEST (held + open indicator); failed: no_unsafe_sources, near_optimal_loss, matches_reference_portfolio |
| B | gpt-5.6-sol-high | GRADED | 75.0 | selected AUDITLOG-LATEST; failed: no_unsafe_sources, near_optimal_loss, matches_reference_portfolio |
| C | claude-opus-5-5-high | GRADED | 75.0 | selected AUDITLOG-LATEST; failed: no_unsafe_sources, near_optimal_loss, matches_reference_portfolio |
| D | composer-2.5 | GRADED | 63.0 | selected AUDITLOG-LATEST + citation issues; failed: no_unsafe_sources, citations_resolvable, no_fabricated_citations, near_optimal_loss, matches_reference_portfolio |

**Graded trials:** 4/4  
**Mean reward (hardened packet):** 72.00  

**Hardness proxy:** mean below 0.90 on local cold trials (redesign trigger ≥0.99 cleared).

**This section is not a platform Model Sweep.**
