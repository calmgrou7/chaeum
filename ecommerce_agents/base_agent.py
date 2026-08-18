"""
채움(Chaeum) 이커머스 멀티 에이전트 시스템 - 베이스 에이전트
Claude API와 tool_use를 이용한 에이전트 실행 루프 공통 구현
"""
import json
import time
from typing import Any, Callable, Optional

import anthropic

from .tools import TOOL_REGISTRY

# 기본 모델: claude-sonnet-4-6
DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8096
MAX_TOOL_ROUNDS = 8  # 무한루프 방지용 최대 도구 호출 횟수


class BaseAgent:
    """
    Claude API를 감싸는 에이전트 베이스 클래스.
    - system_prompt: 에이전트의 역할/페르소나 정의
    - tools: 이 에이전트가 사용할 수 있는 도구 목록 (Claude tool_use 스키마)
    - conversation_history: 멀티턴 대화 이력 (에이전트 세션 동안 누적)
    """

    def __init__(
        self,
        client: anthropic.Anthropic,
        role_name: str,
        system_prompt: str,
        tools: list[dict],
        on_tool_call: Optional[Callable[[str, dict, Any], None]] = None,
    ) -> None:
        self.client = client
        self.role_name = role_name
        self.system_prompt = system_prompt
        self.tools = tools
        self.on_tool_call = on_tool_call          # 도구 호출 시 콜백 (로깅용)
        self.conversation_history: list[dict] = []

    # ──────────────────────────────────────────────────────────
    # 공개 인터페이스
    # ──────────────────────────────────────────────────────────

    def chat(self, user_message: str) -> str:
        """
        단일 메시지를 에이전트에 전달하고 최종 텍스트 응답을 반환합니다.
        도구 호출이 필요한 경우 자동으로 실행하고 결과를 Claude에 피드백합니다.
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        for _ in range(MAX_TOOL_ROUNDS):
            response = self._call_api()

            if response.stop_reason == "end_turn":
                text = self._extract_text(response)
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content,
                })
                return text

            if response.stop_reason == "tool_use":
                # 도구 호출 결과를 히스토리에 추가한 뒤 다시 Claude에 전달
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content,
                })
                tool_results = self._execute_tools(response.content)
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results,
                })
            else:
                # 예상치 못한 stop_reason
                break

        # 루프 초과 → 마지막 텍스트 블록 반환
        return self._extract_text(response)

    def reset_history(self) -> None:
        """대화 이력을 초기화합니다 (새 태스크 시작 시 호출)."""
        self.conversation_history.clear()

    # ──────────────────────────────────────────────────────────
    # 내부 헬퍼
    # ──────────────────────────────────────────────────────────

    def _call_api(self) -> anthropic.types.Message:
        """Claude API를 호출합니다. 429/529 에러 시 지수 백오프로 재시도합니다."""
        delays = [2, 4, 8, 16]
        last_err: Exception | None = None
        for attempt, delay in enumerate([0] + delays):
            if delay:
                time.sleep(delay)
            try:
                kwargs: dict[str, Any] = {
                    "model": DEFAULT_MODEL,
                    "max_tokens": MAX_TOKENS,
                    "system": self.system_prompt,
                    "messages": self.conversation_history,
                }
                if self.tools:
                    kwargs["tools"] = self.tools
                return self.client.messages.create(**kwargs)
            except anthropic.RateLimitError as e:
                last_err = e
            except anthropic.APIStatusError as e:
                if e.status_code in (529, 503):
                    last_err = e
                else:
                    raise
        raise RuntimeError(f"Claude API 호출 실패 (재시도 소진): {last_err}") from last_err

    def _execute_tools(self, content_blocks: list) -> list[dict]:
        """tool_use 블록들을 실행하고 tool_result 목록을 반환합니다."""
        results = []
        for block in content_blocks:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input
            tool_id = block.id

            # 콜백 (로깅/UI 업데이트)
            if self.on_tool_call:
                self.on_tool_call(tool_name, tool_input, None)

            # 실제 함수 실행
            fn = TOOL_REGISTRY.get(tool_name)
            if fn is None:
                result_str = json.dumps({"error": f"알 수 없는 도구: {tool_name}"}, ensure_ascii=False)
            else:
                try:
                    raw_result = fn(**tool_input)
                    result_str = json.dumps(raw_result, ensure_ascii=False, indent=2)
                except Exception as e:
                    result_str = json.dumps({"error": f"도구 실행 오류: {e}"}, ensure_ascii=False)

            if self.on_tool_call:
                self.on_tool_call(tool_name, tool_input, result_str)

            results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": result_str,
            })
        return results

    @staticmethod
    def _extract_text(response: anthropic.types.Message) -> str:
        """응답 컨텐츠 블록에서 텍스트를 추출합니다."""
        texts = [
            block.text
            for block in response.content
            if hasattr(block, "text")
        ]
        return "\n".join(texts).strip()
