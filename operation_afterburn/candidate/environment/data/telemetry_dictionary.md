# Telemetry dictionary (supported fields)

## Timing
- `time` / `event_time`: when the fact occurred operationally.
- `recorded_time`: when the telemetry system ingested the record. May be after the event.
- Investigation decisions use event/effective times at or before the cutoff unless a document says otherwise.

## Identity
- `invocation_id`: CI build invocation.
- `digest` / `manifest_digest` / `image_id`: content digests (`sha256:...`).
- `index_digest`: OCI image index digest; selects platform manifests and is not interchangeable with a platform manifest digest.
- `workload_id`: stable runtime workload identity in inventory.

## Environments
Production clusters are named `*-prod`. Staging clusters are named `*-stage`. Namespace strings alone are not authoritative; reconcile with cluster/environment inventory.

## Disposition vocabulary (outputs)
`EXPOSED`, `CLEARED`, `UNRESOLVED`.

## Response actions (outputs)
`redeploy`, `quarantine`, `isolate`, `observe`, `hold`.
