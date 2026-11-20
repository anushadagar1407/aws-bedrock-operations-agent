from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from operations_agent.adapters.local import AdapterBundle
from operations_agent.domain import ContainerRecord
from operations_agent.retry import classify_ingestion_error


def _timestamp(value: str | None) -> str:
    if value:
        datetime.fromisoformat(value.replace("Z", "+00:00"))  # noqa: FURB162
        return value
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize_report(payload: bytes, source_key: str) -> ContainerRecord:
    data: dict[str, Any] = json.loads(payload.decode("utf-8"))
    required = ("container_id", "terminal", "status")
    missing = [field for field in required if not data.get(field)]
    if missing:
        raise ValueError(f"missing report fields: {', '.join(missing)}")
    status = str(data["status"])
    if status not in {"available", "held", "delayed", "missing", "conflict", "unknown"}:
        raise ValueError(f"unsupported status: {status}")
    return ContainerRecord(
        container_id=str(data["container_id"]),
        terminal=str(data["terminal"]),
        status=status,  # type: ignore[arg-type]
        last_updated=_timestamp(data.get("last_updated")),
        appointment_id=data.get("appointment_id"),
        source_report_key=source_key,
    )


def process_report(message: dict[str, Any], adapters: AdapterBundle) -> ContainerRecord:
    source_key = str(message["report_key"])
    try:
        record = normalize_report(adapters.reports.get(source_key), source_key)
    except Exception as error:
        classified = classify_ingestion_error(error)
        adapters.audit.record(
            {
                "event": "ingestion_failed",
                "report_key": source_key,
                "error_code": classified.code,
                "retryable": classified.retryable,
            }
        )
        if classified.retryable:
            adapters.jobs.enqueue(message)
        else:
            adapters.alerts.publish("Report ingestion failed", classified.message)
        raise
    adapters.containers.upsert(record)
    adapters.audit.record(
        {
            "event": "report_ingested",
            "container_id": record.container_id,
            "report_key": source_key,
            "status": record.status,
        }
    )
    return record

