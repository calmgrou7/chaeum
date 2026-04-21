from __future__ import annotations

from .base_agent import BaseAgent
from ..message_bus import AgentName


class DevAgent(BaseAgent):
    AGENT_NAME = AgentName.APP_DEV
    SYSTEM_PROMPT = """당신은 앱 개발 회사의 앱개발팀 AI 에이전트입니다.

## 역할
- 기술 아키텍처 상세 설계
- API 설계 및 데이터 모델 정의
- 기능별 개발 공수 추정
- 개발 환경 및 CI/CD 파이프라인 설계
- 코드 품질 기준 수립

## 작업 순서
1. read_agent_output("총괄CTO") 또는 컨텍스트에서 CTO 지시사항 확인
2. read_agent_output("기획팀") 으로 기획 결과 확인
3. 기술 명세서 작성
4. save_output으로 결과 저장

## 결과물 형식 (save_output 호출 시)
{
  "platform": "iOS/Android/Cross-platform/Web",
  "tech_stack": {
    "frontend": "...",
    "backend": "...",
    "database": "...",
    "devops": "..."
  },
  "architecture_overview": "...",
  "api_endpoints": [
    {"method": "...", "path": "...", "description": "...", "auth_required": true}
  ],
  "data_models": [
    {"name": "...", "fields": [...], "relations": [...]}
  ],
  "feature_specs": [
    {"feature": "...", "complexity": "상/중/하", "effort_days": 0, "description": "..."}
  ],
  "dev_environment": {...},
  "cicd_pipeline": {...},
  "total_effort_days": 0,
  "recommended_team": {...}
}
"""

    def get_extra_tools(self) -> list[dict]:
        return [
            {
                "name": "design_api_architecture",
                "description": "RESTful API 아키텍처를 설계합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "features": {"type": "array", "items": {"type": "string"}},
                        "auth_type": {"type": "string", "default": "JWT"},
                    },
                    "required": ["features"],
                },
            },
            {
                "name": "estimate_development_effort",
                "description": "기능별 개발 공수를 추정합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "features": {"type": "array", "items": {"type": "string"}},
                        "team_size": {"type": "integer"},
                    },
                    "required": ["features"],
                },
            },
            {
                "name": "design_data_models",
                "description": "데이터베이스 모델을 설계합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entities": {"type": "array", "items": {"type": "string"}},
                        "db_type": {"type": "string", "default": "PostgreSQL"},
                    },
                    "required": ["entities"],
                },
            },
        ]

    def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name in ("design_api_architecture", "estimate_development_effort", "design_data_models"):
            return {
                "tool": tool_name,
                "status": "designed",
                "note": "Claude가 기술 명세를 설계합니다.",
                "input": tool_input,
            }
        return super().handle_tool_call(tool_name, tool_input)
