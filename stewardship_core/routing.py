"""Local-only task routing with deterministic and human-review fallbacks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import DataClass, TaskRequest, TaskResult, TaskType


class LocalModelAdapter(Protocol):
    name: str
    max_context_tokens: int
    supported_tasks: frozenset[TaskType]

    def run(self, request: TaskRequest, payload: str) -> TaskResult: ...


@dataclass(frozen=True)
class RoutingDecision:
    route: str
    model: str | None
    reason: str
    requires_review: bool


class ModelRouter:
    def __init__(self, adapters: tuple[LocalModelAdapter, ...] = ()) -> None:
        self.adapters = adapters

    def choose(self, request: TaskRequest) -> RoutingDecision:
        if request.data_class in {DataClass.CONFIDENTIAL, DataClass.RESTRICTED}:
            allowed = [a for a in self.adapters if request.task_type in a.supported_tasks]
            if not allowed:
                return RoutingDecision("manual_review", None, "no validated local model for protected data", True)
        else:
            allowed = [a for a in self.adapters if request.task_type in a.supported_tasks]
        for adapter in allowed:
            if request.context_tokens <= adapter.max_context_tokens:
                return RoutingDecision("local_model", adapter.name, "validated local adapter within context limit", False)
        if request.task_type in {TaskType.CLASSIFICATION, TaskType.EXTRACTION, TaskType.GOVERNANCE_CHECK}:
            return RoutingDecision("deterministic", None, "model context/resource constraint", False)
        return RoutingDecision("manual_review", None, "no safe local route", True)

    def run(self, request: TaskRequest, payload: str) -> TaskResult:
        decision = self.choose(request)
        if decision.route != "local_model":
            return TaskResult("needs_review" if decision.requires_review else "fallback", None, fallback=decision.route, reason=decision.reason)
        adapter = next(a for a in self.adapters if a.name == decision.model)
        result = adapter.run(request, payload)
        if result.confidence is None or result.confidence < request.confidence_threshold:
            return TaskResult("needs_review", result.confidence, result.output, "manual_review", "confidence below threshold", result.provenance)
        return result
