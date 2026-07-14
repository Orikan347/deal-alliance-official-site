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
template = ROOT / "公開營運資料確認表_待Owner填寫.md"
required_template_sections = (
    "對外營運主體",
    "公開客服聯絡方式",
    "隱私聯絡窗口",
    "隱私政策版本與生效日",
    "使用條款版本與生效日",
    "服務地區與準據法偏好",
    "首批公開資源",
    "不要填帳密、token、客戶／學生資料、付款資料",
)
if not template.exists() or any(marker not in template.read_text(encoding="utf-8") for marker in required_template_sections):
    raise SystemExit("FAIL_OPERATIONAL_READINESS owner input template is missing or unsafe")

print(f"PASS_OPERATIONAL_READINESS_GUARD formal_operation=false owner_inputs_pending={len(expected)} template=ready")
