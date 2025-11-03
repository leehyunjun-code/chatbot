# 🎙️ AI 음성 주식매매 챗봇

음성 또는 키보드로 주식을 매매할 수 있는 웹 채팅 서비스

## ✨ 주요 기능

- 🎤 **음성 입력**: Clova STT로 음성 명령 인식
- ⌨️ **키보드 입력**: 일반 채팅처럼 타이핑
- 📈 **실제 매매**: 한국투자증권 API 연동
- 💰 **현재가 조회**: "삼성전자 현재가?"
- 📊 **잔고/보유종목**: 계좌 정보 확인
- 🤖 **스마트 파싱**: 오타 자동 수정 (Fuzzy Matching)

## 📁 프로젝트 구조

```
chatbot/
├── app.py                 # Flask 메인 서버
├── parser.py              # 명령어 파싱 엔진
├── kis_api.py             # 한국투자증권 API
├── database.py            # MySQL DB 연결
├── stt_tts.py            # Clova STT & gTTS
├── requirements.txt       # 패키지 목록
├── .env.example          # 환경변수 템플릿
├── setup_db.sql          # DB 생성 스크립트
├── templates/
│   └── index.html        # 프론트엔드
└── README.md             # 이 파일
```

## 🚀 빠른 시작

### 1. 사전 준비

- **Python 3.8+** 설치
- **MySQL 8.0+** 설치 및 실행
- **네이버 클라우드** Clova STT API 키 발급 (선택사항)
- **한국투자증권** API 키 발급 (선택사항)

### 2. 설치

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일을 열어서 API 키 입력

# 3. 데이터베이스 생성
mysql -u root -p < setup_db.sql
```

### 3. 실행

```bash
# 서버 시작
python app.py

# 브라우저에서 접속
# http://localhost:5000
```

## ⚙️ 환경변수 설정 (.env)

```bash
# Clova STT API (선택사항 - 음성 인식용)
CLOVA_CLIENT_ID=your_clova_client_id
CLOVA_CLIENT_SECRET=your_clova_client_secret

# 한국투자증권 API (선택사항 - 실제 매매용)
KIS_APP_KEY=your_kis_app_key
KIS_APP_SECRET=your_kis_app_secret
KIS_ACCOUNT_NO=your_account_number

# MySQL 데이터베이스
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=stock_chatbot
DB_PORT=3306
```

### API 키 발급 방법

#### 1️⃣ Clova STT (네이버 클라우드)

1. https://www.ncloud.com 접속
2. 회원가입 및 로그인
3. Console → AI·NAVER API → AI·Application Service
4. Application 등록 → Clova Speech Recognition (CSR) 선택
5. Client ID, Client Secret 발급

#### 2️⃣ 한국투자증권 API

1. https://apiportal.koreainvestment.com 접속
2. 회원가입 (한투 계좌 필요)
3. 앱 등록 → 국내주식주문, 국내주식시세 선택
4. APP_KEY, APP_SECRET 발급
5. 모의투자 계좌번호 등록

## 📖 사용 예시

### 현재가 조회
```
사용자: "삼성전자 현재가?"
봇: 삼성전자 현재가
    💰 72,500원
    📊 전일대비: +500원 (+0.7%)
```

### 매수 주문
```
사용자: "네이버 10주 사줘"
봇: 🔔 주문 확인
    종목: 네이버
    수량: 10주
    예상금액: 1,850,000원
    [✅ 주문실행] [❌ 취소]
```

### 잔고 조회
```
사용자: "내 잔고 확인"
봇: 💰 계좌 정보
    예수금: 1,500,000원
    총 평가액: 2,300,000원
```

## 🧪 테스트

### 파싱 엔진 테스트
```bash
python parser.py
```

### 한투 API 테스트
```bash
python kis_api.py
```

### TTS 테스트
```bash
python stt_tts.py
```

### DB 연결 테스트
```bash
python database.py
```

## 🛠️ 문제 해결

### 1. MySQL 연결 실패
```bash
# MySQL이 실행 중인지 확인
sudo systemctl status mysql

# MySQL 시작
sudo systemctl start mysql
```

### 2. 패키지 설치 오류
```bash
# 가상환경 생성 후 재시도
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Clova STT 오류
- Client ID, Secret 확인
- 월 3,000건 무료 할당량 확인
- 네트워크 방화벽 확인

### 4. 한투 API 오류
- APP_KEY, SECRET 확인
- 계좌번호 형식 확인 (8자리)
- 모의투자/실전투자 구분 확인
- 토큰 만료시 자동 재발급

## 🔒 보안 주의사항

1. **.env 파일을 Git에 커밋하지 마세요!**
2. API 키는 절대 공개하지 마세요
3. 실전투자 전에 모의투자로 충분히 테스트하세요
4. DB 비밀번호는 강력하게 설정하세요

## 📝 개발 일정

- [x] 프로젝트 구조 설계
- [x] 명령어 파싱 엔진
- [x] 한투 API 연동
- [x] 음성 인식 (Clova STT)
- [x] 프론트엔드 UI
- [x] 데이터베이스 연동
- [ ] 사용자 로그인 시스템
- [ ] 다중 계좌 지원
- [ ] 예약 주문 기능
- [ ] 모바일 앱

## 🤝 기여

이슈와 PR은 언제나 환영합니다!

## 📄 라이선스

MIT License

## 📧 문의

문제가 있거나 질문이 있으시면 Issue를 열어주세요.

---

**⚠️ 면책 조항**

이 프로젝트는 교육 목적으로 제작되었습니다.
실제 투자에 사용할 경우 발생하는 손실에 대해 개발자는 책임지지 않습니다.
투자는 본인의 판단과 책임 하에 진행하세요.
