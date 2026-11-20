# AWS Bedrock Operations Agent

An independently owned portfolio project that demonstrates a grounded AI operations workflow with Amazon Bedrock, S3, SQS, Lambda, RDS PostgreSQL, DynamoDB, SNS, API Gateway, a Next.js dashboard, RAGAS, and DeepEval.

The first version uses synthetic terminal reports and container records. It does not connect to private employer systems or contain production credentials.

## Local development

The local mode uses fixture files, SQLite, an in-process queue, and a deterministic model provider. It does not require an AWS account.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
```

The AWS deployment and evaluation setup will be documented as the infrastructure and evaluation layers are added.
