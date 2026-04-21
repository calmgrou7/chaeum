#!/usr/bin/env python3
"""
lead_finder_agent.py - 잠재 고객 발굴 자동화 에이전트

사업 모델: 영업 리드 데이터 수집 대행 / 자사 영업에 직접 활용
스마트폰 활용: CSV를 공유받아 연락처 앱 또는 발송 파이프라인에 연결

기존 agent.py와 호환되는 CSV 형식(company_name, email, address) 출력

사용법:
  python opportunities/lead_finder_agent.py --industry 공장 --region 경기도 --limit 20
  python opportunities/lead_finder_agent.py --industry 제조업 --region 구미 --limit 50
  python opportunities/lead_finder_agent.py --industry 물류창고 --region 인천 --enrich
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Lead:
    company_name: str
    address: str
    phone: str
    category: str
    email: str = ""
    source: str = "naver_place"


# ---------------------------------------------------------------------------
# Step 1: 네이버 플레이스 검색으로 업체 정보 수집
# ---------------------------------------------------------------------------

NAVER_SEARCH_URL = "https://search.naver.com/search.naver"


def _search_naver_place(query: str, display: int = 20) -> list[dict]:
    """네이버 플레이스/지역 검색으로 업체 목록을 가져옵니다."""
    params = {
        "where": "place",
        "query": query,
        "sm": "tab_hty.top",
    }
    try:
        resp = requests.get(NAVER_SEARCH_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ⚠  네이버 검색 오류: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    # 플레이스 결과 파싱
    for item in soup.select("li.TYaxT, div.place_section_content li")[:display]:
        name_el = item.select_one("span.TYaxT, .place_bluelink, span.place_name")
        addr_el = item.select_one("span.LDgIH, .addr")
        phone_el = item.select_one("span.xlx7Q, .phone")
        cat_el = item.select_one("span.KCMnt, .category")

        name = name_el.get_text(strip=True) if name_el else ""
        addr = addr_el.get_text(strip=True) if addr_el else ""
        phone = phone_el.get_text(strip=True) if phone_el else ""
        category = cat_el.get_text(strip=True) if cat_el else ""

        if name:
            results.append({
                "name": name,
                "address": addr,
                "phone": phone,
                "category": category,
            })

    return results


def _search_naver_news_for_leads(industry: str, region: str, limit: int) -> list[dict]:
    """네이버 뉴스/웹에서 업체명+주소 패턴을 추출합니다 (보완 검색)."""
    params = {
        "where": "web",
        "query": f"{region} {industry} 업체 목록",
    }
    try:
        resp = requests.get(NAVER_SEARCH_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for item in soup.select("li.bx._svp_item, div.total_area li")[:limit]:
        title_el = item.select_one("a.api_txt_lines.total_tit, .link_tit")
        desc_el = item.select_one("div.api_txt_lines.dsc_txt, .dsc_txt_wrap")

        title = title_el.get_text(strip=True) if title_el else ""
        desc = desc_el.get_text(strip=True) if desc_el else ""

        # 전화번호 패턴 추출
        phone_match = re.search(r"0\d{1,2}-\d{3,4}-\d{4}", desc + title)
        phone = phone_match.group() if phone_match else ""

        if title and len(title) < 50:
            results.append({
                "name": title[:30],
                "address": region,
                "phone": phone,
                "category": industry,
            })

    return results


def collect_leads(industry: str, region: str, limit: int) -> list[Lead]:
    """네이버 플레이스 검색으로 잠재 고객 목록을 수집합니다."""
    query = f"{region} {industry}"
    print(f"  검색어: '{query}'")

    raw = _search_naver_place(query, display=limit)

    # 결과 부족 시 보완 검색
    if len(raw) < limit // 2:
        print(f"  플레이스 결과 부족 ({len(raw)}건), 웹 검색으로 보완 중...")
        raw += _search_naver_news_for_leads(industry, region, limit - len(raw))

    leads: list[Lead] = []
    seen_names: set[str] = set()

    for item in raw[:limit]:
        name = item.get("name", "").strip()
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        leads.append(Lead(
            company_name=name,
            address=item.get("address", region),
            phone=item.get("phone", ""),
            category=item.get("category", industry),
        ))

    return leads


# ---------------------------------------------------------------------------
# Step 2: AI로 이메일 추정 (--enrich 옵션)
# ---------------------------------------------------------------------------


def enrich_with_email_guess(leads: list[Lead]) -> list[Lead]:
    """회사명에서 이메일 도메인을 추정합니다 (AI 없이 규칙 기반)."""
    for lead in leads:
        name = lead.company_name
        # 한글 회사명 → 영문 추정 (단순 규칙)
        domain_hint = re.sub(r"[^\w]", "", name.lower())[:10]
        if len(domain_hint) >= 3:
            lead.email = f"info@{domain_hint}.co.kr"
    return leads


# ---------------------------------------------------------------------------
# Step 3: CSV 저장 (agent.py 호환 형식)
# ---------------------------------------------------------------------------


def save_leads_csv(leads: list[Lead], industry: str, region: str) -> Path:
    results_dir = Path("results") / "leads"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = results_dir / f"leads_{industry}_{region}_{timestamp}.csv"

    # agent.py 호환 컬럼 우선, 추가 컬럼 뒤에 배치
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["company_name", "email", "address", "phone", "category"])
        for lead in leads:
            writer.writerow([
                lead.company_name,
                lead.email,
                lead.address,
                lead.phone,
                lead.category,
            ])

    return csv_path


def print_leads_table(leads: list[Lead]) -> None:
    print(f"\n{'─'*60}")
    print(f"  {'업체명':<20} {'전화':<16} {'주소'}")
    print(f"{'─'*60}")
    for lead in leads:
        print(f"  {lead.company_name:<20} {lead.phone:<16} {lead.address[:20]}")
    print(f"{'─'*60}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="잠재 고객 발굴 자동화 에이전트")
    parser.add_argument("--industry", required=True, help="업종 (예: 공장, 물류창고, 제조업)")
    parser.add_argument("--region", required=True, help="지역 (예: 경기도, 구미, 인천)")
    parser.add_argument("--limit", type=int, default=20, help="수집할 업체 수 (기본: 20)")
    parser.add_argument("--enrich", action="store_true", help="이메일 추정 활성화")
    args = parser.parse_args()

    print(f"\n[잠재 고객 발굴 에이전트]")
    print(f"  업종: {args.industry} | 지역: {args.region} | 목표: {args.limit}건")

    print(f"\n[Step 1] 네이버 플레이스 검색 중...")
    leads = collect_leads(args.industry, args.region, args.limit)

    if not leads:
        print("  업체를 찾지 못했습니다. 다른 업종/지역을 시도해보세요.")
        sys.exit(1)

    print(f"  ✅ {len(leads)}개 업체 수집 완료")

    if args.enrich:
        print(f"\n[Step 2] 이메일 추정 중...")
        leads = enrich_with_email_guess(leads)
        print(f"  ✅ 이메일 추정 완료")

    print_leads_table(leads)

    print(f"\n[Step 3] CSV 저장 중...")
    csv_path = save_leads_csv(leads, args.industry, args.region)
    print(f"  ✅ CSV 저장: {csv_path}")
    print(f"")
    print(f"  💡 다음 명령으로 바로 보고서 발송 파이프라인에 연결 가능:")
    print(f"     python agent.py --csv {csv_path} --dry-run")
    print(f"  📱 CSV 파일을 스마트폰으로 공유해 영업 연락처로 활용하세요!")


if __name__ == "__main__":
    main()
