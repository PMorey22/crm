from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import hashlib
import logging

from sqlalchemy.orm import Session

from poc20.domain.exceptions import ExternalServiceError
from poc20.infrastructure.repositories import IdempotencyRepository


logger = logging.getLogger(__name__)


@dataclass
class Task:
    task_id: str
    title: str
    due_at: datetime | None
    session_id: str
    property_id: str | None = None
    status: str = "PENDING"


class TaskClient(ABC):
    """Interface for task-management providers."""

    @abstractmethod
    def create_task(
        self,
        title: str,
        session_id: str,
        due_at: datetime | None = None,
        property_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> Task:
        raise NotImplementedError


class MockTaskClient(TaskClient):
    """
    Local task implementation for the POC.

    Tasks are stored in memory and can later be replaced
    by a CRM, task-management API, or n8n workflow.
    """

    def __init__(
        self,
        db: Session | None = None,
    ):
        self.tasks: dict[str, Task] = {}

        self.idempotency_repository = (
            IdempotencyRepository(db)
            if db is not None
            else None
        )

    def create_task(
        self,
        title: str,
        session_id: str,
        due_at: datetime | None = None,
        property_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> Task:

        if not title or not title.strip():
            raise ExternalServiceError(
                "Task title cannot be empty."
            )

        if not session_id:
            raise ExternalServiceError(
                "Session ID is required."
            )

        if idempotency_key:
            existing = self._get_existing_task(
                idempotency_key
            )

            if existing:
                logger.info(
                    "Returning existing task for "
                    "idempotency key %s",
                    idempotency_key,
                )
                return existing

        task_id = self._generate_task_id(
            title=title,
            session_id=session_id,
            due_at=due_at,
            property_id=property_id,
        )

        task = Task(
            task_id=task_id,
            title=title.strip(),
            due_at=due_at,
            session_id=session_id,
            property_id=property_id,
        )

        self.tasks[task_id] = task

        if idempotency_key:
            self._save_idempotency(
                idempotency_key=idempotency_key,
                task_id=task_id,
            )

        logger.info(
            "Task created: %s",
            task_id,
        )

        return task

    def get_task(
        self,
        task_id: str,
    ) -> Task | None:
        return self.tasks.get(task_id)

    def list_tasks(
        self,
        session_id: str | None = None,
    ) -> list[Task]:

        tasks = list(self.tasks.values())

        if session_id is None:
            return tasks

        return [
            task
            for task in tasks
            if task.session_id == session_id
        ]

    def complete_task(
        self,
        task_id: str,
    ) -> Task:

        task = self.tasks.get(task_id)

        if task is None:
            raise ExternalServiceError(
                f"Task not found: {task_id}"
            )

        task.status = "COMPLETED"

        return task

    def _get_existing_task(
        self,
        idempotency_key: str,
    ) -> Task | None:

        if self.idempotency_repository:
            record = self.idempotency_repository.get(
                idempotency_key
            )

            if record and record.resource_id:
                return self.tasks.get(
                    record.resource_id
                )

        for task in self.tasks.values():
            if self._task_fingerprint(task) == idempotency_key:
                return task

        return None

    def _save_idempotency(
        self,
        idempotency_key: str,
        task_id: str,
    ) -> None:

        if not self.idempotency_repository:
            return

        self.idempotency_repository.save(
            idempotency_key=idempotency_key,
            operation="task.create_task",
            resource_id=task_id,
        )

    @staticmethod
    def _generate_task_id(
        title: str,
        session_id: str,
        due_at: datetime | None,
        property_id: str | None,
    ) -> str:

        raw = "|".join(
            [
                title.strip(),
                session_id,
                due_at.isoformat()
                if due_at
                else "",
                property_id or "",
            ]
        )

        return "task_" + hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()[:20]

    @staticmethod
    def _task_fingerprint(
        task: Task,
    ) -> str:

        raw = "|".join(
            [
                task.title,
                task.session_id,
                task.due_at.isoformat()
                if task.due_at
                else "",
                task.property_id or "",
            ]
        )

        return "task_" + hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()[:20]