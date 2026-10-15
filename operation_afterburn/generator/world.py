"""Sealed causal world for Operation AFTERBURN microcosm / scale."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from .ids import digest, h, pick, record_id, short_id, stable_shuffle

UTC = timezone.utc

SERVICES = [
    "payments-api",
    "checkout-bff",
    "inventory-svc",
    "catalog-svc",
    "auth-gateway",
    "fraud-engine",
    "notify-worker",
    "order-orchestrator",
    "shipping-adapter",
    "loyalty-points",
    "search-indexer",
    "media-cdn-edge",
    "tax-calculator",
    "promo-engine",
    "wallet-ledger",
    "risk-scoring",
    "partner-ingest",
    "storefront-web",
    "admin-console",
    "telemetry-collector",
]

CLUSTERS = {
    "us-east-prod": {"region": "us-east", "env": "production"},
    "eu-west-prod": {"region": "eu-west", "env": "production"},
    "ap-south-prod": {"region": "ap-south", "env": "production"},
    "us-east-stage": {"region": "us-east", "env": "staging"},
}

PLATFORMS = ["linux/amd64", "linux/arm64"]
COMPROMISED_POOL = "helix-ci-prod"
COMPROMISED_RUNNER = "helix-ci-prod/slot-12"
CLEAN_POOL = "helix-ci-shadow"
CLEAN_RUNNER = "helix-ci-shadow/slot-3"


def _ts(base: datetime, minutes: int = 0, seconds: int = 0) -> str:
    return (base + timedelta(minutes=minutes, seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_world(seed: int = 42, scale: str = "microcosm") -> dict[str, Any]:
    """Construct sealed truth graph. Never ship this object into agent data."""
    s = str(seed)
    day = datetime(2026, 10, 14, tzinfo=UTC)
    window_start = day.replace(hour=2, minute=10)
    window_end = day.replace(hour=4, minute=5)
    cutoff = day.replace(hour=9, minute=20)

    world: dict[str, Any] = {
        "seed": seed,
        "scale": scale,
        "incident": {
            "incident_id": short_id(s, "INC", "afterburn"),
            "compromised_pool": COMPROMISED_POOL,
            "compromised_runner": COMPROMISED_RUNNER,
            "window_start": _ts(window_start),
            "window_end": _ts(window_end),
            "cutoff": _ts(cutoff),
            "confirmed_at": _ts(cutoff),
            "board_deadline": _ts(day.replace(hour=10, minute=0)),
        },
        "services": [],
        "layers": {},
        "builds": {},
        "images": {},
        "tags": [],
        "admissions": [],
        "rollouts": [],
        "runtime": [],
        "workloads": {},
        "dependencies": [],
        "region_health": [],
        "approvals": [],
        "rollback_artifacts": [],
        "forcing_cases": {},
        "background_noise_factor": 1 if scale == "microcosm" else 8,
    }

    # Shared layers
    clean_base = digest(s, "layer", "base-clean")
    tainted_base = digest(s, "layer", "base-tainted")
    clean_app = digest(s, "layer", "app-clean-generic")
    world["layers"][clean_base] = {"tainted": False, "origin": "base-clean", "record": record_id(s, "LAY", 1)}
    world["layers"][tainted_base] = {
        "tainted": True,
        "origin": "base-built-on-compromised-runner",
        "record": record_id(s, "LAY", 2),
        "produced_by_build": None,  # filled after tainted base build
    }
    world["layers"][clean_app] = {"tainted": False, "origin": "app-clean", "record": record_id(s, "LAY", 3)}

    # Service metadata + quorum groups
    quorum_group = ["auth-gateway", "checkout-bff", "payments-api"]
    for i, name in enumerate(SERVICES):
        world["services"].append(
            {
                "service_id": name,
                "critical": name in quorum_group or name in ("wallet-ledger", "order-orchestrator"),
                "quorum_group": "edge-checkout" if name in quorum_group else None,
                "min_healthy_regions": 2 if name in quorum_group else 1,
                "namespaces": {
                    "production": name.replace("-", ""),
                    "staging": f"{name.replace('-', '')}-preview",
                },
            }
        )

    def add_build(
        key: str,
        *,
        service: str,
        runner: str,
        pool: str,
        t_minutes: int,
        layers: list[str],
        result: str = "SUCCESS",
        vendored_from: str | None = None,
    ) -> dict[str, Any]:
        inv = short_id(s, "build", key)
        # precise time
        btime = day.replace(hour=0) + timedelta(minutes=t_minutes)
        layers = list(layers)
        # Build output blob is the top layer so registry/runtime identity joins to CI output.
        art = digest(s, "artifact", key)
        if art not in layers:
            layers = layers + [art]
        tainted = (pool == COMPROMISED_POOL and window_start <= btime <= window_end) or any(
            world["layers"].get(L, {}).get("tainted") for L in layers
        )
        if vendored_from:
            parent = world["builds"][vendored_from]
            if parent["tainted"]:
                tainted = True
                layers = list(dict.fromkeys(layers + parent["layers"] + [parent["artifact_digest"]]))
        build = {
            "key": key,
            "invocation_id": inv,
            "service": service,
            "runner": runner,
            "pool": pool,
            "time": _ts(btime),
            "result": result,
            "artifact_digest": art,
            "layers": layers,
            "tainted": tainted,
            "attestation_valid": True,
            "vendored_from": vendored_from,
            "ci_record": record_id(s, "CI", len(world["builds"]) + 1),
            "att_record": record_id(s, "ATT", len(world["builds"]) + 1),
            "builder_record": record_id(s, "BLD", len(world["builds"]) + 1),
        }
        world["builds"][key] = build
        # register app layer mapping
        world["layers"][art] = {
            "tainted": tainted,
            "origin": f"artifact:{key}",
            "record": record_id(s, "LAY", 100 + len(world["layers"])),
            "produced_by_build": key,
        }
        return build

    def add_image(key: str, amd_layers: list[str], arm_layers: list[str] | None = None) -> dict[str, Any]:
        arm_layers = arm_layers if arm_layers is not None else amd_layers
        amd_m = digest(s, "manifest", key, "amd64")
        arm_m = digest(s, "manifest", key, "arm64")
        index = digest(s, "index", key)
        img = {
            "key": key,
            "index_digest": index,
            "platforms": {
                "linux/amd64": {"manifest_digest": amd_m, "layers": amd_layers, "oci_record": record_id(s, "OCI", len(world["images"]) * 2 + 1)},
                "linux/arm64": {"manifest_digest": arm_m, "layers": arm_layers, "oci_record": record_id(s, "OCI", len(world["images"]) * 2 + 2)},
            },
            "index_record": record_id(s, "OCI", 900 + len(world["images"])),
        }
        world["images"][key] = img
        return img

    def material_taint_for_manifest(manifest_digest: str) -> bool:
        for img in world["images"].values():
            for p in img["platforms"].values():
                if p["manifest_digest"] == manifest_digest:
                    return any(world["layers"].get(L, {}).get("tainted") for L in p["layers"])
        # direct artifact digest
        for b in world["builds"].values():
            if b["artifact_digest"] == manifest_digest:
                return b["tainted"]
        return False

    def add_workload(
        wid: str,
        *,
        service: str,
        cluster: str,
        platform: str,
        image_key: str,
        running: bool,
        admitted: bool,
        desired_image_key: str | None = None,
        env_override: str | None = None,
        forcing: str | None = None,
        disposition: str | None = None,
        exposure_path: str = "",
        stop_event_time: str | None = None,
        observe_recorded_after_cutoff: bool = False,
        dual_world: bool = False,
    ) -> dict[str, Any]:
        meta = CLUSTERS[cluster]
        env = env_override or meta["env"]
        img = world["images"][image_key]
        running_digest = img["platforms"][platform]["manifest_digest"]
        desired_key = desired_image_key or image_key
        desired_digest = world["images"][desired_key]["platforms"][platform]["manifest_digest"]
        tainted = material_taint_for_manifest(running_digest) if running and admitted and env == "production" else False
        if disposition is None:
            if dual_world:
                disposition = "UNRESOLVED"
            elif env != "production":
                disposition = "CLEARED"
            elif not admitted or not running:
                disposition = "CLEARED"
            elif tainted:
                disposition = "EXPOSED"
            else:
                disposition = "CLEARED"
        ns = world["services"][[x["service_id"] for x in world["services"]].index(service)]["namespaces"][
            "staging" if env == "staging" else "production"
        ]
        # special staging lookalike namespace
        if forcing == "F14":
            ns = "storefront-prod-preview"
            env = "staging"
            disposition = "CLEARED"
        wl = {
            "workload_id": wid,
            "service_id": service,
            "cluster": cluster,
            "region": meta["region"],
            "environment": env,
            "namespace": ns,
            "platform": platform,
            "image_key": image_key,
            "running_digest": running_digest,
            "desired_digest": desired_digest,
            "desired_image_key": desired_key,
            "admitted": admitted,
            "running_at_cutoff": running,
            "disposition": disposition,
            "forcing_case": forcing,
            "exposure_path": exposure_path,
            "stop_event_time": stop_event_time,
            "observe_recorded_after_cutoff": observe_recorded_after_cutoff,
            "dual_world": dual_world,
            "evidence_refs": [],
        }
        world["workloads"][wid] = wl
        return wl

    # --- Build inventory supporting forcing cases ---
    # Tainted base produced during window on compromised runner
    base_build = add_build(
        "base-tainted",
        service="telemetry-collector",
        runner=COMPROMISED_RUNNER,
        pool=COMPROMISED_POOL,
        t_minutes=140,  # 02:20
        layers=[clean_base],
    )
    # Mark tainted_base as produced by this build's artifact content
    # Rebind: use base_build artifact as the tainted shared layer content identity
    tainted_base = base_build["artifact_digest"]
    world["layers"][tainted_base]["tainted"] = True
    world["layers"][tainted_base]["produced_by_build"] = "base-tainted"

    # F03: fraud-engine direct tainted build with valid attestation
    b_fraud = add_build(
        "fraud-tainted",
        service="fraud-engine",
        runner=COMPROMISED_RUNNER,
        pool=COMPROMISED_POOL,
        t_minutes=155,
        layers=[clean_base, digest(s, "layer", "fraud-app")],
    )
    world["layers"][b_fraud["layers"][1]] = {"tainted": True, "origin": "fraud-app", "record": record_id(s, "LAY", 11)}
    img_fraud = add_image("fraud-tainted", b_fraud["layers"])

    # Clean fraud lookalike (different digest)
    b_fraud_clean = add_build(
        "fraud-clean",
        service="fraud-engine",
        runner=CLEAN_RUNNER,
        pool=CLEAN_POOL,
        t_minutes=400,
        layers=[clean_base, digest(s, "layer", "fraud-app-clean")],
    )
    world["layers"][b_fraud_clean["layers"][1]] = {"tainted": False, "origin": "fraud-app-clean", "record": record_id(s, "LAY", 12)}
    img_fraud_clean = add_image("fraud-clean", b_fraud_clean["layers"])

    # F01: payments-api — running tainted; tag later moved to clean
    b_pay_t = add_build(
        "pay-tainted",
        service="payments-api",
        runner=COMPROMISED_RUNNER,
        pool=COMPROMISED_POOL,
        t_minutes=165,
        layers=[clean_base, digest(s, "layer", "pay-app-t")],
    )
    world["layers"][b_pay_t["layers"][1]] = {"tainted": True, "origin": "pay-app-t", "record": record_id(s, "LAY", 13)}
    img_pay_t = add_image("pay-tainted", b_pay_t["layers"])
    b_pay_c = add_build(
        "pay-clean",
        service="payments-api",
        runner=CLEAN_RUNNER,
        pool=CLEAN_POOL,
        t_minutes=480,
        layers=[clean_base, digest(s, "layer", "pay-app-c")],
    )
    world["layers"][b_pay_c["layers"][1]] = {"tainted": False, "origin": "pay-app-c", "record": record_id(s, "LAY", 14)}
    img_pay_c = add_image("pay-clean", b_pay_c["layers"])

    # F02: risk-scoring — index with clean amd64, tainted arm64
    b_risk_amd = add_build(
        "risk-amd-clean",
        service="risk-scoring",
        runner=CLEAN_RUNNER,
        pool=CLEAN_POOL,
        t_minutes=200,
        layers=[clean_base, digest(s, "layer", "risk-amd")],
    )
    world["layers"][b_risk_amd["layers"][1]] = {"tainted": False, "origin": "risk-amd", "record": record_id(s, "LAY", 15)}
    b_risk_arm = add_build(
        "risk-arm-tainted",
        service="risk-scoring",
        runner=COMPROMISED_RUNNER,
        pool=COMPROMISED_POOL,
        t_minutes=175,
        layers=[clean_base, digest(s, "layer", "risk-arm")],
    )
    world["layers"][b_risk_arm["layers"][1]] = {"tainted": True, "origin": "risk-arm", "record": record_id(s, "LAY", 16)}
    img_risk = add_image("risk-mixed", b_risk_amd["layers"], b_risk_arm["layers"])

    # F04: catalog-svc clean builder but tainted base layer
    b_cat = add_build(
        "catalog-transitive",
        service="catalog-svc",
        runner=CLEAN_RUNNER,
        pool=CLEAN_POOL,
        t_minutes=210,
        layers=[tainted_base, digest(s, "layer", "catalog-app")],
    )
    world["layers"][b_cat["layers"][1]] = {"tainted": False, "origin": "catalog-app", "record": record_id(s, "LAY", 17)}
    # force taint via base
    b_cat["tainted"] = True
    world["layers"][b_cat["artifact_digest"]]["tainted"] = True
    img_cat = add_image("catalog-transitive", b_cat["layers"])

    # F05: promo-engine tainted build never admitted
    b_promo = add_build(
        "promo-tainted-rejected",
        service="promo-engine",
        runner=COMPROMISED_RUNNER,
        pool=COMPROMISED_POOL,
        t_minutes=180,
        layers=[clean_base, digest(s, "layer", "promo-app")],
    )
    world["layers"][b_promo["layers"][1]] = {"tainted": True, "origin": "promo-app", "record": record_id(s, "LAY", 18)}
    img_promo = add_image("promo-tainted", b_promo["layers"])
    b_promo_old = add_build(
        "promo-old-clean",
        service="promo-engine",
        runner=CLEAN_RUNNER,
        pool=CLEAN_POOL,
        t_minutes=60,
        layers=[clean_base, digest(s, "layer", "promo-old")],
    )
    world["layers"][b_promo_old["layers"][1]] = {"tainted": False, "origin": "promo-old", "record": record_id(s, "LAY", 19)}
    img_promo_old = add_image("promo-old", b_promo_old["layers"])

    # F06: inventory desired clean, running tainted
    b_inv_t = add_build(
        "inv-tainted",
        service="inventory-svc",
        runner=COMPROMISED_RUNNER,
        pool=COMPROMISED_POOL,
        t_minutes=170,
        layers=[clean_base, digest(s, "layer", "inv-t")],
    )
    world["layers"][b_inv_t["layers"][1]] = {"tainted": True, "origin": "inv-t", "record": record_id(s, "LAY", 20)}
    img_inv_t = add_image("inv-tainted", b_inv_t["layers"])
    b_inv_c = add_build(
        "inv-clean",
        service="inventory-svc",
        runner=CLEAN_RUNNER,
        pool=CLEAN_POOL,
        t_minutes=500,
        layers=[clean_base, digest(s, "layer", "inv-c")],
    )
    world["layers"][b_inv_c["layers"][1]] = {"tainted": False, "origin": "inv-c", "record": record_id(s, "LAY", 21)}
    img_inv_c = add_image("inv-clean", b_inv_c["layers"])

    # F07: shipping stopped before cutoff; delayed observation
    b_ship_t = add_build(
        "ship-tainted",
        service="shipping-adapter",
        runner=COMPROMISED_RUNNER,
        pool=COMPROMISED_POOL,
        t_minutes=160,
        layers=[clean_base, digest(s, "layer", "ship-t")],
    )
    world["layers"][b_ship_t["layers"][1]] = {"tainted": True, "origin": "ship-t", "record": record_id(s, "LAY", 22)}
    img_ship = add_image("ship-tainted", b_ship_t["layers"])

    # F09: tainted rollback candidate for payments
    # already have pay-tainted as previous green-looking rollback
    # F13-ish vendored: order-orchestrator vendors contaminated notify build
    b_notify_t = add_build(
        "notify-tainted",
        service="notify-worker",
        runner=COMPROMISED_RUNNER,
        pool=COMPROMISED_POOL,
        t_minutes=150,
        layers=[clean_base, digest(s, "layer", "notify-t")],
    )
    world["layers"][b_notify_t["layers"][1]] = {"tainted": True, "origin": "notify-t", "record": record_id(s, "LAY", 23)}
    b_order = add_build(
        "order-vendored",
        service="order-orchestrator",
        runner=CLEAN_RUNNER,
        pool=CLEAN_POOL,
        t_minutes=220,
        layers=[clean_base, digest(s, "layer", "order-app")],
        vendored_from="notify-tainted",
    )
    world["layers"][b_order["layers"][1]] = {"tainted": False, "origin": "order-app", "record": record_id(s, "LAY", 24)}
    b_order["tainted"] = True
    world["layers"][b_order["artifact_digest"]]["tainted"] = True
    img_order = add_image("order-vendored", b_order["layers"])
    img_notify = add_image("notify-tainted", b_notify_t["layers"])

    # Background clean builds for remaining services
    bg_images = {}
    for svc in SERVICES:
        key = f"bg-{svc}"
        if key in world["builds"]:
            continue
        # skip if we already created primary images for forcing services — still add clean secondary
        b = add_build(
            key,
            service=svc,
            runner=CLEAN_RUNNER,
            pool=CLEAN_POOL,
            t_minutes=90 + SERVICES.index(svc),
            layers=[clean_base, digest(s, "layer", f"bg-{svc}")],
        )
        world["layers"][b["layers"][1]] = {"tainted": False, "origin": f"bg-{svc}", "record": record_id(s, "LAY", 50 + SERVICES.index(svc))}
        bg_images[svc] = add_image(key, b["layers"])

    # --- Workloads / forcing placements ---
    fc: dict[str, Any] = {}

    # F01 payments running tainted; tag points to clean later
    w_pay = add_workload(
        "wl-payments-useast",
        service="payments-api",
        cluster="us-east-prod",
        platform="linux/amd64",
        image_key="pay-tainted",
        running=True,
        admitted=True,
        desired_image_key="pay-clean",
        forcing="F01",
        disposition="EXPOSED",
        exposure_path="compromised_runner->pay-tainted->running_digest",
    )
    fc["F01"] = {
        "workload_id": w_pay["workload_id"],
        "correct_disposition": "EXPOSED",
        "shortcut_tag_equals_digest": "CLEARED",
        "families": ["registry", "runtime"],
        "action_flip": True,
    }

    # F02 risk arm64 exposed in eu-west; amd64 clean in us-east
    w_risk_arm = add_workload(
        "wl-risk-eu-arm",
        service="risk-scoring",
        cluster="eu-west-prod",
        platform="linux/arm64",
        image_key="risk-mixed",
        running=True,
        admitted=True,
        forcing="F02",
        disposition="EXPOSED",
        exposure_path="compromised_runner->risk-arm-manifest->eu-west",
    )
    w_risk_amd = add_workload(
        "wl-risk-us-amd",
        service="risk-scoring",
        cluster="us-east-prod",
        platform="linux/amd64",
        image_key="risk-mixed",
        running=True,
        admitted=True,
        forcing="F02",
        disposition="CLEARED",
        exposure_path="clean_amd64_manifest",
    )
    fc["F02"] = {
        "workload_id": w_risk_arm["workload_id"],
        "cleared_workload_id": w_risk_amd["workload_id"],
        "correct_disposition": "EXPOSED",
        "shortcut_index_equals_manifest": "CLEARED",  # treating index as single identity may clear arm or expose amd wrongly
        "families": ["oci", "runtime"],
        "action_flip": True,
    }

    # F03 fraud exposed
    w_fraud = add_workload(
        "wl-fraud-useast",
        service="fraud-engine",
        cluster="us-east-prod",
        platform="linux/amd64",
        image_key="fraud-tainted",
        running=True,
        admitted=True,
        forcing="F03",
        disposition="EXPOSED",
        exposure_path="valid_attestation_from_compromised_builder",
    )
    fc["F03"] = {
        "workload_id": w_fraud["workload_id"],
        "correct_disposition": "EXPOSED",
        "shortcut_valid_signature_clean": "CLEARED",
        "families": ["attestation", "builder"],
        "action_flip": True,
    }

    # F04 catalog transitive
    w_cat = add_workload(
        "wl-catalog-useast",
        service="catalog-svc",
        cluster="us-east-prod",
        platform="linux/amd64",
        image_key="catalog-transitive",
        running=True,
        admitted=True,
        forcing="F04",
        disposition="EXPOSED",
        exposure_path="tainted_base_layer_in_clean_builder_image",
    )
    fc["F04"] = {
        "workload_id": w_cat["workload_id"],
        "correct_disposition": "EXPOSED",
        "shortcut_runner_direct_only": "CLEARED",
        "families": ["build", "oci"],
        "action_flip": True,
    }

    # F05 promo never admitted — running old clean
    w_promo = add_workload(
        "wl-promo-useast",
        service="promo-engine",
        cluster="us-east-prod",
        platform="linux/amd64",
        image_key="promo-old",
        running=True,
        admitted=True,
        forcing="F05",
        disposition="CLEARED",
        exposure_path="tainted_build_not_admitted",
    )
    fc["F05"] = {
        "workload_id": w_promo["workload_id"],
        "correct_disposition": "CLEARED",
        "shortcut_build_equals_production": "EXPOSED",
        "families": ["ci", "admission", "runtime"],
        "clearance_flip": True,
    }

    # F06 inventory desired clean, running tainted
    w_inv = add_workload(
        "wl-inventory-useast",
        service="inventory-svc",
        cluster="us-east-prod",
        platform="linux/amd64",
        image_key="inv-tainted",
        running=True,
        admitted=True,
        desired_image_key="inv-clean",
        forcing="F06",
        disposition="EXPOSED",
        exposure_path="desired_superseded_by_old_running_pods",
    )
    fc["F06"] = {
        "workload_id": w_inv["workload_id"],
        "correct_disposition": "EXPOSED",
        "shortcut_desired_equals_running": "CLEARED",
        "families": ["rollout", "runtime"],
        "action_flip": True,
    }

    # F07 shipping stopped; delayed observation
    stop_t = _ts(cutoff - timedelta(minutes=40))
    w_ship = add_workload(
        "wl-shipping-eu",
        service="shipping-adapter",
        cluster="eu-west-prod",
        platform="linux/amd64",
        image_key="ship-tainted",
        running=False,
        admitted=True,
        forcing="F07",
        disposition="CLEARED",
        exposure_path="stopped_before_cutoff_delayed_observation",
        stop_event_time=stop_t,
        observe_recorded_after_cutoff=True,
    )
    fc["F07"] = {
        "workload_id": w_ship["workload_id"],
        "correct_disposition": "CLEARED",
        "shortcut_latest_log_is_live": "EXPOSED",
        "families": ["runtime", "ops"],
        "clearance_flip": True,
    }

    # F09 rollback tainted
    world["rollback_artifacts"].append(
        {
            "service_id": "payments-api",
            "label": "previous-green",
            "image_key": "pay-tainted",
            "digest": img_pay_t["platforms"]["linux/amd64"]["manifest_digest"],
            "tainted": True,
            "available_regions": ["us-east", "eu-west"],
            "record": record_id(s, "RBK", 1),
        }
    )
    world["rollback_artifacts"].append(
        {
            "service_id": "payments-api",
            "label": "last-known-clean",
            "image_key": "pay-clean",
            "digest": img_pay_c["platforms"]["linux/amd64"]["manifest_digest"],
            "tainted": False,
            "available_regions": ["us-east", "eu-west", "ap-south"],
            "record": record_id(s, "RBK", 2),
        }
    )
    world["rollback_artifacts"].append(
        {
            "service_id": "fraud-engine",
            "label": "last-known-clean",
            "image_key": "fraud-clean",
            "digest": img_fraud_clean["platforms"]["linux/amd64"]["manifest_digest"],
            "tainted": False,
            "available_regions": ["us-east", "eu-west", "ap-south"],
            "record": record_id(s, "RBK", 3),
        }
    )
    world["rollback_artifacts"].append(
        {
            "service_id": "catalog-svc",
            "label": "last-known-clean",
            "image_key": "bg-catalog-svc",
            "digest": bg_images["catalog-svc"]["platforms"]["linux/amd64"]["manifest_digest"],
            "tainted": False,
            "available_regions": ["us-east", "eu-west", "ap-south"],
            "record": record_id(s, "RBK", 4),
        }
    )
    world["rollback_artifacts"].append(
        {
            "service_id": "inventory-svc",
            "label": "last-known-clean",
            "image_key": "inv-clean",
            "digest": img_inv_c["platforms"]["linux/amd64"]["manifest_digest"],
            "tainted": False,
            "available_regions": ["us-east", "eu-west", "ap-south"],
            "record": record_id(s, "RBK", 5),
        }
    )
    world["rollback_artifacts"].append(
        {
            "service_id": "risk-scoring",
            "label": "last-known-clean",
            "image_key": "bg-risk-scoring",
            "digest": bg_images["risk-scoring"]["platforms"]["linux/amd64"]["manifest_digest"],
            "tainted": False,
            "available_regions": ["us-east", "ap-south"],  # eu-west replica unavailable intentional for F10-ish
            "record": record_id(s, "RBK", 6),
        }
    )
    world["rollback_artifacts"].append(
        {
            "service_id": "order-orchestrator",
            "label": "last-known-clean",
            "image_key": "bg-order-orchestrator",
            "digest": bg_images["order-orchestrator"]["platforms"]["linux/amd64"]["manifest_digest"],
            "tainted": False,
            "available_regions": ["us-east", "eu-west", "ap-south"],
            "record": record_id(s, "RBK", 7),
        }
    )
    fc["F09"] = {
        "service_id": "payments-api",
        "unsafe_recovery_digest": img_pay_t["platforms"]["linux/amd64"]["manifest_digest"],
        "safe_recovery_digest": img_pay_c["platforms"]["linux/amd64"]["manifest_digest"],
        "correct_action": "redeploy_clean",
        "shortcut_previous_green": "redeploy_tainted",
        "families": ["registry", "oci", "ops"],
        "recovery_flip": True,
    }

    # F11 quorum: auth-gateway + checkout-bff + payments must keep 2 regions
    # Place clean auth in 3 regions; checkout exposed in us-east only
    b_co_t = add_build(
        "checkout-tainted",
        service="checkout-bff",
        runner=COMPROMISED_RUNNER,
        pool=COMPROMISED_POOL,
        t_minutes=168,
        layers=[clean_base, digest(s, "layer", "co-t")],
    )
    world["layers"][b_co_t["layers"][1]] = {"tainted": True, "origin": "co-t", "record": record_id(s, "LAY", 25)}
    img_co = add_image("checkout-tainted", b_co_t["layers"])
    world["rollback_artifacts"].append(
        {
            "service_id": "checkout-bff",
            "label": "last-known-clean",
            "image_key": "bg-checkout-bff",
            "digest": bg_images["checkout-bff"]["platforms"]["linux/amd64"]["manifest_digest"],
            "tainted": False,
            "available_regions": ["us-east", "eu-west", "ap-south"],
            "record": record_id(s, "RBK", 8),
        }
    )
    w_co = add_workload(
        "wl-checkout-useast",
        service="checkout-bff",
        cluster="us-east-prod",
        platform="linux/amd64",
        image_key="checkout-tainted",
        running=True,
        admitted=True,
        forcing="F11",
        disposition="EXPOSED",
        exposure_path="direct_taint_quorum_coupled",
    )
    # Healthy replicas for quorum group
    for cluster, svc, key in [
        ("eu-west-prod", "checkout-bff", "bg-checkout-bff"),
        ("ap-south-prod", "checkout-bff", "bg-checkout-bff"),
        ("us-east-prod", "auth-gateway", "bg-auth-gateway"),
        ("eu-west-prod", "auth-gateway", "bg-auth-gateway"),
        ("ap-south-prod", "auth-gateway", "bg-auth-gateway"),
        ("eu-west-prod", "payments-api", "pay-clean"),
        ("ap-south-prod", "payments-api", "pay-clean"),
    ]:
        add_workload(
            f"wl-{svc}-{cluster}",
            service=svc,
            cluster=cluster,
            platform="linux/amd64",
            image_key=key,
            running=True,
            admitted=True,
            disposition="CLEARED",
        )
    fc["F11"] = {
        "workload_id": w_co["workload_id"],
        "correct_sequence_constraint": "maintain_edge-checkout_quorum_2",
        "shortcut_stop_all": "quorum_violation",
        "families": ["dependencies", "health"],
        "recovery_flip": True,
    }

    # F14 staging lookalike
    w_store = add_workload(
        "wl-storefront-stage",
        service="storefront-web",
        cluster="us-east-stage",
        platform="linux/amd64",
        image_key="fraud-tainted",  # alarming digest in staging
        running=True,
        admitted=True,
        forcing="F14",
        disposition="CLEARED",
        exposure_path="staging_namespace_lookalike",
    )
    fc["F14"] = {
        "workload_id": w_store["workload_id"],
        "correct_disposition": "CLEARED",
        "shortcut_namespace_string_prod": "EXPOSED",
        "families": ["inventory", "runtime"],
        "clearance_flip": True,
    }

    # F15 unresolved partner-ingest
    b_part = add_build(
        "partner-ambiguous",
        service="partner-ingest",
        runner=COMPROMISED_RUNNER,
        pool=COMPROMISED_POOL,
        t_minutes=190,
        layers=[clean_base, digest(s, "layer", "partner-t")],
    )
    world["layers"][b_part["layers"][1]] = {"tainted": True, "origin": "partner-t", "record": record_id(s, "LAY", 26)}
    img_part = add_image("partner-ambiguous", b_part["layers"])
    w_part = add_workload(
        "wl-partner-apsouth",
        service="partner-ingest",
        cluster="ap-south-prod",
        platform="linux/amd64",
        image_key="partner-ambiguous",
        running=False,
        admitted=True,  # admitted but no conclusive runtime
        forcing="F15",
        disposition="UNRESOLVED",
        dual_world=True,
        exposure_path="admission_without_runtime_observation",
    )
    fc["F15"] = {
        "workload_id": w_part["workload_id"],
        "correct_disposition": "UNRESOLVED",
        "shortcut_assume_success": "EXPOSED",
        "families": ["admission", "runtime"],
        "uncertainty_flip": True,
    }

    # F12 post-cutoff approval
    world["approvals"].append(
        {
            "record": record_id(s, "CHG", 1),
            "service_id": "payments-api",
            "change_type": "emergency_redeploy",
            "recorded_time": _ts(cutoff - timedelta(minutes=5)),
            "effective_time": _ts(cutoff + timedelta(minutes=30)),
            "status": "approved",
            "restriction": "effective_after_board_window",
            "usable_at_cutoff": False,
        }
    )
    world["approvals"].append(
        {
            "record": record_id(s, "CHG", 2),
            "service_id": "*",
            "change_type": "containment",
            "recorded_time": _ts(cutoff - timedelta(minutes=25)),
            "effective_time": _ts(cutoff - timedelta(minutes=20)),
            "status": "approved",
            "restriction": "maintain_edge-checkout_min_healthy_regions_2",
            "usable_at_cutoff": True,
        }
    )
    world["approvals"].append(
        {
            "record": record_id(s, "CHG", 3),
            "service_id": "fraud-engine",
            "change_type": "emergency_redeploy",
            "recorded_time": _ts(cutoff - timedelta(minutes=15)),
            "effective_time": _ts(cutoff - timedelta(minutes=10)),
            "status": "approved",
            "restriction": "none",
            "usable_at_cutoff": True,
        }
    )
    world["approvals"].append(
        {
            "record": record_id(s, "CHG", 4),
            "service_id": "catalog-svc",
            "change_type": "emergency_redeploy",
            "recorded_time": _ts(cutoff - timedelta(minutes=12)),
            "effective_time": _ts(cutoff - timedelta(minutes=8)),
            "status": "approved",
            "restriction": "none",
            "usable_at_cutoff": True,
        }
    )
    world["approvals"].append(
        {
            "record": record_id(s, "CHG", 5),
            "service_id": "inventory-svc",
            "change_type": "emergency_redeploy",
            "recorded_time": _ts(cutoff - timedelta(minutes=12)),
            "effective_time": _ts(cutoff - timedelta(minutes=8)),
            "status": "approved",
            "restriction": "none",
            "usable_at_cutoff": True,
        }
    )
    world["approvals"].append(
        {
            "record": record_id(s, "CHG", 6),
            "service_id": "checkout-bff",
            "change_type": "emergency_redeploy",
            "recorded_time": _ts(cutoff - timedelta(minutes=12)),
            "effective_time": _ts(cutoff - timedelta(minutes=8)),
            "status": "approved",
            "restriction": "maintain_edge-checkout_min_healthy_regions_2",
            "usable_at_cutoff": True,
        }
    )
    world["approvals"].append(
        {
            "record": record_id(s, "CHG", 7),
            "service_id": "risk-scoring",
            "change_type": "emergency_redeploy",
            "recorded_time": _ts(cutoff - timedelta(minutes=12)),
            "effective_time": _ts(cutoff - timedelta(minutes=8)),
            "status": "approved",
            "restriction": "prefer_available_regions",
            "usable_at_cutoff": True,
        }
    )
    world["approvals"].append(
        {
            "record": record_id(s, "CHG", 8),
            "service_id": "order-orchestrator",
            "change_type": "emergency_redeploy",
            "recorded_time": _ts(cutoff - timedelta(minutes=12)),
            "effective_time": _ts(cutoff - timedelta(minutes=8)),
            "status": "approved",
            "restriction": "none",
            "usable_at_cutoff": True,
        }
    )
    fc["F12"] = {
        "service_id": "payments-api",
        "correct_authority": "containment_only_until_effective",
        "shortcut_recorded_means_effective": "unauthorized_redeploy",
        "families": ["changes", "timestamps"],
        "recovery_flip": True,
    }

    # F13 order vendored exposure
    w_order = add_workload(
        "wl-order-useast",
        service="order-orchestrator",
        cluster="us-east-prod",
        platform="linux/amd64",
        image_key="order-vendored",
        running=True,
        admitted=True,
        forcing="F13",
        disposition="EXPOSED",
        exposure_path="vendored_notify_output_in_clean_rebuild",
    )
    fc["F13"] = {
        "workload_id": w_order["workload_id"],
        "correct_disposition": "EXPOSED",
        "shortcut_direct_deps_only": "CLEARED",
        "families": ["source", "build", "runtime"],
        "action_flip": True,
    }

    # Additional clean background workloads
    for svc in SERVICES:
        if any(w["service_id"] == svc and w.get("forcing_case") for w in world["workloads"].values()):
            # still add a clean secondary region for some
            pass
        wid = f"wl-bg-{svc}-eu"
        if wid in world["workloads"]:
            continue
        # avoid duplicating explicit ones
        if svc in ("payments-api", "checkout-bff", "auth-gateway", "risk-scoring", "shipping-adapter", "partner-ingest"):
            continue
        add_workload(
            wid,
            service=svc,
            cluster="eu-west-prod",
            platform="linux/amd64",
            image_key=f"bg-{svc}",
            running=True,
            admitted=True,
            disposition="CLEARED",
        )

    # Dependencies / health
    world["dependencies"] = [
        {
            "record": record_id(s, "DEP", 1),
            "group": "edge-checkout",
            "members": ["auth-gateway", "checkout-bff", "payments-api"],
            "min_healthy_regions": 2,
            "rule": "At least two regions must remain healthy for each member during containment.",
        }
    ]
    for region, status in [("us-east", "healthy"), ("eu-west", "healthy"), ("ap-south", "degraded")]:
        world["region_health"].append(
            {
                "record": record_id(s, "HLTH", len(world["region_health"]) + 1),
                "region": region,
                "status": status,
                "notes": "ap-south capacity limited" if region == "ap-south" else "ok",
            }
        )

    # Tag mutations: F01 tag moved to clean after running tainted
    world["tags"] = [
        {
            "record": record_id(s, "REG", 1),
            "repository": "payments-api",
            "tag": "stable",
            "digest": img_pay_t["index_digest"],
            "event": "TAG_MOVED",
            "time": _ts(window_start + timedelta(minutes=60)),
        },
        {
            "record": record_id(s, "REG", 2),
            "repository": "payments-api",
            "tag": "stable",
            "digest": img_pay_c["index_digest"],
            "event": "TAG_MOVED",
            "time": _ts(cutoff - timedelta(minutes=30)),
        },
        {
            "record": record_id(s, "REG", 3),
            "repository": "fraud-engine",
            "tag": "stable",
            "digest": img_fraud["index_digest"],
            "event": "TAG_MOVED",
            "time": _ts(window_start + timedelta(minutes=50)),
        },
        {
            "record": record_id(s, "REG", 4),
            "repository": "risk-scoring",
            "tag": "stable",
            "digest": img_risk["index_digest"],
            "event": "TAG_MOVED",
            "time": _ts(window_start + timedelta(minutes=70)),
        },
    ]

    world["forcing_cases"] = fc
    world["material_taint_fn_note"] = "layers marked tainted in world['layers']"
    return world


def exposed_workloads(world: dict[str, Any]) -> list[dict[str, Any]]:
    return [w for w in world["workloads"].values() if w["disposition"] == "EXPOSED"]


def clone_world(world: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(world)
