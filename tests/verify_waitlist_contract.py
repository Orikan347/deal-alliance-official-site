#!/usr/bin/env python3
"""Fake-receiver E2E for the public waitlist contract; no real data or service."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
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
    seen: dict[str, str] = {}
    accepted_payloads: list[dict[str, object]] = []

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/waitlist":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length))
        required = {"topic", "contact", "consent", "source", "client_request_id"}
        if set(body) != required or body.get("consent") is not True or body.get("source") != "official-site-waitlist":
            response = json.dumps({"ok": False, "status": "rejected"}).encode()
            self.send_response(400)
        else:
            assert "password" not in body and "license_key" not in body
            client_request_id = str(body["client_request_id"])
            request_id = FakeReceiver.seen.setdefault(client_request_id, f"fake-receiver-{len(FakeReceiver.seen) + 1:04d}")
            if body not in FakeReceiver.accepted_payloads:
                FakeReceiver.accepted_payloads.append(body)
            response = json.dumps({"ok": True, "request_id": request_id, "status": "received"}).encode()
            self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, *_args: object) -> None:
        return


def main() -> None:
    FakeReceiver.seen.clear()
    FakeReceiver.accepted_payloads.clear()
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
        with urlopen(request, timeout=3) as duplicate:
            duplicate_result = json.loads(duplicate.read())
            assert duplicate.status == 202
            assert duplicate_result == result
        invalid = dict(FAKE_PAYLOAD, consent=False)
        invalid_request = Request(
            f"http://127.0.0.1:{server.server_port}/waitlist",
            data=json.dumps(invalid).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            urlopen(invalid_request, timeout=3)
            raise AssertionError("invalid consent unexpectedly accepted")
        except HTTPError as error:
            assert error.code == 400
            assert json.loads(error.read()) == {"ok": False, "status": "rejected"}
        assert len(FakeReceiver.accepted_payloads) == 1
        config = (ROOT / "assets/site-config.js").read_text(encoding="utf-8")
        assert 'waitlistEndpoint: ""' in config and 'waitlistMode: "disabled"' in config
        print("PASS_WAITLIST_FAKE_E2E status=202 readback=request_id dedupe=stable reject=400 fake_payload_only default_mode=disabled")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
