import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import requests


class LLMProvider(ABC):
    @abstractmethod
    def summarize(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        timeout: float = 300.0,
        max_retries: int = 1,
    ) -> Optional[str]:
        ...


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: Optional[dict[str, str]] = None,
    timeout: float = 300.0,
    max_retries: int = 1,
) -> Optional[dict[str, Any]]:
    """POST JSON with a timeout and simple retry; return parsed JSON or None.

    Any network, HTTP-status, or JSON-decode error is swallowed and retried up
    to *max_retries* times. Returns ``None`` once all attempts are exhausted so
    callers can fall back gracefully.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # network/status/decode all fall back to retry
            last_exc = exc
            if attempt < max_retries:
                time.sleep(2 * (attempt + 1))

    print(f"LLM request failed after {max_retries + 1} attempt(s): {last_exc}")
    return None
