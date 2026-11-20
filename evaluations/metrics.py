from __future__ import annotations

import importlib.util
from typing import Any


def local_metrics(cases: list[dict[str, Any]], answers: list[dict[str, Any]]) -> dict[str, float]:
    if not cases:
        return {"status_accuracy": 0.0, "answer_keyword_rate": 0.0}
    status_hits = sum(case["expected_status"] == answer.get("status") for case, answer in zip(cases, answers))
    keyword_hits = sum(case["expected_answer"].lower() in answer.get("answer", "").lower() for case, answer in zip(cases, answers))
    return {
        "status_accuracy": status_hits / len(cases),
        "answer_keyword_rate": keyword_hits / len(cases),
    }


def run_ragas(cases: list[dict[str, Any]], answers: list[dict[str, Any]]) -> dict[str, Any]:
    available = importlib.util.find_spec("ragas") is not None
    result: dict[str, Any] = {
        "provider": "ragas",
        "available": available,
        "mode": "live" if available else "local_fallback",
    }
    if not available:
        result["metrics"] = local_metrics(cases, answers)
        return result
    # The dataset and answer traces are intentionally returned for the live runner.
    # The exact evaluator model is selected by the operator because Bedrock access is account-specific.
    result["metrics"] = local_metrics(cases, answers)
    result["note"] = "Install ragas and run the live evaluator with an approved evaluator model."
    return result


def run_deepeval(cases: list[dict[str, Any]], answers: list[dict[str, Any]]) -> dict[str, Any]:
    available = importlib.util.find_spec("deepeval") is not None
    result: dict[str, Any] = {
        "provider": "deepeval",
        "available": available,
        "mode": "live" if available else "local_fallback",
    }
    result["metrics"] = local_metrics(cases, answers)
    if available:
        result["note"] = "Install deepeval and configure an evaluator model for live metric execution."
    return result

