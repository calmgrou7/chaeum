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
    shipping_cost_krw: int = 3000,
    customs_rate_pct: float = 8.0,
    platform_fee_pct: float = 10.0,
    exchange_rate: float = 1380.0,
) -> dict:
    """
    소싱 원가(USD) → 국내 판매가(KRW) 기준 마진 분석을 계산합니다.

    Returns:
        원가, 관부가세, 플랫폼 수수료, 총 비용, 마진액, 마진율 포함 딕셔너리
    """
    source_price_krw = source_price_usd * exchange_rate
    customs_fee_krw = source_price_krw * (customs_rate_pct / 100)
    total_cost_krw = source_price_krw + customs_fee_krw + shipping_cost_krw
    platform_fee_krw = sell_price_krw * (platform_fee_pct / 100)
    net_revenue_krw = sell_price_krw - platform_fee_krw
    profit_krw = net_revenue_krw - total_cost_krw
    margin_rate = (profit_krw / sell_price_krw) * 100 if sell_price_krw > 0 else 0

    return {
        "source_price_usd": source_price_usd,
        "exchange_rate": exchange_rate,
        "source_price_krw": round(source_price_krw),
        "customs_fee_krw": round(customs_fee_krw),
        "shipping_cost_krw": shipping_cost_krw,
        "total_cost_krw": round(total_cost_krw),
        "sell_price_krw": sell_price_krw,
        "platform_fee_krw": round(platform_fee_krw),
        "net_revenue_krw": round(net_revenue_krw),
        "profit_per_unit_krw": round(profit_krw),
        "margin_rate_pct": round(margin_rate, 1),
        "break_even_units_per_month": max(1, round(50000 / profit_krw)) if profit_krw > 0 else 9999,
        "analysis": (
            "✅ 우수 마진" if margin_rate >= 50 else
            "✅ 양호 마진" if margin_rate >= 40 else
            "⚠️ 보통 마진" if margin_rate >= 30 else
            "❌ 낮은 마진 - 재검토 필요"
        ),
    }


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
        "소싱 원가(USD)와 국내 판매가(KRW)를 기반으로 "
        "관부가세, 배송비, 플랫폼 수수료를 포함한 정확한 마진 분석을 실행합니다."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "source_price_usd": {
                "type": "number",
                "description": "해외 소싱 원가 (USD)"
            },
            "sell_price_krw": {
                "type": "integer",
                "description": "국내 판매 예정가 (KRW)"
            },
            "shipping_cost_krw": {
                "type": "integer",
                "description": "배송비 (KRW, 기본 3000원)",
                "default": 3000
            },
            "customs_rate_pct": {
                "type": "number",
                "description": "관세율 % (기본 8%)",
                "default": 8.0
            },
            "platform_fee_pct": {
                "type": "number",
                "description": "플랫폼 수수료 % (기본 10%)",
                "default": 10.0
            }
        },
        "required": ["source_price_usd", "sell_price_krw"]
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
MD_TOOLS = [TOOL_SEARCH_WEB, TOOL_SEARCH_NAVER_SHOPPING, TOOL_CALCULATE_MARGIN]
MARKETING_TOOLS = [TOOL_CALCULATE_MARKETING_ROI, TOOL_SEARCH_WEB]
CEO_TOOLS = [TOOL_EVALUATE_BUSINESS_METRICS, TOOL_CALCULATE_MARGIN]

# 도구 이름 → 실행 함수 매핑
TOOL_REGISTRY: dict[str, Any] = {
    "search_web": search_web,
    "search_naver_shopping": search_naver_shopping,
    "calculate_margin_analysis": calculate_margin_analysis,
    "calculate_marketing_roi": calculate_marketing_roi,
    "evaluate_business_metrics": evaluate_business_metrics,
}
