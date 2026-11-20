from __future__ import annotations

import re
from typing import Protocol
from uuid import uuid4

from operations_agent.adapters.local import AdapterBundle
from operations_agent.domain import AgentResponse, Evidence
from operations_agent.providers.bedrock import BedrockProvider, tool_schema
from operations_agent.tools import (
    create_exception,
    lookup_container,
    retrieve_report,
    validate_status,
)


class ModelProvider(Protocol):
    def answer(self, query: str, evidence: list[Evidence], status: str, reason: str) -> str: ...


class DeterministicProvider:
    def answer(self, query: str, evidence: list[Evidence], status: str, reason: str) -> str:
        del query
        if status == "conflict":
            return f"Manual review required: {reason}"
        if status == "unknown":
            return f"Manual review required: {reason}"
        terminal = next((item.value for item in evidence if item.field == "terminal"), "unknown")
        return f"The container status is {status} at {terminal}. Source evidence agrees with the normalized record."


def _container_id(query: str) -> str:
    match = re.search(r"\b[A-Z]{3,}[0-9]{2,}\b", query.upper())
    if match is None:
        raise ValueError("The query must include a container ID such as ABC123.")
    return match.group(0)


def answer(
    query: str,
    adapters: AdapterBundle,
    model_provider: ModelProvider | None = None,
) -> AgentResponse:
    provider = model_provider or DeterministicProvider()
    audit_id = str(uuid4())
    container_id = _container_id(query)
    trace = ["extract_container_id", "lookup_container", "retrieve_report", "validate_status"]
    try:
        record = lookup_container(container_id, adapters)
    except LookupError:
        response = AgentResponse(
            answer=f"No normalized record was found for {container_id}. Manual review is required.",
            status="missing",
            confidence=0.05,
            evidence=[],
            requires_review=True,
            audit_id=audit_id,
            tool_trace=trace,
        )
        adapters.audit.record({"event": "agent_answer", "container_id": container_id, "status": "missing", "audit_id": audit_id})
        return response

    evidence = retrieve_report(record.source_report_key, adapters)
    validation = validate_status(record, evidence)
    if validation.requires_review:
        exception = create_exception(container_id, validation.reason, evidence, adapters)
        trace.append("create_exception")
        reason = f"{validation.reason} Exception {exception.exception_id} was created."
    else:
        reason = validation.reason
    response = AgentResponse(
        answer=provider.answer(query, evidence, validation.status, reason),
        status=validation.status,
        confidence=validation.confidence,
        evidence=evidence,
        requires_review=validation.requires_review,
        audit_id=audit_id,
        tool_trace=trace,
    )
    adapters.audit.record(
        {
            "event": "agent_answer",
            "container_id": container_id,
            "status": response.status,
            "requires_review": response.requires_review,
            "audit_id": audit_id,
        }
    )
    return response


def answer_with_bedrock(query: str, adapters, provider: BedrockProvider) -> AgentResponse:
    container_id = _container_id(query)
    state: dict[str, object] = {"record": None, "evidence": []}

    def dispatch(name: str, inputs: dict[str, object]) -> dict[str, object]:
        if name == "lookup_container":
            record = lookup_container(str(inputs["container_id"]), adapters)
            state["record"] = record
            return record.__dict__
        if name == "retrieve_report":
            record = state.get("record")
            if record is None:
                raise LookupError("lookup_container must run before retrieve_report")
            report_key = str(inputs.get("report_key") or record.source_report_key)
            evidence = retrieve_report(report_key, adapters)
            state["evidence"] = evidence
            return {"evidence": [item.__dict__ for item in evidence]}
        if name == "validate_status":
            record = state.get("record")
            evidence = state.get("evidence", [])
            if record is None:
                raise LookupError("lookup_container must run before validate_status")
            result = validate_status(record, evidence)
            state["validation"] = result
            return result.__dict__
        if name == "create_exception":
            evidence = state.get("evidence", [])
            exception = create_exception(container_id, str(inputs.get("reason", "Manual review required")), evidence, adapters)
            return exception.__dict__
        raise ValueError(f"Unsupported agent tool: {name}")

    schemas = [
        tool_schema("lookup_container", "Look up the normalized operational record for a container.", {"container_id": {"type": "string"}}, ["container_id"]),
        tool_schema("retrieve_report", "Retrieve source evidence for a container report.", {"report_key": {"type": "string"}}, ["report_key"]),
        tool_schema("validate_status", "Compare normalized data with source evidence.", {}, []),
        tool_schema("create_exception", "Create a manual-review exception for conflicting evidence.", {"reason": {"type": "string"}}, ["reason"]),
    ]
    model_result = provider.answer(query, schemas, dispatch)
    validation = state.get("validation")
    if validation is None:
        status = "unknown"
        confidence = 0.1
        requires_review = True
        evidence = state.get("evidence", [])
    else:
        status = validation.status
        confidence = validation.confidence
        requires_review = validation.requires_review
        evidence = validation.evidence
    audit_id = str(uuid4())
    adapters.audit.record({"event": "bedrock_agent_answer", "container_id": container_id, "status": status, "audit_id": audit_id})
    return AgentResponse(
        answer=str(model_result["text"]),
        status=status,
        confidence=confidence,
        evidence=evidence,
        requires_review=requires_review,
        audit_id=audit_id,
        tool_trace=list(model_result.get("tool_trace", [])),
    )

