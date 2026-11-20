# AWS Bedrock Operations Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a portfolio-ready AI freight-operations assistant that uses Amazon Bedrock tool use, S3, SQS, Lambda, RDS PostgreSQL, DynamoDB, SNS, API Gateway, a Next.js dashboard, RAGAS, DeepEval, CDK infrastructure, and reproducible local tests.

**Architecture:** A Python application layer exposes typed agent tools and local adapters. A TypeScript CDK stack defines the AWS resources and wiring. A Next.js dashboard calls the agent API. Local mode uses synthetic fixtures, SQLite, an in-process queue, and a deterministic Bedrock mock; AWS mode uses Bedrock Runtime, S3, SQS, Lambda, RDS, DynamoDB, SNS, and API Gateway.

**Tech Stack:** Python 3.12, FastAPI-compatible handler contracts, boto3, pytest, RAGAS, DeepEval, TypeScript, AWS CDK, Next.js, React, SQLite, PostgreSQL, Amazon Bedrock Converse API.

**Spec:** `docs/superpowers/specs/2026-11-20-bedrock-operations-agent-design.md`

## Global Constraints

- Use synthetic fixtures only; never commit Trans BC credentials, production URLs, private reports, customer data, or proprietary source code.
- Keep a deterministic local mode that does not require AWS credentials or live Bedrock access.
- Keep AWS deployment optional and explicit; document expected RDS, NAT, Bedrock, and data-transfer costs plus teardown steps.
- Return typed errors for tool failures and never treat missing or conflicting evidence as a confirmed status.
- Use visible repository documentation so the project can be demonstrated during interviews.

---

### Task 1: Repository scaffold and developer commands

**Files:**
- Create: `pyproject.toml`
- Create: `package.json`
- Create: `README.md`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `src/operations_agent/__init__.py`
- Create: `tests/unit/test_health.py`

**Interfaces:**
- Produces `pytest`, `ruff`, `mypy`, `npm run typecheck`, and `npm run test` commands used by later tasks.

- [ ] **Step 1: Write the failing health test**

```python
from operations_agent.health import health


def test_health_reports_local_mode():
    assert health("local") == {"status": "ok", "mode": "local"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/unit/test_health.py -q`

Expected: FAIL because `operations_agent.health` does not exist.

- [ ] **Step 3: Add the minimal health module and project configuration**

```python
# src/operations_agent/health.py
def health(mode: str) -> dict[str, str]:
    return {"status": "ok", "mode": mode}
```

Configure `pyproject.toml` with Python 3.12, pytest, ruff, mypy, boto3, pydantic, and the evaluation dependencies. Configure `package.json` with CDK, TypeScript, Next.js, React, and scripts for synthesis, type checking, and tests.

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/test_health.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml package.json README.md .env.example .gitignore src tests
git commit -m "chore: scaffold operations agent"
```

### Task 2: Typed domain contracts and synthetic fixtures

**Files:**
- Create: `src/operations_agent/domain.py`
- Create: `src/operations_agent/fixtures.py`
- Create: `data/fixtures/reports/available.json`
- Create: `data/fixtures/reports/conflict.json`
- Create: `data/fixtures/reports/missing.json`
- Create: `tests/unit/test_domain.py`

**Interfaces:**
- Produces `ContainerRecord`, `Evidence`, `ValidationResult`, `ExceptionRecord`, `ToolError`, and `AgentResponse` Pydantic models.

- [ ] **Step 1: Write failing validation tests**

```python
from operations_agent.domain import ContainerRecord


def test_container_record_requires_container_id_and_status():
    record = ContainerRecord(
        container_id="ABC123",
        terminal="FSD",
        status="available",
        last_updated="2026-11-20T10:42:00Z",
        appointment_id=None,
        source_report_key="reports/available.json",
    )
    assert record.container_id == "ABC123"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/unit/test_domain.py -q`

Expected: FAIL because the domain models are not defined.

- [ ] **Step 3: Implement the models and fixtures**

Define the exact fields from the spec, use timezone-aware timestamps, constrain status to known values, and model typed retryable errors. Include normal, missing, and conflicting synthetic reports.

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/unit/test_domain.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/operations_agent/domain.py src/operations_agent/fixtures.py data tests/unit/test_domain.py
git commit -m "feat: add domain contracts and fixtures"
```

### Task 3: Local adapters for S3, RDS, DynamoDB, SQS, and SNS

**Files:**
- Create: `src/operations_agent/adapters/local.py`
- Create: `src/operations_agent/adapters/__init__.py`
- Create: `tests/unit/test_local_adapters.py`
- Create: `tests/integration/test_local_flow.py`

**Interfaces:**
- `ReportStore.put(key, body)`, `ReportStore.get(key)`
- `ContainerRepository.upsert(record)`, `ContainerRepository.get(container_id)`
- `AuditRepository.record(event)`, `AuditRepository.list_for(container_id)`
- `JobQueue.enqueue(payload)`, `JobQueue.receive()`
- `AlertPublisher.publish(subject, message)`

- [ ] **Step 1: Write failing adapter tests**

```python
def test_local_report_store_round_trips_bytes(tmp_path):
    store = LocalReportStore(tmp_path)
    store.put("reports/a.json", b"{}")
    assert store.get("reports/a.json") == b"{}"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/unit/test_local_adapters.py -q`

Expected: FAIL because local adapters are not implemented.

- [ ] **Step 3: Implement adapters**

Use filesystem storage for S3, SQLite for RDS, JSONL for DynamoDB audit records, an in-memory queue for SQS, and an in-memory alert list for SNS. Keep the interfaces independent of AWS SDK types.

- [ ] **Step 4: Run unit and integration tests**

Run: `pytest tests/unit/test_local_adapters.py tests/integration/test_local_flow.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/operations_agent/adapters tests
git commit -m "feat: add local storage and messaging adapters"
```

### Task 4: Ingestion normalization and retry behavior

**Files:**
- Create: `src/operations_agent/ingestion.py`
- Create: `src/operations_agent/retry.py`
- Create: `tests/unit/test_ingestion.py`
- Create: `tests/unit/test_retry.py`

**Interfaces:**
- `normalize_report(payload: bytes, source_key: str) -> ContainerRecord`
- `classify_ingestion_error(error: Exception) -> ToolError`
- `process_report(message: dict, adapters: AdapterBundle) -> ContainerRecord`

- [ ] **Step 1: Write failing normalization and retry tests**

```python
def test_normalize_report_maps_synthetic_terminal_fields():
    record = normalize_report(b'{"container_id":"ABC123","status":"available"}', "reports/a.json")
    assert record.container_id == "ABC123"
    assert record.status == "available"


def test_timeout_is_retryable():
    assert classify_ingestion_error(TimeoutError("portal timeout")).retryable is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_ingestion.py tests/unit/test_retry.py -q`

Expected: FAIL because the functions are not defined.

- [ ] **Step 3: Implement normalization and processing**

Parse the synthetic JSON reports, validate required fields, upsert normalized records, record audit events, enqueue retryable failures, and publish SNS-equivalent alerts for non-retryable failures.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_ingestion.py tests/unit/test_retry.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/operations_agent/ingestion.py src/operations_agent/retry.py tests
git commit -m "feat: add report ingestion and retry handling"
```

### Task 5: Agent tools and deterministic local agent

**Files:**
- Create: `src/operations_agent/tools.py`
- Create: `src/operations_agent/agent.py`
- Create: `tests/unit/test_tools.py`
- Create: `tests/unit/test_agent.py`

**Interfaces:**
- `lookup_container(container_id, adapters) -> ContainerRecord`
- `retrieve_report(report_key, adapters) -> list[Evidence]`
- `validate_status(record, evidence) -> ValidationResult`
- `create_exception(container_id, reason, evidence, adapters) -> ExceptionRecord`
- `answer(query, adapters, model_provider) -> AgentResponse`

- [ ] **Step 1: Write failing tool and grounded-response tests**

```python
def test_conflicting_evidence_requires_review(seed_adapters):
    response = answer("What is the status of ABC123?", seed_adapters, DeterministicProvider())
    assert response.requires_review is True
    assert response.status == "conflict"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_tools.py tests/unit/test_agent.py -q`

Expected: FAIL because tools and agent orchestration are missing.

- [ ] **Step 3: Implement bounded tools and deterministic provider**

Implement the four tools from the spec. The deterministic provider maps known synthetic questions to tool calls, creates answers from returned evidence, and refuses unsupported claims. Keep a provider interface compatible with the Bedrock Converse provider.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_tools.py tests/unit/test_agent.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/operations_agent/tools.py src/operations_agent/agent.py tests
git commit -m "feat: add grounded operations agent"
```

### Task 6: Bedrock provider and Lambda/API contracts

**Files:**
- Create: `src/operations_agent/providers/bedrock.py`
- Create: `src/operations_agent/handlers/agent_api.py`
- Create: `src/operations_agent/handlers/ingestion.py`
- Create: `tests/unit/test_bedrock_provider.py`
- Create: `tests/unit/test_handlers.py`

**Interfaces:**
- `BedrockProvider.answer(query, tool_schemas, dispatch_tool) -> AgentResponse`
- `agent_handler(event, context) -> dict`
- `ingestion_handler(event, context) -> dict`

- [ ] **Step 1: Write failing provider and handler tests**

```python
def test_agent_handler_returns_json_response():
    result = agent_handler({"body": '{"query":"status ABC123"}'}, None)
    assert result["statusCode"] == 200
    assert "audit_id" in json.loads(result["body"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_bedrock_provider.py tests/unit/test_handlers.py -q`

Expected: FAIL because the provider and handlers are not implemented.

- [ ] **Step 3: Implement the Bedrock Converse provider and handlers**

Use boto3 `bedrock-runtime.converse` with an environment-selected model ID. Convert tool schemas to Bedrock tool specifications, dispatch bounded tools, enforce a maximum tool-call count, validate the final `AgentResponse`, and return API Gateway-compatible JSON. The handlers must default to local adapters when `APP_MODE=local`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_bedrock_provider.py tests/unit/test_handlers.py -q`

Expected: PASS using a fake Bedrock client.

- [ ] **Step 5: Commit**

```bash
git add src/operations_agent/providers src/operations_agent/handlers tests
git commit -m "feat: add bedrock provider and lambda handlers"
```

### Task 7: Evaluation suite with RAGAS and DeepEval

**Files:**
- Create: `evaluations/dataset.jsonl`
- Create: `evaluations/run_evaluation.py`
- Create: `evaluations/metrics.py`
- Create: `tests/evaluation/test_dataset.py`
- Create: `reports/.gitkeep`

**Interfaces:**
- `load_cases(path) -> list[EvaluationCase]`
- `run_local_evaluation(cases, provider) -> EvaluationReport`
- `run_ragas(cases, answers) -> dict[str, float]`
- `run_deepeval(cases, answers) -> dict[str, float]`

- [ ] **Step 1: Write failing dataset and metric tests**

```python
def test_dataset_contains_normal_missing_and_conflict_cases():
    cases = load_cases("evaluations/dataset.jsonl")
    labels = {case.expected_status for case in cases}
    assert {"available", "missing", "conflict"}.issubset(labels)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/evaluation/test_dataset.py -q`

Expected: FAIL because the evaluation runner is missing.

- [ ] **Step 3: Implement the evaluation dataset and runners**

Add at least 15 synthetic cases covering normal responses, missing data, conflicting data, delayed records, malformed reports, tool-use failures, and unsupported questions. Use RAGAS metrics for faithfulness, answer relevancy, context precision, and context recall. Use DeepEval metrics for task completion, tool-use correctness, hallucination, and a custom grounded-status criterion. Provide local deterministic mode and an optional Bedrock mode.

- [ ] **Step 4: Run the evaluation tests**

Run: `pytest tests/evaluation/test_dataset.py -q && python evaluations/run_evaluation.py --mode local`

Expected: PASS and a JSON report under `reports/`.

- [ ] **Step 5: Commit**

```bash
git add evaluations tests/evaluation reports
git commit -m "feat: add ragas and deepeval evaluation suite"
```

### Task 8: AWS CDK infrastructure

**Files:**
- Create: `infra/bin/app.ts`
- Create: `infra/lib/operations-agent-stack.ts`
- Create: `infra/package.json`
- Create: `infra/tsconfig.json`
- Create: `infra/cdk.json`
- Create: `infra/test/operations-agent-stack.test.ts`

**Interfaces:**
- CDK stack outputs `ApiUrl`, `ReportsBucketName`, `ContainerTableName`, `AuditTableName`, `JobsQueueUrl`, and `AlertsTopicArn`.

- [ ] **Step 1: Write failing CDK assertions**

```typescript
test('creates required event-driven resources', () => {
  const app = new cdk.App();
  const stack = new OperationsAgentStack(app, 'TestStack', { env: { account: '123456789012', region: 'us-east-1' } });
  const template = Template.fromStack(stack);
  template.resourceCountIs('AWS::S3::Bucket', 1);
  template.resourceCountIs('AWS::SQS::Queue', 2);
  template.resourceCountIs('AWS::DynamoDB::Table', 1);
  template.resourceCountIs('AWS::SNS::Topic', 1);
  template.resourceCountIs('AWS::RDS::DBInstance', 1);
});
```

- [ ] **Step 2: Run the CDK test to verify it fails**

Run: `npm --prefix infra test -- --runInBand`

Expected: FAIL because the stack is not implemented.

- [ ] **Step 3: Implement the CDK stack**

Define private S3 storage with removal policy suitable for a portfolio environment, an SQS queue with a dead-letter queue, SNS topic, DynamoDB audit table with a container ID index and point-in-time recovery, an RDS PostgreSQL instance in a VPC, Lambda functions with environment configuration, API Gateway integration, and least-privilege grants. Add CDK outputs and tags for the project name and environment.

- [ ] **Step 4: Run synthesis and assertions**

Run: `npm --prefix infra test -- --runInBand && npm --prefix infra run synth`

Expected: PASS and a synthesized CloudFormation template.

- [ ] **Step 5: Commit**

```bash
git add infra
git commit -m "feat: define aws infrastructure with cdk"
```

### Task 9: Next.js dashboard

**Files:**
- Create: `web/package.json`
- Create: `web/tsconfig.json`
- Create: `web/app/page.tsx`
- Create: `web/app/globals.css`
- Create: `web/lib/api.ts`
- Create: `web/components/AgentQuery.tsx`
- Create: `web/components/EvidencePanel.tsx`
- Create: `web/components/AuditTimeline.tsx`

**Interfaces:**
- `queryAgent(query: string): Promise<AgentResponse>`
- `AgentQuery` submits a question and renders loading, error, and grounded result states.

- [ ] **Step 1: Write the dashboard contract test**

```typescript
test('renders the operations query form', async () => {
  render(<AgentQuery />);
  expect(screen.getByRole('textbox', { name: /container question/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /check status/i })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm --prefix web test -- --runInBand`

Expected: FAIL because the dashboard is not implemented.

- [ ] **Step 3: Implement the dashboard**

Build a single-column responsive dashboard with a query form, result status, confidence, evidence list, tool trace, audit ID, and manual-review alert. Support local API mode through `NEXT_PUBLIC_API_URL` and display clear error states.

- [ ] **Step 4: Run type checks and tests**

Run: `npm --prefix web test -- --runInBand && npm --prefix web run typecheck`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web
git commit -m "feat: add operations agent dashboard"
```

### Task 10: Documentation, CI, local demo, and GitHub publication

**Files:**
- Modify: `README.md`
- Create: `.github/workflows/ci.yml`
- Create: `scripts/demo_local.sh`
- Create: `scripts/check.sh`
- Create: `docs/architecture.md`
- Create: `docs/evaluation.md`

**Interfaces:**
- `scripts/demo_local.sh` runs the local ingestion, agent query, and evaluation flow.
- `scripts/check.sh` runs Python tests, linting, type checks, CDK tests/synthesis, web tests, and web type checks.

- [ ] **Step 1: Write the local demo verification**

```bash
test -x scripts/demo_local.sh
test -x scripts/check.sh
```

- [ ] **Step 2: Run the demo before documentation is complete**

Run: `./scripts/demo_local.sh`

Expected: the initial run fails until all local components are wired.

- [ ] **Step 3: Complete README, architecture, evaluation, and CI**

Document local setup, environment variables, synthetic-data policy, live AWS deployment, Bedrock model access, CDK bootstrap, teardown, RAGAS/DeepEval commands, expected local outputs, and the distinction between independent portfolio work and employer work. The CI workflow runs the same check script without AWS credentials.

- [ ] **Step 4: Run the complete verification**

Run: `./scripts/check.sh && ./scripts/demo_local.sh`

Expected: all checks pass, a local agent response is produced, and an evaluation report is written.

- [ ] **Step 5: Commit and publish the public repository**

```bash
git add .
git commit -m "feat: ship aws bedrock operations agent"
gh repo create anushadagar1407/aws-bedrock-operations-agent --public --source=. --remote=origin --push
```

Expected: the public GitHub repository is created at `https://github.com/anushadagar1407/aws-bedrock-operations-agent` with the implementation, infrastructure, tests, evaluation artifacts, and README.
