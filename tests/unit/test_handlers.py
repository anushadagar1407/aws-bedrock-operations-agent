import json

from operations_agent.handlers.agent_api import agent_handler


def test_agent_handler_returns_json_response(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_ROOT", str(tmp_path))
    result = agent_handler({"body": '{"query":"status ABC123"}'})
    assert result["statusCode"] == 200
    assert "audit_id" in json.loads(result["body"])

