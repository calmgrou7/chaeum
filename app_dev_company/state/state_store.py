from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .project_state import AgentTask, ProjectState, TaskStatus


class StateStore:
    def __init__(self, base_dir: Path = Path("results/projects")):
        self.base_dir = base_dir

    def _project_dir(self, project_id: str) -> Path:
        return self.base_dir / project_id

    def _state_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "state.json"

    def _output_path(self, project_id: str, agent_name: str) -> Path:
        safe_name = agent_name.replace("/", "_")
        return self._project_dir(project_id) / "outputs" / f"{safe_name}.json"

    def save(self, state: ProjectState) -> None:
        path = self._state_path(state.project_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        def _serialize(obj: Any) -> Any:
            if isinstance(obj, AgentTask):
                return {
                    "agent": obj.agent,
                    "task_name": obj.task_name,
                    "status": obj.status.value if isinstance(obj.status, TaskStatus) else obj.status,
                    "output": obj.output,
                    "error": obj.error,
                    "started_at": obj.started_at,
                    "completed_at": obj.completed_at,
                    "ceo_notes": obj.ceo_notes,
                }
            return obj

        payload = {
            "project_id": state.project_id,
            "project_name": state.project_name,
            "description": state.description,
            "created_at": state.created_at,
            "phase": state.phase,
            "final_approved": state.final_approved,
            "tasks": {k: _serialize(v) for k, v in state.tasks.items()},
            "ceo_decisions": state.ceo_decisions,
            "updated_at": datetime.now().isoformat(),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, project_id: str) -> Optional[ProjectState]:
        path = self._state_path(project_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        tasks = {}
        for k, v in data.get("tasks", {}).items():
            tasks[k] = AgentTask(
                agent=v["agent"],
                task_name=v["task_name"],
                status=TaskStatus(v["status"]),
                output=v.get("output"),
                error=v.get("error"),
                started_at=v.get("started_at"),
                completed_at=v.get("completed_at"),
                ceo_notes=v.get("ceo_notes"),
            )
        return ProjectState(
            project_id=data["project_id"],
            project_name=data["project_name"],
            description=data["description"],
            created_at=data["created_at"],
            phase=data.get("phase", "초기화"),
            tasks=tasks,
            ceo_decisions=data.get("ceo_decisions", []),
            final_approved=data.get("final_approved", False),
        )

    def list_projects(self) -> list[str]:
        if not self.base_dir.exists():
            return []
        return [d.name for d in self.base_dir.iterdir() if d.is_dir()]

    def save_agent_output(self, project_id: str, agent_name: str, output: Any) -> Path:
        path = self._output_path(project_id, agent_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load_agent_output(self, project_id: str, agent_name: str) -> Optional[Any]:
        path = self._output_path(project_id, agent_name)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
