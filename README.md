# 산업재해·공장화재 보고서 자동 생성 에이전트 v2.0

산업재해 및 공장화재 보험 컨설턴트를 위한 **완전 자동화 이메일 보고서 생성 에이전트**입니다.

CSV 파일 업로드 한 번으로 최신 사고 정보 수집 → HTML 보고서 생성 → 고객사별 이메일 발송까지 자동으로 처리합니다.

---

## 특징

- **완전 자동화**: CSV 업로드 + 승인만 하면 나머지는 자동 처리
- **최신 정보 수집**: 웹 검색으로 최근 1개월 공장화재 사고 2건 자동 수집
- **개인화 보고서**: 고객사명·주소를 자동 삽입한 HTML 이메일 생성
- **안정적 발송**: Gmail, Outlook, 네이버 메일 등 SMTP 기반 발송
- **결과 추적**: JSON 파일로 발송 기록 자동 저장

---

## 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. CSV 파일 준비

```csv
company_name,email,address
ABC주식회사,contact@abc.com,서울시 강남구 테헤란로 123
XYZ산업,info@xyz.com,대구시 중구 중앙대로 456
현대산업,safety@hyundai.com,경기도 수원시 영통구 789
```

### 3. 환경변수 설정 (선택)

```bash
cp .env.example .env
# .env 파일에 SMTP 정보 입력
```

### 4. 에이전트 실행

```bash
# 테스트 (실제 발송 없음)
python agent.py --csv sample_data/companies.csv --dry-run

# 실제 발송
python agent.py --csv companies.csv

# 승인 단계 건너뛰기
python agent.py --csv companies.csv --yes --smtp-host smtp.gmail.com
```

---

## 파일 구조

```
chaeum/
├── agent.py                  # 메인 에이전트 (7단계 워크플로우)
├── send_email.py             # SMTP 이메일 발송 모듈
├── requirements.txt          # Python 의존성
├── .env.example              # 환경변수 예시
├── config.json.example       # SMTP 설정 예시
├── templates/
│   └── report.html           # HTML 이메일 템플릿 (Jinja2)
├── sample_data/
│   └── companies.csv         # 샘플 고객사 데이터
└── results/                  # 발송 결과 저장 (자동 생성)
```

---

## 워크플로우 (7단계)

```
[Step 1] CSV 검증 및 로드
[Step 2] 웹 검색 - 최근 공장화재 사고 2건 + 중대재해처벌법
[Step 3] HTML 보고서 생성 + 미리보기 저장
[Step 4] 사용자 검토 및 승인
[Step 5] SMTP 설정 입력
[Step 6] 고객사별 이메일 일괄 발송
[Step 7] 결과 JSON 저장
```

---

## SMTP 설정

| 메일 서비스 | 호스트 | 포트 |
|---|---|---|
| Gmail | smtp.gmail.com | 587 |
| Outlook/Hotmail | smtp-mail.outlook.com | 587 |
| 네이버 | smtp.naver.com | 587 |

> **Gmail 사용 시**: 앱 비밀번호 생성 필요 (Google 계정 → 보안 → 앱 비밀번호)

---

## CLI 옵션

```
--csv           고객사 CSV 파일 경로 (필수)
--dry-run       실제 발송 없이 테스트 실행
--yes, -y       발송 전 승인 단계 건너뜀
--smtp-host     SMTP 서버 호스트
--smtp-port     SMTP 포트 (기본: 587)
--smtp-user     SMTP 사용자 이메일
--smtp-password SMTP 비밀번호
--smtp-from     발신자 이메일 주소
```

---

## 시간 절감 효과

| 작업 | 수동 | 자동 |
|---|---|---|
| CSV 읽기 + 검증 | 5분 | 자동 |
| 뉴스 검색 + 정리 | 30분 | 자동 |
| HTML 보고서 작성 | 40분 | 자동 |
| 이메일 작성 + 발송 | 25분 | 자동 |
| **합계** | **100분/월** | **7분/월** |

**93% 시간 절감 (93분 절약)**

---

## 담당자

**이헌영 지점장** — 단체보험 및 공장화재보험 전문 컨설턴트

- 전화: 010-8950-6400
- 팩스: 0504-006-6400
- 상담: 평일 09:00~18:00
