# Evaluation

The evaluation set contains 15 synthetic cases across confirmed availability, conflicting records, missing records, appointments, and manual-review scenarios.

The local runner always computes deterministic status accuracy and answer-keyword rate. It also reports whether the RAGAS and DeepEval packages are installed. Live evaluator execution is optional because it requires an evaluator model, credentials, and account-specific configuration.

RAGAS is used for retrieval and answer quality concepts: faithfulness, answer relevancy, context precision, and context recall.

DeepEval is used for agent behavior concepts: task completion, tool-use correctness, hallucination, and grounded-status custom criteria.

The evaluation output is JSON so it can be stored in DynamoDB in AWS mode or attached to a CI artifact. No private documents are used in the committed dataset.
