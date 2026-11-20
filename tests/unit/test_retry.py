from operations_agent.retry import classify_ingestion_error


def test_timeout_is_retryable() -> None:
    assert classify_ingestion_error(TimeoutError("portal timeout")).retryable is True

