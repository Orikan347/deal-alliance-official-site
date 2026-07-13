#!/usr/bin/env python3
"""Verify the candidate's static-host security header contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADERS = (ROOT / "_headers").read_text(encoding="utf-8")
required = (
    "X-Content-Type-Options: nosniff",
    "Referrer-Policy: strict-origin-when-cross-origin",
    "Permissions-Policy: camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy:",
    "connect-src 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
)
missing = [item for item in required if item not in HEADERS]
if missing:
    raise SystemExit(f"FAIL_HEADERS_CONTRACT missing={missing}")
print("PASS_HEADERS_CONTRACT security_headers=7 candidate_only=true")
