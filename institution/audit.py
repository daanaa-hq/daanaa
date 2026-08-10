"""Append-only, hash-chained operational audit events."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .safety import redact_for_log


class AuditLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, *, actor: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        previous = "GENESIS"
        if self.path.exists():
            with self.path.open("rb") as handle:
                for line in handle:
                    if line.strip():
                        previous = json.loads(line)["event_hash"]
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "actor": actor,
            "metadata": redact_for_log(metadata or {}),
            "previous_hash": previous,
        }
        canonical = json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
        event["event_hash"] = hashlib.sha256(canonical).hexdigest()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return event
