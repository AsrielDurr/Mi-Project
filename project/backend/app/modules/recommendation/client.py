from __future__ import annotations

import json
import os
from typing import Protocol

import httpx


class LlmPort(Protocol):
    model: str

    def complete(self, system_prompt: str, user_prompt: str) -> str: ...


class MiMoClient:
    """Minimal OpenAI-compatible MiMo adapter configured only from environment."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 10,
    ) -> None:
        if not api_key:
            raise ValueError("MIMO_API_KEY is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self.model = model
        self._timeout = timeout_seconds

    @classmethod
    def from_env(cls) -> "MiMoClient":
        return cls(
            api_key=os.getenv("MIMO_API_KEY", ""),
            base_url=os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1"),
            model=os.getenv("MIMO_MODEL", "mimo-v2-flash"),
            timeout_seconds=float(os.getenv("MIMO_TIMEOUT_SECONDS", "10")),
        )

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("MiMo response content must be a string")
        return content


def compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
