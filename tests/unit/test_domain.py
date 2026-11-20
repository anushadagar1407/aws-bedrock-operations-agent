from operations_agent.domain import ContainerRecord


def test_container_record_contains_operational_fields() -> None:
    record = ContainerRecord(
        container_id="ABC123",
        terminal="FSD",
        status="available",
        last_updated="2026-11-20T10:42:00Z",
        appointment_id=None,
        source_report_key="reports/available.json",
    )
    assert record.container_id == "ABC123"
    assert record.status == "available"
