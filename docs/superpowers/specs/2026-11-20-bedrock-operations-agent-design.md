# AWS Bedrock Operations Agent Design

## Goal

Build a portfolio-ready, independently owned AI freight-operations assistant that demonstrates Amazon Bedrock tool use, S3, SQS, Lambda, RDS PostgreSQL, DynamoDB, SNS, API Gateway, a Next.js dashboard, RAGAS evaluation, DeepEval evaluation, infrastructure as code, and reproducible tests without using private company data.

## Scope and ownership

The project is an independent prototype. It uses synthetic terminal reports and container records modeled on common freight workflows. It must not include Trans BC credentials, production URLs, private reports, customer data, or copied proprietary source code. Resume language may describe this project as an independent portfolio project after it is implemented and tested.

## User flow

An operator enters a container question in the dashboard or calls the API. The agent interprets the request with Amazon Bedrock and selects one or more tools: look up a normalized container record, retrieve a source report, validate conflicting status values, or create an exception. The response contains a concise answer, evidence references, confidence and review status, and an audit identifier. Conflicting or incomplete evidence produces a manual-review result and an SNS notification rather than an invented answer.

## Architecture

The Next.js dashboard calls an API Gateway endpoint backed by an agent Lambda. The agent Lambda uses the Bedrock Runtime Converse API with tool definitions and dispatches tools through a small service layer. The lookup tool reads RDS PostgreSQL; the report tool reads S3; the validation tool compares structured and source evidence; and the exception tool writes a DynamoDB audit record and publishes an SNS message.

Document ingestion is asynchronous. Uploading a report to S3 emits an event to SQS. An ingestion Lambda consumes the message, extracts the synthetic report fields, writes normalized records to RDS, records the processing run in DynamoDB, and sends failed messages to an SQS dead-letter queue. SNS is used for processing failures and manual-review exceptions.

The AWS infrastructure is defined in AWS CDK using TypeScript. The application code is Python for Lambda and evaluation services, and TypeScript for the Next.js dashboard and CDK stack. Local development uses fixture data, a local SQLite adapter, a deterministic mock Bedrock provider, and an in-process queue so tests do not require an AWS account.

## Data contracts

`ContainerRecord` contains `container_id`, `terminal`, `status`, `last_updated`, `appointment_id`, and `source_report_key`.

`Evidence` contains `source_type`, `source_id`, `field`, `value`, and `observed_at`.

`AgentResponse` contains `answer`, `status`, `confidence`, `evidence`, `requires_review`, `audit_id`, and `tool_trace`.

The agent tool interface exposes four operations:

1. `lookup_container(container_id) -> ContainerRecord`
2. `retrieve_report(report_key) -> list[Evidence]`
3. `validate_status(container_record, evidence) -> ValidationResult`
4. `create_exception(container_id, reason, evidence) -> ExceptionRecord`

Every tool failure returns a typed error with a retryable flag. The agent never treats a missing or conflicting value as a confirmed status.

## Evaluation

The repository contains a synthetic evaluation set with normal, missing, conflicting, delayed, and malformed cases. RAGAS evaluates faithfulness, answer relevancy, context precision, and context recall over the evidence returned to the agent. DeepEval evaluates task completion, tool-use correctness, hallucination, and a custom grounded-status criterion. Evaluation results are written to JSON locally and can be stored in DynamoDB in AWS mode.

The evaluation runner supports a deterministic mock provider for repeatable CI and an optional Bedrock provider selected through an environment variable. AWS credentials and model access are never required for unit tests. Live Bedrock evaluation is an explicit integration command.

## Security and cost boundaries

Only synthetic data is committed. Secrets are read from environment variables or AWS Secrets Manager in deployment; no credentials are committed. S3 buckets block public access, DynamoDB uses point-in-time recovery in production configuration, and the CDK stack enables removal protection controls appropriate for a portfolio environment. The README documents that RDS, Bedrock, and NAT resources can incur charges and includes teardown instructions.

## Verification

The project must provide unit tests for tool contracts, ingestion normalization, retry classification, grounded-response behavior, and exception creation. Integration tests must exercise the local adapters end to end. CDK synthesis, Python linting, TypeScript type checking, and the evaluation runner must be documented and runnable from a clean checkout.

## Out of scope

The first version does not connect to live terminal portals, use private Trans BC data, submit job applications, or claim production deployment. It does not implement a general-purpose autonomous agent beyond the four bounded operations above.
