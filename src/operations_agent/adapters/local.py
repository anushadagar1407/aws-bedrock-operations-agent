from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import Any
from uuid import uuid4

from operations_agent.domain import ContainerRecord


class LocalReportStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, key: str, body: bytes) -> None:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)

    def get(self, key: str) -> bytes:
        return (self.root / key).read_bytes()


class LocalContainerRepository:
    def __init__(self, path: str | Path) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.execute(
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
        self.connection.commit()

    def upsert(self, record: ContainerRecord) -> None:
        self.connection.execute(
            """
            INSERT INTO containers VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(container_id) DO UPDATE SET
                terminal=excluded.terminal,
                status=excluded.status,
                last_updated=excluded.last_updated,
                appointment_id=excluded.appointment_id,
                source_report_key=excluded.source_report_key
            """,
            (
                record.container_id,
                record.terminal,
                record.status,
                record.last_updated,
                record.appointment_id,
                record.source_report_key,
            ),
        )
        self.connection.commit()

    def get(self, container_id: str) -> ContainerRecord | None:
        row = self.connection.execute(
            "SELECT container_id, terminal, status, last_updated, appointment_id, source_report_key FROM containers WHERE container_id = ?",
            (container_id,),
        ).fetchone()
        if row is None:
            return None
        return ContainerRecord(*row)


class LocalAuditRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: dict[str, Any]) -> str:
        audit_id = event.get("audit_id", str(uuid4()))
        payload = {**event, "audit_id": audit_id}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        return str(audit_id)

    def list_for(self, container_id: str) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item.get("container_id") == container_id:
                events.append(item)
        return events


class LocalJobQueue:
    def __init__(self) -> None:
        self.queue: Queue[dict[str, Any]] = Queue()

    def enqueue(self, payload: dict[str, Any]) -> None:
        self.queue.put(payload)

    def receive(self) -> dict[str, Any] | None:
        if self.queue.empty():
            return None
        return self.queue.get_nowait()


class LocalAlertPublisher:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    def publish(self, subject: str, message: str) -> None:
        self.messages.append({"subject": subject, "message": message})


@dataclass
class AdapterBundle:
    reports: LocalReportStore
    containers: LocalContainerRepository
    audit: LocalAuditRepository
    jobs: LocalJobQueue
    alerts: LocalAlertPublisher

