#!/usr/bin/env python3
"""
Discord Message Collector API (Railway 배포용)
FastAPI를 사용한 Discord 메시지 수집 API 서버
"""

import os
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from discord_api_direct import DiscordAPICollector

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="Discord Message Collector API",
    description="Discord 채널에서 메시지를 수집해서 Supabase에 저장하는 API",
    version="2.0.0"
)

# CORS 설정 (모든 origin 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청/응답 모델
class CollectRequest(BaseModel):
    channel_id: str
    hours: int = 1
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    discord_token: Optional[str] = None

class CollectResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    env_vars_loaded: dict

# 환경변수에서 기본값 로드
DEFAULT_DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DEFAULT_SUPABASE_URL = os.getenv('SUPABASE_URL')
DEFAULT_SUPABASE_KEY = os.getenv('SUPABASE_KEY')
DEFAULT_CHANNEL_ID = os.getenv('DEFAULT_CHANNEL_ID')

@app.get("/", response_model=dict)
async def root():
    """API 서버 정보"""
    return {
        "name": "Discord Message Collector API",
        "version": "2.0.0",
        "description": "Discord 채널에서 메시지를 수집해서 Supabase에 저장",
        "endpoints": {
            "GET /": "서버 정보",
            "GET /health": "헬스 체크",
            "POST /collect": "메시지 수집 (사용자 설정)",
            "GET /collect/quick": "간편 수집 (기본 설정)"
        },
        "example_usage": {
            "quick_collect": "GET /collect/quick?hours=6",
            "custom_collect": "POST /collect with JSON body"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """서버 헬스 체크"""
    env_status = {
        "discord_token": bool(DEFAULT_DISCORD_TOKEN),
        "supabase_url": bool(DEFAULT_SUPABASE_URL),
        "supabase_key": bool(DEFAULT_SUPABASE_KEY),
        "default_channel_id": bool(DEFAULT_CHANNEL_ID)
    }
    
    return HealthResponse(
        status="healthy" if all(env_status.values()) else "partial",
        timestamp=datetime.now().isoformat(),
        env_vars_loaded=env_status
    )

@app.get("/collect/quick", response_model=CollectResponse)
async def quick_collect(hours: int = 1, channel_id: Optional[str] = None):
    """
    간편 메시지 수집 (환경변수 사용)
    
    Query Parameters:
    - hours: 수집할 시간 범위 (기본값: 1)
    - channel_id: Discord 채널 ID (기본값: 환경변수)
    """
    # 환경변수 확인
    if not all([DEFAULT_DISCORD_TOKEN, DEFAULT_SUPABASE_URL, DEFAULT_SUPABASE_KEY]):
        raise HTTPException(
            status_code=500,
            detail="서버 환경변수가 설정되지 않았습니다. POST /collect을 사용해서 직접 설정해주세요."
        )
    
    target_channel_id = channel_id or DEFAULT_CHANNEL_ID
    if not target_channel_id:
        raise HTTPException(
            status_code=400,
            detail="channel_id가 필요합니다."
        )
    
    # 시간 범위 검증
    if hours < 1 or hours > 24:
        raise HTTPException(
            status_code=400,
            detail="hours는 1~24 사이여야 합니다."
        )
    
    try:
        # 수집기 생성 및 실행
        collector = DiscordAPICollector(
            discord_token=DEFAULT_DISCORD_TOKEN,
            supabase_url=DEFAULT_SUPABASE_URL,
            supabase_key=DEFAULT_SUPABASE_KEY
        )
        
        result = collector.collect_and_save(channel_id=target_channel_id, hours=hours)
        
        return CollectResponse(
            status="success",
            message=f"✅ {result['messages_saved']}개 메시지를 성공적으로 수집했습니다!",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Quick collect failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"메시지 수집 중 오류가 발생했습니다: {str(e)}"
        )

@app.post("/collect", response_model=CollectResponse)
async def collect_messages(request: CollectRequest):
    """
    메시지 수집 (사용자 설정)
    
    Request Body:
    - channel_id: Discord 채널 ID (필수)
    - hours: 수집할 시간 범위 (기본값: 1)
    - discord_token: Discord bot 토큰 (선택, 없으면 환경변수 사용)
    - supabase_url: Supabase URL (선택, 없으면 환경변수 사용)
    - supabase_key: Supabase API 키 (선택, 없으면 환경변수 사용)
    """
    # 토큰 설정
    discord_token = request.discord_token or DEFAULT_DISCORD_TOKEN
    supabase_url = request.supabase_url or DEFAULT_SUPABASE_URL
    supabase_key = request.supabase_key or DEFAULT_SUPABASE_KEY
    
    # 필수 파라미터 확인
    if not all([discord_token, supabase_url, supabase_key]):
        missing = []
        if not discord_token: missing.append("discord_token")
        if not supabase_url: missing.append("supabase_url")
        if not supabase_key: missing.append("supabase_key")
        
        raise HTTPException(
            status_code=400,
            detail=f"다음 파라미터가 필요합니다: {', '.join(missing)}"
        )
    
    # 시간 범위 검증
    if request.hours < 1 or request.hours > 24:
        raise HTTPException(
            status_code=400,
            detail="hours는 1~24 사이여야 합니다."
        )
    
    try:
        # 수집기 생성 및 실행
        collector = DiscordAPICollector(
            discord_token=discord_token,
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        
        result = collector.collect_and_save(channel_id=request.channel_id, hours=request.hours)
        
        return CollectResponse(
            status="success",
            message=f"✅ {result['messages_saved']}개 메시지를 성공적으로 수집했습니다!",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Custom collect failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"메시지 수집 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/docs-info")
async def docs_info():
    """API 사용법 안내"""
    return {
        "api_docs": "/docs (Swagger UI)",
        "redoc": "/redoc (ReDoc)",
        "examples": {
            "quick_collect_1h": {
                "method": "GET",
                "url": "/collect/quick?hours=1",
                "description": "기본 설정으로 최근 1시간 메시지 수집"
            },
            "quick_collect_6h": {
                "method": "GET", 
                "url": "/collect/quick?hours=6&channel_id=123456789",
                "description": "특정 채널에서 최근 6시간 메시지 수집"
            },
            "custom_collect": {
                "method": "POST",
                "url": "/collect",
                "body": {
                    "channel_id": "1159487918512017488",
                    "hours": 3,
                    "discord_token": "your-bot-token",
                    "supabase_url": "https://your-project.supabase.co",
                    "supabase_key": "your-supabase-key"
                },
                "description": "사용자 설정으로 메시지 수집"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 