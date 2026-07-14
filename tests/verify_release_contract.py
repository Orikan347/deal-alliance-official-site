#!/usr/bin/env python3
"""Verify release, monitoring, and rollback requirements without external calls."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
contract = json.loads((ROOT / "release_contract.json").read_text(encoding="utf-8"))
if contract["status"] not in {"PENDING_EXTERNAL_RELEASE", "PUBLIC_RELEASE_VERIFIED_PENDING_REGISTRATION", "PUBLIC_RELEASE_VERIFIED_STAGING_ACCOUNT_LIFECYCLE_PASS_CTA_CANDIDATE_ENABLED_PENDING_USER_ACCEPTANCE", "PUBLIC_RELEASE_VERIFIED_CTA_LIVE_PENDING_USER_ACCEPTANCE", "PUBLIC_TECHNICAL_RELEASE_VERIFIED"}:
    raise SystemExit("FAIL_RELEASE_CONTRACT status is unknown")
if contract["origin"] != "https://www.dealalliancehub.com":
    raise SystemExit("FAIL_RELEASE_CONTRACT origin must be the owner-confirmed formal origin")
if contract["origin_status"] not in {"OWNER_CONFIRMED_NOT_DEPLOYED", "PUBLIC_HTTPS_READBACK_VERIFIED"}:
    raise SystemExit("FAIL_RELEASE_CONTRACT origin status is unknown")
workflow = contract["deployment_workflow"]
workflow_path = ROOT / workflow["path"]
if not workflow_path.exists() or workflow["trigger"] != "workflow_dispatch" or workflow["automatic_publish"]:
    raise SystemExit("FAIL_RELEASE_CONTRACT deployment must be manual and owner-approved")
if (workflow.get("provider") != "Cloudflare Pages"
        or workflow.get("build_command") != "bash scripts/build-public.sh"
        or workflow.get("output_directory") != "dist"
        or workflow.get("production_branch") != "agent/official-site-v1"
        or workflow.get("deployed_commit") != "2cf21d6"
        or workflow.get("preceding_release_commit") != "38ad43a"):
    raise SystemExit("FAIL_RELEASE_CONTRACT public technical release provenance is incomplete")
monitoring_runbook = ROOT / "公開監控與回滾演練清單_2026-07-14.md"
required_runbook_markers = (
    "verify_public_release.py",
    "verify_account_portal_public.py",
    "敏感資料",
    "38ad43a",
    "候補 receiver 仍 disabled",
)
if (not monitoring_runbook.exists()
        or any(marker not in monitoring_runbook.read_text(encoding="utf-8") for marker in required_runbook_markers)):
    raise SystemExit("FAIL_RELEASE_CONTRACT monitoring and rollback runbook is incomplete")
for path in contract["required_public_paths"]:
    if path == "/":
        target = ROOT / "index.html"
    elif path.endswith("/"):
        target = ROOT / path.strip("/") / "index.html"
    else:
        target = ROOT / path.strip("/")
    if not target.exists():
        raise SystemExit(f"FAIL_RELEASE_CONTRACT missing={path}")
waitlist = contract["waitlist"]
if waitlist["success_status"] != 202 or waitlist["accepted_status"] != "received" or waitlist["public_list_endpoint"]:
    raise SystemExit("FAIL_RELEASE_CONTRACT unsafe waitlist contract")
account_portal = contract["account_portal"]
if (account_portal["status"] != "PUBLIC_CTA_RELEASE_VERIFIED_PENDING_USER_ACCEPTANCE"
        or account_portal["mode"] != "enabled"
        or account_portal["allowed_origins"] != ["https://app.dealalliancehub.com"]
        or account_portal["approved_origin"] != "https://app.dealalliancehub.com"
        or account_portal["register_url"] != "https://app.dealalliancehub.com/register"
        or account_portal["login_url"] != "https://app.dealalliancehub.com/login"
        or account_portal["register_url_status"] != "HTTPS_200_PRIVATE_STAGING_READBACK_PASS"
        or account_portal["login_url_status"] != "HTTPS_200_PRIVATE_STAGING_READBACK_PASS"
        or account_portal["public_entry_status"] != "PUBLIC_CTA_RELEASE_VERIFIED_NO_CREDENTIAL_FORMS"
        or account_portal["lifecycle_status"] != "STAGING_OAUTH_READBACK_PASS"):
    raise SystemExit("FAIL_RELEASE_CONTRACT unsafe account portal contract")
if account_portal["public_site_behavior"] != "safe_https_register_and_login_links_only_no_credentials_or_session":
    raise SystemExit("FAIL_RELEASE_CONTRACT account portal boundary is incomplete")
for key in ("http_status", "security_headers", "canonical_origin", "sitemap", "waitlist_readback", "account_portal_private_headers"):
    if key not in contract["monitoring"]["checks"]:
        raise SystemExit(f"FAIL_RELEASE_CONTRACT missing monitoring check={key}")
operational = contract.get("operational_readiness", {})
required_owner_inputs = {
    "legal_entity_name",
    "public_support_email",
    "privacy_contact",
    "privacy_policy_version_and_effective_date",
    "terms_version_and_effective_date",
    "service_region_and_governing_law",
    "first_public_resources_with_author_source_and_date",
}
if (operational.get("status") != "PENDING_OWNER_PUBLIC_LEGAL_AND_SUPPORT"
        or operational.get("release_ready") is not False
        or set(operational.get("missing_owner_inputs", [])) != required_owner_inputs
        or "not a formally operational service" not in operational.get("rule", "")):
    raise SystemExit("FAIL_RELEASE_CONTRACT operational readiness boundary is incomplete")
if not contract["rollback"]["artifact"] or not contract["rollback"]["trigger"]:
    raise SystemExit("FAIL_RELEASE_CONTRACT rollback is incomplete")
public_verified = contract["origin_status"] == "PUBLIC_HTTPS_READBACK_VERIFIED"
print(f"PASS_RELEASE_CONTRACT paths={len(contract['required_public_paths'])} monitoring={len(contract['monitoring']['checks'])} public_release_verified={str(public_verified).lower()} account_lifecycle=staging_pass cta=public_release_verified_pending_user_acceptance operational_release_ready=false owner_inputs_pending={len(required_owner_inputs)}")
