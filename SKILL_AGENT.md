# 산업재해·공장화재 보고서 자동 생성 에이전트

## 에이전트 개요

이 에이전트는 단체보험 및 공장화재보험 전문 컨설턴트 **이헌영 지점장**(010-8950-6400)을 위해 설계된 자동화 도구입니다.

CSV 형식의 고객 목록을 입력받아 최신 공장화재 사고 정보를 웹에서 검색하고, 각 고객사에 개인화된 HTML 이메일 보고서를 자동으로 생성·발송합니다.

---

## 에이전트 실행 흐름 (5단계)

### ① STEP 1 — CSV 파일 로드 및 유효성 검사

**목표:** 고객 목록 CSV 파일을 읽어 유효한 데이터만 추출합니다.

**처리 내용:**
- CSV 파일 경로를 인수로 받아 파일을 열고 읽습니다.
- 필수 컬럼(`company_name`, `email`, `address`) 존재 여부를 확인합니다.
- 각 행에 대해 다음을 검사합니다:
  - `company_name`: 빈 값 허용 불가
  - `email`: `@` 포함 여부로 기본 형식 확인
  - `address`: 빈 값 허용 불가
- 유효하지 않은 행은 건너뛰고 경고 메시지를 출력합니다.
- 유효한 고객 목록을 반환하며 총 건수를 콘솔에 출력합니다.

**입력:** `sample_customers.csv` (또는 사용자 지정 경로)
**출력:** 유효한 고객 딕셔너리 리스트

---

### ② STEP 2 — 최신 공장화재 사고 웹 검색 (최근 1개월, 2건)

**목표:** 최근 1개월 이내 발생한 공장화재 사고 2건을 웹에서 검색합니다.

**처리 내용:**
- 검색 키워드: `"공장화재 사고 2025"`, `"산업재해 화재 최근"` 등
- 웹 검색 API 또는 `requests`+`BeautifulSoup`을 활용하여 뉴스 기사를 수집합니다.
- 각 사건에 대해 다음 정보를 추출합니다:
  - 사건 제목 (title)
  - 발생 날짜 (date)
  - 발생 장소 (location)
  - 피해 규모 요약 (summary)
  - 출처 URL (url)
- 실제 웹 검색이 불가능한 경우, 최근 실제 사례를 기반으로 한 예시 데이터를 사용합니다.
- 검색된 2건의 사건 정보를 딕셔너리 형태로 반환합니다.

**출력:** 사고 정보 딕셔너리 2개의 리스트

---

### ③ STEP 3 — 개인화 HTML 보고서 생성

**목표:** 각 고객사별로 맞춤 HTML 이메일 보고서를 생성합니다.

**처리 내용:**
- `sample_report.html` 템플릿 파일을 로드합니다.
- `{{company_name}}` 플레이스홀더를 고객사명으로 치환합니다.
- `{{incident_1_*}}`, `{{incident_2_*}}` 플레이스홀더를 검색된 사고 정보로 채웁니다.
- `{{report_date}}` 를 오늘 날짜로 채웁니다.
- 각 고객사별로 개인화된 HTML 문자열을 생성합니다.
- 생성된 HTML은 이메일 발송에 사용됩니다.

**HTML 구성 섹션:**
1. **인사말** - 고객사명을 포함한 개인화 인사
2. **최근 공장화재 사고 요약** - 2건의 사고 정보 표 형식으로 제시
3. **중대재해처벌법 안내** - 법적 리스크와 의무 사항 설명
4. **보험 상품 소개** - 단체보험 및 공장화재보험 상품 안내
5. **담당자 연락처** - 이헌영 지점장 정보 (010-8950-6400)

**출력:** 고객별 HTML 문자열 딕셔너리 (key: email, value: html_content)

---

### ④ STEP 4 — 사용자 승인 단계 (Human-in-the-Loop)

**목표:** 이메일 발송 전 사용자의 최종 승인을 받습니다.

**처리 내용:**
- 발송 예정 고객 목록을 콘솔에 출력합니다 (회사명, 이메일, 주소).
- 생성된 HTML 보고서 미리보기 (첫 번째 고객 기준 일부 내용)를 출력합니다.
- 사용자에게 다음 옵션을 제시합니다:
  - `y` 또는 `yes`: 전체 발송 진행
  - `n` 또는 `no`: 발송 취소
  - `p` 또는 `preview`: 특정 고객사 HTML 전체 미리보기
- 승인이 거부되면 프로그램을 안전하게 종료합니다.
- `--auto-approve` 플래그가 있을 경우 이 단계를 건너뜁니다 (배치 자동화용).

**출력:** 승인 여부 (bool)

---

### ⑤ STEP 5 — SMTP 이메일 발송 및 결과 추적

**목표:** 승인된 고객 목록에 HTML 이메일을 발송하고 결과를 JSON으로 저장합니다.

**처리 내용:**
- `send_email.py` 모듈의 `EmailSender` 클래스를 사용합니다.
- SMTP 설정(서버, 포트, 계정, 비밀번호)을 환경변수 또는 인수에서 읽습니다.
- 지원 SMTP 서버:
  - Gmail: `smtp.gmail.com:587` (TLS)
  - Outlook: `smtp-mail.outlook.com:587` (TLS)
  - 커스텀: 사용자 지정 호스트/포트
- 각 고객에게 HTML 이메일을 순차 발송합니다.
- 발송 결과를 추적합니다:
  - 성공: 회사명, 이메일, 발송 시각
  - 실패: 회사명, 이메일, 오류 메시지
- 모든 발송 완료 후 결과를 `email_send_results_YYYYMMDD_HHMMSS.json`으로 저장합니다.
- 콘솔에 발송 성공/실패 통계를 출력합니다.

**출력:** JSON 결과 파일

---

## 사용 방법

### 기본 실행

```bash
python agent.py --csv sample_customers.csv \
  --smtp-host smtp.gmail.com \
  --smtp-port 587 \
  --smtp-user your@gmail.com \
  --smtp-password "앱비밀번호" \
  --sender-name "이헌영 지점장"
```

### 자동 승인 모드 (배치 처리)

```bash
python agent.py --csv sample_customers.csv \
  --smtp-host smtp.gmail.com \
  --smtp-port 587 \
  --smtp-user your@gmail.com \
  --smtp-password "앱비밀번호" \
  --auto-approve
```

### 검색만 실행 (이메일 미발송)

```bash
python agent.py --csv sample_customers.csv --dry-run
```

---

## 환경 변수 설정 (선택)

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your@gmail.com
export SMTP_PASSWORD=your_app_password
export SENDER_NAME="이헌영 지점장"
```

---

## 파일 구조

```
industrial-injury-fire-report-agent/
├── manifest.json              # 스킬 메타데이터
├── SKILL_AGENT.md             # 에이전트 프롬프트 및 워크플로우 (현재 파일)
├── agent.py                   # 메인 에이전트 스크립트
├── send_email.py              # SMTP 이메일 발송 모듈
├── sample_customers.csv       # 샘플 고객 목록
├── sample_report.html         # HTML 이메일 템플릿
├── 에이전트형_스킬_최종_정리.txt  # 상세 구조 문서
├── SKILL_INSTALLATION_GUIDE.txt  # 설치 가이드
├── README.md                  # 프로젝트 소개
└── create_skill_package.py    # 스킬 패키지 생성 스크립트
```

---

## 주의 사항

1. **Gmail 사용 시:** 일반 비밀번호 대신 **앱 비밀번호**를 사용하세요 (Google 계정 > 보안 > 앱 비밀번호).
2. **대량 발송 시:** Gmail은 하루 500건, Outlook은 300건 제한이 있습니다.
3. **개인정보 보호:** CSV 파일에 포함된 고객 정보는 안전하게 관리하세요.
4. **중대재해처벌법:** 2022년 1월 27일 시행, 상시근로자 50인 이상 사업장에 적용됩니다.

---

## 담당자 정보

| 항목 | 내용 |
|------|------|
| 이름 | 이헌영 지점장 |
| 전문 분야 | 단체보험 및 공장화재보험 |
| 휴대폰 | 010-8950-6400 |
| 팩스 | 0504-006-6400 |
