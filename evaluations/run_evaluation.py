from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluations.metrics import run_deepeval, run_ragas
from operations_agent.adapters.local import (
    AdapterBundle,
    LocalAlertPublisher,
    LocalAuditRepository,
    LocalContainerRepository,
    LocalJobQueue,
    LocalReportStore,
)
from operations_agent.agent import answer
from operations_agent.domain import ContainerRecord


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def seed_adapters(root: Path) -> AdapterBundle:
    reports = LocalReportStore(root / "reports")
    containers = LocalContainerRepository(root / "operations.db")
    reports.put("reports/available.json", b'{"container_id":"ABC123","terminal":"Fraser Surrey Dock","status":"available","appointment_id":"APT-1001"}')
    reports.put("reports/conflict.json", b'{"container_id":"CONFLICT42","terminal":"DP World","status":"held"}')
    reports.put("reports/missing.json", b'{"container_id":"MISSING99","terminal":"Delta","status":"missing"}')
    containers.upsert(ContainerRecord("ABC123", "Fraser Surrey Dock", "available", "2026-11-20T10:42:00Z", "APT-1001", "reports/available.json"))
    containers.upsert(ContainerRecord("CONFLICT42", "DP World", "available", "2026-11-20T10:42:00Z", None, "reports/conflict.json"))
    containers.upsert(ContainerRecord("MISSING99", "Delta", "missing", "2026-11-20T10:42:00Z", None, "reports/missing.json"))
    return AdapterBundle(reports, containers, LocalAuditRepository(root / "audit.jsonl"), LocalJobQueue(), LocalAlertPublisher())


def run_local(dataset_path: str, report_path: str) -> dict[str, Any]:
    cases = load_cases(dataset_path)
    adapters = seed_adapters(Path(".local/evaluation"))
    answers: list[dict[str, Any]] = []
    for case in cases:
        response = answer(case["input"], adapters)
        answers.append(response.__dict__)
    result = {"cases": len(cases), "ragas": run_ragas(cases, answers), "deepeval": run_deepeval(cases, answers)}
    output = Path(report_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["local"], default="local")
    parser.add_argument("--dataset", default="evaluations/dataset.jsonl")
    parser.add_argument("--report", default="reports/evaluation.json")
    args = parser.parse_args()
    print(json.dumps(run_local(args.dataset, args.report), indent=2, sort_keys=True))
