# Architecture

The system has four bounded layers.

1. The Next.js dashboard sends a question to API Gateway. The agent Lambda uses the Bedrock Converse API and a fixed set of tool schemas.
2. Tool implementations query normalized RDS records, retrieve S3 evidence, validate conflicting values, and create DynamoDB audit events plus SNS alerts.
3. S3 report uploads flow through SQS to the ingestion Lambda. The ingestion Lambda normalizes synthetic reports into RDS and records the processing outcome in DynamoDB.
4. Local mode uses the same domain contracts with filesystem, SQLite, JSONL, in-memory queue, and deterministic-provider adapters. This keeps tests repeatable without credentials.

The agent can answer a confirmed status only when the normalized record and source report agree. Missing or conflicting values produce `requires_review=true` and a manual-review exception.

## Tool contracts

- `lookup_container(container_id)` reads a normalized `ContainerRecord`.
- `retrieve_report(report_key)` returns field-level `Evidence`.
- `validate_status(record, evidence)` returns status, confidence, reason, and review state.
- `create_exception(container_id, reason, evidence)` creates a review record and publishes an alert.

The tool boundary is intentionally small so the Bedrock agent can be tested independently of the AWS adapters.
