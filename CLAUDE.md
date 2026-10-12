# CLAUDE.md

산업재해·공장화재 보험 컨설턴트(1인 사업자)를 위한 **이메일 보고서 자동 발송 에이전트**.
목표는 반복 업무를 줄이는 것 — 변경 시 "사람 손이 덜 가는 방향"을 우선한다.

## 구조

- `agent.py` — 메인 CLI. 7단계 워크플로우:
  1. CSV 로드/검증 (`company_name,email,address` 필수, `utf-8-sig`)
  2. 네이버 뉴스 스크래핑으로 공장화재 2건 + 중대재해처벌법 요약 수집
     (실패 시 하드코딩된 fallback 데이터 사용)
  3. Jinja2로 `templates/report.html` 렌더링 → `results/preview.html`
  4. 사용자 승인 (`--dry-run`/`--yes`면 생략)
  5. SMTP 설정 (CLI 인자 → `.env` → 대화형 입력 순)
  6. 고객사별 발송 (`send_email.send_bulk`, 한 건 실패해도 계속)
  7. `results/<timestamp>_results.json` 저장
- `send_email.py` — SMTP 발송 모듈 (STARTTLS 587 / SSL 465 / 평문), Gmail·Outlook·네이버 프리셋
- `templates/report.html` — 이메일 HTML 템플릿 (`incident1_*`, `incident2_*`, `serious_accident_law_summary` 변수)
- `sample_data/companies.csv` — 테스트용 고객사 3곳
- `config.json.example` — 현재 코드에서 읽지 않음 (설정은 `.env` 사용)

## 실행 / 검증

```bash
pip install -r requirements.txt
python agent.py --csv sample_data/companies.csv --dry-run   # 실제 발송 없음, 스모크 테스트
ruff check agent.py send_email.py                           # 린트
```

- 테스트 스위트는 아직 없음. 변경 후에는 위 `--dry-run`으로 끝까지 도는지 확인.
- 클라우드 세션에서는 search.naver.com 접근이 막혀 있어 fallback 데이터로 동작하는 게 정상.

## 주의

- **실제 이메일 발송은 고객에게 바로 나간다.** `--dry-run` 없이 실행하지 말 것.
- `.env`(SMTP 비밀번호, API 키)와 `results/`는 커밋하지 않는다 (`.gitignore` 처리됨).
- `requirements.txt`의 `anthropic`, `pandas`는 아직 코드에서 사용하지 않음.
- 문서/메시지/주석은 한국어로 작성.
