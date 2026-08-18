"""
채움(Chaeum) 이커머스 멀티 에이전트 시스템 - 데이터 모델
CEO / 마케팅팀장 / MD(소싱팀장) 에이전트가 공유하는 데이터 구조 정의
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class AgentRole(str, Enum):
    CEO = "CEO(대표이사)"
    MARKETING = "마케팅팀장"
    MD = "MD(소싱팀장)"


class MessageType(str, Enum):
    BRIEFING = "업무지시"
    PROPOSAL = "기획제안"
    APPROVAL = "승인"
    REVISION = "수정요청"
    RESPONSE = "보고"
    DISCUSSION = "협의"
    DECISION = "최종결정"


@dataclass
class AgentMessage:
    """에이전트 간 메시지"""
    sender: AgentRole
    recipient: AgentRole
    message_type: MessageType
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender.value,
            "recipient": self.recipient.value,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp,
        }


@dataclass
class ProductProposal:
    """MD 에이전트가 제안하는 상품 기획서"""
    product_name: str
    source_site: str                   # 소싱 사이트 (AliExpress, Alibaba 등)
    source_price_usd: float            # 소싱 원가 (USD)
    estimated_sell_price_krw: int      # 판매가 (KRW)
    category: str                      # 상품 카테고리
    target_customer: str               # 타겟 고객
    margin_rate: float                 # 마진율 (%)
    monthly_sales_potential: int       # 월 예상 판매 수량
    trend_score: int                   # 트렌드 점수 (1~10)
    competition_level: str             # 경쟁 강도 (낮음/중간/높음)
    sourcing_moq: int                  # 최소 주문 수량 (MOQ)
    product_description: str           # 상품 설명
    key_selling_points: List[str]      # 핵심 셀링 포인트
    risks: List[str]                   # 리스크 요인
    source_url: str = ""               # 소싱 URL

    def monthly_revenue_krw(self) -> int:
        return self.estimated_sell_price_krw * self.monthly_sales_potential

    def monthly_profit_krw(self) -> int:
        cost_krw = int(self.source_price_usd * 1380)  # 환율 적용
        return (self.estimated_sell_price_krw - cost_krw) * self.monthly_sales_potential

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_name": self.product_name,
            "source_site": self.source_site,
            "source_price_usd": self.source_price_usd,
            "source_price_krw": int(self.source_price_usd * 1380),
            "estimated_sell_price_krw": self.estimated_sell_price_krw,
            "category": self.category,
            "target_customer": self.target_customer,
            "margin_rate": self.margin_rate,
            "monthly_sales_potential": self.monthly_sales_potential,
            "monthly_revenue_krw": self.monthly_revenue_krw(),
            "monthly_profit_krw": self.monthly_profit_krw(),
            "trend_score": self.trend_score,
            "competition_level": self.competition_level,
            "sourcing_moq": self.sourcing_moq,
            "product_description": self.product_description,
            "key_selling_points": self.key_selling_points,
            "risks": self.risks,
            "source_url": self.source_url,
        }


@dataclass
class MarketingPlan:
    """마케팅팀장 에이전트가 작성하는 마케팅 기획서"""
    product_name: str
    campaign_name: str
    target_segment: str                # 타겟 세그먼트
    channels: List[str]                # 운영 채널 목록
    total_budget_krw: int              # 총 마케팅 예산
    expected_roas: float               # 기대 ROAS
    campaign_duration_days: int        # 캠페인 기간 (일)
    key_messages: List[str]            # 핵심 메시지
    instagram_strategy: str            # 인스타그램 전략
    naver_strategy: str                # 네이버 전략
    kakao_strategy: str                # 카카오 전략
    influencer_plan: str               # 인플루언서 계획
    ad_copy_main: str                  # 메인 광고 카피
    kpi_targets: Dict[str, Any]        # KPI 목표

    def expected_revenue_krw(self, product_price_krw: int) -> int:
        return int(self.total_budget_krw * self.expected_roas)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_name": self.product_name,
            "campaign_name": self.campaign_name,
            "target_segment": self.target_segment,
            "channels": self.channels,
            "total_budget_krw": self.total_budget_krw,
            "expected_roas": self.expected_roas,
            "campaign_duration_days": self.campaign_duration_days,
            "key_messages": self.key_messages,
            "instagram_strategy": self.instagram_strategy,
            "naver_strategy": self.naver_strategy,
            "kakao_strategy": self.kakao_strategy,
            "influencer_plan": self.influencer_plan,
            "ad_copy_main": self.ad_copy_main,
            "kpi_targets": self.kpi_targets,
        }


@dataclass
class BusinessPlan:
    """CEO 에이전트가 최종 승인하는 사업 계획서"""
    title: str
    quarter: str                           # 분기 (예: 2024 Q2)
    approved_products: List[str]           # 승인된 상품 목록
    rejected_products: List[str]           # 반려된 상품 목록
    total_investment_krw: int              # 총 투자액
    expected_monthly_revenue_krw: int      # 예상 월 매출
    expected_monthly_profit_krw: int       # 예상 월 순이익
    launch_timeline: str                   # 론칭 일정
    strategic_rationale: str              # 전략적 근거
    kpi_targets: Dict[str, Any]           # KPI 목표
    action_items: List[Dict[str, str]]    # 실행 과제 목록
    risks_and_mitigations: List[Dict[str, str]]  # 리스크 및 대응 방안

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "quarter": self.quarter,
            "approved_products": self.approved_products,
            "rejected_products": self.rejected_products,
            "total_investment_krw": self.total_investment_krw,
            "expected_monthly_revenue_krw": self.expected_monthly_revenue_krw,
            "expected_monthly_profit_krw": self.expected_monthly_profit_krw,
            "launch_timeline": self.launch_timeline,
            "strategic_rationale": self.strategic_rationale,
            "kpi_targets": self.kpi_targets,
            "action_items": self.action_items,
            "risks_and_mitigations": self.risks_and_mitigations,
        }


@dataclass
class AgentSession:
    """에이전트 세션 전체 상태"""
    session_id: str
    started_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    topic: str = ""                                      # 이번 세션 주제
    messages: List[AgentMessage] = field(default_factory=list)
    product_proposals: List[ProductProposal] = field(default_factory=list)
    marketing_plans: List[MarketingPlan] = field(default_factory=list)
    business_plan: Optional[BusinessPlan] = None

    def add_message(self, msg: AgentMessage) -> None:
        self.messages.append(msg)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "topic": self.topic,
            "messages": [m.to_dict() for m in self.messages],
            "product_proposals": [p.to_dict() for p in self.product_proposals],
            "marketing_plans": [mp.to_dict() for mp in self.marketing_plans],
            "business_plan": self.business_plan.to_dict() if self.business_plan else None,
        }
