"""Authentication and rate limiting for the RAG Citation API.

Provides a simple API-key auth dependency and a basic in-memory rate limiter.
Designed for v0.1 single-tenant deployments. Replace with a database-backed
solution for multi-tenant production use.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request

from src.utils.logging import get_logger

log = get_logger("auth")

API_KEYS = {
    "rag-cite-dev-key": "development",
    "rag-cite-prod-key": "production",
}

# In-memory rate limiter: {client_key: [(timestamp,), ...]}
_rate_limit_buckets: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 100     # requests per window


async def verify_api_key(request: Request) -> str:
    """FastAPI dependency: validates the X-API-Key header.

    Returns the client name if the key is valid. Raises 401 if missing or invalid.
    Skips auth if no API keys are configured (open dev mode).
    """
    if not API_KEYS:
        return "unauthenticated"

    api_key = request.headers.get("X-API-Key", "")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    client_name = API_KEYS.get(api_key)
    if not client_name:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return client_name


async def rate_limit(request: Request, client: str = Depends(verify_api_key)) -> str:
    """FastAPI dependency: enforces per-client rate limits.

    Allows RATE_LIMIT_MAX requests per RATE_LIMIT_WINDOW seconds.
    Raises 429 if exceeded.
    """
    now = time.time()
    bucket = _rate_limit_buckets[client]

    # Prune expired entries
    _rate_limit_buckets[client] = [t for t in bucket if now - t < RATE_LIMIT_WINDOW]

    if len(_rate_limit_buckets[client]) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    _rate_limit_buckets[client].append(now)
    return client


async def verify_demo_key(request: Request) -> str:
    """Dependency: validates X-API-Key for /query.

    If no API_KEY is configured, the endpoint is open.
    If DEMO_API_KEY is configured, accepts keys matching it OR the main api_key.
    """
    from src.config.settings import settings

    configured_key = settings.api_key
    demo_key = settings.demo_api_key

    if not configured_key and not demo_key:
        return "unauthenticated"

    key = request.headers.get("X-API-Key", "")
    if configured_key and key == configured_key:
        return "authenticated"
    if demo_key and key == demo_key:
        return "demo"

    if configured_key or demo_key:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key header")

    return "unauthenticated"
