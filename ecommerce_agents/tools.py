"""
채움(Chaeum) 이커머스 멀티 에이전트 시스템 - 공유 도구 모음
각 에이전트가 Claude tool_use로 호출하는 함수들과 스키마 정의
"""
import json
import time
import requests
from bs4 import BeautifulSoup
from typing import Any
from urllib.parse import quote


# ──────────────────────────────────────────────────────────────
# 1. 실제 실행 함수 (Python)
# ──────────────────────────────────────────────────────────────

def search_web(query: str, num_results: int = 6) -> list[dict]:
    """DuckDuckGo HTML 검색으로 웹 결과를 가져옵니다."""
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}&kl=kr-kr"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for r in soup.select(".result__body")[:num_results]:
            title_el = r.select_one(".result__title")
            snippet_el = r.select_one(".result__snippet")
            url_el = r.select_one(".result__url")
            results.append({
                "title": title_el.get_text(strip=True) if title_el else "",
                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                "url": url_el.get_text(strip=True) if url_el else "",
            })
        return results if results else [{"info": "검색 결과 없음. Claude 자체 지식을 활용하세요."}]
    except Exception as e:
        return [{"error": f"웹 검색 실패: {e}. Claude 자체 지식을 활용하세요."}]


def search_naver_shopping(query: str, num_results: int = 5) -> list[dict]:
    """네이버 쇼핑에서 국내 시장 가격 정보를 조회합니다."""
    url = f"https://search.shopping.naver.com/search/all?query={quote(query)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://shopping.naver.com/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        # 상품 카드 파싱 (네이버 쇼핑 구조)
        items = soup.select("div.adProduct_item__1Uy1K, div.product_item__MDtDF")[:num_results]
        for item in items:
            name_el = item.select_one(".product_title__mstw4, .adProduct_title__XLZCK")
            price_el = item.select_one(".price_num__S2p_v, .adProduct_price__1T7ej")
            mall_el = item.select_one(".product_mall_title__1SHaw, .adProduct_mall__title")
            results.append({
                "name": name_el.get_text(strip=True) if name_el else "",
                "price": price_el.get_text(strip=True) if price_el else "",
                "mall": mall_el.get_text(strip=True) if mall_el else "",
            })

        if not results:
            # 구조 변경 대비 fallback
            return [{
                "info": f"네이버 쇼핑에서 '{query}' 검색 결과를 파싱하지 못했습니다. "
                        "Claude 자체 시장 지식을 활용하세요."
            }]
        return results
    except Exception as e:
        return [{"error": f"네이버 쇼핑 조회 실패: {e}"}]


def calculate_margin_analysis(
    source_price_usd: float,
    sell_price_krw: int,
    intl_shipping_krw: int = 6000,
    domestic_shipping_krw: int = 3500,
    packaging_cost_krw: int = 2000,
    return_rate_pct: float = 3.0,
    customs_rate_pct: float = 8.0,
    platform_fee_pct: float = 10.0,
    exchange_rate: float = 1380.0,
    customs_threshold_usd: float = 150.0,
) -> dict:
    """
    해외 소싱 원가(USD) → 국내 판매가(KRW) 기준 현실적인 마진을 계산합니다.

    비용 항목:
      - 해외→한국 국제 배송비 (intl_shipping_krw)
      - 관세: CIF 기준, $150 이하 목록통관 시 면제
      - 부가세: 10% (과세표준+관세 기준), 목록통관 시 면제
      - 국내 택배비 (domestic_shipping_krw)
      - 포장재비 (packaging_cost_krw)
      - 반품 충당금 (return_rate_pct % of 판매가)
      - 플랫폼 수수료 (platform_fee_pct % of 판매가)
    """
    source_price_krw = source_price_usd * exchange_rate
    cif_value_krw = source_price_krw + intl_shipping_krw  # CIF = 상품가 + 국제배송비

    # 목록통관 여부: 상품 소싱가 $150 이하이면 관세+부가세 면제
    is_customs_exempt = source_price_usd <= customs_threshold_usd
    customs_fee_krw = 0 if is_customs_exempt else round(cif_value_krw * customs_rate_pct / 100)
    vat_fee_krw = 0 if is_customs_exempt else round((cif_value_krw + customs_fee_krw) * 0.10)

    total_landed_cost_krw = (
        source_price_krw
        + intl_shipping_krw
        + customs_fee_krw
        + vat_fee_krw
        + domestic_shipping_krw
        + packaging_cost_krw
    )

    platform_fee_krw = round(sell_price_krw * platform_fee_pct / 100)
    return_reserve_krw = round(sell_price_krw * return_rate_pct / 100)
    net_revenue_krw = sell_price_krw - platform_fee_krw - return_reserve_krw

    profit_krw = net_revenue_krw - total_landed_cost_krw
    margin_rate = (profit_krw / sell_price_krw * 100) if sell_price_krw > 0 else 0

    # 마진 개선 팁
    tips = []
    if is_customs_exempt:
        tips.append("✅ 목록통관 적용 중 ($150 이하) — 관세+부가세 면제로 마진 유리")
    else:
        tips.append(f"⚠️ 일반통관 적용 ($150 초과) — 관세 {customs_fee_krw:,}원 + 부가세 {vat_fee_krw:,}원 발생")
        tips.append("💡 건당 $150 이하로 소량 분할 배송 시 관세 절감 가능")
    if intl_shipping_krw > 4000:
        tips.append("💡 Alibaba 해상 대량 소싱(50개+) 시 국제배송비 개당 1,500~2,000원으로 절감 가능")
    if margin_rate < 25:
        tips.append("💡 판매가 인상 또는 1688 구매대행으로 원가 절감 검토 필요")

    return {
        "source_price_usd": source_price_usd,
        "exchange_rate": exchange_rate,
        "source_price_krw": round(source_price_krw),
        "intl_shipping_krw": intl_shipping_krw,
        "cif_value_krw": round(cif_value_krw),
        "customs_exempt": is_customs_exempt,
        "customs_exempt_reason": f"소싱가 ${source_price_usd} ≤ $150 목록통관 면세" if is_customs_exempt else f"소싱가 ${source_price_usd} > $150 일반통관",
        "customs_fee_krw": customs_fee_krw,
        "vat_fee_krw": vat_fee_krw,
        "domestic_shipping_krw": domestic_shipping_krw,
        "packaging_cost_krw": packaging_cost_krw,
        "total_landed_cost_krw": round(total_landed_cost_krw),
        "sell_price_krw": sell_price_krw,
        "platform_fee_krw": platform_fee_krw,
        "return_reserve_krw": return_reserve_krw,
        "net_revenue_krw": net_revenue_krw,
        "profit_per_unit_krw": round(profit_krw),
        "margin_rate_pct": round(margin_rate, 1),
        "break_even_units_per_month": max(1, round(50000 / profit_krw)) if profit_krw > 0 else 9999,
        "analysis": (
            "✅ 우수 마진" if margin_rate >= 35 else
            "✅ 양호 마진" if margin_rate >= 25 else
            "⚠️ 보통 마진" if margin_rate >= 15 else
            "❌ 낮은 마진 - 소싱가/판매가 재검토 필요"
        ),
        "sourcing_tips": tips,
    }


def get_sourcing_site_info(site: str = "all") -> dict:
    """
    해외 소싱 플랫폼별 수수료·절차·배송비·관세 정보를 반환합니다.
    site: "aliexpress" | "alibaba" | "1688" | "dhgate" | "korean_customs" | "all"
    """
    data = {
        "aliexpress": {
            "name": "AliExpress (알리익스프레스)",
            "best_for": "소량 테스트 (1~50개), 빠른 시작",
            "buyer_fee_pct": 0,
            "seller_commission_pct": "3.3~8.8% (2025.2 신설, 판매가에 반영됨)",
            "payment_methods": ["신용카드 (수수료 없음)", "페이팔"],
            "shipping_to_korea": {
                "small_under_500g": "4,000~8,000원/개 (AliExpress 표준 배송)",
                "medium_500g_1kg": "7,000~13,000원/개",
                "delivery_days": "7~20일 (표준), 3~7일 (급행 DHL/FedEx)",
                "tip": "에어패킷(ePacket) 이용 시 소형 4,000~6,000원, 7~15일",
            },
            "customs_strategy": "건당 $150 이하 목록통관 → 관세+부가세 면제. 소량 테스트에 최적",
            "moq": "1개~",
            "pros": ["가입 즉시 구매 가능", "소량 테스트", "다양한 공급업체", "목록통관 활용 용이"],
            "cons": ["판매자 수수료 인상으로 가격 상승", "품질 편차 큼", "대량 시 단가 불리"],
            "sourcing_procedure": [
                "1. AliExpress 가입 (무료)",
                "2. 상품 검색 → 공급업체 리뷰/별점 확인 (4.5★ 이상 권장)",
                "3. 샘플 1~3개 주문 (배송비 포함 가격 확인)",
                "4. 수령 후 품질 검수",
                "5. 합격 시 20~50개 재주문, 국내 판매 시작",
            ],
        },
        "alibaba": {
            "name": "Alibaba.com (알리바바)",
            "best_for": "대량 소싱 (100개+), 가격 협상, OEM",
            "buyer_fee_pct": 0,
            "payment_methods": ["T/T 전신환 (수수료 $20~50 고정)", "신용카드 (3%)", "Trade Assurance (안전결제)"],
            "shipping_to_korea": {
                "sea_lcl_per_unit": "1,000~3,000원/개 (100개+ 묶음 해상)",
                "sea_fcl_20gp": "$459~661 USD (컨테이너 전체)",
                "air_per_kg": "$1.73/kg (1,000kg+), 소형 개당 2,000~5,000원",
                "delivery_days": "해상 7~14일, 항공 3~4일",
            },
            "customs_strategy": "대량 소싱 → 일반통관 (관세 8% CIF + 부가세 10%). 단가 낮아 전체 마진은 유리",
            "moq": "50~500개 (협상 가능)",
            "pros": ["최저 단가", "OEM/ODM 가능", "Trade Assurance 보호", "직접 공장과 거래"],
            "cons": ["T/T 이체 수수료", "대량 초기 투자 필요", "리드타임 2~4주", "샘플비 발생"],
            "sourcing_procedure": [
                "1. Alibaba 가입 → 상품 검색",
                "2. 공급업체 Verified/Gold Supplier 필터 적용",
                "3. 샘플 요청 (샘플비 $10~50 + 배송비)",
                "4. 가격 협상: MOQ 낮추기, 단가 인하, 포장 조건 협의",
                "5. Trade Assurance로 결제 (안전결제)",
                "6. 생산 2~4주 → 선적 → 한국 통관 → 입고",
            ],
        },
        "1688": {
            "name": "1688.com (중국 내수 도매)",
            "best_for": "중소량 (20~200개), 최저가 소싱, 다양한 품목",
            "buyer_fee_pct": 0,
            "agent_fee_pct": "5~10% (구매대행 수수료, 일부 1.3%~)",
            "payment_methods": ["알리페이 (중국 계정 필요 → 대행사 통해 처리)"],
            "shipping_to_korea": {
                "china_domestic": "2,000~4,000원/개 (1688 → 포워딩 창고)",
                "air_forwarding": "25,000~40,000원/kg (항공 포워딩)",
                "sea_forwarding": "8,000~15,000원/kg (해상 포워딩)",
                "delivery_days": "항공 7~12일, 해상 12~20일",
                "tip": "소형 경량 상품은 항공이 현실적. kg당 계산되므로 무거운 상품은 해상 권장",
            },
            "customs_strategy": "건당 $150 이하로 포장 조절 시 목록통관 가능. 대행사와 협의 필요",
            "moq": "1개~ (단, 대행 수수료로 소량 비효율, 20개+ 권장)",
            "pros": ["중국 내 최저가", "AliExpress 대비 30~50% 저렴", "다양한 공급업체"],
            "cons": ["중국어 필수 (대행사 이용)", "대행 수수료 발생", "포워딩 복잡", "품질 편차"],
            "sourcing_procedure": [
                "1. 한국 구매대행사 선택 (키위커머스, 중판, 희명무역 등)",
                "2. 대행사 사이트에서 1688 URL 또는 상품명으로 검색",
                "3. 구매 요청 → 대행사가 알리페이로 결제 (대행료 5~10%)",
                "4. 중국 내 창고 집화 (1~3일)",
                "5. 포워딩 신청 → 항공/해상 선택",
                "6. 한국 통관 → 수령",
            ],
        },
        "dhgate": {
            "name": "DHgate (디에이치게이트)",
            "best_for": "소~중량 도매 (10~200개), 빠른 배송",
            "buyer_fee_pct": 0,
            "payment_methods": ["신용카드 (2~3%)", "페이팔", "에스크로"],
            "shipping_to_korea": {
                "small_under_500g": "4,000~7,000원/개",
                "medium_500g_1kg": "7,000~12,000원/개",
                "delivery_days": "7~15일",
            },
            "customs_strategy": "AliExpress와 유사. $150 이하 목록통관 활용",
            "moq": "1개~ (소량 가능)",
            "pros": ["AliExpress보다 저렴한 경우 많음", "빠른 배송", "에스크로 보호"],
            "cons": ["공급업체 신뢰도 편차", "카드 수수료 2~3%", "AS 어려움"],
            "sourcing_procedure": [
                "1. DHgate 가입 → 상품 검색",
                "2. 셀러 평점/거래량 확인",
                "3. 소량 주문 → 품질 확인",
                "4. 대량 주문 시 셀러에 직접 할인 요청",
            ],
        },
        "korean_customs": {
            "name": "한국 관세 규정 (수입 시)",
            "목록통관_면세": {
                "기준": "건당 미화 $150 이하 (미국발은 $200)",
                "계산_기준": "상품가 기준 (국제 배송비 제외)",
                "면제_항목": "관세 + 부가세 전액 면제",
                "주의": "재고 소싱 목적은 면세 범위 논란 있으므로 소량 분할 배송 권장",
            },
            "일반통관": {
                "기준": "$150 초과",
                "관세": "CIF 기준 × 세율 (홈데코/세라믹 HS6912~6913: 8%)",
                "부가세": "(CIF + 관세) × 10%",
                "계산_예시": "상품 $50 + 배송 $10 = CIF $60 → 관세 $4.8 + 부가세 $6.48",
            },
            "hs_codes": {
                "세라믹 캔들홀더": "HS 6912.00 / 6913.10 → 관세 8%",
                "대리석 트레이": "HS 6802.99 (천연석) 또는 6913.90 → 관세 8%",
                "초음파 디퓨저": "HS 8509.80 (가전기기) → KC 인증 필수, 관세 8%",
                "LED 무드등": "HS 8513.10 (조명기기) → KC + UN38.3 인증 필수, 관세 8%",
            },
            "인증_필수_품목": {
                "전자기기/전기제품": "KC 인증 (전기용품 및 생활용품 안전관리법)",
                "배터리_포함": "UN38.3 인증 추가 필요",
                "화장품": "식약처 수입 신고",
            },
        },
    }

    if site == "all":
        return {
            "comparison": {
                "platform": ["AliExpress", "1688+대행", "Alibaba", "DHgate"],
                "best_for": ["소량 테스트", "중소량 최저가", "대량 OEM", "소~중량 도매"],
                "moq": ["1개~", "20개+ 권장", "50~500개", "1개~"],
                "intl_shipping_per_unit_krw": ["4,000~8,000", "6,000~15,000", "1,000~3,000(해상)", "4,000~7,000"],
                "customs_advantage": ["목록통관 용이", "조건부 가능", "일반통관", "목록통관 용이"],
                "sourcing_cost_vs_aliexpress": ["기준", "-30~50% 저렴", "-40~60% 저렴(대량)", "-10~20% 저렴"],
            },
            "recommendation": (
                "1단계 테스트: AliExpress 또는 DHgate로 소량(10~30개) 주문, 품질/수요 확인\n"
                "2단계 확장: 1688 구매대행으로 전환, 원가 절감\n"
                "3단계 스케일업: Alibaba 직거래 + 해상 대량 소싱, OEM 패키지 적용"
            ),
            **data,
        }

    return data.get(site, {"error": f"알 수 없는 플랫폼: {site}. aliexpress/alibaba/1688/dhgate/korean_customs/all 중 선택"})


def calculate_marketing_roi(
    marketing_budget_krw: int,
    product_price_krw: int,
    expected_roas: float = 3.5,
    platform_fee_pct: float = 10.0,
) -> dict:
    """마케팅 예산 대비 예상 매출/수익을 계산합니다."""
    expected_revenue_krw = int(marketing_budget_krw * expected_roas)
    expected_units_sold = expected_revenue_krw // product_price_krw
    platform_fee = int(expected_revenue_krw * platform_fee_pct / 100)
    net_revenue = expected_revenue_krw - platform_fee
    roi = ((net_revenue - marketing_budget_krw) / marketing_budget_krw) * 100

    return {
        "marketing_budget_krw": marketing_budget_krw,
        "expected_roas": expected_roas,
        "expected_revenue_krw": expected_revenue_krw,
        "expected_units_sold": expected_units_sold,
        "platform_fee_krw": platform_fee,
        "net_revenue_krw": net_revenue,
        "marketing_roi_pct": round(roi, 1),
        "cpa_krw": round(marketing_budget_krw / max(1, expected_units_sold)),
        "assessment": (
            "✅ 우수한 마케팅 효율" if roi >= 200 else
            "✅ 양호한 마케팅 효율" if roi >= 100 else
            "⚠️ 보통 효율 - 최적화 필요" if roi >= 50 else
            "❌ 낮은 효율 - 전략 재검토"
        ),
    }


def evaluate_business_metrics(
    monthly_revenue_krw: int,
    monthly_cost_krw: int,
    initial_investment_krw: int,
    target_annual_revenue_krw: int = 10_000_000_000,
) -> dict:
    """사업 지표를 평가하고 연간 목표 대비 기여도를 분석합니다."""
    monthly_profit = monthly_revenue_krw - monthly_cost_krw
    annual_revenue_projection = monthly_revenue_krw * 12
    profit_margin_pct = (monthly_profit / monthly_revenue_krw * 100) if monthly_revenue_krw > 0 else 0
    payback_months = (initial_investment_krw / monthly_profit) if monthly_profit > 0 else 9999
    contribution_to_target_pct = (annual_revenue_projection / target_annual_revenue_krw) * 100

    return {
        "monthly_revenue_krw": monthly_revenue_krw,
        "monthly_cost_krw": monthly_cost_krw,
        "monthly_profit_krw": monthly_profit,
        "annual_revenue_projection_krw": annual_revenue_projection,
        "profit_margin_pct": round(profit_margin_pct, 1),
        "payback_period_months": round(payback_months, 1),
        "contribution_to_100b_target_pct": round(contribution_to_target_pct, 2),
        "assessment": (
            "✅ 목표 달성 기여 우수" if contribution_to_target_pct >= 5 else
            "✅ 안정적 기여" if contribution_to_target_pct >= 2 else
            "⚠️ 소규모 기여" if contribution_to_target_pct >= 1 else
            "❌ 기여도 낮음 - 포트폴리오 재검토"
        ),
    }


# ──────────────────────────────────────────────────────────────
# 2. Claude tool_use 스키마 정의
# ──────────────────────────────────────────────────────────────

TOOL_SEARCH_WEB = {
    "name": "search_web",
    "description": (
        "해외 쇼핑 사이트(AliExpress, Alibaba, Amazon 등) 또는 시장 트렌드 정보를 "
        "웹에서 검색합니다. 소싱 상품 리서치, 트렌드 파악, 경쟁사 가격 조사에 활용하세요."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "검색어 (영어 또는 한국어). 예: 'AliExpress trending home decor 2024', '2024 인테리어 소품 트렌드'"
            },
            "num_results": {
                "type": "integer",
                "description": "가져올 결과 수 (기본 6)",
                "default": 6
            }
        },
        "required": ["query"]
    }
}

TOOL_SEARCH_NAVER_SHOPPING = {
    "name": "search_naver_shopping",
    "description": (
        "네이버 쇼핑에서 국내 시장 가격과 경쟁 상품을 조회합니다. "
        "국내 판매가 벤치마크 및 경쟁 분석에 활용하세요."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "검색할 상품명 (한국어 권장). 예: '미니 공기청정기', '감성 캔들홀더'"
            },
            "num_results": {
                "type": "integer",
                "description": "가져올 결과 수 (기본 5)",
                "default": 5
            }
        },
        "required": ["query"]
    }
}

TOOL_CALCULATE_MARGIN = {
    "name": "calculate_margin_analysis",
    "description": (
        "해외 소싱 원가(USD)와 국내 판매가(KRW)를 기반으로 국제배송비·관세(CIF 기준)·"
        "부가세·포장재비·반품충당금·플랫폼 수수료를 모두 포함한 현실적인 마진을 계산합니다. "
        "목록통관($150 이하 면세) 여부도 자동 판단합니다."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "source_price_usd": {
                "type": "number",
                "description": "해외 소싱 원가 (USD). $150 이하이면 목록통관 면세 자동 적용"
            },
            "sell_price_krw": {
                "type": "integer",
                "description": "국내 판매 예정가 (KRW)"
            },
            "intl_shipping_krw": {
                "type": "integer",
                "description": "해외→한국 국제 배송비 (KRW). AliExpress 소형 약 6,000원, Alibaba 해상 대량 약 1,500원",
                "default": 6000
            },
            "domestic_shipping_krw": {
                "type": "integer",
                "description": "국내 택배비 (KRW, 기본 3,500원)",
                "default": 3500
            },
            "packaging_cost_krw": {
                "type": "integer",
                "description": "포장재비 박스+에어캡 (KRW, 기본 2,000원)",
                "default": 2000
            },
            "return_rate_pct": {
                "type": "number",
                "description": "반품 충당금 비율 % (기본 3%)",
                "default": 3.0
            },
            "customs_rate_pct": {
                "type": "number",
                "description": "관세율 % (기본 8%, CIF 기준 적용)",
                "default": 8.0
            },
            "platform_fee_pct": {
                "type": "number",
                "description": "플랫폼 수수료 % (기본 10%. 네이버 4~5%, 쿠팡 8~11%)",
                "default": 10.0
            }
        },
        "required": ["source_price_usd", "sell_price_krw"]
    }
}

TOOL_GET_SOURCING_INFO = {
    "name": "get_sourcing_site_info",
    "description": (
        "AliExpress·Alibaba·1688·DHgate 각 해외 소싱 플랫폼의 수수료·절차·배송비·"
        "한국 관세 규정을 반환합니다. 상품 소싱 전 반드시 조회하여 정확한 비용을 파악하세요."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "site": {
                "type": "string",
                "enum": ["aliexpress", "alibaba", "1688", "dhgate", "korean_customs", "all"],
                "description": (
                    "조회할 플랫폼. "
                    "'all'이면 전체 비교표 반환 (소싱 전략 수립 시 권장)"
                )
            }
        },
        "required": ["site"]
    }
}

TOOL_CALCULATE_MARKETING_ROI = {
    "name": "calculate_marketing_roi",
    "description": (
        "마케팅 예산 투입 대비 예상 매출과 ROI를 계산합니다. "
        "채널별 예산 배분 및 ROAS 설정 시 활용하세요."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "marketing_budget_krw": {
                "type": "integer",
                "description": "총 마케팅 예산 (KRW)"
            },
            "product_price_krw": {
                "type": "integer",
                "description": "상품 판매가 (KRW)"
            },
            "expected_roas": {
                "type": "number",
                "description": "기대 ROAS (기본 3.5배)",
                "default": 3.5
            }
        },
        "required": ["marketing_budget_krw", "product_price_krw"]
    }
}

TOOL_EVALUATE_BUSINESS_METRICS = {
    "name": "evaluate_business_metrics",
    "description": (
        "월 매출/비용/투자 데이터를 기반으로 수익성 지표를 평가하고 "
        "100억 연 매출 목표 대비 기여도를 분석합니다."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "monthly_revenue_krw": {
                "type": "integer",
                "description": "월 예상 매출 (KRW)"
            },
            "monthly_cost_krw": {
                "type": "integer",
                "description": "월 예상 비용 (원가 + 마케팅 포함, KRW)"
            },
            "initial_investment_krw": {
                "type": "integer",
                "description": "초기 투자액 (재고 매입비 등, KRW)"
            }
        },
        "required": ["monthly_revenue_krw", "monthly_cost_krw", "initial_investment_krw"]
    }
}


# 에이전트별 사용 가능한 도구 집합
MD_TOOLS = [TOOL_GET_SOURCING_INFO, TOOL_SEARCH_WEB, TOOL_SEARCH_NAVER_SHOPPING, TOOL_CALCULATE_MARGIN]
MARKETING_TOOLS = [TOOL_CALCULATE_MARKETING_ROI, TOOL_SEARCH_WEB]
CEO_TOOLS = [TOOL_EVALUATE_BUSINESS_METRICS, TOOL_CALCULATE_MARGIN]

# 도구 이름 → 실행 함수 매핑
TOOL_REGISTRY: dict[str, Any] = {
    "search_web": search_web,
    "search_naver_shopping": search_naver_shopping,
    "get_sourcing_site_info": get_sourcing_site_info,
    "calculate_margin_analysis": calculate_margin_analysis,
    "calculate_marketing_roi": calculate_marketing_roi,
    "evaluate_business_metrics": evaluate_business_metrics,
}
