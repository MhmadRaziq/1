# Incident notice — suspected build-runner compromise

**Incident ID:** INC-83e378abf0  
**Confirmed:** 2026-10-14T09:20:00Z  
**Investigation cutoff:** 2026-10-14T09:20:00Z  
**Board decision deadline:** 2026-10-14T10:00:00Z

## Confirmed facts
Security engineering confirmed that the ephemeral build-runner environment used by pool `helix-ci-prod` was compromised between **2026-10-14T02:10:00Z** and **2026-10-14T04:05:00Z**. Runner identity of primary concern: `helix-ci-prod/slot-12`.

CI dashboards continue to show successful builds and authenticated attestations. Treat attestation authenticity and builder trustworthiness as separate questions.

## Ask
By the cutoff, determine which production workloads materially run code affected by the compromised build path, which apparent matches are not material exposures, and which response sequence reduces risk without violating availability commitments.

This packet is offline and complete. Do not use the network or perform live changes.
