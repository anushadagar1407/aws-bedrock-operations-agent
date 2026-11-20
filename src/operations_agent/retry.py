from __future__ import annotations

from operations_agent.domain import ToolError


def classify_ingestion_error(error: Exception) -> ToolError:
    if isinstance(error, (TimeoutError, ConnectionError)):
        return ToolError("transient_ingestion_failure", str(error), True)
    return ToolError("invalid_ingestion_payload", str(error), False)

