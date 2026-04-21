from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .agents.cto_agent import CTOAgent
from .agents.design_agent import DesignAgent
from .agents.dev_agent import DevAgent
from .agents.management_agent import ManagementAgent
from .agents.marketing_agent import MarketingAgent
from .agents.planning_agent import PlanningAgent
from .agents.research_agent import ResearchAgent
from .message_bus import AgentName, Message, MessageBus, MessageType, Priority
from .state.project_state import AgentTask, ProjectState, TaskStatus
from .state.state_store import StateStore


class ProjectOrchestrator:
    """
    CEO 입력부터 최종 승인까지 전체 워크플로우를 조율한다.

    Phase 1 - 리서치:    ResearchAgent 실행
    Phase 2 - 기획:      PlanningAgent 실행 (리서치 결과 활용)
    Phase 3 - CTO 검토:  CTOAgent 실행 → Dev/Design 위임 처리
    Phase 4 - 경영 계획: ManagementAgent 실행
    Phase 5 - 마케팅:    MarketingAgent 실행
    Phase 6 - CEO 최종:  전체 결과 통합 보고 → CEO 승인
    """

    def __init__(
        self,
        state: ProjectState,
        bus: MessageBus,
        store: StateStore,
        api_key: str,
    ):
        self.state = state
        self.bus = bus
        self.store = store
        kwargs = dict(bus=bus, state=state, store=store, api_key=api_key)
        self.agents = {
            AgentName.RESEARCH: ResearchAgent(**kwargs),
            AgentName.PLANNING: PlanningAgent(**kwargs),
            AgentName.CTO: CTOAgent(**kwargs),
            AgentName.APP_DEV: DevAgent(**kwargs),
            AgentName.DESIGN: DesignAgent(**kwargs),
            AgentName.MANAGEMENT: ManagementAgent(**kwargs),
            AgentName.MARKETING: MarketingAgent(**kwargs),
        }

    # ------------------------------------------------------------------
    # Main workflow entry point
    # ------------------------------------------------------------------

    def run_full_workflow(self, ceo_request: str) -> None:
        self._banner(f"프로젝트 시작: {self.state.project_name}")

        self._phase_header("Phase 1 · 리서치팀 — 시장 조사")
        self._run_agent(
            AgentName.RESEARCH,
            f"다음 앱에 대한 시장 리서치를 수행하세요: {ceo_request}",
        )

        self._phase_header("Phase 2 · 기획팀 — 프로젝트 기획")
        self._run_agent(
            AgentName.PLANNING,
            "리서치 결과를 바탕으로 프로젝트 계획을 수립하세요. "
            "read_agent_output('리서치팀')으로 리서치 결과를 먼저 확인하세요.",
        )
        self._process_ceo_approvals()

        self._phase_header("Phase 3 · 총괄CTO — 기술 검토 및 팀 위임")
        self._run_agent(
            AgentName.CTO,
            "기획안을 검토하고 기술 스택을 결정한 뒤, "
            "앱개발팀과 디자인팀에 작업을 위임하세요. "
            "read_agent_output('기획팀')으로 기획 결과를 먼저 확인하세요.",
        )
        self._flush_cto_delegations()
        self._process_ceo_approvals()

        self._phase_header("Phase 4 · 경영팀 — 자원 및 예산 계획")
        self._run_agent(
            AgentName.MANAGEMENT,
            "모든 팀의 결과물을 바탕으로 자원 계획과 예산을 수립하세요. "
            "read_agent_output을 사용하여 기획팀, 앱개발팀, 디자인팀 결과를 확인하세요.",
        )
        self._process_ceo_approvals()

        self._phase_header("Phase 5 · 마케팅팀 — 출시 전략")
        self._run_agent(
            AgentName.MARKETING,
            "앱 출시를 위한 마케팅 전략을 수립하세요. "
            "read_agent_output으로 리서치팀과 기획팀 결과를 확인하세요.",
        )
        self._process_ceo_approvals()

        self._phase_header("Phase 6 · CEO 최종 보고")
        self._present_final_report()

    # ------------------------------------------------------------------
    # Agent execution
    # ------------------------------------------------------------------

    def _run_agent(self, agent_name: AgentName, task: str, context: dict | None = None) -> dict:
        self.state.tasks[agent_name.value] = AgentTask(
            agent=agent_name.value,
            task_name=task[:60],
            status=TaskStatus.IN_PROGRESS,
            started_at=datetime.now().isoformat(),
        )
        self.state.phase = agent_name.value
        self.store.save(self.state)

        result = self.agents[agent_name].run(task, context)

        self.state.tasks[agent_name.value].status = TaskStatus.DONE
        self.state.tasks[agent_name.value].output = result
        self.state.tasks[agent_name.value].completed_at = datetime.now().isoformat()
        self.state.outputs[agent_name.value] = result
        self.store.save(self.state)
        return result

    def _flush_cto_delegations(self) -> None:
        """CTO가 버스에 보낸 Dev/Design 위임 메시지를 처리한다."""
        for target in (AgentName.APP_DEV, AgentName.DESIGN):
            messages = self.bus.receive(target)
            for msg in messages:
                if msg.msg_type == MessageType.TASK_REQUEST:
                    label = "앱개발팀" if target == AgentName.APP_DEV else "디자인팀"
                    self._phase_header(f"  ↳ CTO 위임: {label}")
                    self._run_agent(
                        target,
                        json.dumps(msg.content, ensure_ascii=False),
                        context={"cto_instruction": msg.subject},
                    )

    # ------------------------------------------------------------------
    # CEO approval gate
    # ------------------------------------------------------------------

    def _process_ceo_approvals(self) -> None:
        ceo_msgs = self.bus.receive(AgentName.CEO)
        for msg in ceo_msgs:
            if not msg.requires_ceo_approval:
                continue
            self._print_approval_request(msg)
            decision, notes = self._get_ceo_decision()
            self._record_ceo_decision(msg, decision, notes)

            reply = Message(
                sender=AgentName.CEO,
                recipient=msg.sender,
                msg_type=MessageType.CEO_DECISION,
                subject=f"Re: {msg.subject}",
                content={"decision": decision, "notes": notes},
                reply_to=msg.message_id,
            )
            self.bus.send(reply)

    def _print_approval_request(self, msg: Message) -> None:
        sep = "=" * 60
        print(f"\n{sep}")
        print(f"  [CEO 승인 요청] {msg.subject}")
        print(f"  발신: {msg.sender.value}")
        print(f"  요약: {msg.content.get('summary', '')}")
        print(f"  {'-'*56}")
        details = msg.content.get("details", {})
        for k, v in details.items():
            v_str = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
            print(f"  {k}: {v_str[:120]}")
        print(sep)

    def _get_ceo_decision(self) -> tuple[str, str]:
        decision_map = {"y": "approved", "n": "rejected", "m": "modify"}
        while True:
            choice = input("\n  결정 [y=승인 / n=거부 / m=수정요청]: ").strip().lower()
            if choice in decision_map:
                break
        notes = ""
        if choice in ("n", "m"):
            notes = input("  피드백 메모 (Enter 건너뜀): ").strip()
        return decision_map[choice], notes

    def _record_ceo_decision(self, msg: Message, decision: str, notes: str) -> None:
        self.state.ceo_decisions.append(
            {
                "message_id": msg.message_id,
                "subject": msg.subject,
                "from_agent": msg.sender.value,
                "decision": decision,
                "notes": notes,
                "decided_at": datetime.now().isoformat(),
            }
        )
        self.store.save(self.state)

    # ------------------------------------------------------------------
    # Final consolidated report
    # ------------------------------------------------------------------

    def _present_final_report(self) -> None:
        report = self._build_report()
        self._print_report(report)

        out_path = self.store.save_agent_output(
            self.state.project_id, "final_report", report
        )
        print(f"\n  종합 보고서 저장됨: {out_path}")

        sep = "=" * 60
        print(f"\n{sep}")
        print("  [최종 CEO 결재] 프로젝트를 승인하시겠습니까?")
        print(sep)

        while True:
            choice = input("  결정 [y=승인 / n=거부]: ").strip().lower()
            if choice in ("y", "n"):
                break

        notes = ""
        if choice == "n":
            notes = input("  거부 이유: ").strip()

        self.state.final_approved = (choice == "y")
        self.state.ceo_decisions.append(
            {
                "type": "final_approval",
                "decision": "approved" if self.state.final_approved else "rejected",
                "notes": notes,
                "decided_at": datetime.now().isoformat(),
            }
        )
        self.store.save(self.state)

        status_label = "✅ 승인됨 — 프로젝트 실행 단계로 진입합니다." if self.state.final_approved else "❌ 거부됨"
        print(f"\n  {status_label}")
        print(f"  프로젝트 ID: {self.state.project_id}")

    def _build_report(self) -> dict[str, Any]:
        def _load(name: str) -> Any:
            return self.store.load_agent_output(self.state.project_id, name)

        return {
            "project_id": self.state.project_id,
            "project_name": self.state.project_name,
            "generated_at": datetime.now().isoformat(),
            "research": _load(AgentName.RESEARCH.value),
            "planning": _load(AgentName.PLANNING.value),
            "cto_overview": _load(AgentName.CTO.value),
            "dev_spec": _load(AgentName.APP_DEV.value),
            "design_spec": _load(AgentName.DESIGN.value),
            "management": _load(AgentName.MANAGEMENT.value),
            "marketing": _load(AgentName.MARKETING.value),
            "ceo_decisions": self.state.ceo_decisions,
        }

    def _print_report(self, report: dict) -> None:
        sep = "=" * 60
        print(f"\n{sep}")
        print(f"  종합 프로젝트 보고서: {report['project_name']}")
        print(sep)

        sections = [
            ("리서치팀", "research"),
            ("기획팀", "planning"),
            ("총괄CTO", "cto_overview"),
            ("앱개발팀", "dev_spec"),
            ("디자인팀", "design_spec"),
            ("경영팀", "management"),
            ("마케팅팀", "marketing"),
        ]

        for label, key in sections:
            data = report.get(key)
            if not data:
                print(f"\n  [{label}] 결과 없음")
                continue
            print(f"\n  [{label}]")
            for k, v in data.items():
                v_str = (
                    json.dumps(v, ensure_ascii=False)[:150]
                    if isinstance(v, (dict, list))
                    else str(v)[:150]
                )
                print(f"    {k}: {v_str}")

        if report["ceo_decisions"]:
            print(f"\n  [CEO 결재 이력] 총 {len(report['ceo_decisions'])}건")
            for d in report["ceo_decisions"]:
                print(f"    • {d.get('subject', d.get('type', '?'))} → {d['decision']}")

        print(f"\n{sep}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _banner(self, text: str) -> None:
        sep = "=" * 60
        print(f"\n{sep}")
        print(f"  {text}")
        print(sep)

    def _phase_header(self, text: str) -> None:
        print(f"\n{'─'*60}")
        print(f"  {text}")
        print(f"{'─'*60}")
