#!/usr/bin/env python3
"""Verify release, monitoring, and rollback requirements without external calls."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
contract = json.loads((ROOT / "release_contract.json").read_text(encoding="utf-8"))
if contract["status"] != "PENDING_EXTERNAL_RELEASE":
    raise SystemExit("FAIL_RELEASE_CONTRACT status must remain pending")
if contract["origin"] != "https://www.dealalliancehub.com":
    raise SystemExit("FAIL_RELEASE_CONTRACT origin must be the owner-confirmed formal origin")
if contract["origin_status"] != "OWNER_CONFIRMED_NOT_DEPLOYED":
    raise SystemExit("FAIL_RELEASE_CONTRACT origin status must remain not deployed")
workflow = contract["deployment_workflow"]
workflow_path = ROOT / workflow["path"]
if not workflow_path.exists() or workflow["trigger"] != "workflow_dispatch" or workflow["automatic_publish"]:
    raise SystemExit("FAIL_RELEASE_CONTRACT deployment must be manual and owner-approved")
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
for key in ("http_status", "security_headers", "canonical_origin", "sitemap", "waitlist_readback"):
    if key not in contract["monitoring"]["checks"]:
        raise SystemExit(f"FAIL_RELEASE_CONTRACT missing monitoring check={key}")
if not contract["rollback"]["artifact"] or not contract["rollback"]["trigger"]:
    raise SystemExit("FAIL_RELEASE_CONTRACT rollback is incomplete")
print(f"PASS_RELEASE_CONTRACT paths={len(contract['required_public_paths'])} monitoring={len(contract['monitoring']['checks'])} external_pending=true")
