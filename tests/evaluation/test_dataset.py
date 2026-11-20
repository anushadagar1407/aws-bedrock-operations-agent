from evaluations.run_evaluation import load_cases


def test_dataset_contains_normal_missing_and_conflict_cases() -> None:
    cases = load_cases("evaluations/dataset.jsonl")
    labels = {case["expected_status"] for case in cases}
    assert len(cases) >= 15
    assert {"available", "missing", "conflict"}.issubset(labels)
