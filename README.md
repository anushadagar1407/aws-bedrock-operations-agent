# AWS Bedrock Operations Agent

An independently owned portfolio project that demonstrates a grounded AI freight-operations workflow with Amazon Bedrock, S3, SQS, Lambda, RDS PostgreSQL, DynamoDB, SNS, API Gateway, a Next.js dashboard, RAGAS, and DeepEval.

The agent answers container-status questions by combining structured records with source reports. It returns evidence, confidence, an audit ID, and a manual-review result when sources conflict. The committed data is synthetic; the project does not connect to private employer systems or contain production credentials.

## Local demo

Local mode uses fixture files, SQLite, an in-process queue, and a deterministic provider. It does not require an AWS account or Bedrock access.

```bash
python3.13 -m venv .venv13
source .venv13/bin/activate
python -m pip install -e '.[dev]'
./scripts/demo_local.sh
```

The demo ingests synthetic reports, asks the local agent about a normal container and a conflicting container, then writes an evaluation report under `reports/evaluation.json`.

## Run checks

```bash
./scripts/check.sh
```

The check script runs Python tests and linting, CDK assertions and synthesis, and the Next.js test, typecheck, and production build.

## AWS deployment

The CDK stack in `infra/` creates S3 for source reports, SQS plus a dead-letter queue for ingestion and retries, Lambda for ingestion and agent execution, RDS PostgreSQL for normalized records, DynamoDB for audit history, SNS for alerts, API Gateway for the agent endpoint, and a VPC with private application subnets and an isolated database subnet.

Install Node.js and configure an AWS account with Bedrock model access before deployment. The AWS CLI is not required for synthesis, but AWS credentials and CDK bootstrap are required for deployment.

```bash
npm --prefix infra install
npx --prefix infra cdk bootstrap
npm --prefix infra run synth
npx --prefix infra cdk deploy
```

The stack uses synthetic fixtures by default. RDS, NAT, Bedrock, and data-transfer charges can apply. Destroy the portfolio environment when it is no longer needed:

```bash
npx --prefix infra cdk destroy
```

## Evaluation

`evaluations/dataset.jsonl` contains normal, missing, conflict, delayed, and malformed scenarios. The local runner reports deterministic status accuracy and answer-keyword results. When the optional packages and an approved evaluator model are configured, the same runner exposes RAGAS and DeepEval integration points for faithfulness, answer relevancy, context precision/recall, task completion, hallucination, and tool-use checks.

```bash
python evaluations/run_evaluation.py --mode local
```

See [docs/architecture.md](docs/architecture.md) and [docs/evaluation.md](docs/evaluation.md) for the data flow, contracts, and evaluation approach.
