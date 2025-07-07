# Google Cloud Run 배포 가이드

Discord Chat Exporter API를 Google Cloud Run에 배포하는 완전한 가이드입니다.

## 📋 사전 요구사항

1. **Google Cloud 계정** 및 프로젝트 생성
2. **gcloud CLI** 설치 및 인증
3. **Discord Bot 토큰** 및 **Supabase 설정**

## 🛠️ 1단계: Google Cloud 설정

### gcloud CLI 설치

**macOS:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Ubuntu/Debian:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Windows:** [Google Cloud SDK 설치 페이지](https://cloud.google.com/sdk/docs/install)에서 다운로드

### 인증 및 프로젝트 설정

```bash
# Google Cloud 인증
gcloud auth login

# 프로젝트 설정 (프로젝트 ID를 본인의 것으로 변경)
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# 청구 계정 연결 확인
gcloud beta billing projects describe $PROJECT_ID
```

## 🚀 2단계: 자동 배포

### 간단한 배포 (권장)

```bash
# 배포 스크립트 실행
./deploy-gcp.sh your-gcp-project-id us-central1
```

### 수동 배포

```bash
# 필요한 API 활성화
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 빌드 및 배포
gcloud builds submit --config cloudbuild.yaml .
```

## 🔑 3단계: 환경변수 설정

### 방법 1: 직접 환경변수 설정

```bash
gcloud run services update discord-chat-exporter --region=us-central1 \
  --set-env-vars \
  DISCORD_TOKEN="your_discord_bot_token",\
  SUPABASE_URL="https://your-project.supabase.co",\
  SUPABASE_KEY="your_supabase_anon_key",\
  DEFAULT_CHANNEL_ID="your_default_channel_id"
```

### 방법 2: Secret Manager 사용 (권장)

#### Secret 생성
```bash
# Discord 토큰
echo "your_discord_bot_token" | gcloud secrets create discord-token --data-file=-

# Supabase URL
echo "https://your-project.supabase.co" | gcloud secrets create supabase-url --data-file=-

# Supabase Key
echo "your_supabase_anon_key" | gcloud secrets create supabase-key --data-file=-

# 기본 채널 ID
echo "your_default_channel_id" | gcloud secrets create default-channel-id --data-file=-
```

#### Secret Manager API 활성화
```bash
gcloud services enable secretmanager.googleapis.com
```

#### Cloud Run에 Secret 연결
```bash
gcloud run services update discord-chat-exporter --region=us-central1 \
  --set-secrets \
  DISCORD_TOKEN=discord-token:latest,\
  SUPABASE_URL=supabase-url:latest,\
  SUPABASE_KEY=supabase-key:latest,\
  DEFAULT_CHANNEL_ID=default-channel-id:latest
```

#### IAM 권한 설정
```bash
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT="$PROJECT_ID-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

## ✅ 4단계: 배포 확인

### 서비스 상태 확인
```bash
gcloud run services describe discord-chat-exporter --region=us-central1
```

### 서비스 URL 확인
```bash
SERVICE_URL=$(gcloud run services describe discord-chat-exporter --region=us-central1 --format="value(status.url)")
echo "서비스 URL: $SERVICE_URL"
echo "API 문서: $SERVICE_URL/docs"
```

### 헬스 체크
```bash
curl "$SERVICE_URL/health"
```

## 📊 5단계: 모니터링 및 로그

### 로그 확인
```bash
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=discord-chat-exporter" --limit=50
```

### 실시간 로그 모니터링
```bash
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=discord-chat-exporter"
```

### Cloud Console에서 모니터링
1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. Cloud Run > discord-chat-exporter 선택
3. "로그" 탭에서 실시간 로그 확인

## 🔧 6단계: 고급 설정

### 자동 스케일링 설정
```bash
gcloud run services update discord-chat-exporter --region=us-central1 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80
```

### 리소스 제한 설정
```bash
gcloud run services update discord-chat-exporter --region=us-central1 \
  --memory=2Gi \
  --cpu=2 \
  --timeout=3600
```

### 도메인 연결 (선택사항)
```bash
gcloud run domain-mappings create --service=discord-chat-exporter --domain=api.yourdomain.com --region=us-central1
```

## 🐛 문제 해결

### 자주 발생하는 오류

#### 1. 빌드 실패
```bash
# 로그 확인
gcloud builds log <BUILD_ID>

# Docker 캐시 클리어 후 재시도
gcloud builds submit --config cloudbuild.yaml . --no-cache
```

#### 2. 메모리 부족
```bash
# 메모리 증가
gcloud run services update discord-chat-exporter --region=us-central1 --memory=2Gi
```

#### 3. 환경변수 오류
```bash
# 환경변수 확인
gcloud run services describe discord-chat-exporter --region=us-central1 --format="export" | grep -A 10 "env:"
```

#### 4. Secret 접근 오류
```bash
# IAM 권한 재설정
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT="$PROJECT_ID-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

## 💰 비용 관리

### 예상 비용
- **Cloud Run**: 요청당 과금, 무료 티어 포함
- **Container Registry**: 저장소 비용
- **Cloud Build**: 빌드 시간당 과금
- **Secret Manager**: 액세스당 소액 과금

### 비용 절약 팁
1. **최소 인스턴스 0으로 설정**: 사용하지 않을 때 완전히 종료
2. **적절한 메모리/CPU 설정**: 과도한 리소스 할당 방지
3. **빌드 최적화**: Docker 레이어 캐싱 활용

## 🔄 업데이트 및 재배포

### 코드 변경 후 재배포
```bash
# 간단한 재배포
./deploy-gcp.sh your-gcp-project-id

# 또는 수동으로
gcloud builds submit --config cloudbuild.yaml .
```

### 롤백
```bash
# 이전 버전으로 롤백
gcloud run services update-traffic discord-chat-exporter --region=us-central1 --to-revisions=PREVIOUS_REVISION=100
```

## 📚 유용한 명령어

```bash
# 서비스 삭제
gcloud run services delete discord-chat-exporter --region=us-central1

# 모든 빌드 히스토리 확인
gcloud builds list --limit=10

# 특정 빌드 로그 확인
gcloud builds log BUILD_ID

# 서비스 목록 확인
gcloud run services list

# 리전별 서비스 확인
gcloud run services list --region=us-central1
```

## 🎯 API 사용 예시

배포 완료 후 API 사용 방법:

```bash
# 서비스 URL 확인
SERVICE_URL="https://discord-chat-exporter-xxx-uc.a.run.app"

# 헬스 체크
curl "$SERVICE_URL/health"

# 메시지 수집 (동기)
curl -X POST "$SERVICE_URL/collect/sync" \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "your_channel_id", "hours": 1}'

# API 문서 확인
# 브라우저에서 $SERVICE_URL/docs 접속
```

---

📝 **참고**: 이 가이드는 Discord Chat Exporter API의 Google Cloud Run 배포를 위한 완전한 가이드입니다. 추가 질문이나 문제가 있으시면 이슈를 생성해 주세요. 