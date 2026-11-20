from operations_agent.adapters.local import LocalContainerRepository
from operations_agent.domain import ContainerRecord


def test_local_container_repository_round_trips_record(tmp_path) -> None:
    repository = LocalContainerRepository(tmp_path / "operations.db")
    record = ContainerRecord(
        container_id="ABC123",
        terminal="FSD",
        status="available",
        last_updated="2026-11-20T10:42:00Z",
        appointment_id="APT-1001",
        source_report_key="reports/available.json",
    )
    repository.upsert(record)
    assert repository.get("ABC123") == record
