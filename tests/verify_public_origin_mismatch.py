#!/usr/bin/env python3
"""GET-only parity gate for retired public routes.

Compare the current Cloudflare Pages deployment preview with the formal public origin.
This verifier deliberately has no cookie jar, authentication, request body,
or redirect follow.  A retired route must return the same 404 response on both
origins; otherwise a deployment must be treated as blocked rather than partly
released.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from html import unescape
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


PAGES_PREVIEW_ORIGIN = "https://a94e57a5.deal-alliance-official-site.pages.dev"
PUBLIC_ORIGIN = "https://www.dealalliancehub.com"
RETIRED_PATHS = ("/tools/life-number-calculator/",)
USER_AGENT = "DealAllianceOriginMismatchGate/1.0"


class NoRedirect(HTTPRedirectHandler):
    """Surface redirects as their real HTTP response instead of following them."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


@dataclass(frozen=True)
class Snapshot:
    status: int
    title: str
    content_fingerprint: str


def validate_origin(value: str, *, allow_http_fixtures: bool = False) -> str:
    """Accept an HTTPS base URL; a Pages deployment may include a repo path."""

    candidate = value.rstrip("/")
    parsed = urlsplit(candidate)
    is_loopback = parsed.hostname in {"127.0.0.1", "::1", "localhost"}
    allowed_scheme = parsed.scheme == "https" or (
        allow_http_fixtures and parsed.scheme == "http" and is_loopback
    )
    if (
        not allowed_scheme
        or not parsed.netloc
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise ValueError("origin must be an HTTPS base URL without credentials, query, or fragment")
    return candidate


def validate_path(value: str) -> str:
    parsed = urlsplit(value)
    if not value.startswith("/") or value.startswith("//") or parsed.scheme or parsed.netloc:
        raise ValueError(f"path must be origin-relative: {value!r}")
    if parsed.query or parsed.fragment:
        raise ValueError(f"path must not contain query or fragment: {value!r}")
    return value


def title_from(body: bytes) -> str:
    match = re.search(rb"<title\b[^>]*>(.*?)</title\s*>", body, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return re.sub(r"\s+", " ", unescape(match.group(1).decode("utf-8", "replace"))).strip()


def fetch_snapshot(origin: str, path: str, *, timeout: float) -> Snapshot:
    """Issue one explicit GET and return enough response state for parity checks."""

    request = Request(
        origin + path,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.1"},
        method="GET",
    )
    opener = build_opener(NoRedirect())
    try:
        response = opener.open(request, timeout=timeout)
        status = response.getcode()
        body = response.read()
    except HTTPError as error:
        status = error.code
        body = error.read()
    except (URLError, TimeoutError) as error:
        raise RuntimeError(f"GET failed: {error}") from error
    return Snapshot(
        status=status,
        title=title_from(body),
        content_fingerprint=hashlib.sha256(body).hexdigest(),
    )


def compare(path: str, preview: Snapshot, public: Snapshot) -> list[str]:
    failures: list[str] = []
    if preview.status != public.status:
        failures.append(
            f"check=http_status_mismatch preview={preview.status} public={public.status}"
        )
    if preview.status != 404 or public.status != 404:
        failures.append(
            f"check=retired_path_not_404 preview={preview.status} public={public.status}"
        )
    if preview.title != public.title:
        failures.append(
            f"check=title_mismatch preview={preview.title!r} public={public.title!r}"
        )
    if preview.content_fingerprint != public.content_fingerprint:
        failures.append(
            "check=content_fingerprint_mismatch "
            f"preview_sha256={preview.content_fingerprint} public_sha256={public.content_fingerprint}"
        )
    return [f"path={path} {failure}" for failure in failures]


def run(
    preview_origin: str,
    public_origin: str,
    paths: Iterable[str],
    *,
    timeout: float,
) -> list[str]:
    failures: list[str] = []
    for path in paths:
        preview = fetch_snapshot(preview_origin, path, timeout=timeout)
        public = fetch_snapshot(public_origin, path, timeout=timeout)
        failures.extend(compare(path, preview, public))
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preview-origin",
        default=PAGES_PREVIEW_ORIGIN,
        help="HTTPS Cloudflare Pages preview base URL; a deployment path is allowed",
    )
    parser.add_argument("--public-origin", default=PUBLIC_ORIGIN, help="HTTPS formal public base URL")
    parser.add_argument("--retired-path", action="append", dest="retired_paths")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument(
        "--allow-http-fixtures",
        action="store_true",
        help="test-only: allow HTTP only for localhost/loopback fixture origins",
    )
    args = parser.parse_args(argv)
    try:
        preview_origin = validate_origin(
            args.preview_origin, allow_http_fixtures=args.allow_http_fixtures
        )
        public_origin = validate_origin(
            args.public_origin, allow_http_fixtures=args.allow_http_fixtures
        )
        paths = tuple(validate_path(path) for path in (args.retired_paths or RETIRED_PATHS))
        if args.timeout <= 0:
            raise ValueError("timeout must be positive")
    except ValueError as error:
        print(f"BLOCKED_PUBLIC_ORIGIN_MISMATCH check=invalid_input detail={error}")
        return 2

    try:
        failures = run(preview_origin, public_origin, paths, timeout=args.timeout)
    except RuntimeError as error:
        print(f"BLOCKED_PUBLIC_ORIGIN_MISMATCH check=readonly_get_failed detail={error}")
        return 2

    if failures:
        for failure in failures:
            print(f"BLOCKED_PUBLIC_ORIGIN_MISMATCH {failure}")
        return 2

    print(
        "PASS_PUBLIC_ORIGIN_PARITY "
        f"preview={preview_origin} public={public_origin} retired_paths={len(paths)} "
        "method=GET cookies=none auth=none request_body=none"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
