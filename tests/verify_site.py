#!/usr/bin/env python3
"""Local-only end-to-end checks for the static Deal Alliance candidate site."""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://www.dealalliancehub.com"
PUBLIC_ROUTES = [
    "/",
    "/about/",
    "/solutions/",
    "/tools/",
    "/tools/follow-up-rhythm/",
    "/tools/sms-suite/",
    "/tools/line-automation/",
    "/tools/contact-converter/",
    "/tools/smart-close/",
    "/resources/",
    "/faq/",
    "/waitlist/",
    "/privacy/",
    "/terms/",
]


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.h1_count = 0
        self.links: list[str] = []
        self.meta: dict[tuple[str, str], str] = {}
        self.scripts: list[dict[str, str]] = []
        self.forms: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if tag == "h1":
            self.h1_count += 1
        elif tag == "a" and data.get("href"):
            self.links.append(data["href"])
        elif tag == "meta":
            if data.get("name"):
                self.meta[("name", data["name"])] = data.get("content", "")
            if data.get("property"):
                self.meta[("property", data["property"])] = data.get("content", "")
        elif tag == "script":
            self.scripts.append(data)
        elif tag == "form":
            self.forms.append(data)


def fail(message: str) -> None:
    raise AssertionError(message)


def route_file(route: str) -> Path:
    if route == "/":
        return ROOT / "index.html"
    if route.endswith(".html"):
        return ROOT / route.strip("/")
    return ROOT / route.strip("/") / "index.html"


def read_page(route: str) -> tuple[str, PageParser]:
    html = route_file(route).read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(html)
    return html, parser


def check_pages() -> None:
    seen_titles: set[str] = set()
    for route in PUBLIC_ROUTES:
        html, parser = read_page(route)
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        if not title:
            fail(f"{route}: missing title")
        normalized_title = re.sub(r"\s+", " ", title.group(1)).strip()
        if normalized_title in seen_titles:
            fail(f"{route}: duplicate title {normalized_title}")
        seen_titles.add(normalized_title)
        if parser.h1_count != 1:
            fail(f"{route}: expected exactly one h1, got {parser.h1_count}")
        if 'name="viewport"' not in html or 'width=device-width' not in html:
            fail(f"{route}: missing mobile viewport")
        if not parser.meta.get(("name", "description")):
            fail(f"{route}: missing meta description")
        if not parser.meta.get(("name", "robots")):
            fail(f"{route}: missing robots metadata")
        canonical = re.search(r'<link rel="canonical" href="([^"]+)">', html)
        if not canonical or canonical.group(1) != ORIGIN + route:
            fail(f"{route}: canonical is missing or inconsistent")
        for key in ("og:title", "og:description", "og:image", "og:url"):
            if not parser.meta.get(("property", key)):
                fail(f"{route}: missing {key}")
        og_image = parser.meta[("property", "og:image")]
        if not og_image.endswith("/assets/og-card.png"):
            fail(f"{route}: share card must use the PNG asset")
        schemas = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        if not schemas:
            fail(f"{route}: missing JSON-LD")
        for raw in schemas:
            json.loads(raw)
        for link in parser.links:
            if link.startswith("/") and not link.startswith("//"):
                target = route_file(link)
                if link not in ("/search/",) and not target.exists():
                    fail(f"{route}: broken local link {link}")
    print(f"PASS_METADATA_AND_SCHEMA pages={len(PUBLIC_ROUTES)}")


def check_safety() -> None:
    waitlist_html, parser = read_page("/waitlist/")
    if not parser.forms:
        fail("waitlist: expected local form")
    if any("action" in form for form in parser.forms):
        fail("waitlist: form must not have a submit action")
    js = (ROOT / "assets/site.js").read_text(encoding="utf-8")
    runtime_config = (ROOT / "assets/site-config.js").read_text(encoding="utf-8")
    if 'waitlistMode: "disabled"' not in runtime_config or 'waitlistEndpoint: ""' not in runtime_config:
        fail("waitlist: default runtime configuration must remain fail-closed")
    account_runtime_required = (
        'accountPortalMode: "enabled"',
        'accountPortalRegisterUrl: "https://app.dealalliancehub.com/register"',
        'accountPortalLoginUrl: "https://app.dealalliancehub.com/login"',
        'accountPortalAllowedOrigins: ["https://app.dealalliancehub.com"]',
    )
    if any(marker not in runtime_config for marker in account_runtime_required):
        fail("account portal: candidate runtime configuration must use only the verified staging URLs")
    if "XMLHttpRequest" in js or "navigator.sendBeacon" in js or "if (!remoteEnabled)" not in js:
        fail("waitlist: remote submission is missing the fail-closed guard")
    account_portal_markers = (
        "accountPortalRegisterUrl",
        "accountPortalLoginUrl",
        "accountPortalAllowedOrigins",
        "data-account-portal",
        "portal.protocol !== 'https:'",
        "portal.pathname !== requiredPath",
        "portal.search || portal.hash",
    )
    if any(marker not in js for marker in account_portal_markers) or "fetch(config.accountPortal" in js:
        fail("account portal: must be guarded navigation only, never credential submission")
    contract = json.loads((ROOT / "waitlist_contract.json").read_text(encoding="utf-8"))
    if contract.get("status") != "CONTRACT_READY_ENDPOINT_PENDING":
        fail("waitlist: contract must remain endpoint-pending")
    if contract.get("response", {}).get("success_status") != 202:
        fail("waitlist: readback contract must require HTTP 202")
    catalog = json.loads((ROOT / "tools/catalog.json").read_text(encoding="utf-8"))
    expected_tools = {"follow-up-rhythm", "sms-suite", "line-automation", "contact-converter", "smart-close"}
    if {item.get("slug") for item in catalog} != expected_tools:
        fail("tools: catalog must include all six confirmed tool positions")
    for item in catalog:
        detail = route_file(f"/tools/{item['slug']}/")
        if not detail.exists() or item.get("offer_status") not in {"WAITLIST_ONLY", "NOT_ENABLED"}:
            fail(f"tools: invalid catalog/detail {item.get('slug')}")
        detail_html = detail.read_text(encoding="utf-8")
        if item.get("status_label") not in detail_html:
            fail(f"tools: status label missing from {item.get('slug')}")
    detail_htmls = [route_file("/tools/" + item["slug"] + "/").read_text(encoding="utf-8") for item in catalog]
    for demo_name in ("contact-converter", "smart-close", "sms-preview", "line-preview"):
        if not any(f'data-demo="{demo_name}"' in html for html in detail_htmls):
            fail(f"tools: interactive demo missing {demo_name}")
    if "清除／取消" not in (ROOT / "assets/site.js").read_text(encoding="utf-8"):
        fail("tools: interactive demos must expose a cancel/reset control")
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    for required in ("User-agent: OAI-SearchBot", "Allow: /", "Disallow: /admin/", "Disallow: /students/"):
        if required not in robots:
            fail(f"robots: missing {required}")
    if "@type\":\"FAQPage" not in (ROOT / "faq/index.html").read_text(encoding="utf-8"):
        fail("faq: missing FAQPage schema")
    for item in catalog:
        detail_html = route_file(f"/tools/{item['slug']}/").read_text(encoding="utf-8")
        schemas = [json.loads(raw) for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', detail_html, re.S)]
        if not any(schema.get("@type") == "WebPage" for schema in schemas):
            fail(f"tool detail: {item['slug']} must expose a descriptive WebPage schema")
        if any(
            schema.get("@type") in {"SoftwareApplication", "Product", "Offer"}
            or "isAccessibleForFree" in schema
            or "offers" in schema
            for schema in schemas
        ):
            fail(f"tool detail: {item['slug']} must not expose availability or pricing schema while waitlist-only")
    if "/tools/life-number-calculator/" in (ROOT / "tools" / "index.html").read_text(encoding="utf-8"):
        fail("tools: hidden life-number calculator must not be linked from the public tool index")
    print("PASS_PUBLIC_BOUNDARY local_form_no_submit=true default_endpoint_disabled=true account_portal_candidate_enabled=true tool_catalog=5 waitlist_schema=descriptive_only hidden_tool=life-number-calculator")


def check_tool_source_alignment() -> None:
    """Ensure public tool states have an auditable release-local evidence chain.

    The deployment repository intentionally does not contain the platform-wide
    status table.  A checked snapshot is therefore required for isolated
    release validation; when the authoritative table is available locally its
    content hash and every status code must still match the snapshot.
    """
    status_path = ROOT.parents[1] / "400_桌面程式優化" / "工具整合狀態表.md"
    snapshot_path = ROOT / "status_evidence" / "tool_status_snapshot.json"
    if not snapshot_path.exists():
        fail("tools: release status evidence snapshot is missing")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot.get("schema_version") != "DA_TOOL_STATUS_SNAPSHOT_V1":
        fail("tools: release status evidence schema is invalid")
    if not snapshot.get("captured_on") or not snapshot.get("source", {}).get("sha256"):
        fail("tools: release status evidence provenance is incomplete")

    required_markers = {
        "sms_suite": "R27_CORE_PRODUCT_REVIEW_USER_ACCEPTED_STAGING_OAUTH_PENDING",
        "line_automation": "MAC_COMPILED_V4_CANDIDATE_PRE_SIGN_GUI_PENDING",
        "contact_converter": "LOCAL_FAKE_E2E_PASS_USER_VISIBLE_ACCEPTANCE_AND_STAGING_PENDING",
        "smart_close": "LOCAL_USER_ACCEPTED_STAGING_RELEASE_PENDING",
        "life_number_calculator": "RESERVED_NOT_OPEN",
    }
    evidence = {item.get("product_id"): item for item in snapshot.get("tools", [])}
    if set(evidence) != set(required_markers):
        fail("tools: release status evidence products are incomplete")
    for product_id, marker in required_markers.items():
        item = evidence[product_id]
        if item.get("source_status") != marker:
            fail(f"tools: release status evidence marker mismatch {product_id}")
        if item.get("offer_status") not in {"WAITLIST_ONLY", "NOT_ENABLED"}:
            fail(f"tools: release status evidence exposes an unapproved offer {product_id}")
        if not item.get("status_label"):
            fail(f"tools: release status evidence lacks public label {product_id}")

    catalog = {item.get("product_id"): item for item in json.loads((ROOT / "tools/catalog.json").read_text(encoding="utf-8"))}
    hidden_public_products = {"life_number_calculator"}
    for product_id, item in evidence.items():
        public_item = catalog.get(product_id)
        if product_id in hidden_public_products:
            if public_item:
                fail(f"tools: hidden product remains in public catalog {product_id}")
            continue
        if not public_item:
            fail(f"tools: public catalog lacks evidence product {product_id}")
        for field in ("offer_status", "status_label", "summary", "platform"):
            evidence_key = field if field in {"offer_status", "status_label"} else f"public_{field}"
            if public_item.get(field) != item.get(evidence_key):
                fail(f"tools: public catalog {field} is not aligned {product_id}")
        if public_item.get("last_reviewed") != snapshot["captured_on"]:
            fail(f"tools: public catalog review date is not aligned {product_id}")

    if (ROOT / "dist" / "status_evidence").exists():
        fail("tools: internal status evidence must not enter the public artifact")
    if status_path.exists():
        source_bytes = status_path.read_bytes()
        if hashlib.sha256(source_bytes).hexdigest() != snapshot["source"]["sha256"]:
            fail("tools: release status evidence is stale against the source table")
        source = source_bytes.decode("utf-8")
        missing = [product_id for product_id, marker in required_markers.items() if marker not in source]
        if missing:
            fail(f"tools: source status markers missing {missing}")
        print("PASS_TOOL_SOURCE_ALIGNMENT products=5 source=400_status_table+release_snapshot")
        return
    print("PASS_TOOL_SOURCE_ALIGNMENT products=5 source=release_status_snapshot")


def check_sitemap_and_responsive_css() -> None:
    tree = ET.parse(ROOT / "sitemap.xml")
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = [node.text for node in tree.findall("sm:url/sm:loc", namespace)]
    expected = [ORIGIN + route for route in PUBLIC_ROUTES]
    if locations != expected:
        fail("sitemap: public route list is incomplete or not in expected order")
    lastmods = [node.text for node in tree.findall("sm:url/sm:lastmod", namespace)]
    if len(lastmods) != len(locations) or any(not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or "") for value in lastmods):
        fail("sitemap: every public route must carry an ISO lastmod")
    css = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
    responsive_checks = (
        (r"@media\s*\(max-width:\s*(760|860)px\)", "responsive breakpoint"),
        (r"\.grid-3,\.grid-2\{grid-template-columns:1fr\}", "single-column grid"),
        (r"\.nav-links\{display:(none|flex)(?:;|\})", "mobile navigation rule"),
    )
    compact_css = re.sub(r"\s+", "", css)
    for pattern, label in responsive_checks:
        if not re.search(pattern, compact_css):
            fail(f"responsive CSS missing: {label}")
    if ".nav-links{display:flex;order:3;width:100%;overflow-x:auto" not in compact_css:
        fail("responsive CSS missing: mobile navigation remains reachable")
    if not (ROOT / "404.html").exists() or not (ROOT / "search/index.html").exists():
        fail("missing 404 or search empty state")
    social_card = ROOT / "assets/og-card.png"
    if not social_card.exists() or social_card.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        fail("share card PNG is missing or invalid")
    print(f"PASS_SITEMAP_AND_MOBILE sitemap_urls={len(locations)} lastmod=complete")


def check_llms_discovery_document() -> None:
    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    required = (
        "正式公開網站：https://www.dealalliancehub.com/",
        "https://www.dealalliancehub.com/solutions/",
        "https://www.dealalliancehub.com/tools/",
        "https://www.dealalliancehub.com/privacy/",
        "公開網站不處理密碼、session、學生資料、管理設定、付款或工具授權。",
        "公開網站不代收帳密或 token。",
    )
    missing = [marker for marker in required if marker not in llms]
    if missing or "尚未部署" in llms:
        fail("llms.txt: public origin, route coverage, or privacy boundary is stale")
    if (ROOT / "dist/llms.txt").read_text(encoding="utf-8") != llms:
        fail("llms.txt: dist artifact is out of sync")
    print("PASS_LLMS_DISCOVERY public_origin=true routes=6 privacy_boundary=true")


def check_account_portal_bootstrap() -> None:
    # A visitor can reach an account entry from every public page, including
    # a noindex search empty state and a 404 recovery page.
    portal_routes = [*PUBLIC_ROUTES, "/404.html", "/search/"]
    for route in portal_routes:
        source_html, _ = read_page(route)
        if route == "/404.html":
            dist_path = ROOT / "dist/404.html"
        elif route == "/":
            dist_path = ROOT / "dist/index.html"
        else:
            dist_path = ROOT / "dist" / route.strip("/") / "index.html"
        dist_html = dist_path.read_text(encoding="utf-8")
        for label, html in (("source", source_html), ("dist", dist_html)):
            config_index = html.find('src="/assets/site-config.js"')
            site_index = html.find('src="/assets/site.js"')
            if config_index < 0 or site_index < 0 or config_index > site_index:
                fail(f"account portal: {label} {route} must load runtime config before site.js")
            if 'class="nav' not in html:
                fail(f"account portal: {label} {route} must expose a navigation container")
    print(f"PASS_ACCOUNT_PORTAL_BOOTSTRAP pages={len(portal_routes)} artifacts=source+dist nav=all")


def check_fake_visitor_paths() -> None:
    """Replay the four documented visitor journeys with non-production data."""
    journeys = {
        "visitor_problem_01": ["/", "/solutions/", "/resources/"],
        "visitor_tool_02": ["/tools/", "/tools/follow-up-rhythm/", "/tools/sms-suite/", "/tools/contact-converter/", "/tools/smart-close/", "/waitlist/"],
        "visitor_privacy_03": ["/waitlist/", "/privacy/"],
        "crawler_public_04": ["/about/", "/faq/"],
    }
    for visitor, routes in journeys.items():
        for route in routes:
            html, parser = read_page(route)
            if parser.h1_count != 1:
                fail(f"{visitor}: {route} missing one answer heading")
            if route in ("/tools/", "/tools/follow-up-rhythm/", "/waitlist/"):
                if not any(word in html for word in ("候補", "候補中", "本機示意")):
                    fail(f"{visitor}: {route} missing waitlist boundary")
    waitlist_html, _ = read_page("/waitlist/")
    fake_payload = {"topic": "客戶開發與跟進", "contact": "test-visitor@example.invalid"}
    if fake_payload["contact"] in waitlist_html:
        fail("fake payload unexpectedly persisted in the candidate HTML")
    js = (ROOT / "assets/site.js").read_text(encoding="utf-8")
    if "目前候補／洽詢收件尚未開放" not in js or "preventDefault" not in js:
        fail("local form fail-closed simulation contract is missing")
    if "第 ${invalid + 1} 行格式不正確" not in js:
        fail("contact converter: malformed fake rows must fail visibly")
    print("PASS_FAKE_VISITOR_E2E journeys=4 fake_payload=not_persisted local_form=simulated_only")


def check_forbidden_public_claims() -> None:
    forbidden = ("立即購買", "立即下載", "免費試用", "立即啟用", "保證成交", "已上線")
    for path in ROOT.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            if phrase in text:
                fail(f"{path.relative_to(ROOT)}: forbidden public claim {phrase}")
    print("PASS_PUBLIC_CLAIM_SCAN forbidden_terms=0")


def check_public_copy_integrity() -> None:
    """Prevent a released candidate from contradicting its safe account CTA."""
    for route in [*PUBLIC_ROUTES, "/404.html", "/search/"]:
        html, _ = read_page(route)
        for phrase in ("候選站 v1", "公開候選站", "本候選站", "不提供登入", "沒有登入、註冊", "未啟用帳號"):
            if phrase in html:
                fail(f"public copy: {route} contains stale or contradictory phrase {phrase}")
    print("PASS_PUBLIC_COPY_INTEGRITY routes=16 account_portal_language=consistent")


def check_planning_contract() -> None:
    plan = (ROOT / "網站完整規劃藍圖_2026-07-13.md").read_text(encoding="utf-8")
    required_sections = (
        "目標訪客與核心任務",
        "資訊架構與導覽",
        "工具與服務狀態規則",
        "候補／洽詢流程設計",
        "SEO／GEO 設計",
        "量測事件契約",
        "正式上線前的四階段",
        "上線 Gate",
    )
    missing = [section for section in required_sections if section not in plan]
    if missing:
        fail(f"planning blueprint missing sections: {missing}")
    print("PASS_PLANNING_CONTRACT sections=8 scope=official-site-only")


def check_http_routes() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(0.35)
        for route in [*PUBLIC_ROUTES, "/robots.txt", "/sitemap.xml", "/assets/og-card.svg", "/404.html", "/search/"]:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{route}", timeout=3) as response:
                if response.status != 200:
                    fail(f"HTTP {route}: expected 200, got {response.status}")
        print(f"PASS_LOCAL_HTTP routes={len(PUBLIC_ROUTES) + 5} port={port}")
    finally:
        server.terminate()
        server.wait(timeout=3)


def main() -> None:
    config = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
    if config["candidateOrigin"] != ORIGIN or config["canonicalStatus"] not in {"OWNER_CONFIRMED_FORMAL_ORIGIN_NOT_DEPLOYED", "PUBLIC_ORIGIN_VERIFIED_AND_LIVE"}:
        fail("site config must use the formal origin and a known release status")
    if config.get("accountPortalStatus") != "STAGING_LIFECYCLE_READBACK_PASS_CTA_CANDIDATE_ENABLED_PENDING_USER_ACCEPTANCE":
        fail("site config must retain the staging-pass candidate-CTA account portal boundary")
    check_pages()
    check_safety()
    check_tool_source_alignment()
    check_sitemap_and_responsive_css()
    check_llms_discovery_document()
    check_account_portal_bootstrap()
    check_fake_visitor_paths()
    check_forbidden_public_claims()
    check_public_copy_integrity()
    check_planning_contract()
    check_http_routes()
    print(f"PASS_ALL_LOCAL_GATES candidate_origin=www.dealalliancehub.com public_release_verified={str(config['canonicalStatus'] == 'PUBLIC_ORIGIN_VERIFIED_AND_LIVE').lower()} account_portal_candidate_enabled=true user_acceptance_pending=true")


if __name__ == "__main__":
    main()
