from operations_agent.health import health


def test_health_reports_local_mode() -> None:
    assert health("local") == {"status": "ok", "mode": "local"}
