# Discord Collector API

FastAPI 기반의 Discord 메시지 수집 시스템

## 📁 프로젝트 구조

```
Collector/
├── bin/                      # DiscordChatExporter CLI 바이너리
│   ├── DiscordChatExporter.Cli     # 메인 실행 파일
│   ├── *.dll                       # .NET 라이브러리들
│   └── *.dylib                     # macOS 네이티브 라이브러리들
├── discord_api_server.py     # FastAPI 서버
├── discord_api_client.py     # API 클라이언트
├── discord_to_supabase.py    # 핵심 수집 모듈
├── start_server.py           # 서버 시작 스크립트
├── quick_collect.py          # 빠른 수집 스크립트
├── auto_collector.py         # 레거시 자동 수집기
├── simple_collector.py       # 레거시 간단 수집기
├── requirements.txt          # 의존성 패키지
└── README.md                # 이 문서
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
cd .. && python3 -m venv discord_collector_env
source discord_collector_env/bin/activate
cd Collector

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정 (중요!)
cp config.env .env  # 또는 직접 .env 파일 생성
# .env 파일을 편집해서 실제 토큰/키 입력
```

⚠️ **보안 주의사항**: `config.env` 파일에는 실제 토큰이 들어있으니 절대 Git에 커밋하지 마세요!

### 2. API 서버 시작

```bash
# 서버 시작
python start_server.py

# 또는 직접 실행
python discord_api_server.py
```

서버가 시작되면:
- 🌐 API 주소: http://localhost:8000
- 📝 문서: http://localhost:8000/docs

### 3. 메시지 수집

#### 방법 1: 빠른 수집 (권장)
```bash
python quick_collect.py
```

#### 방법 2: 대화형 클라이언트
```bash
python discord_api_client.py
```

#### 방법 3: API 직접 호출
```bash
# Momentum Messengers 자동 수집
curl "http://localhost:8000/collect/momentum?days=1"

# 커스텀 채널 수집
curl -X POST "http://localhost:8000/collect/sync" \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "1159487918512017488", "days": 1}'
```

## 🔧 API 엔드포인트

### 서버 상태
- `GET /` - 서버 상태 정보
- `GET /health` - 헬스 체크

### 메시지 수집
- `POST /collect/sync` - 동기 수집 (결과 즉시 반환)
- `POST /collect` - 비동기 수집 (백그라운드 실행)
- `GET /collect/momentum` - Momentum Messengers 자동 수집

### 작업 관리
- `GET /tasks` - 모든 작업 목록
- `GET /tasks/{task_id}` - 특정 작업 상태

## 📊 API 요청/응답 예시

### 메시지 수집 요청
```json
{
  "channel_id": "1159487918512017488",
  "days": 1
}
```

### 수집 완료 응답
```json
{
  "status": "completed",
  "message": "메시지 수집이 완료되었습니다.",
  "messages_count": 181,
  "execution_time": "0:02:05"
}
```

## 🎯 설정 정보

### Discord 설정
- **서버**: Momentum Messengers (환경변수: `DEFAULT_SERVER_ID`)
- **채널**: main-stock-chat (환경변수: `DEFAULT_CHANNEL_ID`)
- **토큰**: 환경변수 `DISCORD_TOKEN`에서 로드

### Supabase 설정
- **프로젝트**: tmywnnshruqmoaempwwi
- **테이블**: discord_messages
- **URL**: 환경변수 `SUPABASE_URL`에서 로드
- **키**: 환경변수 `SUPABASE_KEY`에서 로드

### 테이블 스키마
```sql
discord_messages (
  timestamp TIMESTAMP,
  author_name TEXT,
  reference_message_content TEXT,
  content TEXT,
  attachments JSONB,
  embeds JSONB,
  id TEXT PRIMARY KEY,
  reference_message_id TEXT,
  created_at TIMESTAMP DEFAULT NOW()
)
```

## 💡 사용법

### 1. 서버/클라이언트 분리 구조
- **서버**: Discord CLI 실행 및 Supabase 저장 담당
- **클라이언트**: API 호출 및 사용자 인터페이스 담당

### 2. 동기 vs 비동기 수집
- **동기**: 결과를 즉시 반환 (작은 데이터용)
- **비동기**: 백그라운드 실행 후 상태 조회 (큰 데이터용)

### 3. 작업 모니터링
```python
# 작업 상태 조회
import requests

response = requests.get("http://localhost:8000/tasks")
print(response.json())
```

## ☁️ Google Cloud 배포

### 빠른 배포 (권장)
```bash
# 빠른 배포 스크립트 실행
./quick-deploy-gcp.sh your-gcp-project-id

# 환경변수 설정
gcloud run services update discord-chat-exporter --region=us-central1 \
  --set-env-vars \
  DISCORD_TOKEN="your_token",\
  SUPABASE_URL="your_url",\
  SUPABASE_KEY="your_key"
```

### 수동 배포
```bash
# 전체 배포 스크립트
./deploy-gcp.sh your-gcp-project-id us-central1

# 또는 직접 빌드
gcloud builds submit --config cloudbuild.yaml .
```

### 배포 후 사용
```bash
# 서비스 URL 확인
SERVICE_URL=$(gcloud run services describe discord-chat-exporter --region=us-central1 --format="value(status.url)")

# API 테스트
curl "$SERVICE_URL/health"
curl "$SERVICE_URL/docs"  # 브라우저에서 열기
```

📚 **자세한 가이드**: [Google Cloud 배포 가이드](GOOGLE_CLOUD_DEPLOYMENT.md)

## 🔍 문제 해결

### 서버 연결 실패
```bash
# 서버가 실행 중인지 확인
curl http://localhost:8000/health

# 포트 사용 확인
lsof -i :8000
```

### Discord CLI 오류
```bash
# CLI 파일 존재 확인
ls -la ./bin/DiscordChatExporter.Cli

# 실행 권한 확인
chmod +x ./bin/DiscordChatExporter.Cli
```

### Supabase 연결 오류
1. 프로젝트 URL 확인
2. API 키 유효성 확인
3. 테이블 스키마 확인

### Google Cloud 배포 오류
```bash
# 빌드 로그 확인
gcloud builds log <BUILD_ID>

# 서비스 로그 확인
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# 환경변수 확인
gcloud run services describe discord-chat-exporter --region=us-central1
```

## 🎨 특징

### ✅ 장점
- **API 기반**: RESTful API로 다른 시스템과 연동 용이
- **비동기 처리**: 대용량 데이터 수집 시 서버 블록 방지
- **상태 관리**: 작업 진행상황 실시간 모니터링
- **자동 문서**: FastAPI 자동 API 문서 생성
- **모듈화**: 서버/클라이언트 분리로 유지보수 용이

### 🎯 개선점
- **인증**: 현재 토큰이 하드코딩됨
- **스케일링**: 단일 서버 구조
- **로깅**: 상세한 로그 시스템 필요
- **모니터링**: 메트릭 수집 및 알림 시스템

## 🚦 레거시 파일

기존 파일들은 호환성을 위해 유지됨:
- `auto_collector.py` - 기존 자동 수집기
- `simple_collector.py` - 기존 간단 수집기

## 📞 지원

문제가 발생하면:
1. API 문서 확인: http://localhost:8000/docs
2. 서버 상태 확인: http://localhost:8000/health
3. 로그 확인: 서버 콘솔 출력

---

**성진아, API 기반으로 완전히 새로운 구조가 완성됐어! 🎉** 