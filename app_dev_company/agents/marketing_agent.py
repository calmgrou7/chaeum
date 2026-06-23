from __future__ import annotations

from .base_agent import BaseAgent
from ..message_bus import AgentName


class MarketingAgent(BaseAgent):
    AGENT_NAME = AgentName.MARKETING
    SYSTEM_PROMPT = """당신은 앱 개발 회사의 마케팅팀 AI 에이전트입니다.

## 역할
- 앱 출시(GTM) 전략 수립
- 채널별 마케팅 캠페인 설계
- 타깃 사용자 획득 전략(UA)
- 브랜드 포지셔닝 및 메시지 개발
- 성장 지표(CAC, LTV, DAU) 목표 설정

## 작업 순서
1. read_agent_output("리서치팀") 으로 시장/경쟁 데이터 확인
2. read_agent_output("기획팀") 으로 앱 컨셉 및 타깃 확인
3. GTM 전략 및 마케팅 플랜 수립
4. 마케팅 예산이 대규모이면 request_ceo_approval 호출
5. save_output으로 결과 저장

## 결과물 형식 (save_output 호출 시)
{
  "brand_positioning": {
    "tagline": "...",
    "value_proposition": "...",
    "tone_of_voice": "..."
  },
  "target_segments": [
    {"segment": "...", "size": "...", "priority": "주요/보조"}
  ],
  "gtm_strategy": {
    "launch_phase": "...",
    "soft_launch_plan": "...",
    "full_launch_plan": "..."
  },
  "marketing_channels": [
    {"channel": "...", "budget_ratio": "...", "kpi": "...", "tactics": [...]}
  ],
  "content_strategy": {...},
  "growth_plan": {
    "month_1": {...},
    "month_3": {...},
    "month_6": {...},
    "month_12": {...}
  },
  "budget_breakdown_krw": {
    "digital_ads": 0,
    "influencer": 0,
    "content_creation": 0,
    "pr_events": 0,
    "total_monthly": 0
  },
  "unit_economics": {
    "target_cac_krw": 0,
    "estimated_ltv_krw": 0,
    "ltv_cac_ratio": 0.0
  },
  "success_metrics": [...]
}
"""

    def get_extra_tools(self) -> list[dict]:
        return [
            {
                "name": "design_gtm_strategy",
                "description": "앱 출시 전략(Go-To-Market)을 설계합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "app_category": {"type": "string"},
                        "target_users": {"type": "object"},
                        "competitors": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["app_category"],
                },
            },
            {
                "name": "plan_marketing_channels",
                "description": "효과적인 마케팅 채널 믹스를 계획합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "budget_krw": {"type": "integer"},
                        "target_demographic": {"type": "string"},
                        "app_type": {"type": "string"},
                    },
                    "required": ["app_type"],
                },
            },
            {
                "name": "estimate_unit_economics",
                "description": "CAC, LTV, ROI를 추정합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "market_size": {"type": "string"},
                        "ad_budget_monthly_krw": {"type": "integer"},
                        "app_category": {"type": "string"},
                    },
                    "required": ["app_category"],
                },
            },
        ]

    def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name in ("design_gtm_strategy", "plan_marketing_channels", "estimate_unit_economics"):
            return {
                "tool": tool_name,
                "status": "planned",
                "note": "Claude가 마케팅 전략을 수립합니다.",
                "input": tool_input,
            }
        return super().handle_tool_call(tool_name, tool_input)
