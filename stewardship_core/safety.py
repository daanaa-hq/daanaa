"""Deterministic trust-boundary checks for untrusted external content."""

from __future__ import annotations

import re
from typing import Any

_INJECTION_PATTERNS = (
    r"ignore\s+(?:all|any|the)\s+(?:previous|prior|above)\s+instructions?",
    r"system\s*message",
    r"developer\s*message",
    r"reveal\s+(?:the\s+)?(?:prompt|secret|credential|token)",
    r"follow\s+these\s+instructions?\s*:",
    r"you\s+are\s+now\s+(?:an?|the)\s+",
)


def detect_prompt_injection(text: str) -> tuple[bool, tuple[str, ...]]:
    hits = tuple(pattern for pattern in _INJECTION_PATTERNS if re.search(pattern, text, re.I))
    return bool(hits), hits


def redact_for_log(value: Any) -> Any:
    """Keep operational metadata while preventing raw message leakage."""
    if isinstance(value, str):
        return f"<redacted:{len(value)} chars>"
    if isinstance(value, dict):
        return {str(k): redact_for_log(v) for k, v in value.items() if k not in {"body", "raw", "token", "secret"}}
    if isinstance(value, (list, tuple)):
        return [redact_for_log(item) for item in value]
    return value
