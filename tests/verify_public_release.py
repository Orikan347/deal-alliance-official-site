#!/usr/bin/env python3
"""Read-only public release Gate for the official-site candidate.

This script performs GET requests only. It never submits the waitlist form and
never reads private/operator endpoints. Run it only after the public host is
authorized and deployed.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener


FORMAL_ORIGIN = "https://www.dealalliancehub.com"
ROOT_ORIGIN = "https://dealalliancehub.com"
PUBLIC_PATHS = [
    "/", "/about/", "/solutions/", "/tools/",
    "/tools/follow-up-rhythm/", "/tools/sms-suite/",
    "/tools/line-automation/", "/tools/contact-converter/",
    "/tools/smart-close/", "/tools/life-number-calculator/",
    "/resources/", "/faq/", "/waitlist/", "/privacy/", "/terms/",
    "/404.html", "/robots.txt", "/sitemap.xml", "/llms.txt",
]
REQUIRED_HEADERS = ("content-security-policy", "x-content-type-options", "referrer-policy")
PUBLIC_DOH_URL = "https://cloudflare-dns.com/dns-query"
RESOLVER_MODES: set[str] = set()


class MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.canonical = ""
        self.og_url = ""
        self.json_ld: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href", "")
        if tag == "meta" and values.get("property") == "og:url":
            self.og_url = values.get("content", "")
        if tag == "script" and values.get("type") == "application/ld+json":
            self._collecting_json_ld = True

    def handle_data(self, data: str) -> None:
        if getattr(self, "_collecting_json_ld", False):
            self.json_ld.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._collecting_json_ld = False


class CurlResponse:
    """Minimal response adapter for the public DNS-over-HTTPS fallback."""

    def __init__(self, status: int, headers: dict[str, str], body: bytes, final_url: str) -> None:
        self.status = status
        self.headers = headers
        self._body = body
        self._final_url = final_url

    def read(self) -> bytes:
        return self._body

    def geturl(self) -> str:
        return self._final_url


def get_via_public_doh(url: str) -> CurlResponse:
    """Fetch through a public resolver when the local machine resolver is stale.

    This remains read-only: curl performs a GET only, follows normal HTTPS
    redirects, and never posts to the waitlist or any operator endpoint.
    """
    with tempfile.TemporaryDirectory(prefix="deal-alliance-release-gate-") as temporary_dir:
        headers_path = f"{temporary_dir}/headers.txt"
        body_path = f"{temporary_dir}/body.bin"
        result = subprocess.run(
            [
                "curl", "--doh-url", PUBLIC_DOH_URL, "--location", "--silent", "--show-error",
                "--max-time", "20", "--dump-header", headers_path, "--output", body_path,
                "--write-out", "%{http_code}\\n%{url_effective}", url,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise URLError(f"public_doh_fetch_failed={result.stderr.strip()}")
        output = result.stdout.splitlines()
        if len(output) < 2 or not output[0].isdigit():
            raise URLError("public_doh_fetch_missing_status")
        raw_headers = open(headers_path, "r", encoding="utf-8", errors="replace").read()
        header_blocks = [block for block in re.split(r"\\r?\\n\\r?\\n", raw_headers) if block.strip()]
        final_block = next((block for block in reversed(header_blocks) if block.startswith("HTTP/")), "")
        headers: dict[str, str] = {}
        for line in final_block.splitlines()[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.lower()] = value.strip()
        body = open(body_path, "rb").read()
    RESOLVER_MODES.add("public_doh")
    return CurlResponse(int(output[0]), headers, body, output[1])


def get(opener, url: str):
    request = Request(url, headers={"User-Agent": "DealAllianceReleaseGate/1.0"})
    try:
        response = opener.open(request, timeout=15)
    except URLError:
        return get_via_public_doh(url)
    RESOLVER_MODES.add("system_dns")
    return response


def fail(message: str) -> None:
    print(f"FAIL_PUBLIC_RELEASE {message}")
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", default=FORMAL_ORIGIN)
    args = parser.parse_args()
    origin = args.origin.rstrip("/")
    if not origin.startswith("https://"):
        fail("origin_must_be_https")

    opener = build_opener()
    try:
        root_response = get(opener, ROOT_ORIGIN + "/")
    except (HTTPError, URLError, TimeoutError) as error:
        fail(f"root_unreachable={error}")
    root_final = root_response.geturl().rstrip("/")
    if root_final != FORMAL_ORIGIN:
        fail(f"root_redirect_final={root_final}")
    if root_response.status not in (200, 301, 302, 307, 308):
        fail(f"root_status={root_response.status}")

    checked = 0
    for path in PUBLIC_PATHS:
        url = origin + path
        try:
            response = get(opener, url)
            body = response.read().decode("utf-8", "replace")
        except (HTTPError, URLError, TimeoutError) as error:
            fail(f"path={path} unreachable={error}")
        if response.status != 200:
            fail(f"path={path} status={response.status}")
        checked += 1
        if path.endswith("/") and path not in ("/robots.txt", "/sitemap.xml", "/llms.txt"):
            for header in REQUIRED_HEADERS:
                if not response.headers.get(header):
                    fail(f"path={path} missing_header={header}")
            parser_state = MetaParser()
            parser_state.feed(body)
            expected = origin + path
            if parser_state.canonical != expected:
                fail(f"path={path} canonical={parser_state.canonical!r}")
            if parser_state.og_url != expected:
                fail(f"path={path} og_url={parser_state.og_url!r}")
            try:
                json_ld = [json.loads(item) for item in parser_state.json_ld if item.strip()]
            except json.JSONDecodeError:
                fail(f"path={path} invalid_json_ld")
            if not json_ld:
                fail(f"path={path} missing_json_ld")
            if "official-domain-pending.invalid" in body:
                fail(f"path={path} placeholder_origin_present")

    sitemap_url = origin + "/sitemap.xml"
    try:
        sitemap = get(opener, sitemap_url).read().decode("utf-8", "replace")
    except (HTTPError, URLError, TimeoutError) as error:
        fail(f"sitemap_unreachable={error}")
    if origin not in sitemap or sitemap.count("<loc>") != 15:
        fail("sitemap_origin_or_count_mismatch")

    resolver = "+".join(sorted(RESOLVER_MODES))
    print(f"PASS_PUBLIC_RELEASE origin={origin} paths={checked} root_redirect=www crawler_assets=ok waitlist_post=not_performed resolver={resolver}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
