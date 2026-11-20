from operations_agent.ingestion import normalize_report


def test_normalize_report_maps_synthetic_terminal_fields() -> None:
    record = normalize_report(
        b'{"container_id":"ABC123","terminal":"FSD","status":"available"}',
        "reports/a.json",
    )
    assert record.container_id == "ABC123"
    assert record.status == "available"
