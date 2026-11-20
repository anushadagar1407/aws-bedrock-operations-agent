from operations_agent.adapters.local import LocalReportStore


def test_local_report_store_round_trips_bytes(tmp_path) -> None:
    store = LocalReportStore(tmp_path)
    store.put("reports/a.json", b"{}")
    assert store.get("reports/a.json") == b"{}"
