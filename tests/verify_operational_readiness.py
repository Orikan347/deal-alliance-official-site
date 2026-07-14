#!/usr/bin/env python3
"""Guard against calling a technically valid candidate a formal operating service."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
contract = json.loads((ROOT / "release_contract.json").read_text(encoding="utf-8"))
operational = contract.get("operational_readiness", {})
expected = [
    "legal_entity_name",
    "public_support_email",
    "privacy_contact",
    "privacy_policy_version_and_effective_date",
    "terms_version_and_effective_date",
    "service_region_and_governing_law",
    "first_public_resources_with_author_source_and_date",
]

if operational.get("status") != "PENDING_OWNER_PUBLIC_LEGAL_AND_SUPPORT":
    raise SystemExit("FAIL_OPERATIONAL_READINESS unknown status")
if operational.get("release_ready") is not False:
    raise SystemExit("FAIL_OPERATIONAL_READINESS must stay false until owner evidence is approved")
if operational.get("missing_owner_inputs") != expected:
    raise SystemExit("FAIL_OPERATIONAL_READINESS missing-input checklist drift")
if "not a formally operational service" not in operational.get("rule", ""):
    raise SystemExit("FAIL_OPERATIONAL_READINESS release boundary missing")

print(f"PASS_OPERATIONAL_READINESS_GUARD formal_operation=false owner_inputs_pending={len(expected)}")
