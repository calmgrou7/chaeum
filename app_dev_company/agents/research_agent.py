from __future__ import annotations

from .base_agent import BaseAgent
from ..message_bus import AgentName


class ResearchAgent(BaseAgent):
    AGENT_NAME = AgentName.RESEARCH
    SYSTEM_PROMPT = """당신은 앱 개발 회사의 리서치팀 AI 에이전트입니다.

## 역할
- 시장 규모 및 성장성 분석
- 경쟁 앱 벤치마킹
- 타깃 사용자 분석
- 트렌드 및 기술 동향 파악
- 수익화 모델 리서치

## 결과물 형식 (save_output 호출 시)
{
  "market_overview": {
    "market_name": "...",
    "market_size_krw": "...",
    "growth_rate": "...",
    "maturity": "신흥/성장/성숙"
  },
  "top_competitors": [
    {"name": "...", "features": [...], "rating": "...", "weakness": "..."}
  ],
  "target_users": {
    "primary": "...",
    "secondary": "...",
    "pain_points": [...],
    "key_needs": [...]
  },
  "trends": [...],
  "opportunity_score": 0-100,
  "key_insights": [...],
  "recommended_differentiators": [...]
}
"""

    def get_extra_tools(self) -> list[dict]:
        return [
            {
                "name": "analyze_market",
                "description": "앱 카테고리의 국내외 시장 현황을 분석합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "app_category": {"type": "string", "description": "분석할 앱 카테고리 (예: 배달, 헬스케어, 핀테크)"},
                        "region": {"type": "string", "default": "Korea", "description": "분석 대상 지역"},
                    },
                    "required": ["app_category"],
                },
            },
            {
                "name": "benchmark_competitors",
                "description": "주요 경쟁 앱의 기능, 가격, 평점을 벤치마킹합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "app_category": {"type": "string"},
                        "num_competitors": {"type": "integer", "default": 5},
                    },
                    "required": ["app_category"],
                },
            },
            {
                "name": "analyze_user_needs",
                "description": "타깃 사용자의 니즈와 페인포인트를 분석합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "app_type": {"type": "string"},
                        "target_demographic": {"type": "string"},
                    },
                    "required": ["app_type"],
                },
            },
        ]

    def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "analyze_market":
            return {
                "tool": "analyze_market",
                "status": "analyzed",
                "note": "Claude가 직접 시장 데이터를 분석하여 결과를 생성합니다.",
                "category": tool_input.get("app_category"),
            }
        if tool_name == "benchmark_competitors":
            return {
                "tool": "benchmark_competitors",
                "status": "benchmarked",
                "note": "Claude가 경쟁사 데이터를 분석하여 결과를 생성합니다.",
                "category": tool_input.get("app_category"),
            }
        if tool_name == "analyze_user_needs":
            return {
                "tool": "analyze_user_needs",
                "status": "analyzed",
                "note": "Claude가 사용자 니즈를 분석합니다.",
                "app_type": tool_input.get("app_type"),
            }
        return super().handle_tool_call(tool_name, tool_input)
