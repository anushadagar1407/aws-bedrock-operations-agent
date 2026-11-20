from __future__ import annotations

from typing import Any

from operations_agent.handlers.agent_api import local_adapters
from operations_agent.ingestion import process_report


def ingestion_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    del context
    adapters = local_adapters()
    records = []
    for message in event.get("Records", [event]):
        body = message.get("body", message)
        records.append(process_report(body, adapters))
    return {"statusCode": 200, "records": [record.__dict__ for record in records]}

