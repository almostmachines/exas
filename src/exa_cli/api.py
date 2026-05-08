"""Thin HTTP wrapper over the Exa /search endpoint."""

from __future__ import annotations

from typing import Any

import httpx

API_URL = "https://api.exa.ai/search"
DEFAULT_TIMEOUT = 60.0


class ExaError(RuntimeError):
    pass


def search(payload: dict[str, Any], api_key: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }
    try:
        resp = httpx.post(API_URL, headers=headers, json=payload, timeout=timeout)
    except httpx.TimeoutException as e:
        raise ExaError(f"Request timed out after {timeout}s") from e
    except httpx.HTTPError as e:
        raise ExaError(f"HTTP error: {e}") from e

    if resp.status_code >= 400:
        body = resp.text.strip()
        raise ExaError(f"Exa API returned {resp.status_code}: {body}")

    try:
        return resp.json()
    except ValueError as e:
        raise ExaError(f"Could not parse Exa response as JSON: {resp.text[:200]}") from e
