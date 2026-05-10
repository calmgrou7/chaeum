from __future__ import annotations

import json
import os
from typing import Any, Optional

import anthropic

from ..message_bus import AgentName, Message, MessageBus, MessageType, Priority
from ..state.project_state import ProjectState, TaskStatus
from ..state.state_store import StateStore

# ---------------------------------------------------------------------------
# Shared tool schemas (available to every agent)
# ---------------------------------------------------------------------------

SHARED_TOOLS: list[dict] = [
    {
        "name": "send_message_to_agent",
        "description": "다른 에이전트에게 메시지나 작업 요청을 보냅니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "recipient": {
                    "type": "string",
                    "enum": [n.value for n in AgentName if n != AgentName.CEO],
                    "description": "수신 에이전트 이름",
                },
                "subject": {"type": "string", "description": "메시지 제목"},
                "content": {"type": "object", "description": "메시지 본문 (구조화 JSON)"},
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "critical"],
                    "default": "normal",
                },
            },
            "required": ["recipient", "subject", "content"],
        },
    },
    {
        "name": "read_agent_output",
        "description": "다른 에이전트가 저장한 결과물을 읽습니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "enum": [n.value for n in AgentName if n != AgentName.CEO],
                    "description": "읽을 에이전트 이름",
                }
            },
            "required": ["agent_name"],
        },
    },
    {
        "name": "request_ceo_approval",
        "description": "중요한 결정사항을 CEO에게 승인 요청합니다. 주요 예산·방향전환·출시 결정 시 사용.",
        "input_schema": {
            "type": "object",
            "properties": {
                "proposal_title": {"type": "string", "description": "승인 안건 제목"},
                "proposal_summary": {
                    "type": "string",
                    "description": "CEO가 빠르게 이해할 수 있는 요약 (3줄 이내)",
                },
                "details": {"type": "object", "description": "세부 내용"},
            },
            "required": ["proposal_title", "proposal_summary", "details"],
        },
    },
    {
        "name": "save_output",
        "description": "현재 에이전트의 최종 결과물을 저장합니다. 작업 완료 시 반드시 호출하세요.",
        "input_schema": {
            "type": "object",
            "properties": {
                "output": {"type": "object", "description": "저장할 결과 JSON"},
            },
            "required": ["output"],
        },
    },
]


class BaseAgent:
    """
    모든 부서 에이전트의 기반 클래스.
    Claude API tool_use 루프를 관리하고 공통 도구를 제공한다.
    """

    AGENT_NAME: AgentName = AgentName.CEO  # 서브클래스에서 override
    MODEL: str = "claude-sonnet-4-6"
    MAX_ITERATIONS: int = 12
    SYSTEM_PROMPT: str = ""  # 서브클래스에서 override

    def __init__(
        self,
        bus: MessageBus,
        state: ProjectState,
        store: StateStore,
        api_key: str = "",
    ):
        self.bus = bus
        self.state = state
        self.store = store
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY", ""))
        self._final_output: Optional[dict] = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, task_description: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        print(f"\n{'─'*50}")
        print(f"[{self.AGENT_NAME.value}] 작업 시작")
        print(f"  └ {task_description[:80]}")

        self._final_output = None
        system_prompt = self._build_system_prompt()
        history: list[dict] = [
            {"role": "user", "content": self._build_initial_message(task_description, context or {})}
        ]

        for iteration in range(self.MAX_ITERATIONS):
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=4096,
                system=system_prompt,
                tools=self._all_tools(),
                messages=history,
            )

            history.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                # If save_output was never called, try one more forced call
                if self._final_output is None:
                    history.append({
                        "role": "user",
                        "content": (
                            "아직 save_output 도구를 호출하지 않았습니다. "
                            "지금 바로 위에서 작성한 분석 결과 전체를 "
                            "save_output 도구의 output 파라미터에 JSON 형태로 담아 호출하세요. "
                            "반드시 save_output 도구 호출로만 응답하세요."
                        ),
                    })
                    continue
                break

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"  [{self.AGENT_NAME.value}] 도구: {block.name}")
                        result = self._dispatch_tool(block.name, block.input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result, ensure_ascii=False),
                            }
                        )
                history.append({"role": "user", "content": tool_results})
                continue

            break

        result = self._final_output or {"status": "complete", "agent": self.AGENT_NAME.value}
        print(f"  [{self.AGENT_NAME.value}] 완료 (output={'저장됨' if self._final_output else '없음'})")
        return result

    # ------------------------------------------------------------------
    # Tool dispatch
    # ------------------------------------------------------------------

    def _dispatch_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "send_message_to_agent":
            return self._tool_send_message(**tool_input)
        if tool_name == "read_agent_output":
            return self._tool_read_agent_output(**tool_input)
        if tool_name == "request_ceo_approval":
            return self._tool_request_ceo_approval(**tool_input)
        if tool_name == "save_output":
            return self._tool_save_output(**tool_input)
        return self.handle_tool_call(tool_name, tool_input)

    def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        """서브클래스에서 에이전트별 도구를 구현."""
        return {"error": f"알 수 없는 도구: {tool_name}"}

    # ------------------------------------------------------------------
    # Shared tool implementations
    # ------------------------------------------------------------------

    def _tool_send_message(
        self,
        recipient: str,
        subject: str,
        content: dict,
        priority: str = "normal",
        **_: Any,
    ) -> dict:
        try:
            recipient_enum = AgentName(recipient)
        except ValueError:
            return {"error": f"알 수 없는 수신자: {recipient}"}

        msg = Message(
            sender=self.AGENT_NAME,
            recipient=recipient_enum,
            msg_type=MessageType.TASK_REQUEST,
            subject=subject,
            content=content,
            priority=Priority(priority),
        )
        self.bus.send(msg)
        return {"sent": True, "message_id": msg.message_id, "to": recipient}

    def _tool_read_agent_output(self, agent_name: str, **_: Any) -> dict:
        output = self.store.load_agent_output(self.state.project_id, agent_name)
        if output is None:
            return {"available": False, "message": f"{agent_name}의 결과가 아직 없습니다."}
        return {"available": True, "output": output}

    def _tool_request_ceo_approval(
        self,
        proposal_title: str,
        proposal_summary: str,
        details: dict,
        **_: Any,
    ) -> dict:
        msg = Message(
            sender=self.AGENT_NAME,
            recipient=AgentName.CEO,
            msg_type=MessageType.CEO_APPROVAL,
            subject=proposal_title,
            content={"summary": proposal_summary, "details": details},
            priority=Priority.CRITICAL,
            requires_ceo_approval=True,
        )
        self.bus.send(msg)
        return {"queued_for_ceo": True, "message_id": msg.message_id}

    def _tool_save_output(self, output: dict, **_: Any) -> dict:
        self._final_output = output
        path = self.store.save_agent_output(self.state.project_id, self.AGENT_NAME.value, output)
        return {"saved": True, "path": str(path)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _all_tools(self) -> list[dict]:
        return SHARED_TOOLS + self.get_extra_tools()

    def get_extra_tools(self) -> list[dict]:
        """서브클래스에서 에이전트 전용 도구를 반환."""
        return []

    def _build_system_prompt(self) -> str:
        return (
            f"당신은 '{self.AGENT_NAME.value}' 역할을 담당하는 AI 에이전트입니다.\n"
            f"현재 프로젝트: {self.state.project_name}\n"
            f"현재 단계: {self.state.phase}\n\n"
            f"{self.SYSTEM_PROMPT}\n\n"
            "## 필수 규칙 (반드시 준수)\n"
            "1. 작업을 마친 후 **반드시** 'save_output' 도구를 호출해야 합니다.\n"
            "   save_output 없이 대화를 끝내면 작업 결과가 유실됩니다.\n"
            "   save_output이 성공적으로 호출된 후에만 작업이 완료된 것입니다.\n"
            "2. 주요 예산·방향 결정 시 'request_ceo_approval' 도구를 사용하세요.\n"
            "3. 다른 팀의 결과가 필요하면 'read_agent_output' 도구를 사용하세요.\n"
            "4. 모든 응답은 한국어로 작성하세요.\n\n"
            "## save_output 호출 방법\n"
            "분석과 계획을 모두 완료한 후, 마지막 행동으로 반드시 save_output을 호출하세요:\n"
            "  save_output(output={결과 JSON})\n"
            "텍스트 응답만 하고 save_output을 빠뜨리면 안 됩니다.\n"
        )

    def _build_initial_message(self, task: str, context: dict) -> str:
        parts = [f"## 작업 지시\n{task}"]
        if context:
            parts.append(f"\n## 추가 컨텍스트\n{json.dumps(context, ensure_ascii=False, indent=2)}")
        parts.append(
            "\n## 완료 기준\n"
            "위 작업을 모두 수행한 뒤, **마지막 단계로 반드시 save_output 도구를 호출**하여 "
            "결과 JSON을 저장하세요. save_output 호출 없이 작업을 종료하면 결과가 사라집니다."
        )
        return "\n".join(parts)
