from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class AgentName(str, Enum):
    CEO = "CEO"
    PLANNING = "기획팀"
    RESEARCH = "리서치팀"
    MANAGEMENT = "경영팀"
    APP_DEV = "앱개발팀"
    DESIGN = "디자인팀"
    CTO = "총괄CTO"
    MARKETING = "마케팅팀"


class MessageType(str, Enum):
    TASK_REQUEST = "TASK_REQUEST"
    TASK_RESULT = "TASK_RESULT"
    CEO_APPROVAL = "CEO_APPROVAL"
    CEO_DECISION = "CEO_DECISION"
    STATUS_UPDATE = "STATUS_UPDATE"
    ESCALATION = "ESCALATION"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Message:
    sender: AgentName
    recipient: AgentName
    msg_type: MessageType
    subject: str
    content: dict[str, Any]
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    reply_to: Optional[str] = None
    priority: Priority = Priority.NORMAL
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    requires_ceo_approval: bool = False


@dataclass
class MessageBus:
    project_id: str
    _queues: dict[str, list[Message]] = field(default_factory=dict)
    _log_path: Optional[Path] = None

    def set_log_path(self, path: Path) -> None:
        self._log_path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, message: Message) -> None:
        key = message.recipient.value
        self._queues.setdefault(key, []).append(message)
        if self._log_path:
            with open(self._log_path, "a", encoding="utf-8") as f:
                record = {
                    "message_id": message.message_id,
                    "from": message.sender.value,
                    "to": message.recipient.value,
                    "type": message.msg_type.value,
                    "subject": message.subject,
                    "priority": message.priority.value,
                    "created_at": message.created_at,
                    "requires_ceo_approval": message.requires_ceo_approval,
                    "content_preview": str(message.content)[:200],
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def receive(self, agent: AgentName) -> list[Message]:
        return self._queues.pop(agent.value, [])

    def peek(self, agent: AgentName) -> list[Message]:
        return list(self._queues.get(agent.value, []))

    def has_pending_ceo_approvals(self) -> bool:
        ceo_queue = self._queues.get(AgentName.CEO.value, [])
        return any(m.requires_ceo_approval for m in ceo_queue)
