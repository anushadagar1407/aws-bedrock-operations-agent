from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Status = Literal["available", "held", "delayed", "missing", "conflict", "unknown"]


@dataclass(frozen=True)
class ContainerRecord:
    container_id: str
    terminal: str
    status: Status
    last_updated: str
    appointment_id: str | None
    source_report_key: str


@dataclass(frozen=True)
class Evidence:
    source_type: str
    source_id: str
    field: str
    value: str
    observed_at: str


@dataclass(frozen=True)
class ValidationResult:
    status: Status
    confidence: float
    requires_review: bool
    reason: str
    evidence: list[Evidence] = field(default_factory=list)


@dataclass(frozen=True)
class ExceptionRecord:
    exception_id: str
    container_id: str
    reason: str
    status: str
    evidence: list[Evidence] = field(default_factory=list)


@dataclass(frozen=True)
class ToolError:
    code: str
    message: str
    retryable: bool
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResponse:
    answer: str
    status: Status
    confidence: float
    evidence: list[Evidence]
    requires_review: bool
    audit_id: str
    tool_trace: list[str]

