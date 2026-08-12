"""Authentication and rate limiting for the RAG Citation API.

v0.1: API key via settings + optional demo key. In-memory rate limit.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request

from src.config.settings import settings
from src.utils.logging import get_logger

log = get_logger("auth")

# In-memory rate limiter: {client_key: [timestamps]}
_rate_limit_buckets: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 60  # requests per window per client


def _header_key(request: Request) -> str:
    return (request.headers.get("X-API-Key") or "").strip()


async def verify_api_key(request: Request) -> str:
    """Require X-API-Key when settings.api_key is set. Open if unset."""
    configured = (settings.api_key or "").strip()
    if not configured:
        return "open"

    key = _header_key(request)
    if not key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if key != configured:
        # Also accept demo key for read-ish ops only via verify_demo_key;
        # ingest stays locked to main API_KEY.
        raise HTTPException(status_code=403, detail="Invalid API key")
    return "authenticated"


async def verify_demo_key(request: Request) -> str:
    """Allow main API_KEY, DEMO_API_KEY, or open mode when neither is set."""
    configured = (settings.api_key or "").strip()
    demo = (settings.demo_api_key or "").strip()

    if not configured and not demo:
        return "open"

    key = _header_key(request)
    if configured and key == configured:
        return "authenticated"
    if demo and key == demo:
        return "demo"
    if not key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    raise HTTPException(status_code=403, detail="Invalid API key")


async def rate_limit(request: Request) -> str:
    """Per-IP (and key) sliding window. Applied to expensive routes."""
    key = _header_key(request) or (request.client.host if request.client else "anon")
    now = time.time()
    bucket = [t for t in _rate_limit_buckets[key] if now - t < RATE_LIMIT_WINDOW]
    if len(bucket) >= RATE_LIMIT_MAX:
        log.warning("rate_limit_exceeded", client=key[:16])
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    bucket.append(now)
    _rate_limit_buckets[key] = bucket
    return key
