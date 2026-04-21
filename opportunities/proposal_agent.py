#!/usr/bin/env python3
"""
proposal_agent.py - 맞춤 영업 제안서 자동 생성 에이전트

사업 모델: 보험 영업 전 맞춤 제안서 자동 생성으로 상담 성공률 향상
스마트폰 활용: 고객 상담 중 스마트폰으로 정보 입력 → 제안서 자동 발송

사용법:
  python opportunities/proposal_agent.py --company ABC공장 --industry 제조업 --employees 50
  python opportunities/proposal_agent.py --company XYZ물류 --industry 물류창고 --employees 30 --email contact@xyz.com
  python opportunities/proposal_agent.py --company 테스트 --industry 식품제조 --employees 20 --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

# send_email.py는 상위 디렉토리에 있으므로 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))
from send_email import SMTPConfig, EmailMessage, send_single

load_dotenv()

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ProposalData:
    company_name: str
    industry: str
    employees: int
    address: str
    needs_analysis: str
    recommended_products: list[dict]  # [{"name": ..., "coverage": ..., "premium_range": ...}]
    key_risks: list[str]
    special_notes: str
    report_date: str


# ---------------------------------------------------------------------------
# Step 1: Claude로 맞춤 보험 니즈 분석
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """당신은 한국의 산업재해 및 공장화재보험 전문 컨설턴트입니다.
고객사 정보를 바탕으로 맞춤 보험 니즈를 분석하고 추천 상품을 제안합니다.
반드시 JSON 형식으로만 응답하세요. 마크다운 코드 블록 없이 순수 JSON만 출력하세요."""

ANALYSIS_PROMPT = """\
다음 고객사 정보를 분석하여 맞춤 보험 제안서 내용을 JSON으로 생성해주세요.

고객사 정보:
- 회사명: {company_name}
- 업종: {industry}
- 직원수: {employees}명
- 주소: {address}

다음 JSON 형식으로 반환하세요:
{{
  "needs_analysis": "이 업종/규모에서 가장 중요한 보험 니즈 2~3문장",
  "recommended_products": [
    {{
      "name": "보험 상품명",
      "coverage": "주요 보장 내용 (1~2문장)",
      "premium_range": "예상 월 보험료 범위 (예: 15~25만원)"
    }}
  ],
  "key_risks": ["주요 리스크 1", "주요 리스크 2", "주요 리스크 3"],
  "special_notes": "이 고객사에 특별히 강조할 포인트 1~2문장"
}}

추천 상품은 2~3개, 업종 특성에 맞는 실제적인 내용으로 작성해주세요.
"""

PROPOSAL_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>맞춤 보험 제안서 - {{ company_name }}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: '맑은 고딕', Malgun Gothic, Arial, sans-serif; background: #f0f2f5; color: #1a1a2e; }
  .wrapper { max-width: 680px; margin: 0 auto; background: #fff; }
  .header { background: linear-gradient(135deg, #0d2137 0%, #1a3a5c 100%); color: #fff; padding: 40px 32px 32px; text-align: center; }
  .header-badge { display: inline-block; background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); border-radius: 20px; padding: 6px 16px; font-size: 12px; letter-spacing: 1px; margin-bottom: 16px; }
  .header h1 { font-size: 22px; font-weight: 700; line-height: 1.4; margin-bottom: 8px; }
  .header-subtitle { font-size: 13px; opacity: 0.8; }
  .section { padding: 28px 32px; border-bottom: 1px solid #f0f2f5; }
  .section-title { font-size: 16px; font-weight: 700; color: #0d2137; margin-bottom: 16px; padding-left: 12px; border-left: 4px solid #1a3a5c; }
  .company-box { background: #f8fafc; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; }
  .company-box .name { font-size: 20px; font-weight: 700; color: #0d2137; margin-bottom: 4px; }
  .company-box .meta { font-size: 13px; color: #666; }
  .needs-text { font-size: 14px; line-height: 1.8; color: #444; background: #fffbf0; border-left: 3px solid #f0a500; padding: 14px 18px; border-radius: 4px; }
  .risk-list { list-style: none; }
  .risk-list li { padding: 8px 0 8px 24px; position: relative; font-size: 14px; color: #444; border-bottom: 1px solid #f5f5f5; }
  .risk-list li::before { content: "⚠"; position: absolute; left: 0; color: #e74c3c; }
  .product-card { background: #f8fafc; border-radius: 8px; padding: 18px 20px; margin-bottom: 12px; border: 1px solid #e8edf2; }
  .product-card .product-name { font-size: 15px; font-weight: 700; color: #1a3a5c; margin-bottom: 8px; }
  .product-card .coverage { font-size: 13px; color: #555; line-height: 1.6; margin-bottom: 8px; }
  .product-card .premium { font-size: 13px; font-weight: 600; color: #0d7a3e; background: #e8f5ee; padding: 4px 10px; border-radius: 4px; display: inline-block; }
  .special-note { background: #fff3f3; border-left: 3px solid #e74c3c; padding: 14px 18px; border-radius: 4px; font-size: 14px; color: #444; line-height: 1.8; }
  .cta { background: #0d2137; color: #fff; padding: 28px 32px; text-align: center; }
  .cta h2 { font-size: 18px; margin-bottom: 12px; }
  .cta p { font-size: 13px; opacity: 0.85; margin-bottom: 20px; }
  .cta-btn { display: inline-block; background: #fff; color: #0d2137; font-weight: 700; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-size: 14px; }
  .contact { padding: 24px 32px; background: #f8fafc; }
  .contact-name { font-size: 16px; font-weight: 700; color: #0d2137; margin-bottom: 4px; }
  .contact-info { font-size: 13px; color: #666; line-height: 1.8; }
  .footer { padding: 16px 32px; text-align: center; font-size: 11px; color: #aaa; background: #f0f2f5; }
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <div class="header-badge">맞춤 보험 제안서</div>
    <h1>{{ company_name }} 귀중<br>맞춤형 보험 솔루션 안내</h1>
    <p class="header-subtitle">{{ report_date }} 기준 | 업종: {{ industry }} | 직원 {{ employees }}명</p>
  </div>

  <div class="section">
    <div class="section-title">귀사 보험 니즈 분석</div>
    <div class="company-box">
      <div class="name">{{ company_name }}</div>
      <div class="meta">{{ industry }} | 직원 {{ employees }}명 | {{ address }}</div>
    </div>
    <div class="needs-text">{{ needs_analysis }}</div>
  </div>

  <div class="section">
    <div class="section-title">주요 리스크 요인</div>
    <ul class="risk-list">
      {% for risk in key_risks %}
      <li>{{ risk }}</li>
      {% endfor %}
    </ul>
  </div>

  <div class="section">
    <div class="section-title">추천 보험 상품</div>
    {% for product in recommended_products %}
    <div class="product-card">
      <div class="product-name">{{ product.name }}</div>
      <div class="coverage">{{ product.coverage }}</div>
      <span class="premium">예상 월 보험료: {{ product.premium_range }}</span>
    </div>
    {% endfor %}
  </div>

  <div class="section">
    <div class="section-title">컨설턴트 특별 안내</div>
    <div class="special-note">{{ special_notes }}</div>
  </div>

  <div class="cta">
    <h2>지금 바로 무료 상담 신청하세요</h2>
    <p>귀사 맞춤 보험료 산출 및 상세 설명을 제공해 드립니다.<br>평일 09:00~18:00 상담 가능합니다.</p>
    <a href="tel:010-8950-6400" class="cta-btn">📞 010-8950-6400 전화 상담</a>
  </div>

  <div class="contact">
    <div class="contact-name">이헌영 지점장</div>
    <div class="contact-info">
      단체보험 및 공장화재보험 전문 컨설턴트<br>
      전화: 010-8950-6400 | 팩스: 0504-006-6400<br>
      상담: 평일 09:00~18:00
    </div>
  </div>

  <div class="footer">
    본 제안서는 고객사 정보를 바탕으로 자동 생성된 참고 자료입니다.
    실제 보험료는 심사 결과에 따라 달라질 수 있습니다.
  </div>
</div>
</body>
</html>
"""


def analyze_needs(company_name: str, industry: str, employees: int, address: str) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ⚠  ANTHROPIC_API_KEY 환경변수가 없습니다.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    prompt = ANALYSIS_PROMPT.format(
        company_name=company_name,
        industry=industry,
        employees=employees,
        address=address,
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    import json, re
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return {"needs_analysis": "분석 오류", "recommended_products": [], "key_risks": [], "special_notes": ""}
        return json.loads(match.group())


# ---------------------------------------------------------------------------
# Step 2: HTML 제안서 생성
# ---------------------------------------------------------------------------


def render_proposal(data: ProposalData) -> str:
    from jinja2 import Environment
    env = Environment()
    template = env.from_string(PROPOSAL_TEMPLATE)
    return template.render(
        company_name=data.company_name,
        industry=data.industry,
        employees=data.employees,
        address=data.address,
        report_date=data.report_date,
        needs_analysis=data.needs_analysis,
        recommended_products=data.recommended_products,
        key_risks=data.key_risks,
        special_notes=data.special_notes,
    )


def save_proposal(html: str, company_name: str) -> Path:
    results_dir = Path("results") / "proposals"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = results_dir / f"proposal_{company_name}_{timestamp}.html"
    path.write_text(html, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="맞춤 영업 제안서 자동 생성 에이전트")
    parser.add_argument("--company", required=True, help="고객사명")
    parser.add_argument("--industry", required=True, help="업종 (예: 제조업, 물류창고, 식품제조)")
    parser.add_argument("--employees", type=int, required=True, help="직원 수")
    parser.add_argument("--address", default="", help="주소 (선택)")
    parser.add_argument("--email", default="", help="발송할 이메일 주소 (선택)")
    parser.add_argument("--dry-run", action="store_true", help="이메일 발송 없이 HTML만 생성")
    args = parser.parse_args()

    print(f"\n[맞춤 영업 제안서 에이전트]")
    print(f"  고객사: {args.company} | 업종: {args.industry} | 직원: {args.employees}명")

    print(f"\n[Step 1] Claude AI로 보험 니즈 분석 중...")
    analysis = analyze_needs(args.company, args.industry, args.employees, args.address)
    print(f"  ✅ 분석 완료")

    data = ProposalData(
        company_name=args.company,
        industry=args.industry,
        employees=args.employees,
        address=args.address or f"{args.industry} 소재지",
        needs_analysis=analysis.get("needs_analysis", ""),
        recommended_products=analysis.get("recommended_products", []),
        key_risks=analysis.get("key_risks", []),
        special_notes=analysis.get("special_notes", ""),
        report_date=datetime.now().strftime("%Y년 %m월 %d일"),
    )

    print(f"\n[Step 2] HTML 제안서 생성 중...")
    html = render_proposal(data)
    saved = save_proposal(html, args.company)
    print(f"  ✅ 제안서 저장: {saved}")

    # 콘솔 미리보기
    print(f"\n--- 제안서 요약 ---")
    print(f"  보험 니즈: {data.needs_analysis[:80]}...")
    print(f"  추천 상품: {len(data.recommended_products)}개")
    for p in data.recommended_products:
        print(f"    • {p.get('name', '')} ({p.get('premium_range', '')})")
    print(f"  주요 리스크: {', '.join(data.key_risks[:3])}")

    if args.email:
        print(f"\n[Step 3] 이메일 발송 {'(dry-run)' if args.dry_run else ''}...")

        smtp_host = os.getenv("SMTP_HOST", "")
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        smtp_from = os.getenv("SMTP_FROM", smtp_user)

        if not smtp_host and not args.dry_run:
            print("  ⚠  SMTP 설정이 없습니다. --dry-run 으로 실행하거나 .env에 SMTP 정보를 입력하세요.")
        else:
            smtp_config = SMTPConfig(
                host=smtp_host or "smtp.gmail.com",
                port=int(os.getenv("SMTP_PORT", "587")),
                user=smtp_user or "test@example.com",
                password=smtp_password or "",
                from_address=smtp_from or "test@example.com",
            )
            message = EmailMessage(
                to_address=args.email,
                subject=f"[맞춤 제안서] {args.company} 보험 솔루션 안내 - 이헌영 지점장",
                html_body=html,
                plain_body=f"{args.company} 맞춤 보험 제안서입니다. HTML 이메일을 지원하는 클라이언트에서 확인해주세요.",
            )
            result = send_single(smtp_config, message, dry_run=args.dry_run)
            if result.success:
                print(f"  ✅ 이메일 {'발송 완료 (dry-run)' if args.dry_run else '발송 완료'}: {args.email}")
            else:
                print(f"  ⚠  발송 실패: {result.error}")

    print(f"\n완료!")
    print(f"  📄 HTML 제안서: {saved}")
    print(f"  📱 파일을 열어 스마트폰에서 확인하거나 고객에게 이메일로 발송하세요!")


if __name__ == "__main__":
    main()
