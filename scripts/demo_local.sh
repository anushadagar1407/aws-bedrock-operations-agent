#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python_bin="${PYTHON_BIN:-.venv13/bin/python}"
if [[ ! -x "$python_bin" ]]; then
  python_bin="python3"
fi

rm -rf .local/demo
LOCAL_ROOT=.local/demo "$python_bin" - <<'PY'
from pathlib import Path

from operations_agent.adapters.local import LocalReportStore
from operations_agent.agent import answer
from operations_agent.domain import ContainerRecord
from operations_agent.handlers.agent_api import local_adapters
from operations_agent.ingestion import process_report

root = Path(".local/demo")
adapters = local_adapters(root)
reports = LocalReportStore(root / "reports")
reports.put("reports/available.json", b'{"container_id":"ABC123","terminal":"Fraser Surrey Dock","status":"available","appointment_id":"APT-1001"}')
reports.put("reports/conflict.json", b'{"container_id":"CONFLICT42","terminal":"DP World","status":"held"}')
process_report({"report_key": "reports/available.json"}, adapters)
process_report({"report_key": "reports/conflict.json"}, adapters)
adapters.containers.upsert(ContainerRecord("CONFLICT42", "DP World", "available", "2026-11-20T10:42:00Z", None, "reports/conflict.json"))
for query in ("What is the status of ABC123?", "What is the status of CONFLICT42?"):
    result = answer(query, adapters)
    print(result.answer)
    print({"status": result.status, "requires_review": result.requires_review, "audit_id": result.audit_id})
PY

"$python_bin" evaluations/run_evaluation.py --mode local
