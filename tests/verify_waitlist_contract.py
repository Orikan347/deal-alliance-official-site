#!/usr/bin/env python3
"""Fake-receiver E2E for the public waitlist contract; no real data or service."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FAKE_PAYLOAD = {
    "topic": "客戶開發與跟進",
    "contact": "fake-visitor@example.invalid",
    "consent": True,
    "source": "official-site-waitlist",
    "client_request_id": "00000000-0000-4000-8000-000000000001",
}


class FakeReceiver(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/waitlist":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length))
        required = {"topic", "contact", "consent", "source", "client_request_id"}
        assert set(body) == required
        assert body["consent"] is True
        assert body["source"] == "official-site-waitlist"
        assert "password" not in body and "license_key" not in body
        response = json.dumps({"ok": True, "request_id": "fake-receiver-0001", "status": "received"}).encode()
        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, *_args: object) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeReceiver)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/waitlist",
            data=json.dumps(FAKE_PAYLOAD).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=3) as response:
            result = json.loads(response.read())
            assert response.status == 202
            assert result == {"ok": True, "request_id": "fake-receiver-0001", "status": "received"}
        config = (ROOT / "assets/site-config.js").read_text(encoding="utf-8")
        assert 'waitlistEndpoint: ""' in config and 'waitlistMode: "disabled"' in config
        print("PASS_WAITLIST_FAKE_E2E status=202 readback=request_id fake_payload_only default_mode=disabled")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
