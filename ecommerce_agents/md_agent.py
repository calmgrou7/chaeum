"""
채움(Chaeum) 이커머스 멀티 에이전트 시스템 - MD(소싱팀장) 에이전트
해외 사이트 트렌드 상품 발굴, 마진 분석, 상품 기획서 작성을 담당합니다.
"""
import anthropic

from .base_agent import BaseAgent
from .tools import MD_TOOLS

# ──────────────────────────────────────────────────────────────
# MD 에이전트 시스템 프롬프트
# ──────────────────────────────────────────────────────────────
MD_SYSTEM_PROMPT = """
당신은 연 매출 100억원 규모 이커머스 쇼핑몰 **채움(Chaeum)**의 MD(소싱팀장)입니다.
10년 이상의 해외 소싱 경력을 보유하고 있으며, 트렌드를 가장 빠르게 포착하는 것으로 유명합니다.

## 회사 정보
- 회사명: 채움(Chaeum)
- 연 매출: 100억원 (월 평균 8.3억원)
- 주력 카테고리: 라이프스타일, 뷰티, 홈데코, 패션잡화, 건강/웰니스
- 고객층: 20~40대 트렌드 민감 소비자

## 나의 역할
- AliExpress, Alibaba, 1688.com, Amazon, DHgate 등 해외 플랫폼에서 상품 발굴
- 시장 트렌드 분석 및 유망 카테고리 선정
- 정확한 마진 분석 (원가 + 관세 + 배송비 + 플랫폼 수수료 포함)
- 상품별 기획서 작성 (타겟, 셀링포인트, 리스크 포함)
- MOQ(최소주문수량) 협상 및 공급업체 관리

## 소싱 기준
1. **마진율**: 순마진 45% 이상 (관세 + 플랫폼 수수료 차감 후)
2. **트렌드 점수**: 7점 이상 (10점 만점)
3. **MOQ**: 50개 이하 선호 (테스트 소싱)
4. **배송 기간**: 7~14일 이내
5. **경쟁 강도**: 낮음~중간 선호
6. **월 예상 판매**: 최소 100개 이상

## 주요 소싱 사이트 전문성
- **AliExpress**: 소량 테스트, B2C 소싱 ($1~$20)
- **Alibaba**: 대량 도매 ($3~$50, MOQ 50~500개)
- **1688.com**: 중국 내수용 도매 (최저가)
- **Amazon.com**: 글로벌 트렌드/베스트셀러 파악
- **DHgate**: 중간 규모 도매

## 환율 기준
- USD → KRW: 1 USD = 1,380 KRW
- 관세율: 카테고리별 8~13%
- 부가세: 10%

## 보고 형식
상품 기획서 제출 시 반드시 다음을 포함하세요:
1. 상품명 + 카테고리
2. 소싱처 + 원가(USD)
3. 국내 권장 판매가(KRW)
4. 마진율 계산 결과 (도구 활용)
5. 타겟 고객 + 월 예상 판매량
6. 트렌드 점수 (근거 포함)
7. 경쟁 분석 (국내 시장)
8. 핵심 셀링포인트 3가지
9. 리스크 요인 2가지

항상 한국어로 응답하고, 구체적인 수치와 근거를 제시하세요.
CEO와 마케팅팀이 의사결정을 내릴 수 있도록 충분한 정보를 제공하세요.
"""


class MDAgent(BaseAgent):
    """
    해외 소싱 MD 에이전트.
    트렌드 리서치 → 마진 분석 → 상품 기획서 작성을 수행합니다.
    """

    def __init__(
        self,
        client: anthropic.Anthropic,
        on_tool_call=None,
    ) -> None:
        super().__init__(
            client=client,
            role_name="MD(소싱팀장)",
            system_prompt=MD_SYSTEM_PROMPT,
            tools=MD_TOOLS,
            on_tool_call=on_tool_call,
        )

    def research_and_propose(self, briefing: str) -> str:
        """
        CEO의 업무지시(briefing)를 받아 해외 상품 소싱 및 기획서를 작성합니다.

        Args:
            briefing: 이번 소싱 과제에 대한 지시사항

        Returns:
            상품 기획서 (텍스트)
        """
        self.reset_history()
        prompt = f"""
[CEO 업무지시]
{briefing}

위 지시에 따라 다음 단계로 진행해주세요:

1. 먼저 **search_web** 도구로 최신 해외 트렌드 상품을 3~4개 카테고리에서 조사하세요.
   (예: "AliExpress best sellers 2024 home decor", "trending products Korea 2024", "Amazon rising products lifestyle")

2. 각 카테고리에서 유망 상품을 1~2개씩 발굴하고, **search_naver_shopping** 도구로 국내 경쟁 가격을 확인하세요.

3. 유망 상품 3~5개에 대해 **calculate_margin_analysis** 도구로 정확한 마진을 계산하세요.

4. 최종적으로 **마진율 상위 3~4개 상품**의 상품 기획서를 아래 양식으로 작성하세요:

---
## 📦 상품 기획서 [번호]: [상품명]
- **카테고리**:
- **소싱처**: (AliExpress/Alibaba 등) | **원가**: USD X.XX → KRW XXX,XXX
- **국내 판매가**: KRW X,XXX,XXX
- **마진율**: XX.X% (도구 계산 결과 기준)
- **타겟 고객**:
- **월 예상 판매량**: XXX개
- **트렌드 점수**: X/10 (근거: )
- **경쟁 강도**: 낮음/중간/높음
- **MOQ**: XX개
- **핵심 셀링포인트**:
  1.
  2.
  3.
- **리스크 요인**:
  1.
  2.
---

반드시 도구를 사용하여 실제 데이터를 기반으로 작성하세요.
"""
        return self.chat(prompt)

    def respond_to_ceo_feedback(self, ceo_feedback: str, original_proposals: str) -> str:
        """
        CEO의 피드백에 대한 수정 답변을 작성합니다.

        Args:
            ceo_feedback: CEO의 피드백 내용
            original_proposals: 원본 제안서

        Returns:
            수정된 제안서 또는 답변
        """
        prompt = f"""
[원본 상품 기획서]
{original_proposals}

[CEO 피드백]
{ceo_feedback}

CEO의 피드백을 반영하여 답변해주세요.
추가 조사가 필요하다면 도구를 활용하고, 수정된 내용을 명확히 표시해주세요.
"""
        return self.chat(prompt)
