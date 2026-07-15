#!/usr/bin/env python3
"""Loopback fixture E2E tests for verify_public_origin_mismatch.py."""

from __future__ import annotations

import subprocess
import sys
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest import mock


VERIFIER = Path(__file__).with_name("verify_public_origin_mismatch.py")
CURRENT_CLOUDFLARE_PAGES_PREVIEW = "https://a94e57a5.deal-alliance-official-site.pages.dev"


def load_verifier_module():
    spec = spec_from_file_location("verify_public_origin_mismatch_under_test", VERIFIER)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load verifier module")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VERIFIER_MODULE = load_verifier_module()


class FixtureHandler(BaseHTTPRequestHandler):
    status = 404
    body = b"<html><title>Retired route</title><body>not found</body></html>"
    methods: list[str] = []

    def do_GET(self) -> None:  # noqa: N802 - HTTP handler API
        type(self).methods.append("GET")
        self.send_response(type(self).status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(type(self).body)

    def log_message(self, format: str, *args: object) -> None:
        return


@contextmanager
def fixture(status: int, body: bytes):
    handler = type("ConfiguredFixtureHandler", (FixtureHandler,), {"status": status, "body": body, "methods": []})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", handler
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def run_gate(preview: str, public: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VERIFIER),
            "--preview-origin",
            preview,
            "--public-origin",
            public,
            "--allow-http-fixtures",
            "--timeout",
            "2",
        ],
        check=False,
        capture_output=True,
        text=True,
    )


class OriginMismatchE2ETest(unittest.TestCase):
    def test_cli_default_uses_current_cloudflare_pages_preview(self) -> None:
        with mock.patch.object(VERIFIER_MODULE, "run", return_value=[]) as run:
            self.assertEqual(VERIFIER_MODULE.main([]), 0)
        self.assertEqual(VERIFIER_MODULE.PAGES_PREVIEW_ORIGIN, CURRENT_CLOUDFLARE_PAGES_PREVIEW)
        self.assertEqual(run.call_args.args[0], CURRENT_CLOUDFLARE_PAGES_PREVIEW)

    def test_matching_retired_responses_pass_with_get_only(self) -> None:
        body = b"<html><title>Retired route</title><body>not found</body></html>"
        with fixture(404, body) as (preview, preview_handler), fixture(404, body) as (public, public_handler):
            result = run_gate(preview + "/pages-preview", public)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS_PUBLIC_ORIGIN_PARITY", result.stdout)
        self.assertEqual(preview_handler.methods, ["GET"])
        self.assertEqual(public_handler.methods, ["GET"])

    def test_status_difference_blocks_public_origin(self) -> None:
        body = b"<html><title>Retired route</title><body>not found</body></html>"
        with fixture(404, body) as (preview, _), fixture(200, body) as (public, _):
            result = run_gate(preview, public)
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED_PUBLIC_ORIGIN_MISMATCH", result.stdout)
        self.assertIn("http_status_mismatch", result.stdout)
        self.assertIn("retired_path_not_404", result.stdout)

    def test_title_difference_blocks_public_origin(self) -> None:
        with fixture(404, b"<html><title>Preview retired</title></html>") as (preview, _), fixture(
            404, b"<html><title>Public retired</title></html>"
        ) as (public, _):
            result = run_gate(preview, public)
        self.assertEqual(result.returncode, 2)
        self.assertIn("title_mismatch", result.stdout)
        self.assertIn("content_fingerprint_mismatch", result.stdout)

    def test_same_title_with_different_content_blocks_public_origin(self) -> None:
        with fixture(404, b"<html><title>Retired</title><body>preview</body></html>") as (preview, _), fixture(
            404, b"<html><title>Retired</title><body>public</body></html>"
        ) as (public, _):
            result = run_gate(preview, public)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("title_mismatch", result.stdout)
        self.assertIn("content_fingerprint_mismatch", result.stdout)

    def test_production_mode_rejects_http_before_network(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(VERIFIER),
                "--preview-origin",
                "http://127.0.0.1:1",
                "--public-origin",
                "http://127.0.0.1:1",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("check=invalid_input", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
