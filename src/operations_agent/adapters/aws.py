from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import boto3

from operations_agent.domain import ContainerRecord


class AWSReportStore:
    def __init__(self, bucket: str) -> None:
        self.bucket = bucket
        self.client = boto3.client("s3")

    def put(self, key: str, body: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=body)

    def get(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()


class AWSContainerRepository:
    def __init__(self, secret_arn: str) -> None:
        self.secret_arn = secret_arn
        self.secrets = boto3.client("secretsmanager")
        self._connection: Any = None

    def _connection_for_request(self) -> Any:
        vendor_path = Path(__file__).resolve().parents[2] / "vendor"
        if str(vendor_path) not in sys.path:
            sys.path.insert(0, str(vendor_path))
        import pg8000.dbapi

        secret = json.loads(self.secrets.get_secret_value(SecretId=self.secret_arn)["SecretString"])
        return pg8000.dbapi.connect(
            user=secret["username"],
            password=secret["password"],
            host=secret["host"],
            port=int(secret.get("port", 5432)),
            database=secret.get("dbname", "operations"),
            timeout=10,
        )

    def _ensure_table(self, connection: Any) -> None:
        connection.run(
            """
            CREATE TABLE IF NOT EXISTS containers (
                container_id TEXT PRIMARY KEY,
                terminal TEXT NOT NULL,
                status TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                appointment_id TEXT,
                source_report_key TEXT NOT NULL
            )
            """
        )
        connection.commit()

    def upsert(self, record: ContainerRecord) -> None:
        connection = self._connection_for_request()
        try:
            self._ensure_table(connection)
            connection.run(
                """
                INSERT INTO containers VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT(container_id) DO UPDATE SET
                    terminal=EXCLUDED.terminal,
                    status=EXCLUDED.status,
                    last_updated=EXCLUDED.last_updated,
                    appointment_id=EXCLUDED.appointment_id,
                    source_report_key=EXCLUDED.source_report_key
                """,
                (record.container_id, record.terminal, record.status, record.last_updated, record.appointment_id, record.source_report_key),
            )
            connection.commit()
        finally:
            connection.close()

    def get(self, container_id: str) -> ContainerRecord | None:
        connection = self._connection_for_request()
        try:
            self._ensure_table(connection)
            rows = connection.run(
                "SELECT container_id, terminal, status, last_updated, appointment_id, source_report_key FROM containers WHERE container_id = %s",
                (container_id,),
            )
            return ContainerRecord(*rows[0]) if rows else None
        finally:
            connection.close()


class AWSAuditRepository:
    def __init__(self, table_name: str) -> None:
        self.table = boto3.resource("dynamodb").Table(table_name)

    def record(self, event: dict[str, Any]) -> str:
        audit_id = str(event.get("audit_id", uuid4()))
        item = {**event, "audit_id": audit_id, "created_at": datetime.now(UTC).isoformat()}
        self.table.put_item(Item=item)
        return audit_id

    def list_for(self, container_id: str) -> list[dict[str, Any]]:
        return self.table.query(
            IndexName="container-index",
            KeyConditionExpression=boto3.dynamodb.conditions.Key("container_id").eq(container_id),
        ).get("Items", [])


class AWSJobQueue:
    def __init__(self, queue_url: str) -> None:
        self.queue_url = queue_url
        self.client = boto3.client("sqs")

    def enqueue(self, payload: dict[str, Any]) -> None:
        self.client.send_message(QueueUrl=self.queue_url, MessageBody=json.dumps(payload))


class AWSAlertPublisher:
    def __init__(self, topic_arn: str) -> None:
        self.topic_arn = topic_arn
        self.client = boto3.client("sns")

    def publish(self, subject: str, message: str) -> None:
        self.client.publish(TopicArn=self.topic_arn, Subject=subject[:100], Message=message)


@dataclass
class AWSAdapterBundle:
    reports: AWSReportStore
    containers: AWSContainerRepository
    audit: AWSAuditRepository
    jobs: AWSJobQueue
    alerts: AWSAlertPublisher


def aws_adapters() -> AWSAdapterBundle:
    return AWSAdapterBundle(
        reports=AWSReportStore(os.environ["REPORTS_BUCKET"]),
        containers=AWSContainerRepository(os.environ["RDS_SECRET_ARN"]),
        audit=AWSAuditRepository(os.environ["AUDIT_TABLE_NAME"]),
        jobs=AWSJobQueue(os.environ["JOBS_QUEUE_URL"]),
        alerts=AWSAlertPublisher(os.environ["ALERTS_TOPIC_ARN"]),
    )

