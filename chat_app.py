"""
채움(Chaeum) 이커머스 멀티 에이전트 - 카카오톡 스타일 채팅 UI
Flask + SSE로 에이전트 대화를 실시간 채팅으로 표시합니다.
"""
import json
import os
import queue
import threading
import time
from datetime import datetime
from typing import Optional

from flask import Flask, Response, jsonify, render_template, request, stream_with_context

app = Flask(__name__, template_folder="templates")

# 전역 메시지 큐 (SSE 스트리밍용)
_msg_queue: queue.Queue = queue.Queue()
_run_lock = threading.Lock()
_is_running = False


def _emit(event_type: str, data: dict) -> None:
    """SSE 이벤트를 큐에 추가합니다."""
    _msg_queue.put({"event": event_type, "data": data})


def _run_workflow(quarter: str, topic: str, context: str, api_key: str) -> None:
    """백그라운드 스레드에서 멀티 에이전트 워크플로우를 실행합니다."""
    global _is_running
    try:
        # 오케스트레이터를 동적으로 임포트 (스레드 안에서)
        from ecommerce_agents.orchestrator import EcommerceOrchestrator
        from ecommerce_agents.models import AgentRole

        # 에이전트별 색상/이모지 (카카오톡 프로필처럼)
        AGENT_META = {
            AgentRole.CEO: {"name": "CEO 대표이사", "emoji": "👔", "color": "ceo"},
            AgentRole.MARKETING: {"name": "마케팅팀장", "emoji": "📣", "color": "marketing"},
            AgentRole.MD: {"name": "MD 소싱팀장", "emoji": "🛒", "color": "md"},
        }

        def on_phase_change(phase_num: int, phase_name: str) -> None:
            _emit("phase", {
                "phase": phase_num,
                "name": phase_name,
                "time": datetime.now().strftime("%H:%M"),
            })

        def on_tool_call(tool_name: str, tool_input: dict, result) -> None:
            if result is None:
                _emit("tool_start", {
                    "tool": tool_name,
                    "input": json.dumps(tool_input, ensure_ascii=False)[:80],
                    "time": datetime.now().strftime("%H:%M"),
                })
            else:
                preview = str(result)[:100].replace("\n", " ")
                _emit("tool_end", {
                    "tool": tool_name,
                    "preview": preview,
                    "time": datetime.now().strftime("%H:%M"),
                })

        orchestrator = EcommerceOrchestrator(
            api_key=api_key,
            verbose=False,
            on_phase_change=on_phase_change,
        )

        # 각 에이전트의 on_tool_call 콜백 연결
        orchestrator.ceo.on_tool_call = on_tool_call
        orchestrator.marketing.on_tool_call = on_tool_call
        orchestrator.md.on_tool_call = on_tool_call

        # ── Phase별 메시지를 SSE로 전송하기 위해 오케스트레이터 래핑 ──
        original_record = orchestrator._record_message

        def patched_record(sender, recipient, msg_type, content):
            original_record(sender, recipient, msg_type, content)
            meta = AGENT_META.get(sender, {"name": str(sender), "emoji": "🤖", "color": "system"})
            # 긴 메시지는 청크로 나눠 전송 (한 번에 너무 크면 SSE 버퍼 이슈)
            chunk_size = 2000
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            for idx, chunk in enumerate(chunks):
                _emit("message", {
                    "sender": meta["name"],
                    "emoji": meta["emoji"],
                    "color": meta["color"],
                    "recipient": AGENT_META.get(recipient, {}).get("name", str(recipient)),
                    "msg_type": msg_type.value if hasattr(msg_type, "value") else str(msg_type),
                    "content": chunk,
                    "chunk_idx": idx,
                    "total_chunks": len(chunks),
                    "time": datetime.now().strftime("%H:%M"),
                })

        orchestrator._record_message = patched_record

        _emit("status", {"text": "🚀 채움 이커머스 멀티 에이전트 시스템 시작!", "time": datetime.now().strftime("%H:%M")})
        session = orchestrator.run(quarter=quarter, topic=topic, context=context, save_report=True)
        _emit("done", {
            "session_id": session.session_id,
            "msg_count": len(session.messages),
            "time": datetime.now().strftime("%H:%M"),
        })
    except Exception as e:
        _emit("error", {"text": str(e), "time": datetime.now().strftime("%H:%M")})
    finally:
        _is_running = False


@app.route("/")
def index():
    return render_template("kakao_chat.html")


@app.route("/start", methods=["POST"])
def start():
    global _is_running
    if _is_running:
        return jsonify({"ok": False, "msg": "이미 실행 중입니다."})

    data = request.get_json() or {}
    quarter = data.get("quarter", "2025 Q3")
    topic = data.get("topic", "신규 시즌 상품 기획")
    context = data.get("context", "")
    api_key = data.get("api_key") or os.environ.get("ANTHROPIC_API_KEY", "")

    if not api_key:
        return jsonify({"ok": False, "msg": "API 키를 입력해주세요."})

    # 큐 비우기
    while not _msg_queue.empty():
        try:
            _msg_queue.get_nowait()
        except queue.Empty:
            break

    _is_running = True
    t = threading.Thread(target=_run_workflow, args=(quarter, topic, context, api_key), daemon=True)
    t.start()
    return jsonify({"ok": True})


@app.route("/stream")
def stream():
    """SSE 엔드포인트 - 클라이언트가 실시간으로 메시지를 수신합니다."""
    def generate():
        while True:
            try:
                item = _msg_queue.get(timeout=30)
                event = item["event"]
                payload = json.dumps(item["data"], ensure_ascii=False)
                yield f"event: {event}\ndata: {payload}\n\n"
                if event in ("done", "error"):
                    break
            except queue.Empty:
                # 연결 유지 heartbeat
                yield ": heartbeat\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/status")
def status():
    return jsonify({"running": _is_running})


if __name__ == "__main__":
    # .env 파일 로드
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    print("\n" + "="*60)
    print("  채움(Chaeum) 카카오톡 스타일 채팅 UI")
    print("  브라우저에서 열기: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
