#!/bin/bash

# Google Cloud Run 배포 스크립트
# Discord Chat Exporter API

set -e  # 에러 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수 정의
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 설정 검증
print_status "Google Cloud 설정 확인 중..."

# gcloud 설치 확인
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI가 설치되지 않았습니다."
    print_error "https://cloud.google.com/sdk/docs/install 에서 설치하세요."
    exit 1
fi

# 프로젝트 ID 입력받기
if [ -z "$1" ]; then
    echo "사용법: $0 <PROJECT_ID> [REGION]"
    echo "예시: $0 my-gcp-project us-central1"
    exit 1
fi

PROJECT_ID=$1
REGION=${2:-us-central1}  # 기본값: us-central1
SERVICE_NAME="discord-chat-exporter"

print_status "프로젝트 ID: $PROJECT_ID"
print_status "리전: $REGION"
print_status "서비스 이름: $SERVICE_NAME"

# 프로젝트 설정
print_status "Google Cloud 프로젝트 설정 중..."
gcloud config set project $PROJECT_ID

# API 활성화
print_status "필요한 API 활성화 중..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 환경변수 파일 확인
if [ ! -f "config.env" ]; then
    print_warning "config.env 파일이 없습니다."
    print_warning "환경변수를 수동으로 설정해야 합니다."
fi

# Docker 이미지 빌드 및 배포 (Cloud Build 사용)
print_status "Cloud Build를 사용하여 빌드 및 배포 시작..."

# Cloud Build 실행
gcloud builds submit --config cloudbuild.yaml .

# 배포 상태 확인
print_status "배포 상태 확인 중..."
gcloud run services describe $SERVICE_NAME --region=$REGION

# 서비스 URL 가져오기
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

print_status "배포 완료!"
print_status "서비스 URL: $SERVICE_URL"
print_status "API 문서: $SERVICE_URL/docs"

# 환경변수 설정 안내
print_warning "중요: 환경변수를 설정해야 합니다:"
print_warning "1. Discord 토큰"
print_warning "2. Supabase 설정"
print_warning ""
print_warning "다음 명령어로 환경변수를 설정하세요:"
echo "gcloud run services update $SERVICE_NAME --region=$REGION \\"
echo "  --set-env-vars DISCORD_TOKEN=your_token,SUPABASE_URL=your_url,SUPABASE_KEY=your_key"

print_status "배포 스크립트 실행 완료!" 