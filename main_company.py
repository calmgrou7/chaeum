#!/usr/bin/env python3
"""
main_company.py — 채움 앱개발 회사 종합 에이전트 시스템

사용법:
  python main_company.py "배달 앱 개발해줘"
  python main_company.py "헬스케어 앱 기획해줘" --model claude-opus-4-7
  python main_company.py --resume --project-id proj_20260421_abc123
  python main_company.py --list-projects
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from app_dev_company.message_bus import MessageBus
from app_dev_company.orchestrator import ProjectOrchestrator
from app_dev_company.state.project_state import ProjectState
from app_dev_company.state.state_store import StateStore


def _generate_project_id() -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    short_id = str(uuid.uuid4())[:6]
    return f"proj_{date_str}_{short_id}"


def _print_project_list(store: StateStore) -> None:
    projects = store.list_projects()
    if not projects:
        print("  저장된 프로젝트가 없습니다.")
        return

    sep = "=" * 60
    print(f"\n{sep}")
    print("  저장된 프로젝트 목록")
    print(sep)
    for pid in projects:
        state = store.load(pid)
        if state:
            status = "✅ 승인됨" if state.final_approved else f"⏳ {state.phase}"
            print(f"  • {pid}")
            print(f"      이름: {state.project_name}")
            print(f"      상태: {status}")
            print(f"      생성: {state.created_at[:10]}")
    print(sep)


def _print_welcome() -> None:
    sep = "=" * 60
    print(f"\n{sep}")
    print("  채움 앱개발 회사 종합 에이전트 시스템")
    print(f"  {'─'*54}")
    print("  CEO(당신)가 지시하면 에이전트들이 자율적으로 협업합니다.")
    print(f"{'─'*56}")
    print("  부서: 리서치팀 · 기획팀 · 총괄CTO · 앱개발팀 ·")
    print("        디자인팀 · 경영팀 · 마케팅팀")
    print(sep)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="채움 앱개발 회사 종합 에이전트 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main_company.py "배달 앱 개발해줘"
  python main_company.py "헬스케어 앱 기획해줘" --model claude-opus-4-7
  python main_company.py --resume --project-id proj_20260421_abc123
  python main_company.py --list-projects
        """,
    )
    parser.add_argument(
        "request",
        nargs="?",
        help="CEO 지시사항 (예: '배달 앱 개발해줘')",
    )
    parser.add_argument("--project-id", help="재개할 프로젝트 ID")
    parser.add_argument("--resume", action="store_true", help="중단된 프로젝트 재개")
    parser.add_argument("--list-projects", action="store_true", help="프로젝트 목록 출력")
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Claude 모델 (기본: claude-sonnet-4-6)",
    )
    parser.add_argument("--api-key", help="Anthropic API 키 (기본: ANTHROPIC_API_KEY 환경변수)")
    parser.add_argument("--yes", "-y", action="store_true", help="모든 CEO 승인을 자동으로 통과")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        print(
            "오류: ANTHROPIC_API_KEY 환경변수 또는 --api-key 옵션이 필요합니다.\n"
            "  .env 파일에 ANTHROPIC_API_KEY=your_key 를 추가하세요."
        )
        sys.exit(1)

    store = StateStore()

    if args.list_projects:
        _print_project_list(store)
        return

    _print_welcome()

    # ── 프로젝트 초기화 또는 재개 ─────────────────────────────────────
    if args.resume:
        if not args.project_id:
            print("오류: --resume 사용 시 --project-id 가 필요합니다.")
            sys.exit(1)
        state = store.load(args.project_id)
        if not state:
            print(f"오류: 프로젝트를 찾을 수 없습니다: {args.project_id}")
            sys.exit(1)
        ceo_request = state.description
        print(f"\n  [재개] 프로젝트: {state.project_name} (ID: {state.project_id})")
    else:
        ceo_request = args.request
        if not ceo_request:
            print("오류: CEO 지시사항을 입력하세요.")
            print("  예시: python main_company.py \"배달 앱 개발해줘\"")
            sys.exit(1)

        project_id = _generate_project_id()
        state = ProjectState(
            project_id=project_id,
            project_name=ceo_request[:50],
            description=ceo_request,
            created_at=datetime.now().isoformat(),
        )
        store.save(state)
        print(f"\n  새 프로젝트 생성됨")
        print(f"  ID     : {project_id}")
        print(f"  지시사항: {ceo_request}")

    # ── 에이전트 모델 override ──────────────────────────────────────────
    # (각 에이전트가 인스턴스화될 때 MODEL 클래스 변수를 설정)
    from app_dev_company.agents import base_agent
    base_agent.BaseAgent.MODEL = args.model

    # ── 버스 & 오케스트레이터 ───────────────────────────────────────────
    bus = MessageBus(project_id=state.project_id)
    log_path = Path("results/projects") / state.project_id / "messages.jsonl"
    bus.set_log_path(log_path)

    orchestrator = ProjectOrchestrator(state, bus, store, api_key, auto_approve=args.yes)
    orchestrator.run_full_workflow(ceo_request)

    print(f"\n  모든 결과가 results/projects/{state.project_id}/ 에 저장되었습니다.")


if __name__ == "__main__":
    main()
