#!/usr/bin/env python3
"""Verify the candidate website-operations skill with de-identified change scenarios."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/orikan-website-product-operations-candidate/SKILL.md"
CARD = ROOT / "skills/orikan-website-product-operations-candidate/task-card.template.md"
FIXTURES = ROOT / "skills/orikan-website-product-operations-candidate/scenario-fixtures.json"
PROMOTION = ROOT / "skills/orikan-website-product-operations-candidate/promotion_manifest.json"


def require(text: str, tokens: list[str], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"{label} missing: {', '.join(missing)}")


def main() -> None:
    skill = SKILL.read_text(encoding="utf-8")
    card = CARD.read_text(encoding="utf-8")
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    promotion = json.loads(PROMOTION.read_text(encoding="utf-8"))

    if promotion["status"] != "APPROVED_FOR_HUB_PROMOTION":
        raise AssertionError("promotion manifest is not user-approved")
    if promotion["skill"] != "orikan-website-product-operations":
        raise AssertionError("promotion manifest points to the wrong skill")
    required_promotion_steps = {
        "copy_candidate_to_hub_master",
        "add_skill_catalog_entry",
        "add_routing_map_rule",
        "register_skill_contract",
        "create_or_sync_installed_copy",
        "run_drift_audit",
        "run_route_smoke",
        "run_deidentified_scenarios",
    }
    if set(promotion["promotion_steps"]) != required_promotion_steps:
        raise AssertionError("promotion manifest steps are incomplete")

    require(
        skill,
        [
            "### 第一輪：只做視覺好看，為什麼不夠",
            "### 第二輪：只做 SEO／GEO 清單，為什麼不夠",
            "### 第三輪：只靠一次交付，為什麼不夠",
            "### 第四輪：規則很完整，為什麼仍可能做不好",
            "## 第四輪落地：分級 Gate、頁面契約與設計判準",
            "### A. 變更分級",
            "### B. 每頁的不可省略「頁面契約」",
            "### C. 視覺不是「有質感」：三個可見判準",
            "### D. 量測與內容保鮮",
            "## 永久準則",
            "### 4. SEO／GEO Gate",
            "公開與私有分離",
            "無障礙也是 GEO",
            "## 外站研究轉化｜雷蒙30內容系統保留規則",
            "內容飛輪的固定路徑",
            "內容來源卡",
            "## 內容來源分層｜先確認「拿什麼資料說話」",
            "訪客產品文案與內部狀態分層",
            "DMG、簽章、staging、版本代號、工程測試結果",
            "找不到獨立來源的產品，一律不渲染成公開工具",
            "不處理網站以外的營運",
            "回滾",
            "不取代既有 Skill",
            "status: APPROVED_FOR_HUB_PROMOTION",
        ],
        "skill contract",
    )
    require(
        card,
        [
            "目標訪客與他現在的問題",
            "事實來源、owner、最後核對日",
            "去識別化假資料與 E2E 路徑",
            "變更等級",
            "頁面契約",
            "5 秒承諾",
            "NO_BASELINE",
            "回滾 artifact／版本",
            "本輪新規則",
        ],
        "task card",
    )

    cases = fixtures["cases"]
    if len(cases) != 6:
        raise AssertionError("fixture must contain six change scenarios")

    seen = set()
    for case in cases:
        case_id = case["id"]
        if case_id in seen:
            raise AssertionError(f"duplicate case: {case_id}")
        seen.add(case_id)
        if not case["required_lanes"]:
            raise AssertionError(f"{case_id}: required_lanes cannot be empty")
        if case.get("change_class") not in {"QUICK", "STANDARD", "HIGH_RISK"}:
            raise AssertionError(f"{case_id}: invalid change_class")
        if case["external_action"] and not case.get("requires_user_approval"):
            raise AssertionError(f"{case_id}: external action must require user approval")
        if case.get("offer_status") == "WAITLIST_ONLY":
            forbidden = set(case.get("forbidden_claims", []))
            if not {"download", "purchase", "free trial", "offer price"}.issubset(forbidden):
                raise AssertionError(f"{case_id}: waitlist boundary is incomplete")
        if case_id == "public-resource-article":
            expected = {"author", "published_or_updated_date", "source", "scope_or_limit"}
            if set(case.get("required_facts", [])) != expected:
                raise AssertionError(f"{case_id}: authority facts are incomplete")
        if case_id == "content-flywheel-resource-update":
            expected = {"source", "public_permission", "last_reviewed", "reader_problem"}
            if set(case.get("required_facts", [])) != expected:
                raise AssertionError(f"{case_id}: content source card is incomplete")
            forbidden = set(case.get("forbidden_claims", []))
            if not {"private content", "unverified claim", "automatic publishing"}.issubset(forbidden):
                raise AssertionError(f"{case_id}: content publishing boundary is incomplete")
        if case_id == "quick-layout-correction":
            forbidden = set(case.get("forbidden_claims", []))
            if case["change_class"] != "QUICK" or not {
                "cta destination change", "schema change", "data collection"
            }.issubset(forbidden):
                raise AssertionError(f"{case_id}: quick-change boundary is incomplete")

    print(
        "PASS_WEBSITE_PRODUCT_OPERATIONS_CANDIDATE "
        f"hub_promotion=approved critiques=4 raymond_transfer=retained scenarios={len(cases)} "
        "public_boundary=fail_closed seo_geo=people_first "
        "external_actions=approval_required"
    )


if __name__ == "__main__":
    main()
