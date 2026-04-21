from __future__ import annotations

from .base_agent import BaseAgent
from ..message_bus import AgentName


class PlanningAgent(BaseAgent):
    AGENT_NAME = AgentName.PLANNING
    SYSTEM_PROMPT = """당신은 앱 개발 회사의 기획팀 AI 에이전트입니다.

## 역할
- 프로젝트 요구사항 정의 및 범위 설정
- MVP(최소 기능 제품) 기능 선별
- 마일스톤 및 로드맵 수립
- 리스크 식별 및 대응 방안 제시
- 수익 모델 설계

## 작업 순서
1. read_agent_output("리서치팀") 으로 리서치 결과 확인
2. 프로젝트 계획 수립
3. 중요한 방향 결정 시 request_ceo_approval 호출
4. save_output으로 결과 저장

## 결과물 형식 (save_output 호출 시)
{
  "project_name": "...",
  "vision": "...",
  "mvp_features": [
    {"feature": "...", "priority": "필수/선택", "description": "..."}
  ],
  "roadmap": {
    "phase1": {"name": "...", "duration_weeks": 0, "deliverables": [...]},
    "phase2": {"name": "...", "duration_weeks": 0, "deliverables": [...]},
    "phase3": {"name": "...", "duration_weeks": 0, "deliverables": [...]}
  },
  "revenue_model": {...},
  "risks": [{"risk": "...", "mitigation": "..."}],
  "success_kpis": [...],
  "total_timeline_weeks": 0
}
"""

    def get_extra_tools(self) -> list[dict]:
        return [
            {
                "name": "define_mvp_scope",
                "description": "MVP 범위를 정의하고 기능 우선순위를 결정합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "app_concept": {"type": "string"},
                        "constraints": {
                            "type": "object",
                            "description": "예산, 기간, 팀 규모 등의 제약사항",
                        },
                    },
                    "required": ["app_concept"],
                },
            },
            {
                "name": "create_roadmap",
                "description": "단계별 개발 로드맵을 생성합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "features": {"type": "array", "items": {"type": "string"}},
                        "total_weeks": {"type": "integer"},
                    },
                    "required": ["features"],
                },
            },
        ]

    def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "define_mvp_scope":
            return {
                "tool": "define_mvp_scope",
                "status": "defined",
                "note": "Claude가 MVP 범위를 분석합니다.",
                "concept": tool_input.get("app_concept"),
            }
        if tool_name == "create_roadmap":
            return {
                "tool": "create_roadmap",
                "status": "created",
                "note": "Claude가 로드맵을 생성합니다.",
            }
        return super().handle_tool_call(tool_name, tool_input)
