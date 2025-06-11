#!/usr/bin/env python3
"""
환경 설정 관리 모듈
.env 파일과 환경변수를 통해 설정을 로드합니다.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드 (config.env 파일 우선, 없으면 .env 파일)
env_file = Path(__file__).parent / "config.env"
if not env_file.exists():
    env_file = Path(__file__).parent / ".env"

if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ 환경변수 로드됨: {env_file}")
else:
    print("⚠️  .env 파일을 찾을 수 없습니다. 시스템 환경변수를 사용합니다.")

# Discord 설정
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("❌ DISCORD_TOKEN이 설정되지 않았습니다!")

# Supabase 설정
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://tmywnnshruqmoaempwwi.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
if not SUPABASE_KEY:
    raise ValueError("❌ SUPABASE_KEY가 설정되지 않았습니다!")

# 기본 채널 설정
DEFAULT_CHANNEL_ID = os.getenv('DEFAULT_CHANNEL_ID', '1159487918512017488')
DEFAULT_SERVER_ID = os.getenv('DEFAULT_SERVER_ID', '1159481575235403857')

# API 서버 설정
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))

# 메시지 수집 설정
COLLECTION_DAYS = int(os.getenv('COLLECTION_DAYS', 5))

# 설정 확인 함수
def validate_config():
    """설정값들이 제대로 로드되었는지 확인"""
    missing = []
    
    if not DISCORD_TOKEN:
        missing.append('DISCORD_TOKEN')
    if not SUPABASE_KEY:
        missing.append('SUPABASE_KEY')
    
    if missing:
        raise ValueError(f"❌ 다음 환경변수들이 설정되지 않았습니다: {', '.join(missing)}")
    
    return True

# 설정 정보 출력 (토큰 마스킹)
def print_config():
    """현재 설정 정보를 안전하게 출력"""
    print("🔧 현재 설정:")
    print(f"  ├─ Discord 토큰: {DISCORD_TOKEN[:20]}...{DISCORD_TOKEN[-10:] if len(DISCORD_TOKEN) > 30 else '***'}")
    print(f"  ├─ Supabase URL: {SUPABASE_URL}")
    print(f"  ├─ Supabase 키: {SUPABASE_KEY[:20]}...{SUPABASE_KEY[-10:] if len(SUPABASE_KEY) > 30 else '***'}")
    print(f"  ├─ 기본 채널: {DEFAULT_CHANNEL_ID}")
    print(f"  ├─ 기본 서버: {DEFAULT_SERVER_ID}")
    print(f"  ├─ API 호스트: {API_HOST}")
    print(f"  ├─ API 포트: {API_PORT}")
    print(f"  └─ 수집 기간: {COLLECTION_DAYS}일")

if __name__ == "__main__":
    validate_config()
    print_config() 