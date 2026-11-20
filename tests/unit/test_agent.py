from operations_agent.adapters.local import AdapterBundle, LocalAlertPublisher, LocalAuditRepository, LocalContainerRepository, LocalJobQueue, LocalReportStore
from operations_agent.domain import ContainerRecord
from operations_agent.agent import answer


def test_conflicting_evidence_creates_review_exception(tmp_path) -> None:
    reports = LocalReportStore(tmp_path / "reports")
    reports.put("reports/conflict.json", b'{"container_id":"CONFLICT42","terminal":"DP World","status":"held"}')
    containers = LocalContainerRepository(tmp_path / "operations.db")
    containers.upsert(ContainerRecord("CONFLICT42", "DP World", "available", "2026-11-20T10:42:00Z", None, "reports/conflict.json"))
    adapters = AdapterBundle(reports, containers, LocalAuditRepository(tmp_path / "audit.jsonl"), LocalJobQueue(), LocalAlertPublisher())
    response = answer("What is the status of CONFLICT42?", adapters)
    assert response.requires_review is True
    assert response.status == "conflict"
    assert adapters.alerts.messages
