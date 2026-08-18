#!/usr/bin/env python3
"""
채움(Chaeum) 이커머스 멀티 에이전트 시스템 - 메인 실행 파일

세 에이전트 (CEO / 마케팅팀장 / MD) 가 협업하여
  1. CEO가 분기 방향을 설정하고
  2. MD가 해외 사이트에서 마진 좋은 상품을 소싱·기획하고
  3. CEO가 검토 후 마케팅팀에 지시하고
  4. 마케팅팀이 채널별 캠페인을 기획하고
  5. CEO가 최종 사업 계획을 승인하는
자동화 워크플로우를 실행합니다.

사용법:
    # 기본 실행 (대화형)
    python main_ecommerce.py

    # 파라미터 지정
    python main_ecommerce.py --quarter "2025 Q2" --topic "감성 홈데코 신상품"

    # 조용한 모드 (결과만 파일 저장)
    python main_ecommerce.py --quiet

환경변수:
    ANTHROPIC_API_KEY: Anthropic API 키 (필수)
"""
import argparse
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


def print_banner() -> None:
    """시작 배너를 출력합니다."""
    banner = r"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║      채움(Chaeum) 이커머스 멀티 에이전트 시스템  v1.0               ║
║                                                                      ║
║   🏢 CEO Agent     — 전략 방향 설정 & 최종 의사결정                 ║
║   📣 Marketing Agent — 채널별 마케팅 캠페인 기획                    ║
║   🔍 MD Agent      — 해외 소싱 & 상품 기획서 작성                   ║
║                                                                      ║
║   세 에이전트가 실시간으로 소통하며 상품 기획 → 마케팅 전략을        ║
║   자동으로 수립합니다.  (Powered by Claude claude-sonnet-4-6)              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def check_api_key() -> str:
    """API 키를 확인하고 반환합니다."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("\n❌ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        print("   다음 중 하나의 방법으로 설정해주세요:\n")
        print("   1) .env 파일에 추가:")
        print("      ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx\n")
        print("   2) 환경변수로 설정:")
        print("      export ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx\n")
        print("   3) 실행 시 직접 입력 (아래 프롬프트)\n")

        api_key = input("   API 키를 직접 입력하세요 (건너뛰려면 Enter): ").strip()
        if not api_key:
            print("\n🚫 API 키 없이는 실행할 수 없습니다. 종료합니다.")
            sys.exit(1)
        os.environ["ANTHROPIC_API_KEY"] = api_key

    masked = api_key[:12] + "..." + api_key[-4:] if len(api_key) > 16 else "***"
    print(f"\n✅ API 키 확인됨: {masked}\n")
    return api_key


def get_user_inputs(args: argparse.Namespace) -> tuple[str, str, str]:
    """사용자로부터 세션 파라미터를 입력받습니다."""
    quarters = ["2025 Q1", "2025 Q2", "2025 Q3", "2025 Q4", "2026 Q1", "2026 Q2"]
    topics = [
        "감성 홈데코 & 인테리어 소품 신규 론칭",
        "건강/웰니스 라이프스타일 상품 발굴",
        "뷰티 & 스킨케어 해외 소싱 기획",
        "패션잡화 & 악세서리 트렌드 상품",
        "스마트홈 & 전자기기 소품 소싱",
        "반려동물 용품 신규 카테고리 진출",
    ]

    # quarter
    quarter = args.quarter
    if not quarter:
        print("\n📅 분기를 선택하세요:")
        for i, q in enumerate(quarters, 1):
            print(f"   {i}. {q}")
        choice = input(f"   선택 (1~{len(quarters)}, 기본 2): ").strip()
        try:
            idx = int(choice) - 1 if choice else 1
            quarter = quarters[max(0, min(idx, len(quarters) - 1))]
        except ValueError:
            quarter = quarters[1]
    print(f"   ✓ 선택된 분기: {quarter}")

    # topic
    topic = args.topic
    if not topic:
        print("\n🎯 이번 시즌 소싱/기획 주제를 선택하세요:")
        for i, t in enumerate(topics, 1):
            print(f"   {i}. {t}")
        print(f"   {len(topics)+1}. 직접 입력")
        choice = input(f"   선택 (1~{len(topics)+1}, 기본 1): ").strip()
        try:
            idx = int(choice) - 1 if choice else 0
            if idx == len(topics):
                topic = input("   주제 입력: ").strip() or topics[0]
            else:
                topic = topics[max(0, min(idx, len(topics) - 1))]
        except ValueError:
            topic = topics[0]
    print(f"   ✓ 선택된 주제: {topic}")

    # context
    context = args.context or ""
    if not context and not args.quiet:
        print("\n📝 추가 컨텍스트 (선택사항):")
        print("   예: '전분기 홈데코 매출 +40% 성장, 감성 캔들/향초 카테고리 주목'")
        context = input("   컨텍스트 (없으면 Enter): ").strip()

    return quarter, topic, context


def run_demo_mode() -> None:
    """API 키 없이 시스템 구조를 시연하는 데모 모드."""
    print("\n" + "─" * 70)
    print("  📋 데모 모드: 시스템 아키텍처 안내")
    print("─" * 70)
    print("""
채움(Chaeum) 이커머스 멀티 에이전트 시스템 구조:

┌─────────────────────────────────────────────────────────────────┐
│                    EcommerceOrchestrator                        │
│                   (에이전트 협업 관리자)                         │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  CEO Agent  │    │ Marketing Agent │    │    MD Agent     │
│  (대표이사) │    │ (마케팅팀장)     │    │ (소싱팀장)       │
│             │    │                 │    │                 │
│ • 방향 설정 │    │ • SNS 전략      │    │ • 해외 소싱 리서치 │
│ • 기획 검토 │    │ • 네이버 광고   │    │ • 마진 분석      │
│ • 예산 승인 │    │ • 인플루언서    │    │ • 상품 기획서    │
│ • 최종 결정 │    │ • ROI 계산      │    │ • 트렌드 분석    │
└─────────────┘    └─────────────────┘    └─────────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                    [공유 도구 (Tools)]
                    • search_web (DuckDuckGo)
                    • search_naver_shopping
                    • calculate_margin_analysis
                    • calculate_marketing_roi
                    • evaluate_business_metrics

워크플로우:
  Phase 0 → CEO 분기 오리엔테이션
  Phase 1 → MD 해외 소싱 리서치 + 상품 기획서
  Phase 2 → CEO 기획서 검토 + 마케팅팀 지시
  Phase 3 → 마케팅팀 채널별 캠페인 기획
  Phase 4 → CEO 최종 사업 계획 승인
  Phase 5 → JSON/TXT 보고서 저장

결과물:
  📦 상품 기획서 (소싱처, 원가, 마진율, 셀링포인트)
  📣 마케팅 기획서 (채널별 전략, 예산, KPI, 광고 카피)
  🏢 사업 계획서 (투자계획, 매출 목표, 실행 과제)
""")
    print("─" * 70)
    print("  실행하려면 ANTHROPIC_API_KEY를 설정하고 다시 시도해주세요.")
    print("─" * 70 + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="채움(Chaeum) 이커머스 멀티 에이전트 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main_ecommerce.py
  python main_ecommerce.py --quarter "2025 Q2" --topic "감성 홈데코 신상품"
  python main_ecommerce.py --quiet --report-dir ./output
  python main_ecommerce.py --demo
        """,
    )
    parser.add_argument(
        "--quarter", "-q",
        type=str,
        default="",
        help="대상 분기 (예: '2025 Q2')",
    )
    parser.add_argument(
        "--topic", "-t",
        type=str,
        default="",
        help="이번 시즌 소싱/기획 주제",
    )
    parser.add_argument(
        "--context", "-c",
        type=str,
        default="",
        help="추가 컨텍스트 (시장 상황, 전 분기 실적 등)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="에이전트 대화 출력 없이 조용한 모드로 실행",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="결과 파일 저장 안 함",
    )
    parser.add_argument(
        "--report-dir",
        type=str,
        default="reports",
        help="보고서 저장 디렉터리 (기본: reports/)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="API 키 없이 시스템 구조 시연 (데모 모드)",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="확인 프롬프트 생략 (자동 진행)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print_banner()

    # 데모 모드
    if args.demo:
        run_demo_mode()
        return

    # API 키 확인
    api_key = check_api_key()

    # 사용자 입력
    quarter, topic, context = get_user_inputs(args)

    # 확인
    print("\n" + "─" * 70)
    print(f"  🚀 실행 설정 확인")
    print("─" * 70)
    print(f"  분기: {quarter}")
    print(f"  주제: {topic}")
    print(f"  컨텍스트: {context or '없음'}")
    print(f"  출력 모드: {'조용한 모드' if args.quiet else '상세 모드'}")
    print(f"  보고서 저장: {'안 함' if args.no_save else args.report_dir}")
    print("─" * 70)

    if not args.quiet and not args.yes:
        try:
            confirm = input("\n  위 설정으로 실행하시겠습니까? (Enter: 확인 / q: 취소): ").strip()
            if confirm.lower() == "q":
                print("\n취소되었습니다.")
                return
        except EOFError:
            pass  # 비대화형 환경에서는 자동 진행

    print(f"\n  ⏳ 에이전트 시스템 초기화 중...\n")

    # 오케스트레이터 생성 및 실행
    try:
        from ecommerce_agents import EcommerceOrchestrator

        orchestrator = EcommerceOrchestrator(
            api_key=api_key,
            verbose=not args.quiet,
        )

        start_time = time.time()
        session = orchestrator.run(
            quarter=quarter,
            topic=topic,
            context=context,
            save_report=not args.no_save,
            report_dir=args.report_dir,
        )
        elapsed = time.time() - start_time

        # 최종 요약
        print("\n" + "═" * 70)
        print("  📊 세션 요약")
        print("═" * 70)
        print(f"  세션 ID: {session.session_id}")
        print(f"  주제: {session.topic}")
        print(f"  에이전트 메시지 수: {len(session.messages)}건")
        print(f"  소요 시간: {elapsed:.1f}초")
        if not args.no_save:
            print(f"  보고서 저장 위치: {args.report_dir}/")
        print("═" * 70)
        print("\n✅ 채움(Chaeum) 이커머스 멀티 에이전트 시스템 실행 완료!\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}\n")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
