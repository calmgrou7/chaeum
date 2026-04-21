#!/usr/bin/env python3
"""
consultant.py - 소상공인 대상 AI 경영 컨설팅 CLI

사용법:
  python consultant.py
"""

from __future__ import annotations

import os
import sys

import anthropic
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """당신은 15년 이상의 현장 경험을 가진 소상공인 전문 경영 컨설턴트입니다.
자영업자, 소상공인 대표들의 업종·규모·경영 현황을 깊이 분석하여 실질적인 도움을 제공합니다.

분석 원칙:
- 경영 리스크: 발생 가능성, 사업 존속에 미치는 영향, 대응 시급성을 기준으로 순위 결정
- 성장 전략 및 역량: 영향력(매출·수익 기여), 미래 수요 전망, 얼마나 빠르게 실행 가능한지 기준으로 순위 결정
- 모든 조언은 대한민국 소상공인 현실(인건비, 임대료, 경쟁 환경, 정부 지원책 등)에 기반하여 구체적으로 제시
- 업종별 특수성을 반영한 맞춤형 분석 제공
- 실행 가능한 구체적 액션 아이템 포함"""


def gather_business_info() -> dict:
    print("\n" + "=" * 55)
    print("  소상공인 AI 경영 컨설팅")
    print("=" * 55)
    print("사업체 정보를 입력해 주세요.\n")

    business_type = input("업종 (예: 카페, 음식점, 소매업, 미용실): ").strip()
    employee_count = input("직원 수 (예: 혼자, 2명, 5명): ").strip()
    years_in_business = input("운영 기간 (예: 6개월, 2년, 7년): ").strip()
    main_concerns = input("현재 가장 큰 고민이나 어려움: ").strip()

    return {
        "업종": business_type,
        "직원수": employee_count,
        "운영기간": years_in_business,
        "주요고민": main_concerns,
    }


def build_initial_prompt(info: dict) -> str:
    return f"""다음 소상공인 대표님의 사업체를 분석해 주세요.

【사업체 정보】
- 업종: {info['업종']}
- 직원 수: {info['직원수']}
- 운영 기간: {info['운영기간']}
- 현재 주요 고민: {info['주요고민']}

위 정보를 바탕으로 아래 두 가지를 분석해 주세요.

---

## 1. 경영 리스크 진단 (10가지)

이 사업체에서 가장 주의해야 할 경영 위험 요소 10가지를 찾아주세요.
각 항목마다:
- 위험 요소명
- 왜 위험한지 (구체적 상황 설명)
- 즉시 할 수 있는 대응 방안

발생 가능성 × 사업 영향 × 시급성을 기준으로 1위부터 순위를 매겨주세요.

---

## 2. 성장 전략 및 핵심 역량 (10가지)

대표님이 경쟁에서 살아남고 대체 불가능한 위치를 만들기 위한 핵심 역량과 전략 10가지를 제시해 주세요.
각 항목마다:
- 역량/전략명
- 왜 이것이 중요한지
- 실행 방법 (첫 번째 단계)

영향력 × 미래 수요 × 실행 속도를 기준으로 1위부터 순위를 매겨주세요."""


def stream_response(client: anthropic.Anthropic, messages: list) -> str:
    full_response = ""
    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text
    print()
    return full_response


def run() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("오류: ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        print(".env 파일에 ANTHROPIC_API_KEY=your_api_key 를 추가해 주세요.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    info = gather_business_info()

    messages: list[dict] = []
    messages.append({"role": "user", "content": build_initial_prompt(info)})

    print("\n" + "=" * 55)
    print("  분석 중입니다. 잠시만 기다려 주세요...")
    print("=" * 55 + "\n")

    response = stream_response(client, messages)
    messages.append({"role": "assistant", "content": response})

    while True:
        print("\n" + "-" * 55)
        print("추가로 궁금한 점을 질문하세요. (종료: q)")
        user_input = input("> ").strip()

        if user_input.lower() in {"q", "quit", "종료", "exit"}:
            print("\n컨설팅을 종료합니다. 감사합니다!")
            break

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        print("\n" + "=" * 55 + "\n")
        response = stream_response(client, messages)
        messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    run()
