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
from operations_agent.agent import answer


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
    response = answer(str(payload["query"]), local_adapters(os.getenv("LOCAL_ROOT", ".local")))
    return {"statusCode": 200, "headers": {"content-type": "application/json"}, "body": json.dumps(response.__dict__, default=str)}

