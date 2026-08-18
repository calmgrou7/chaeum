"""
채움(Chaeum) 이커머스 멀티 에이전트 시스템 - 오케스트레이터
CEO / 마케팅팀장 / MD 세 에이전트가 협업하는 자동화 워크플로우를 관리합니다.

워크플로우:
  Phase 0: CEO 분기 오리엔테이션 (방향 설정)
  Phase 1: MD 상품 리서치 + 기획서 작성
  Phase 2: CEO 상품 기획서 검토 + 마케팅팀 지시
  Phase 3: 마케팅팀 채널별 캠페인 기획
  Phase 4: CEO 최종 사업 계획 승인
  Phase 5: 결과 보고서 저장
"""
import json
import os
import uuid
from datetime import datetime
from typing import Callable, Optional

import anthropic

from .ceo_agent import CEOAgent
from .marketing_agent import MarketingAgent
from .md_agent import MDAgent
from .models import AgentMessage, AgentRole, AgentSession, MessageType


# ──────────────────────────────────────────────────────────────
# ANSI 컬러 코드 (rich 없이 예쁜 터미널 출력)
# ──────────────────────────────────────────────────────────────
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_DARK = "\033[40m"
    BG_BLUE = "\033[44m"


def _header(text: str, color: str = Colors.CYAN) -> str:
    line = "─" * 70
    return f"\n{color}{Colors.BOLD}{line}\n  {text}\n{line}{Colors.RESET}\n"


def _speaker(role: AgentRole, color: str) -> str:
    return f"{color}{Colors.BOLD}[{role.value}]{Colors.RESET}"


ROLE_COLORS = {
    AgentRole.CEO: Colors.YELLOW,
    AgentRole.MARKETING: Colors.MAGENTA,
    AgentRole.MD: Colors.GREEN,
}


class EcommerceOrchestrator:
    """
    세 에이전트를 조율하는 메인 오케스트레이터.

    사용 예:
        orchestrator = EcommerceOrchestrator(api_key="sk-...")
        orchestrator.run(quarter="2025 Q2", topic="라이프스타일 소품 신상품 론칭")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        verbose: bool = True,
        on_phase_change: Optional[Callable[[int, str], None]] = None,
    ) -> None:
        """
        Args:
            api_key: Anthropic API 키 (없으면 ANTHROPIC_API_KEY 환경변수 사용)
            verbose: 에이전트 대화를 터미널에 출력할지 여부
            on_phase_change: 페이즈 변경 시 호출되는 콜백 함수
        """
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY가 설정되지 않았습니다.\n"
                "환경변수를 설정하거나 api_key 파라미터를 전달하세요."
            )

        self.client = anthropic.Anthropic(api_key=api_key)
        self.verbose = verbose
        self.on_phase_change = on_phase_change

        # 에이전트 초기화
        self.ceo = CEOAgent(
            client=self.client,
            on_tool_call=self._on_tool_call,
        )
        self.marketing = MarketingAgent(
            client=self.client,
            on_tool_call=self._on_tool_call,
        )
        self.md = MDAgent(
            client=self.client,
            on_tool_call=self._on_tool_call,
        )

        self.session: Optional[AgentSession] = None

    # ──────────────────────────────────────────────────────────
    # 메인 실행 엔트리포인트
    # ──────────────────────────────────────────────────────────

    def run(
        self,
        quarter: str = "2025 Q2",
        topic: str = "신규 시즌 상품 기획",
        context: str = "",
        save_report: bool = True,
        report_dir: str = "reports",
    ) -> AgentSession:
        """
        전체 멀티 에이전트 워크플로우를 실행합니다.

        Args:
            quarter: 대상 분기 (예: "2025 Q2")
            topic: 이번 세션의 주제/과제
            context: 추가 컨텍스트 (시장 상황, 전 분기 실적 등)
            save_report: 결과를 파일로 저장할지 여부
            report_dir: 보고서 저장 디렉터리

        Returns:
            AgentSession: 전체 세션 결과
        """
        session_id = str(uuid.uuid4())[:8]
        self.session = AgentSession(
            session_id=session_id,
            topic=topic,
        )

        self._print(_header(
            f"채움(Chaeum) 이커머스 멀티 에이전트 시스템 v1.0\n"
            f"  세션 ID: {session_id} | {quarter} | {topic}",
            Colors.CYAN,
        ))

        # ── Phase 0: CEO 분기 오리엔테이션 ──────────────────────
        phase0_result = self._phase_0_orientation(quarter, context)

        # ── Phase 1: MD 상품 리서치 ──────────────────────────────
        phase1_result = self._phase_1_md_research(quarter, topic, phase0_result)

        # ── Phase 2: CEO 기획서 검토 + 마케팅팀 지시 ─────────────
        phase2_result = self._phase_2_ceo_review(phase1_result)

        # ── Phase 3: 마케팅팀 캠페인 기획 ──────────────────────────
        phase3_result = self._phase_3_marketing_plans(phase1_result, phase2_result)

        # ── Phase 4: CEO 최종 승인 ──────────────────────────────
        phase4_result = self._phase_4_final_decision(phase1_result, phase3_result, phase2_result)

        # ── Phase 5: 보고서 저장 ────────────────────────────────
        if save_report:
            self._save_report(report_dir)

        self._print(_header("✅ 모든 에이전트 협업이 완료되었습니다!", Colors.GREEN))
        self._print(
            f"{Colors.CYAN}📁 결과 보고서: {report_dir}/session_{session_id}.json{Colors.RESET}\n"
            if save_report else ""
        )

        return self.session

    # ──────────────────────────────────────────────────────────
    # Phase별 구현
    # ──────────────────────────────────────────────────────────

    def _phase_0_orientation(self, quarter: str, context: str) -> str:
        """Phase 0: CEO가 분기 방향을 설정합니다."""
        self._start_phase(0, "CEO 분기 오리엔테이션 & 방향 설정")

        result = self.ceo.set_quarterly_direction(quarter, context)

        self._record_message(AgentRole.CEO, AgentRole.MD, MessageType.BRIEFING, result)
        self._record_message(AgentRole.CEO, AgentRole.MARKETING, MessageType.BRIEFING, result)
        self._print_agent_response(AgentRole.CEO, result)

        return result

    def _phase_1_md_research(
        self, quarter: str, topic: str, ceo_orientation: str
    ) -> str:
        """Phase 1: MD가 해외 소싱 리서치 후 상품 기획서를 제출합니다."""
        self._start_phase(1, "MD 해외 소싱 리서치 & 상품 기획서 작성")

        briefing = f"""
[{quarter} MD 업무 지시]
이번 시즌 주제: {topic}

CEO 오리엔테이션 주요 내용:
{ceo_orientation[:800]}

위 방향성을 바탕으로 해외 소싱 리서치를 진행하고,
마진율 45% 이상, 트렌드 점수 7점 이상인 유망 상품 3~4개를 발굴해 기획서를 제출해주세요.
"""
        result = self.md.research_and_propose(briefing)

        self._record_message(AgentRole.MD, AgentRole.CEO, MessageType.PROPOSAL, result)
        self._print_agent_response(AgentRole.MD, result)

        return result

    def _phase_2_ceo_review(self, md_proposals: str) -> str:
        """Phase 2: CEO가 MD 기획서를 검토하고 마케팅팀에 지시합니다."""
        self._start_phase(2, "CEO 상품 기획서 검토 & 마케팅팀 지시")

        result = self.ceo.review_md_proposals(md_proposals)

        self._record_message(AgentRole.CEO, AgentRole.MD, MessageType.RESPONSE, result)
        self._record_message(AgentRole.CEO, AgentRole.MARKETING, MessageType.BRIEFING, result)
        self._print_agent_response(AgentRole.CEO, result)

        return result

    def _phase_3_marketing_plans(
        self, md_proposals: str, ceo_direction: str
    ) -> str:
        """Phase 3: 마케팅팀이 채널별 캠페인 기획서를 작성합니다."""
        self._start_phase(3, "마케팅팀 채널별 캠페인 기획서 작성")

        result = self.marketing.create_marketing_plans(
            ceo_direction=ceo_direction,
            product_proposals=md_proposals,
        )

        self._record_message(AgentRole.MARKETING, AgentRole.CEO, MessageType.PROPOSAL, result)
        self._print_agent_response(AgentRole.MARKETING, result)

        # 마케팅팀 실행 체크리스트 추가
        self._print(
            f"\n{Colors.MAGENTA}{Colors.BOLD}  ↳ 실행 체크리스트 작성 중...{Colors.RESET}\n"
        )
        checklist = self.marketing.create_launch_checklist(result)
        self._record_message(AgentRole.MARKETING, AgentRole.CEO, MessageType.RESPONSE, checklist)
        self._print_agent_response(AgentRole.MARKETING, checklist, title="실행 체크리스트")

        return result

    def _phase_4_final_decision(
        self,
        md_proposals: str,
        marketing_plans: str,
        ceo_initial_review: str,
    ) -> str:
        """Phase 4: CEO가 최종 사업 계획을 결정합니다."""
        self._start_phase(4, "CEO 최종 사업 계획 승인 & 팀 공유")

        result = self.ceo.make_final_decision(
            md_proposals=md_proposals,
            marketing_plans=marketing_plans,
            ceo_initial_review=ceo_initial_review,
        )

        self._record_message(AgentRole.CEO, AgentRole.MD, MessageType.DECISION, result)
        self._record_message(AgentRole.CEO, AgentRole.MARKETING, MessageType.DECISION, result)
        self._print_agent_response(AgentRole.CEO, result, title="최종 사업 계획서")

        return result

    # ──────────────────────────────────────────────────────────
    # 유틸리티
    # ──────────────────────────────────────────────────────────

    def _start_phase(self, phase_num: int, phase_name: str) -> None:
        phase_colors = {
            0: Colors.YELLOW,
            1: Colors.GREEN,
            2: Colors.YELLOW,
            3: Colors.MAGENTA,
            4: Colors.YELLOW,
        }
        color = phase_colors.get(phase_num, Colors.CYAN)
        self._print(_header(f"Phase {phase_num}: {phase_name}", color))
        if self.on_phase_change:
            self.on_phase_change(phase_num, phase_name)

    def _print_agent_response(
        self,
        role: AgentRole,
        response: str,
        title: str = "",
    ) -> None:
        if not self.verbose:
            return
        color = ROLE_COLORS.get(role, Colors.WHITE)
        speaker = _speaker(role, color)
        label = f" — {title}" if title else ""
        print(f"\n{speaker}{label}\n")
        # 긴 응답은 그대로 출력
        print(f"{response}\n")
        print(f"{color}{'─' * 70}{Colors.RESET}\n")

    def _print(self, text: str) -> None:
        if self.verbose:
            print(text)

    def _record_message(
        self,
        sender: AgentRole,
        recipient: AgentRole,
        msg_type: MessageType,
        content: str,
    ) -> None:
        if self.session:
            self.session.add_message(
                AgentMessage(
                    sender=sender,
                    recipient=recipient,
                    message_type=msg_type,
                    content=content,
                )
            )

    def _on_tool_call(self, tool_name: str, tool_input: dict, result) -> None:
        if not self.verbose:
            return
        if result is None:
            # 도구 호출 시작
            print(
                f"  {Colors.CYAN}🔧 도구 호출: {Colors.BOLD}{tool_name}{Colors.RESET}"
                f"{Colors.CYAN} | 입력: {json.dumps(tool_input, ensure_ascii=False, separators=(',',':'))[:100]}...{Colors.RESET}"
            )
        else:
            # 도구 결과
            preview = str(result)[:120].replace("\n", " ")
            print(
                f"  {Colors.GREEN}✓ 도구 결과 ({tool_name}): {preview}...{Colors.RESET}\n"
            )

    def _save_report(self, report_dir: str) -> None:
        if not self.session:
            return

        os.makedirs(report_dir, exist_ok=True)
        session_id = self.session.session_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON 전체 세션 저장
        json_path = os.path.join(report_dir, f"session_{session_id}_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.session.to_dict(), f, ensure_ascii=False, indent=2)

        # 텍스트 요약 저장
        txt_path = os.path.join(report_dir, f"summary_{session_id}_{timestamp}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"채움(Chaeum) 이커머스 멀티 에이전트 시스템 결과 보고서\n")
            f.write(f"세션 ID: {session_id}\n")
            f.write(f"주제: {self.session.topic}\n")
            f.write(f"생성 시각: {timestamp}\n\n")
            f.write("=" * 70 + "\n\n")
            for i, msg in enumerate(self.session.messages, 1):
                f.write(
                    f"[{i}] {msg.sender} → {msg.recipient} ({msg.message_type})\n"
                    f"{msg.timestamp}\n\n"
                    f"{msg.content}\n\n"
                    f"{'─' * 70}\n\n"
                )

        if self.verbose:
            print(
                f"\n{Colors.CYAN}💾 보고서 저장 완료:{Colors.RESET}\n"
                f"  📄 JSON: {json_path}\n"
                f"  📝 요약: {txt_path}\n"
            )
