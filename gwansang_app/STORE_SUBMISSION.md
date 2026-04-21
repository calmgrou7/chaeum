# 관상사주 앱 스토어 제출 가이드

## 1. 사전 준비

### Apple App Store
- Apple Developer Program 가입: https://developer.apple.com/programs/
- 연간 $99 (USD) 결제
- 맥북 + Xcode 15+ 필요

### Google Play Store
- Google Play Console 가입: https://play.google.com/console
- 일회성 $25 (USD) 결제
- Android Studio 필요 (선택)

---

## 2. 환경 설정

```bash
# Node.js 18+ 및 EAS CLI 설치
npm install -g eas-cli

# 로그인
eas login

# 프로젝트 초기화 (EAS project ID 발급)
cd gwansang_app
eas init
```

---

## 3. 백엔드 배포

```bash
cd backend

# Railway 배포 (추천)
# 1. railway.app 가입
# 2. 새 프로젝트 생성
# 3. GitHub 연결 또는 railway up 명령어
# 4. 환경변수 설정: ANTHROPIC_API_KEY=your_key

# 또는 Render.com 배포
# 1. render.com 가입
# 2. New Web Service → GitHub 연결
# 3. Build Command: pip install -r requirements.txt
# 4. Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

배포 후 `gwansang_app/app.json`의 `apiBaseUrl`을 배포된 URL로 수정:
```json
"extra": {
  "apiBaseUrl": "https://your-deployed-backend.railway.app"
}
```

---

## 4. 앱 빌드

### Android (APK / AAB)

```bash
# eas.json 설정 확인 후
eas build --platform android --profile production
```

빌드 완료 후 `.aab` 파일 다운로드

### iOS

```bash
eas build --platform ios --profile production
```

- Apple Developer 인증서 자동 생성 또는 기존 인증서 사용
- 빌드 완료 후 `.ipa` 파일 다운로드

---

## 5. 스토어 등록 정보

### 앱 이름
- 한국어: 관상사주 - 얼굴로 보는 운명
- 영어: FaceFortune - Korean Physiognomy

### 앱 설명 (한국어)
```
📸 사진 한 장으로 나의 관상을 AI가 분석해드립니다!

🔮 관상사주란?
동양 철학에서 관상(觀相)과 사주(四柱)는 서로 영향을 주고받습니다.
얼굴의 이마·눈·코·입·귀가 각각 다른 운을 나타냅니다.

✨ 주요 기능
• AI 관상 분석 — 사진으로 이마·눈·코·입·귀 부위별 운세 파악
• 사주 연동 — 생년월일시로 사주를 계산하고 관상과 비교
• 관상 보정 필터 — 6가지 관상 개선 필터로 운이 바뀌는 것을 체험
• 맞춤 업체 추천 — 에스테틱, 반영구, 두피케어, 두피문신, 성형외과 추천

💡 관상이 바뀌면 사주가 바뀐다
필터로 인상을 개선하거나 전문 시술로 실제 관상을 바꾸면
주변 사람들의 반응이 달라지고 기회도 달라집니다.

📍 주변 전문 업체 추천
분석 결과에 맞는 에스테틱, 반영구 메이크업, 두피 케어, 성형외과를 추천해드립니다.
```

### 카테고리
- 주 카테고리: Lifestyle (라이프스타일)
- 보조 카테고리: Health & Fitness (건강/피트니스)

### 연령 등급
- 4+ (만 4세 이상, 특별한 제한 없음)

### 키워드 (App Store)
관상, 사주, 얼굴운세, 관상분석, 사주팔자, 필터, 에스테틱, 반영구, 두피케어, 운세

---

## 6. 스토어 제출

### Google Play
```bash
# AAB 파일 직접 업로드 또는 EAS Submit 사용
eas submit --platform android --profile production
```
또는 Google Play Console → 프로덕션 → 새 버전 → AAB 업로드

### App Store
```bash
eas submit --platform ios --profile production
```
또는 Transporter 앱으로 .ipa 업로드 → App Store Connect에서 제출

---

## 7. 심사 대기

| 플랫폼 | 평균 심사 기간 |
|--------|--------------|
| Google Play | 1~3일 |
| Apple App Store | 1~7일 |

### Apple 심사 주의사항
- 실제 동작하는 백엔드 URL 필수 (심사 시 테스트)
- 개인정보처리방침 URL 필수
- 카메라 사용 목적 명확히 기재 (이미 infoPlist에 추가됨)
- 관상/운세 앱은 엔터테인먼트 목적임을 명시

---

## 8. 개인정보처리방침 (필수)

앱 출시 전 다음 내용을 포함한 개인정보처리방침 페이지를 만드세요:
- 수집 정보: 카메라/갤러리 사진 (분석 후 서버 미저장)
- 위치 정보: 주변 업체 추천 목적
- 생년월일시: 기기 내 저장, 서버 전송 없음

무료 개인정보처리방침 생성: https://www.privacypolicygenerator.info
