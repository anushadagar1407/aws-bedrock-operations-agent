from __future__ import annotations

from collections.abc import Callable
from typing import Any


class BedrockProvider:
    def __init__(self, client: Any, model_id: str, max_rounds: int = 5) -> None:
        self.client = client
        self.model_id = model_id
        self.max_rounds = max_rounds

    def answer(
        self,
        query: str,
        tool_schemas: list[dict[str, Any]],
        dispatch_tool: Callable[[str, dict[str, Any]], dict[str, Any]],
    ) -> dict[str, Any]:
        messages: list[dict[str, Any]] = [{"role": "user", "content": [{"text": query}]}]
        trace: list[str] = []
        for _ in range(self.max_rounds):
            response = self.client.converse(
                modelId=self.model_id,
                messages=messages,
                toolConfig={"tools": tool_schemas},
            )
            message = response["output"]["message"]
            messages.append(message)
            tool_uses = [item["toolUse"] for item in message.get("content", []) if "toolUse" in item]
            if not tool_uses:
                text = " ".join(item["text"] for item in message.get("content", []) if "text" in item).strip()
                return {"text": text, "tool_trace": trace, "stop_reason": response.get("stopReason", "end_turn")}
            results: list[dict[str, Any]] = []
            for tool_use in tool_uses:
                name = str(tool_use["name"])
                trace.append(name)
                try:
                    result = dispatch_tool(name, dict(tool_use.get("input", {})))
                    results.append({"toolResult": {"toolUseId": tool_use["toolUseId"], "content": [{"json": result}]}})
                except Exception as error:
                    results.append(
                        {
                            "toolResult": {
                                "toolUseId": tool_use["toolUseId"],
                                "status": "error",
                                "content": [{"text": str(error)}],
                            }
                        }
                    )
            messages.append({"role": "user", "content": results})
        raise RuntimeError("Bedrock agent exceeded its tool-call limit")


def tool_schema(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "toolSpec": {
            "name": name,
            "description": description,
            "inputSchema": {"json": {"type": "object", "properties": properties, "required": required}},
        }
    }

