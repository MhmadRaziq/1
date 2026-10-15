# Service recovery commitments

## Edge checkout quorum
Services `auth-gateway`, `checkout-bff`, and `payments-api` form group `edge-checkout`. During incident response, at least **two regions** must remain healthy for each member. Do not stop or quarantine all healthy regional replicas of these services in a single step.

## Regional notes
- `us-east` and `eu-west` are primary failover pair.
- `ap-south` may be capacity-constrained; confirm region health before relying on it for recovery.

## Change windows
Emergency containment that preserves quorum is pre-authorized under the standing containment approval. Redeploys require a service-specific approval that is effective by the investigation cutoff.
