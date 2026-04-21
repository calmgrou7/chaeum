#!/usr/bin/env python3
"""
business_explorer.py - AI + 스마트폰 수익화 사업 기회 분석 에이전트

사용법:
  python business_explorer.py
  python business_explorer.py --category 보험
  python business_explorer.py --top 5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class BusinessIdea:
    rank: int
    name: str
    description: str
    monthly_income_range: str
    difficulty: str        # 쉬움 / 보통 / 어려움
    startup_cost: str      # 무료 / 1만원 이하 / 10만원 이하
    smartphone_only: bool
    time_to_first_income: str
    how_to_start: str
    score: float


# ---------------------------------------------------------------------------
# Step 1: Claude API로 사업 아이디어 생성 및 평가
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """당신은 AI 창업 컨설턴트입니다.
스마트폰만으로 시작할 수 있는 AI 기반 수익화 사업 아이디어를 분석합니다.
반드시 JSON 형식으로만 응답하세요. 마크다운 코드 블록 없이 순수 JSON만 출력하세요."""

IDEA_PROMPT = """\
2026년 현재 AI 기술과 스마트폰만으로 수익화할 수 있는 사업 아이디어 20개를 생성하고 평가해주세요.

{category_filter}

각 아이디어는 다음 기준으로 0~10점 채점:
- 실행 용이성 (10=매우 쉬움)
- 초기비용 저렴도 (10=완전 무료)
- 월 수익 잠재력 (10=100만원 이상)
- 스마트폰 친화성 (10=스마트폰만으로 완결)

다음 JSON 형식으로 반환하세요:
{{
  "ideas": [
    {{
      "name": "사업 이름",
      "description": "한 줄 설명",
      "monthly_income_range": "예상 월 수입 범위 (예: 30~100만원)",
      "difficulty": "쉬움",
      "startup_cost": "무료",
      "smartphone_only": true,
      "time_to_first_income": "첫 수입까지 예상 기간 (예: 2주)",
      "how_to_start": "시작 방법 1~2문장",
      "scores": {{
        "ease": 9,
        "low_cost": 10,
        "income_potential": 7,
        "smartphone_friendly": 10
      }}
    }}
  ]
}}
"""


def _score_idea(scores: dict) -> float:
    weights = {"ease": 0.3, "low_cost": 0.2, "income_potential": 0.3, "smartphone_friendly": 0.2}
    return sum(scores.get(k, 0) * w for k, w in weights.items())


def fetch_ideas(category: str | None = None) -> list[BusinessIdea]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ⚠  ANTHROPIC_API_KEY 환경변수가 없습니다. .env 파일을 확인하세요.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    category_filter = (
        f"특히 '{category}' 관련 사업에 집중해주세요."
        if category
        else "보험, 마케팅, 콘텐츠, 전자상거래, 교육, 번역 등 다양한 분야를 포함해주세요."
    )

    prompt = IDEA_PROMPT.format(category_filter=category_filter)

    print("  Claude AI에 사업 아이디어 분석 요청 중...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # JSON 파싱
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # 코드 블록이 포함된 경우 제거
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            print("  ⚠  응답 파싱 실패")
            return []
        data = json.loads(match.group())

    ideas: list[BusinessIdea] = []
    for i, item in enumerate(data.get("ideas", []), start=1):
        score = _score_idea(item.get("scores", {}))
        ideas.append(BusinessIdea(
            rank=i,
            name=item.get("name", ""),
            description=item.get("description", ""),
            monthly_income_range=item.get("monthly_income_range", ""),
            difficulty=item.get("difficulty", ""),
            startup_cost=item.get("startup_cost", ""),
            smartphone_only=item.get("smartphone_only", False),
            time_to_first_income=item.get("time_to_first_income", ""),
            how_to_start=item.get("how_to_start", ""),
            score=round(score, 2),
        ))

    return sorted(ideas, key=lambda x: x.score, reverse=True)


# ---------------------------------------------------------------------------
# Step 2: 상위 N개 출력
# ---------------------------------------------------------------------------

DIFFICULTY_ICON = {"쉬움": "🟢", "보통": "🟡", "어려움": "🔴"}


def print_top_ideas(ideas: list[BusinessIdea], top_n: int) -> None:
    print(f"\n{'='*60}")
    print(f"  📱 AI + 스마트폰 수익화 사업 TOP {top_n}")
    print(f"{'='*60}")

    for idea in ideas[:top_n]:
        icon = DIFFICULTY_ICON.get(idea.difficulty, "⚪")
        phone = "📱" if idea.smartphone_only else "💻"
        print(f"\n[{idea.rank}위] {idea.name}  (점수: {idea.score}/10)")
        print(f"  {idea.description}")
        print(f"  💰 월 수입: {idea.monthly_income_range}")
        print(f"  {icon} 난이도: {idea.difficulty}  |  💵 초기비용: {idea.startup_cost}")
        print(f"  {phone} 스마트폰만으로: {'가능' if idea.smartphone_only else '일부 PC 필요'}")
        print(f"  ⏱  첫 수입까지: {idea.time_to_first_income}")
        print(f"  ▶  시작 방법: {idea.how_to_start}")

    print(f"\n{'='*60}")


# ---------------------------------------------------------------------------
# Step 3: 마크다운 보고서 저장
# ---------------------------------------------------------------------------


def save_report(ideas: list[BusinessIdea], top_n: int) -> Path:
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = results_dir / f"business_opportunities_{timestamp}.md"

    lines = [
        f"# AI + 스마트폰 수익화 사업 기회 보고서",
        f"",
        f"생성일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}",
        f"",
        f"---",
        f"",
        f"## TOP {top_n} 추천 사업",
        f"",
    ]

    for idea in ideas[:top_n]:
        phone = "✅" if idea.smartphone_only else "❌"
        lines += [
            f"### {idea.rank}위. {idea.name} (점수: {idea.score}/10)",
            f"",
            f"{idea.description}",
            f"",
            f"| 항목 | 내용 |",
            f"|------|------|",
            f"| 월 예상 수입 | {idea.monthly_income_range} |",
            f"| 난이도 | {idea.difficulty} |",
            f"| 초기비용 | {idea.startup_cost} |",
            f"| 스마트폰만으로 가능 | {phone} |",
            f"| 첫 수입까지 | {idea.time_to_first_income} |",
            f"",
            f"**시작 방법**: {idea.how_to_start}",
            f"",
            f"---",
            f"",
        ]

    lines += [
        f"## 전체 아이디어 목록 (점수순)",
        f"",
        f"| 순위 | 사업명 | 점수 | 난이도 | 월수입 |",
        f"|------|--------|------|--------|--------|",
    ]
    for i, idea in enumerate(ideas, 1):
        lines.append(f"| {i} | {idea.name} | {idea.score} | {idea.difficulty} | {idea.monthly_income_range} |")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="AI + 스마트폰 수익화 사업 기회 분석기")
    parser.add_argument("--category", default=None, help="집중할 사업 카테고리 (예: 보험, 마케팅)")
    parser.add_argument("--top", type=int, default=10, help="상위 N개 출력 (기본: 10)")
    args = parser.parse_args()

    print("\n[Step 1] AI 사업 기회 분석 중 (Claude API 호출)...")
    ideas = fetch_ideas(category=args.category)

    if not ideas:
        print("  아이디어를 가져오지 못했습니다.")
        sys.exit(1)

    print(f"  ✅ 총 {len(ideas)}개 아이디어 수집 완료")

    print("\n[Step 2] 상위 사업 출력...")
    print_top_ideas(ideas, args.top)

    print("\n[Step 3] 보고서 저장 중...")
    report_path = save_report(ideas, args.top)
    print(f"  ✅ 보고서 저장: {report_path}")

    print("\n완료! 아래 에이전트로 바로 사업을 시작할 수 있습니다:")
    print("  📝 SNS 콘텐츠 자동화  →  python opportunities/sns_content_agent.py")
    print("  🔍 잠재 고객 발굴     →  python opportunities/lead_finder_agent.py")
    print("  📄 영업 제안서 생성   →  python opportunities/proposal_agent.py")


if __name__ == "__main__":
    main()
