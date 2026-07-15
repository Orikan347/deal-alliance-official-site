#!/usr/bin/env python3
"""Report the official-site goal truth without treating candidate Gates as release proof."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
site = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
contract = json.loads((ROOT / "release_contract.json").read_text(encoding="utf-8"))
catalog = json.loads((ROOT / "tools/catalog.json").read_text(encoding="utf-8"))

if site.get("accountPortalStatus") != "PUBLIC_CTA_DISABLED_PENDING_OWNER_EMAIL_READBACK":
    raise SystemExit("FAIL_GOAL_READINESS account CTA must remain disabled until owner email readback")
portal = contract.get("account_portal", {})
if portal.get("mode") != "disabled" or portal.get("allowed_origins") != []:
    raise SystemExit("FAIL_GOAL_READINESS account portal no longer matches the fail-closed boundary")
if contract.get("status") != "PUBLIC_TECHNICAL_RELEASE_VERIFIED":
    raise SystemExit("FAIL_GOAL_READINESS technical release evidence is missing")
candidate_content = contract.get("candidate_content_release", {})
if candidate_content.get("status") != "PUBLIC_ORIGIN_READBACK_PASS_OPERATIONAL_PENDING":
    raise SystemExit("FAIL_GOAL_READINESS candidate content release state is inconsistent")
if not catalog or any(item.get("offer_status") not in {"WAITLIST_ONLY", "NOT_ENABLED"} for item in catalog):
    raise SystemExit("FAIL_GOAL_READINESS public catalog exposes an unapproved service")
operational = contract.get("operational_readiness", {})
if operational.get("release_ready") is not False or operational.get("status") != "PENDING_OWNER_PUBLIC_LEGAL_AND_SUPPORT":
    raise SystemExit("FAIL_GOAL_READINESS operational status must remain owner-pending")
if contract.get("monitoring", {}).get("external_setup_status") != "PENDING_OWNER_CONFIGURATION":
    raise SystemExit("FAIL_GOAL_READINESS monitoring setup status is inconsistent")
if not (ROOT / "tests" / "verify_public_release.py").exists():
    raise SystemExit("FAIL_GOAL_READINESS public readback Gate is missing")

print(
    "PASS_GOAL_READINESS_AUDIT "
    "visitor_understanding=public_technical_release_verified "
    "registration=deidentified_remote_pass_owner_email_readback_pending "
    "authorized_services=none_public_account_cta_disabled "
    "seo_geo=technical_gate_ready "
    "operational=false "
    "monitoring=owner_pending "
    "origin=public_https_readback_verified candidate_content=public_origin_readback_pass_operational_pending"
)
