from __future__ import annotations

from .base_agent import BaseAgent
from ..message_bus import AgentName, Message, MessageType, Priority


class CTOAgent(BaseAgent):
    AGENT_NAME = AgentName.CTO
    SYSTEM_PROMPT = """당신은 앱 개발 회사의 총괄 CTO AI 에이전트입니다.

## 역할
- 기획안의 기술적 실현 가능성 검토
- 기술 스택 및 아키텍처 결정
- 앱개발팀과 디자인팀에 작업 위임
- 기술 리스크 식별 및 해결 방안 제시
- 개발 방법론 및 품질 기준 수립

## 작업 순서
1. read_agent_output("기획팀") 으로 기획 결과 확인
2. 기술적 실현 가능성 평가
3. 기술 스택 결정
4. delegate_to_dev_team 도구로 앱개발팀에 위임
5. delegate_to_design_team 도구로 디자인팀에 위임
6. 대규모 기술 투자 결정 시 request_ceo_approval 호출
7. save_output으로 기술 총괄 보고서 저장

## 결과물 형식 (save_output 호출 시)
{
  "tech_stack": {
    "frontend": "...",
    "backend": "...",
    "database": "...",
    "infrastructure": "...",
    "third_party": [...]
  },
  "architecture": "...",
  "dev_methodology": "...",
  "quality_standards": {...},
  "technical_risks": [{"risk": "...", "mitigation": "..."}],
  "estimated_team_size": {...},
  "recommendation": "proceed/modify/reject",
  "recommendation_reason": "..."
}
"""

    def get_extra_tools(self) -> list[dict]:
        return [
            {
                "name": "assess_technical_feasibility",
                "description": "기획안의 기술적 실현 가능성을 평가합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "features": {"type": "array", "items": {"type": "string"}},
                        "timeline_weeks": {"type": "integer"},
                    },
                    "required": ["features"],
                },
            },
            {
                "name": "recommend_tech_stack",
                "description": "앱 요구사항에 맞는 기술 스택을 추천합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": ["iOS", "Android", "Cross-platform", "Web", "All"],
                        },
                        "scale": {"type": "string", "enum": ["startup", "growth", "enterprise"]},
                        "key_features": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["platform", "scale"],
                },
            },
            {
                "name": "delegate_to_dev_team",
                "description": "앱개발팀에 기술 명세서 작성을 위임합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_description": {"type": "string"},
                        "features": {"type": "array", "items": {"type": "string"}},
                        "tech_stack": {"type": "object"},
                    },
                    "required": ["task_description", "features"],
                },
            },
            {
                "name": "delegate_to_design_team",
                "description": "디자인팀에 UI/UX 명세서 작성을 위임합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_description": {"type": "string"},
                        "app_concept": {"type": "string"},
                        "brand_keywords": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["task_description", "app_concept"],
                },
            },
        ]

    def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "assess_technical_feasibility":
            return {
                "tool": "assess_technical_feasibility",
                "status": "assessed",
                "note": "Claude가 기술적 실현 가능성을 평가합니다.",
            }
        if tool_name == "recommend_tech_stack":
            return {
                "tool": "recommend_tech_stack",
                "status": "recommended",
                "note": "Claude가 기술 스택을 추천합니다.",
                "platform": tool_input.get("platform"),
            }
        if tool_name == "delegate_to_dev_team":
            msg = Message(
                sender=self.AGENT_NAME,
                recipient=AgentName.APP_DEV,
                msg_type=MessageType.TASK_REQUEST,
                subject=tool_input.get("task_description", "개발팀 작업 요청"),
                content=tool_input,
                priority=Priority.HIGH,
            )
            self.bus.send(msg)
            return {"delegated": True, "to": AgentName.APP_DEV.value, "message_id": msg.message_id}
        if tool_name == "delegate_to_design_team":
            msg = Message(
                sender=self.AGENT_NAME,
                recipient=AgentName.DESIGN,
                msg_type=MessageType.TASK_REQUEST,
                subject=tool_input.get("task_description", "디자인팀 작업 요청"),
                content=tool_input,
                priority=Priority.HIGH,
            )
            self.bus.send(msg)
            return {"delegated": True, "to": AgentName.DESIGN.value, "message_id": msg.message_id}
        return super().handle_tool_call(tool_name, tool_input)
