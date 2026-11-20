from operations_agent.providers.bedrock import BedrockProvider, tool_schema


class FakeBedrock:
    def __init__(self) -> None:
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"toolUse": {"toolUseId": "1", "name": "lookup_container", "input": {"container_id": "ABC123"}}}],
                    }
                },
                "stopReason": "tool_use",
            }
        return {"output": {"message": {"role": "assistant", "content": [{"text": "Container is available."}]}}, "stopReason": "end_turn"}


def test_bedrock_provider_dispatches_tool_and_returns_text() -> None:
    provider = BedrockProvider(FakeBedrock(), "test-model")
    result = provider.answer(
        "status ABC123",
        [tool_schema("lookup_container", "Look up a container", {"container_id": {"type": "string"}}, ["container_id"])],
        lambda name, inputs: {"name": name, **inputs},
    )
    assert result["text"] == "Container is available."
    assert result["tool_trace"] == ["lookup_container"]
