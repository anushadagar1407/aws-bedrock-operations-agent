from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from operations_agent.adapters.local import AdapterBundle
from operations_agent.domain import (
    ContainerRecord,
    Evidence,
    ExceptionRecord,
    ToolError,
    ValidationResult,
)


def lookup_container(container_id: str, adapters: AdapterBundle) -> ContainerRecord:
    record = adapters.containers.get(container_id)
    if record is None:
        raise LookupError(f"container not found: {container_id}")
    return record


def retrieve_report(report_key: str, adapters: AdapterBundle) -> list[Evidence]:
    payload = json.loads(adapters.reports.get(report_key).decode("utf-8"))
    observed_at = str(payload.get("last_updated") or datetime.now(timezone.utc).isoformat())
    return [
        Evidence("terminal_report", report_key, key, str(value), observed_at)
        for key, value in payload.items()
        if key in {"container_id", "terminal", "status", "appointment_id"}
        and value is not None
    ]


def validate_status(record: ContainerRecord, evidence: list[Evidence]) -> ValidationResult:
    status_values = {item.value for item in evidence if item.field == "status"}
    if not status_values:
        return ValidationResult(
            status="unknown",
            confidence=0.1,
            requires_review=True,
            reason="The source report does not contain a status.",
            evidence=evidence,
        )
    if record.status not in status_values:
        return ValidationResult(
            status="conflict",
            confidence=0.2,
            requires_review=True,
            reason=f"Database status {record.status!r} conflicts with report status {sorted(status_values)!r}.",
            evidence=evidence,
        )
    return ValidationResult(
        status=record.status,
        confidence=0.98,
        requires_review=False,
        reason="The normalized record agrees with the source report.",
        evidence=evidence,
    )


def create_exception(
    container_id: str,
    reason: str,
    evidence: list[Evidence],
    adapters: AdapterBundle,
) -> ExceptionRecord:
    exception = ExceptionRecord(
        exception_id=str(uuid4()),
        container_id=container_id,
        reason=reason,
        status="open",
        evidence=evidence,
    )
    adapters.audit.record(
        {
            "event": "manual_review_exception",
            "exception_id": exception.exception_id,
            "container_id": container_id,
            "reason": reason,
        }
    )
    adapters.alerts.publish("Manual review required", reason)
    return exception

