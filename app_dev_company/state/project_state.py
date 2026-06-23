from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_CEO = "waiting_ceo"
    APPROVED = "approved"
    REJECTED = "rejected"
    DONE = "done"


@dataclass
class AgentTask:
    agent: str
    task_name: str
    status: TaskStatus = TaskStatus.PENDING
    output: Optional[dict] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    ceo_notes: Optional[str] = None


@dataclass
class ProjectState:
    project_id: str
    project_name: str
    description: str
    created_at: str
    phase: str = "초기화"
    tasks: dict[str, AgentTask] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    ceo_decisions: list[dict] = field(default_factory=list)
    final_approved: bool = False
