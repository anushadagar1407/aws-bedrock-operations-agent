from __future__ import annotations

import json
import os
from typing import Any

from operations_agent.handlers.agent_api import local_adapters
from operations_agent.ingestion import process_report


def ingestion_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    del context
    if os.getenv("APP_MODE", "local") == "aws":
        from operations_agent.adapters.aws import aws_adapters

        adapters = aws_adapters()
    else:
        adapters = local_adapters()
    records = []
    for message in event.get("Records", [event]):
        body = message.get("body", message)
        if isinstance(body, str):
            body = json.loads(body)
        if "Records" in body:
            key = body["Records"][0]["s3"]["object"]["key"]
            body = {"report_key": key}
        records.append(process_report(body, adapters))
    return {"statusCode": 200, "records": [record.__dict__ for record in records]}

