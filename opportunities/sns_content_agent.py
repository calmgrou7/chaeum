#!/usr/bin/env python3
"""
sns_content_agent.py - SNS/블로그 콘텐츠 자동 생성 에이전트

사업 모델: 소상공인/보험 대상 SNS 콘텐츠 대행 (월 30~50만원/계정)
스마트폰 활용: 생성된 텍스트를 복사해서 인스타그램/블로그에 바로 포스팅

사용법:
  python opportunities/sns_content_agent.py --industry 보험 --topic 화재보험
  python opportunities/sns_content_agent.py --industry 카페 --topic 신메뉴 --platform blog
  python opportunities/sns_content_agent.py --industry 보험 --topic 실손보험 --platform all
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# 플랫폼별 프롬프트 설정
# ---------------------------------------------------------------------------

PLATFORM_CONFIGS = {
    "instagram": {
        "name": "인스타그램",
        "instruction": "인스타그램 포스팅 5개를 작성하세요. 각 포스팅은 이모지 포함, 150자 내외, 해시태그 10개 포함.",
        "format": "포스팅 {n}:\n{text}\n\n해시태그: {hashtags}",
    },
    "blog": {
        "name": "네이버 블로그",
        "instruction": "네이버 블로그 글 1개를 작성하세요. 제목 포함, 800~1200자, SEO를 위한 키워드 자연스럽게 포함, 소제목(##) 3개 이상.",
        "format": "제목: {title}\n\n{body}",
    },
    "kakao": {
        "name": "카카오스토리/페이스북",
        "instruction": "카카오스토리 또는 페이스북용 짧은 포스팅 3개를 작성하세요. 각 포스팅 100자 내외, 친근한 말투, 이모지 포함.",
        "format": "포스팅 {n}:\n{text}",
    },
}

SYSTEM_PROMPT = """당신은 한국 SNS 마케팅 전문가입니다.
주어진 업종과 주제에 맞는 자연스럽고 매력적인 SNS 콘텐츠를 생성합니다.
고객이 공감하고 공유하고 싶어하는 콘텐츠를 만들어주세요."""


def generate_content(industry: str, topic: str, platform: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ⚠  ANTHROPIC_API_KEY 환경변수가 없습니다.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    config = PLATFORM_CONFIGS[platform]

    prompt = f"""\
업종: {industry}
주제/키워드: {topic}
플랫폼: {config['name']}

{config['instruction']}

콘텐츠 방향:
- 전문성과 친근함을 동시에 담아주세요
- 독자가 행동하고 싶어지는 마무리 문구 포함
- 실제로 바로 사용 가능한 완성된 형태로 작성
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()


def save_content(industry: str, topic: str, platform: str, content: str) -> Path:
    results_dir = Path("results") / "sns_content"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{industry}_{topic}_{platform}_{timestamp}.txt"
    path = results_dir / filename

    header = f"""{'='*60}
SNS 콘텐츠 자동 생성 결과
업종: {industry} | 주제: {topic} | 플랫폼: {PLATFORM_CONFIGS[platform]['name']}
생성일: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}
{'='*60}

"""
    path.write_text(header + content, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="SNS/블로그 콘텐츠 자동 생성 에이전트")
    parser.add_argument("--industry", required=True, help="업종 (예: 보험, 카페, 부동산)")
    parser.add_argument("--topic", required=True, help="콘텐츠 주제/키워드 (예: 화재보험, 신메뉴)")
    parser.add_argument(
        "--platform",
        default="instagram",
        choices=["instagram", "blog", "kakao", "all"],
        help="플랫폼 선택 (기본: instagram)",
    )
    args = parser.parse_args()

    platforms = list(PLATFORM_CONFIGS.keys()) if args.platform == "all" else [args.platform]

    print(f"\n[SNS 콘텐츠 자동 생성 에이전트]")
    print(f"  업종: {args.industry} | 주제: {args.topic}")
    print(f"  플랫폼: {', '.join(PLATFORM_CONFIGS[p]['name'] for p in platforms)}")

    for platform in platforms:
        print(f"\n[{PLATFORM_CONFIGS[platform]['name']}] 콘텐츠 생성 중...")
        content = generate_content(args.industry, args.topic, platform)

        print(f"\n{'─'*50}")
        print(content)
        print(f"{'─'*50}")

        saved = save_content(args.industry, args.topic, platform, content)
        print(f"\n  ✅ 저장 완료: {saved}")
        print(f"  📱 스마트폰에서 위 텍스트를 복사해 {PLATFORM_CONFIGS[platform]['name']}에 바로 포스팅하세요!")

    print(f"\n총 {len(platforms)}개 플랫폼 콘텐츠 생성 완료!")


if __name__ == "__main__":
    main()
