from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    priority: Priority = Priority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    metadata: dict = field(default_factory=dict)

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING

    def mark_completed(self) -> None:
        self.status = TaskStatus.COMPLETED

    def mark_failed(self) -> None:
        self.status = TaskStatus.FAILED
