"""API key authentication for KeplAI."""

import hmac
import os

from fastapi import Header, HTTPException


async def verify_api_key(x_api_key: str | None = Header(None)) -> str:
    """Validate the X-API-Key header against KEPLAI_API_KEY env var.

    If KEPLAI_API_KEY is not set, authentication is disabled (dev mode).
    """
    valid_key = os.getenv("KEPLAI_API_KEY")

    if not valid_key:
        # No key configured — allow all requests (local dev)
        return ""

    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if not hmac.compare_digest(x_api_key, valid_key):
        raise HTTPException(status_code=403, detail="Invalid API key")

    return x_api_key
