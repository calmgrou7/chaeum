#!/usr/bin/env python3
"""
agent.py - 산업재해·공장화재 보고서 자동 생성 에이전트 (v2.0)

사용법:
  python agent.py --csv sample_data/companies.csv
  python agent.py --csv companies.csv --dry-run
  python agent.py --csv companies.csv --smtp-host smtp.gmail.com --smtp-port 587
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from send_email import (
    SMTPConfig,
    EmailMessage,
    SendResult,
    send_bulk,
    gmail_config,
    outlook_config,
)

load_dotenv()

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Company:
    company_name: str
    email: str
    address: str


@dataclass
class FireIncident:
    title: str
    cause: str
    keywords: list[str]


@dataclass
class ReportData:
    incidents: list[FireIncident]
    serious_accident_law_summary: str


@dataclass
class AgentResult:
    company_name: str
    email: str
    success: bool
    error: Optional[str] = None
    sent_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Step 1: CSV 로드 및 검증
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = {"company_name", "email", "address"}


def load_companies(csv_path: str) -> list[Company]:
    """CSV 파일을 읽어 Company 목록을 반환합니다."""
    print("\n[Step 1] CSV 파일 로드 및 검증 중...")
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

    companies: list[Company] = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV 파일이 비어 있습니다.")
        missing = REQUIRED_COLUMNS - {c.strip().lower() for c in reader.fieldnames}
        if missing:
            raise ValueError(f"CSV에 필수 컬럼이 없습니다: {missing}")

        for i, row in enumerate(reader, start=2):
            name = row.get("company_name", "").strip()
            email = row.get("email", "").strip()
            address = row.get("address", "").strip()
            if not name or not email:
                print(f"  ⚠  {i}행 건너뜀 (company_name 또는 email 누락)")
                continue
            companies.append(Company(company_name=name, email=email, address=address))

    print(f"  ✅ 총 {len(companies)}개 고객사 로드 완료")
    for c in companies:
        print(f"     • {c.company_name} <{c.email}>")
    return companies


# ---------------------------------------------------------------------------
# Step 2: 웹 검색 (공장화재 + 중대재해처벌법)
# ---------------------------------------------------------------------------

NAVER_NEWS_URL = "https://search.naver.com/search.naver"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _search_naver_news(query: str, display: int = 5) -> list[dict]:
    """네이버 뉴스 검색 결과를 파싱하여 반환합니다."""
    params = {
        "where": "news",
        "query": query,
        "sm": "tab_opt",
        "sort": "1",  # 최신순
        "pd": "4",    # 1개월
        "display": display,
    }
    try:
        resp = requests.get(NAVER_NEWS_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  ⚠  검색 요청 실패: {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    for article in soup.select("div.news_area")[:display]:
        title_el = article.select_one("a.news_tit")
        desc_el = article.select_one("div.dsc_wrap")
        if not title_el:
            continue
        items.append({
            "title": title_el.get_text(strip=True),
            "description": desc_el.get_text(strip=True) if desc_el else "",
            "url": title_el.get("href", ""),
        })
    return items


def _extract_keywords(title: str, description: str) -> list[str]:
    """제목/설명에서 주요 키워드를 추출합니다."""
    candidate_keywords = [
        "전기 합선", "용접 불꽃", "화학물질 누출", "과부하", "가스 누출",
        "마찰열", "인화성 물질", "배선 불량", "방화", "자연발화",
        "안전장치 미비", "관리 소홀", "과전류", "폭발", "화재",
        "산업재해", "중대재해", "사망", "부상", "대피",
    ]
    found = []
    combined = title + " " + description
    for kw in candidate_keywords:
        if kw in combined and kw not in found:
            found.append(kw)
        if len(found) >= 4:
            break
    # 최소 2개 보장
    if len(found) < 2:
        found = ["화재", "안전관리"]
    return found[:4]


def _infer_cause(title: str, description: str) -> str:
    """제목/설명에서 발생 원인을 추론합니다."""
    text = title + " " + description
    cause_map = {
        "합선": "전기 합선으로 인한 화재 발생",
        "용접": "용접 작업 중 불꽃 비산으로 인한 화재",
        "가스": "가스 누출로 인한 폭발 및 화재",
        "화학": "화학물질 취급 부주의로 인한 화재",
        "과부하": "전기 과부하로 인한 화재 발생",
        "배선": "노후 배선 불량으로 인한 화재",
        "인화": "인화성 물질 관리 소홀로 인한 화재",
    }
    for keyword, cause in cause_map.items():
        if keyword in text:
            return cause
    return "정확한 원인 조사 중 (현장 합동 감식 예정)"


def search_incidents(count: int = 2) -> list[FireIncident]:
    """최근 공장화재 사고 정보를 검색합니다."""
    print("\n[Step 2] 최신 공장화재 사고 검색 중 (병렬 처리)...")
    queries = ["공장 화재 사고", "산업단지 화재", "공장 폭발 화재"]
    raw: list[dict] = []
    seen_titles: set[str] = set()

    for q in queries:
        results = _search_naver_news(q, display=3)
        for item in results:
            title_key = item["title"][:20]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                raw.append(item)
        if len(raw) >= count:
            break

    incidents: list[FireIncident] = []
    for item in raw[:count]:
        cause = _infer_cause(item["title"], item["description"])
        keywords = _extract_keywords(item["title"], item["description"])
        incidents.append(FireIncident(
            title=item["title"],
            cause=cause,
            keywords=keywords,
        ))
        print(f"  ✅ [{len(incidents)}] {item['title'][:50]}...")

    # 검색 실패 시 기본 데이터 사용
    if len(incidents) < count:
        print("  ⚠  검색 결과 부족, 기본 데이터로 보완합니다.")
        fallbacks = [
            FireIncident(
                title="경기도 안산 반월공단 플라스틱 가공공장 화재 발생",
                cause="전기 합선으로 인한 화재 발생 (노후 전선 관리 불량)",
                keywords=["전기 합선", "배선 불량", "화재", "산업재해"],
            ),
            FireIncident(
                title="인천 남동공단 금속 가공업체 용접 중 화재",
                cause="용접 작업 중 불꽃 비산으로 인한 인화성 물질 착화",
                keywords=["용접 불꽃", "인화성 물질", "화재", "안전관리"],
            ),
        ]
        while len(incidents) < count:
            incidents.append(fallbacks[len(incidents)])

    return incidents[:count]


def search_serious_accident_law() -> str:
    """중대재해처벌법 최신 정보를 검색합니다."""
    print("  🔍 중대재해처벌법 최신 현황 검색 중...")
    results = _search_naver_news("중대재해처벌법 2024 2025 처벌 판례", display=2)
    summary_parts = []
    for r in results:
        if r["description"]:
            summary_parts.append(r["description"][:80])

    if summary_parts:
        return (
            "중대재해처벌법(2022년 시행)은 사업주·경영책임자가 안전보건 의무를 위반하여 "
            "중대산업재해가 발생한 경우 형사처벌을 강화한 법률입니다. "
            + " ".join(summary_parts[:1])
        )

    return (
        "중대재해처벌법(2022년 1월 27일 시행)은 상시근로자 5인 이상 사업장에 적용되며, "
        "경영책임자가 안전보건관리체계 구축 의무를 이행하지 않아 중대산업재해가 발생할 경우 "
        "1년 이상 징역 또는 10억 원 이하 벌금에 처해질 수 있습니다. "
        "2024년부터 50인 미만 사업장으로도 확대 적용되어 모든 사업주의 각별한 주의가 필요합니다."
    )


def collect_report_data() -> ReportData:
    """보고서에 필요한 모든 데이터를 수집합니다."""
    incidents = search_incidents(count=2)
    law_summary = search_serious_accident_law()
    return ReportData(incidents=incidents, serious_accident_law_summary=law_summary)


# ---------------------------------------------------------------------------
# Step 3: HTML 보고서 생성
# ---------------------------------------------------------------------------

TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_report(company: Company, report_data: ReportData) -> str:
    """Jinja2 템플릿으로 HTML 보고서를 렌더링합니다."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    template = env.get_template("report.html")

    inc = report_data.incidents
    context = {
        "company_name": company.company_name,
        "address": company.address,
        "report_date": datetime.now().strftime("%Y년 %m월 %d일"),
        "incident1_title": inc[0].title if len(inc) > 0 else "",
        "incident1_cause": inc[0].cause if len(inc) > 0 else "",
        "incident1_keywords": inc[0].keywords if len(inc) > 0 else [],
        "incident2_title": inc[1].title if len(inc) > 1 else "",
        "incident2_cause": inc[1].cause if len(inc) > 1 else "",
        "incident2_keywords": inc[1].keywords if len(inc) > 1 else [],
        "serious_accident_law_summary": report_data.serious_accident_law_summary,
    }
    return template.render(**context)


def preview_report(html: str) -> None:
    """HTML 보고서 미리보기를 출력합니다."""
    preview_path = Path("results") / "preview.html"
    preview_path.parent.mkdir(exist_ok=True)
    preview_path.write_text(html, encoding="utf-8")
    print(f"\n[Step 3] HTML 보고서 생성 완료")
    print(f"  📄 미리보기 저장됨: {preview_path}")
    print(f"  💡 브라우저에서 열어서 확인하세요.")


# ---------------------------------------------------------------------------
# Step 4: 사용자 승인
# ---------------------------------------------------------------------------


def ask_approval() -> bool:
    """사용자에게 발송 승인을 요청합니다."""
    print("\n[Step 4] 사용자 검토 및 승인")
    print("  위 미리보기를 확인하신 후 발송 여부를 결정하세요.")
    while True:
        answer = input("  보고서를 발송하시겠습니까? [y/n]: ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  'y' 또는 'n'을 입력하세요.")


# ---------------------------------------------------------------------------
# Step 5: SMTP 설정 수집
# ---------------------------------------------------------------------------


def collect_smtp_config(args: argparse.Namespace) -> SMTPConfig:
    """CLI 인수 또는 환경변수에서 SMTP 설정을 수집합니다."""
    host = args.smtp_host or os.getenv("SMTP_HOST", "")
    port = args.smtp_port or int(os.getenv("SMTP_PORT", "587"))
    user = args.smtp_user or os.getenv("SMTP_USER", "")
    password = args.smtp_password or os.getenv("SMTP_PASSWORD", "")
    from_addr = args.smtp_from or os.getenv("SMTP_FROM", user)

    # 대화형 입력
    if not host:
        print("\n[Step 5] SMTP 설정 입력")
        print("  (환경변수 또는 --smtp-* 옵션으로 미리 설정할 수 있습니다)")
        host = input("  SMTP 호스트 (예: smtp.gmail.com): ").strip()
        port = int(input("  SMTP 포트 (예: 587): ").strip() or "587")
        user = input("  SMTP 사용자: ").strip()
        import getpass
        password = getpass.getpass("  SMTP 비밀번호: ")
        from_addr = input(f"  발신자 주소 [{user}]: ").strip() or user

    return SMTPConfig(
        host=host,
        port=port,
        user=user,
        password=password,
        from_address=from_addr,
        use_tls=(port == 587),
        use_ssl=(port == 465),
    )


# ---------------------------------------------------------------------------
# Step 6: 이메일 발송
# ---------------------------------------------------------------------------

EMAIL_SUBJECT = "[산업재해 안전 보고서] 최신 공장화재 사고 동향 및 중대재해처벌법 안내"


def build_messages(
    companies: list[Company],
    report_data: ReportData,
) -> list[tuple[Company, EmailMessage]]:
    """각 고객사별 이메일 메시지를 생성합니다."""
    pairs: list[tuple[Company, EmailMessage]] = []
    for company in companies:
        html = render_report(company, report_data)
        msg = EmailMessage(
            to_address=company.email,
            subject=EMAIL_SUBJECT,
            html_body=html,
        )
        pairs.append((company, msg))
    return pairs


def _progress_cb(result: SendResult, idx: int, total: int) -> None:
    status = "✅" if result.success else "❌"
    err = f" ({result.error})" if result.error else ""
    print(f"  {status} [{idx}/{total}] {result.to_address}{err}")


def send_reports(
    smtp_config: SMTPConfig,
    companies: list[Company],
    report_data: ReportData,
    dry_run: bool = False,
) -> list[AgentResult]:
    """모든 고객사에게 보고서를 발송합니다."""
    label = "(DRY-RUN)" if dry_run else ""
    print(f"\n[Step 6] 이메일 발송 시작 {label}")

    pairs = build_messages(companies, report_data)
    messages = [m for _, m in pairs]

    results_raw = send_bulk(
        smtp_config,
        messages,
        dry_run=dry_run,
        progress_callback=_progress_cb,
    )

    results: list[AgentResult] = []
    now = datetime.now().isoformat()
    for (company, _), raw in zip(pairs, results_raw):
        results.append(AgentResult(
            company_name=company.company_name,
            email=company.email,
            success=raw.success,
            error=raw.error,
            sent_at=now if raw.success else None,
        ))
    return results


# ---------------------------------------------------------------------------
# Step 7: 결과 저장
# ---------------------------------------------------------------------------


def save_results(results: list[AgentResult]) -> Path:
    """발송 결과를 JSON 파일로 저장합니다."""
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = results_dir / f"{timestamp}_results.json"

    success = sum(1 for r in results if r.success)
    fail = len(results) - success
    payload = {
        "generated_at": datetime.now().isoformat(),
        "summary": {"total": len(results), "success": success, "failure": fail},
        "details": [asdict(r) for r in results],
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[Step 7] 결과 저장 완료")
    print(f"  📊 성공: {success}건 / 실패: {fail}건 / 전체: {len(results)}건")
    print(f"  💾 결과 파일: {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="산업재해·공장화재 보고서 자동 생성 및 이메일 발송 에이전트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python agent.py --csv sample_data/companies.csv --dry-run
  python agent.py --csv companies.csv --smtp-host smtp.gmail.com --smtp-port 587
        """,
    )
    parser.add_argument("--csv", required=True, help="고객사 CSV 파일 경로")
    parser.add_argument("--dry-run", action="store_true", help="실제 이메일 발송 없이 테스트 실행")
    parser.add_argument("--yes", "-y", action="store_true", help="발송 전 승인 단계 건너뜀")
    parser.add_argument("--smtp-host", help="SMTP 서버 호스트")
    parser.add_argument("--smtp-port", type=int, default=0, help="SMTP 포트 (기본: 587)")
    parser.add_argument("--smtp-user", help="SMTP 사용자 이메일")
    parser.add_argument("--smtp-password", help="SMTP 비밀번호 (앱 비밀번호 권장)")
    parser.add_argument("--smtp-from", help="발신자 이메일 주소")
    return parser.parse_args()


def main() -> None:
    print("=" * 60)
    print("  산업재해·공장화재 보고서 자동 생성 에이전트 v2.0")
    print("=" * 60)

    args = parse_args()

    # Step 1: CSV 로드
    try:
        companies = load_companies(args.csv)
    except (FileNotFoundError, ValueError) as exc:
        print(f"\n❌ 오류: {exc}", file=sys.stderr)
        sys.exit(1)

    if not companies:
        print("\n⚠  유효한 고객사가 없습니다. CSV 파일을 확인하세요.", file=sys.stderr)
        sys.exit(1)

    # Step 2: 데이터 수집
    report_data = collect_report_data()

    # Step 3: 샘플 보고서 미리보기 생성
    sample_html = render_report(companies[0], report_data)
    preview_report(sample_html)

    # Step 4: 승인 (dry-run 또는 --yes 시 건너뜀)
    if not args.dry_run and not args.yes:
        if not ask_approval():
            print("\n발송을 취소했습니다.")
            sys.exit(0)

    # Step 5: SMTP 설정 (dry-run 시 더미 설정)
    if args.dry_run:
        from send_email import SMTPConfig as _SMTP
        smtp_config = _SMTP(
            host="localhost", port=25, user="test", password="test",
            from_address="test@example.com",
        )
    else:
        smtp_config = collect_smtp_config(args)

    # Step 6: 발송
    results = send_reports(smtp_config, companies, report_data, dry_run=args.dry_run)

    # Step 7: 결과 저장
    save_results(results)

    print("\n✅ 에이전트 실행 완료!")


if __name__ == "__main__":
    main()
