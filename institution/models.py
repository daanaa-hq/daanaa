"""Typed, provider-neutral models for safe institutional workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class DataClass(str, Enum):
    PUBLIC = "tier_0_public"
    INTERNAL = "tier_1_internal"
    CONFIDENTIAL = "tier_2_confidential"
    RESTRICTED = "tier_2_restricted"


class RetentionClass(str, Enum):
    TRANSIENT = "transient"
    RAW_MESSAGE_30D = "raw_message_30d"
    OPERATIONAL = "operational"
    GOVERNANCE = "governance"
    MANUAL_REVIEW = "manual_review"


class TaskType(str, Enum):
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    DRAFTING = "drafting"
    RETRIEVAL = "retrieval"
    GOVERNANCE_CHECK = "governance_check"


@dataclass(frozen=True)
class TaskRequest:
    task_type: TaskType
    data_class: DataClass
    required_quality: str = "standard"
    context_tokens: int = 0
    latency_budget_ms: int = 5000
    confidence_threshold: float = 0.8
    contains_external_content: bool = False
    task_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True)
class TaskResult:
    status: str
    confidence: float | None
    output: Any = None
    fallback: str | None = None
    reason: str | None = None
    provenance: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class GovernanceDocument:
    path: str
    authority_rank: int
    sha256: str
    exists: bool
    role: str


@dataclass(frozen=True)
class Contradiction:
    subject: str
    sources: tuple[str, ...]
    description: str
    status: str = "unresolved"


def jsonable(value: Any) -> Any:
    """Convert dataclasses/enums for audit records without serializing secrets."""
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: jsonable(getattr(value, key)) for key in value.__dataclass_fields__}
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value
