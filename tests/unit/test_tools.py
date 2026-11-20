from operations_agent.adapters.local import (
    AdapterBundle,
    LocalAlertPublisher,
    LocalAuditRepository,
    LocalContainerRepository,
    LocalJobQueue,
    LocalReportStore,
)
from operations_agent.domain import ContainerRecord
from operations_agent.tools import retrieve_report, validate_status


def _adapters(tmp_path) -> AdapterBundle:
    reports = LocalReportStore(tmp_path / "reports")
    reports.put(
        "reports/a.json",
        b'{"container_id":"ABC123","terminal":"FSD","status":"available"}',
    )
    containers = LocalContainerRepository(tmp_path / "operations.db")
    containers.upsert(ContainerRecord("ABC123", "FSD", "available", "2026-11-20T10:42:00Z", None, "reports/a.json"))
    return AdapterBundle(reports, containers, LocalAuditRepository(tmp_path / "audit.jsonl"), LocalJobQueue(), LocalAlertPublisher())


def test_conflicting_evidence_requires_review(tmp_path) -> None:
    adapters = _adapters(tmp_path)
    record = adapters.containers.get("ABC123")
    assert record is not None
    evidence = retrieve_report("reports/a.json", adapters)
    evidence = [item if item.field != "status" else item.__class__(item.source_type, item.source_id, item.field, "held", item.observed_at) for item in evidence]
    result = validate_status(record, evidence)
    assert result.requires_review is True
    assert result.status == "conflict"
