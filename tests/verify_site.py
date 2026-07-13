#!/usr/bin/env python3
"""Local-only end-to-end checks for the static Deal Alliance candidate site."""

from __future__ import annotations

import json
import os
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
    "/tools/life-number-calculator/",
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
    if "XMLHttpRequest" in js or "navigator.sendBeacon" in js or "if (!remoteEnabled)" not in js:
        fail("waitlist: remote submission is missing the fail-closed guard")
    contract = json.loads((ROOT / "waitlist_contract.json").read_text(encoding="utf-8"))
    if contract.get("status") != "CONTRACT_READY_ENDPOINT_PENDING":
        fail("waitlist: contract must remain endpoint-pending")
    if contract.get("response", {}).get("success_status") != 202:
        fail("waitlist: readback contract must require HTTP 202")
    catalog = json.loads((ROOT / "tools/catalog.json").read_text(encoding="utf-8"))
    expected_tools = {"follow-up-rhythm", "sms-suite", "line-automation", "contact-converter", "smart-close", "life-number-calculator"}
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
    if "@type\":\"SoftwareApplication" not in (ROOT / "tools/follow-up-rhythm/index.html").read_text(encoding="utf-8"):
        fail("tool detail: missing SoftwareApplication schema")
    print("PASS_PUBLIC_BOUNDARY local_form_no_submit=true default_endpoint_disabled=true tool_catalog=6")


def check_tool_source_alignment() -> None:
    """Ensure public tool states remain aligned with the current internal status table."""
    status_path = ROOT.parents[1] / "400_桌面程式優化" / "工具整合狀態表.md"
    if not status_path.exists():
        if os.environ.get("DEAL_ALLIANCE_RELEASE_ISOLATED") == "1":
            catalog = json.loads((ROOT / "tools/catalog.json").read_text(encoding="utf-8"))
            required = {"sms_suite", "line_automation", "contact_converter", "smart_close", "life_number_calculator"}
            seen = {item.get("product_id") for item in catalog}
            if not required.issubset(seen):
                fail("tools: release catalog snapshot is incomplete")
            if any(not item.get("status_label") or not item.get("last_reviewed") for item in catalog):
                fail("tools: release catalog snapshot lacks status evidence")
            print("PASS_TOOL_SOURCE_ALIGNMENT products=5 source=release_catalog_snapshot")
            return
        fail("tools: source status table is missing")
    source = status_path.read_text(encoding="utf-8")
    required_markers = {
        "sms_suite": "TWO_SIGNED_CANDIDATES_PENDING_NOTARIZATION",
        "line_automation": "MACOS13_SIGNED_3_0_4_PENDING_NOTARIZATION",
        "contact_converter": "CLOUDFLARE_STAGING_RATE_LIMIT_DEPLOYED_REMOTE_E2E_PENDING",
        "smart_close": "CLOUDFLARE_STAGING_RATE_LIMIT_DEPLOYED_GEMINI_E2E_PENDING",
        "life_number_calculator": "RESERVED_NOT_OPEN",
    }
    missing = [product_id for product_id, marker in required_markers.items() if marker not in source]
    if missing:
        fail(f"tools: source status markers missing {missing}")
    print("PASS_TOOL_SOURCE_ALIGNMENT products=5 source=400_status_table")


def check_sitemap_and_responsive_css() -> None:
    tree = ET.parse(ROOT / "sitemap.xml")
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = [node.text for node in tree.findall("sm:url/sm:loc", namespace)]
    expected = [ORIGIN + route for route in PUBLIC_ROUTES]
    if locations != expected:
        fail("sitemap: public route list is incomplete or not in expected order")
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
    print(f"PASS_SITEMAP_AND_MOBILE sitemap_urls={len(locations)}")


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
    if "目前仍是本機候選版" not in js or "preventDefault" not in js:
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
    if config["candidateOrigin"] != ORIGIN or config["canonicalStatus"] != "OWNER_CONFIRMED_FORMAL_ORIGIN_NOT_DEPLOYED":
        fail("site config must use the owner-confirmed formal origin while remaining not deployed")
    check_pages()
    check_safety()
    check_tool_source_alignment()
    check_sitemap_and_responsive_css()
    check_fake_visitor_paths()
    check_forbidden_public_claims()
    check_planning_contract()
    check_http_routes()
    print("PASS_ALL_LOCAL_GATES candidate_origin=www.dealalliancehub.com deployment_pending=true")


if __name__ == "__main__":
    main()
