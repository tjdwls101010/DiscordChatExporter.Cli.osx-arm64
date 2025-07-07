#!/bin/bash

# Google Cloud Run 빠른 배포 스크립트
# Discord Chat Exporter API

set -e

echo "🚀 Discord Chat Exporter API - Google Cloud Run 빠른 배포"
echo "================================================"

# 1. 프로젝트 ID 입력 받기
if [ -z "$1" ]; then
    echo "📝 Google Cloud 프로젝트 ID를 입력하세요:"
    read -p "프로젝트 ID: " PROJECT_ID
else
    PROJECT_ID=$1
fi

echo "📋 프로젝트 ID: $PROJECT_ID"

# 2. 리전 선택 (기본값: us-central1)
REGION=${2:-us-central1}
echo "🌍 리전: $REGION"

# 3. gcloud 설정
echo "⚙️  Google Cloud 설정 중..."
gcloud config set project $PROJECT_ID

# 4. 필요한 API 활성화
echo "🔧 필요한 API 활성화 중..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com

# 5. 빌드 및 배포
echo "🏗️  빌드 및 배포 시작..."
gcloud builds submit --config cloudbuild.yaml .

# 6. 서비스 URL 가져오기
echo "🔍 서비스 URL 확인 중..."
SERVICE_URL=$(gcloud run services describe discord-chat-exporter --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")

if [ -n "$SERVICE_URL" ]; then
    echo "✅ 배포 완료!"
    echo "🌐 서비스 URL: $SERVICE_URL"
    echo "📚 API 문서: $SERVICE_URL/docs"
    echo "🏥 헬스 체크: $SERVICE_URL/health"
else
    echo "⚠️  서비스 URL을 가져올 수 없습니다. 배포 상태를 확인하세요."
fi

echo ""
echo "🔑 다음 단계: 환경변수 설정"
echo "================================"
echo "1. Discord 토큰, Supabase URL, Supabase Key를 준비하세요."
echo "2. 다음 명령어로 환경변수를 설정하세요:"
echo ""
echo "gcloud run services update discord-chat-exporter --region=$REGION \\"
echo "  --set-env-vars \\"
echo "  DISCORD_TOKEN=\"your_discord_token\",\\"
echo "  SUPABASE_URL=\"https://your-project.supabase.co\",\\"
echo "  SUPABASE_KEY=\"your_supabase_key\",\\"
echo "  DEFAULT_CHANNEL_ID=\"your_channel_id\""
echo ""
echo "📖 자세한 가이드: docs/GOOGLE_CLOUD_DEPLOYMENT.md"
echo ""
echo "🎉 Happy coding!" 