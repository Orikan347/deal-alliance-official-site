#!/usr/bin/env python3
"""GET-only Gate for the public account entry pages.

The public official site never collects credentials.  The dedicated app
origin is the sole place where a visitor may see the reviewed registration
or login form.  This check only reads those pages: it never submits a form,
sends email, or invokes lifecycle routes.
"""

from __future__ import annotations

import argparse
import ipaddress
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse


ORIGIN = "https://app.dealalliancehub.com"
PATHS = ("/register", "/login")


def fail(message: str) -> None:
    print(f"FAIL_ACCOUNT_PORTAL_PUBLIC {message}")
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", default=ORIGIN)
    parser.add_argument("--resolve-ip", default="", help="Optional public IPv4 for SNI-only DNS-cache bypass")
    args = parser.parse_args()
    origin = args.origin.rstrip("/")
    parsed = urlparse(origin)
    if origin != ORIGIN or parsed.scheme != "https" or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
        fail("origin_must_be_exact_bare_https_app_origin")
    if args.resolve_ip:
        try:
            address = ipaddress.ip_address(args.resolve_ip)
        except ValueError:
            fail("resolve_ip_invalid")
        if address.version != 4 or address.is_private or address.is_loopback or address.is_reserved or address.is_multicast:
            fail("resolve_ip_must_be_public_ipv4")

    curl = shutil.which("curl") or "/usr/bin/curl"
    if not Path(curl).exists():
        fail("curl_missing")
    for route in PATHS:
        with tempfile.TemporaryDirectory(prefix="deal-alliance-account-page-") as temporary_dir:
            headers = Path(temporary_dir) / "headers.txt"
            body = Path(temporary_dir) / "body.html"
            command = [curl, "--silent", "--show-error", "--max-time", "20", "--dump-header", str(headers), "--output", str(body), "--write-out", "%{http_code}", origin + route]
            if args.resolve_ip:
                command[1:1] = ["--resolve", f"app.dealalliancehub.com:443:{args.resolve_ip}"]
            result = subprocess.run(command, check=False, capture_output=True, text=True)
            if result.returncode != 0:
                fail(f"route={route} fetch_failed={result.stderr.strip()}")
            if result.stdout.strip() != "200":
                fail(f"route={route} status={result.stdout.strip()!r}")
            header_text = headers.read_text(encoding="utf-8", errors="replace").lower()
            for marker in ("cache-control: no-store", "x-robots-tag: noindex", "referrer-policy: no-referrer", "x-content-type-options: nosniff"):
                if marker not in header_text:
                    fail(f"route={route} missing_header={marker}")
            html = body.read_text(encoding="utf-8", errors="replace").lower()
            expected_api = "/api/auth/register" if route == "/register" else "/api/auth/login"
            if "<form" not in html or "type=\"email\"" not in html or "type=\"password\"" not in html:
                fail(f"route={route} reviewed_credential_form_missing")
            if expected_api not in html:
                fail(f"route={route} expected_same_origin_api_missing")
            if "http://" in html or "action=\"http" in html or "action='http" in html:
                fail(f"route={route} unsafe_credential_destination")
    resolver = "explicit_sni_dns_pin" if args.resolve_ip else "system_dns"
    print(f"PASS_ACCOUNT_PORTAL_PUBLIC origin={origin} paths=2 private_headers=ok credential_forms=app_only_same_origin resolver={resolver}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
