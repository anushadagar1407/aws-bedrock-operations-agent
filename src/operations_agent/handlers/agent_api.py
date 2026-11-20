from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from operations_agent.adapters.local import (
    AdapterBundle,
    LocalAlertPublisher,
    LocalAuditRepository,
    LocalContainerRepository,
    LocalJobQueue,
    LocalReportStore,
)
from operations_agent.agent import answer, answer_with_bedrock
from operations_agent.providers.bedrock import BedrockProvider


def local_adapters(root: str | Path = ".local") -> AdapterBundle:
    base = Path(root)
    return AdapterBundle(
        reports=LocalReportStore(base / "reports"),
        containers=LocalContainerRepository(base / "operations.db"),
        audit=LocalAuditRepository(base / "audit.jsonl"),
        jobs=LocalJobQueue(),
        alerts=LocalAlertPublisher(),
    )


def agent_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    del context
    body = event.get("body", event)
    payload = json.loads(body) if isinstance(body, str) else body
    if os.getenv("APP_MODE", "local") == "aws":
        import boto3

        response = answer_with_bedrock(
            str(payload["query"]),
            __import__("operations_agent.adapters.aws", fromlist=["aws_adapters"]).aws_adapters(),
            BedrockProvider(boto3.client("bedrock-runtime"), os.environ["BEDROCK_MODEL_ID"]),
        )
    else:
        response = answer(str(payload["query"]), local_adapters(os.getenv("LOCAL_ROOT", ".local")))
    return {"statusCode": 200, "headers": {"content-type": "application/json"}, "body": json.dumps(response.__dict__, default=str)}

