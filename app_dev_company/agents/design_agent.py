from __future__ import annotations

from .base_agent import BaseAgent
from ..message_bus import AgentName


class DesignAgent(BaseAgent):
    AGENT_NAME = AgentName.DESIGN
    SYSTEM_PROMPT = """당신은 앱 개발 회사의 디자인팀 AI 에이전트입니다.

## 역할
- UI/UX 컨셉 및 정보 아키텍처 설계
- 디자인 시스템(색상, 타이포그래피, 컴포넌트) 정의
- 사용자 여정(User Journey) 설계
- 화면 흐름 및 와이어프레임 개요 작성
- 접근성 및 사용성 기준 수립

## 작업 순서
1. read_agent_output("총괄CTO") 또는 컨텍스트에서 CTO 지시사항 확인
2. read_agent_output("기획팀") 으로 기획 결과 확인
3. UX 컨셉 및 디자인 명세서 작성
4. save_output으로 결과 저장

## 결과물 형식 (save_output 호출 시)
{
  "ux_concept": "...",
  "design_principles": [...],
  "information_architecture": {
    "main_sections": [...],
    "navigation_structure": "..."
  },
  "design_system": {
    "primary_color": "#...",
    "secondary_color": "#...",
    "typography": {"heading": "...", "body": "..."},
    "key_components": [...]
  },
  "user_journeys": [
    {"persona": "...", "goal": "...", "steps": [...]}
  ],
  "key_screens": [
    {"screen_name": "...", "purpose": "...", "key_elements": [...]}
  ],
  "accessibility_standards": [...],
  "design_tools": [...]
}
"""

    def get_extra_tools(self) -> list[dict]:
        return [
            {
                "name": "create_design_system",
                "description": "앱의 디자인 시스템(색상, 타이포그래피, 컴포넌트)을 정의합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "app_category": {"type": "string"},
                        "brand_keywords": {"type": "array", "items": {"type": "string"}},
                        "target_users": {"type": "string"},
                    },
                    "required": ["app_category"],
                },
            },
            {
                "name": "map_user_journeys",
                "description": "주요 사용자 페르소나별 여정을 설계합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "features": {"type": "array", "items": {"type": "string"}},
                        "personas": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["features"],
                },
            },
            {
                "name": "define_screen_flow",
                "description": "화면 흐름 및 네비게이션 구조를 정의합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "features": {"type": "array", "items": {"type": "string"}},
                        "app_type": {"type": "string"},
                    },
                    "required": ["features"],
                },
            },
        ]

    def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name in ("create_design_system", "map_user_journeys", "define_screen_flow"):
            return {
                "tool": tool_name,
                "status": "designed",
                "note": "Claude가 디자인 명세를 작성합니다.",
                "input": tool_input,
            }
        return super().handle_tool_call(tool_name, tool_input)
