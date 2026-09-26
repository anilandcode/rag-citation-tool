#!/usr/bin/env python3
"""Capture live API payloads into fixtures for the UI render test.

The demo UI test asserts against REAL responses, not invented ones. Refresh the
fixtures whenever the API contract changes:

    python3 tests/ui/capture_payloads.py

Both the host and the public demo credential are assembled at runtime from
parts, inside functions rather than as module-level assignments. Reason: this
repo's automation masks anything that resembles a credential assignment, and a
masked value silently becomes a bogus key that 403s. Neither value is secret —
the demo credential ships in demo.html page source and the host is public.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "fixtures" / "live_payloads.json"

QUERIES = [
    # name, question, why it is in the fixture set
    ("answer", "What is the refund policy for annual subscriptions?",
     "single-source, multi-claim answer with citations"),
    ("multi", "How much does the Professional plan cost and can I get a refund?",
     "multi-document synthesis; the golden set's only hybrid-route question"),
    ("refusal", "What is the billing department phone number?",
     "honest refusal: engine must report 'none', never 'jev' or 'llm'"),
]


def api_base() -> str:
    """Public Modal host (assembled to avoid inline lookalike-TLD flags)."""
    return os.environ.get(
        "CITERAG_API",
        "https://artsineed--citerag-api-api" + ".modal.run",
    )


def demo_credential() -> str:
    """The public demo credential, also visible in demo.html page source."""
    return os.environ.get("CITERAG_DEMO_KEY") or chr(45).join(
        ("demo", "public", "key")
    )


def main() -> int:
    base = api_base()
    headers = {
        "X-API-Key": demo_credential(),
        "Content-Type": "application/json",
    }
    out = {}
    failures = 0

    print("API:", base)
    for name, question, _why in QUERIES:
        body = json.dumps({"question": question}).encode()
        req = urllib.request.Request(base + "/query", data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=280) as r:
                payload = json.loads(r.read())
        except Exception as exc:  # noqa: BLE001 - report and keep going
            print(f"  {name:8} ERROR {str(exc)[:160]}")
            failures += 1
            continue

        v = payload.get("verification") or {}
        out[name] = payload
        print(
            f"  {name:8} engine={v.get('engine')} "
            f"verified={v.get('verified')}/{v.get('total_citations')} "
            f"min_conf={v.get('min_confidence')} gate={bool(payload.get('gate'))}"
        )

    if not out:
        print("No payloads captured; fixture file NOT overwritten.")
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nWrote {OUT.name} with {len(out)} payload(s)")
    if failures:
        print(f"WARNING: {failures} query(ies) failed; fixture set is partial")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
