from __future__ import annotations

from .base_agent import BaseAgent
from ..message_bus import AgentName


class ManagementAgent(BaseAgent):
    AGENT_NAME = AgentName.MANAGEMENT
    SYSTEM_PROMPT = """당신은 앱 개발 회사의 경영팀 AI 에이전트입니다.

## 역할
- 프로젝트 전체 일정 및 마일스톤 관리
- 인적 자원 배분 계획
- 예산 편성 및 비용 추정
- 리스크 관리 계획
- KPI 및 성과 지표 설정

## 작업 순서
1. read_agent_output("기획팀") 으로 기획 결과 확인
2. read_agent_output("앱개발팀") 으로 개발 공수 확인
3. read_agent_output("디자인팀") 으로 디자인 범위 확인
4. 자원 계획 및 예산 수립
5. 예산이 대규모(1억 원 이상)이면 request_ceo_approval 호출
6. save_output으로 결과 저장

## 결과물 형식 (save_output 호출 시)
{
  "team_composition": {
    "developers": {"count": 0, "roles": [...]},
    "designers": {"count": 0, "roles": [...]},
    "pm": {"count": 0},
    "qa": {"count": 0}
  },
  "project_schedule": {
    "total_weeks": 0,
    "phases": [
      {"phase": "...", "weeks": 0, "start_week": 0, "end_week": 0, "deliverables": [...]}
    ]
  },
  "budget_breakdown_krw": {
    "personnel": 0,
    "infrastructure": 0,
    "tools_licenses": 0,
    "contingency": 0,
    "total": 0
  },
  "risk_management": [
    {"risk": "...", "probability": "상/중/하", "impact": "상/중/하", "response": "..."}
  ],
  "kpis": [...],
  "critical_path": [...]
}
"""

    def get_extra_tools(self) -> list[dict]:
        return [
            {
                "name": "calculate_project_budget",
                "description": "프로젝트 전체 예산을 산정합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "team_size": {"type": "integer"},
                        "duration_weeks": {"type": "integer"},
                        "infrastructure_needs": {"type": "string"},
                    },
                    "required": ["team_size", "duration_weeks"],
                },
            },
            {
                "name": "build_project_schedule",
                "description": "프로젝트 전체 일정표를 작성합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "phases": {"type": "array", "items": {"type": "string"}},
                        "total_effort_days": {"type": "integer"},
                    },
                    "required": ["phases"],
                },
            },
        ]

    def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name in ("calculate_project_budget", "build_project_schedule"):
            return {
                "tool": tool_name,
                "status": "calculated",
                "note": "Claude가 예산 및 일정을 산정합니다.",
                "input": tool_input,
            }
        return super().handle_tool_call(tool_name, tool_input)
