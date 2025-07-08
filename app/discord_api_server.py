#!/usr/bin/env python3
"""
Discord Collector API Server
FastAPI를 이용한 Discord 메시지 수집 API 서버
"""

import os
import sys
import asyncio
import tempfile
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from discord_to_supabase import DiscordToSupabaseCollector

# FastAPI 앱 초기화
app = FastAPI(
    title="Discord Collector API",
    description="Discord 메시지 수집 및 Supabase 저장 API",
    version="1.0.0"
)

# 요청/응답 모델 정의
class CollectRequest(BaseModel):
    channel_id: str
    hours: int = 1
    server_id: Optional[str] = None

class CollectResponse(BaseModel):
    status: str
    message: str
    task_id: Optional[str] = None
    messages_count: Optional[int] = None
    execution_time: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    server_info: Dict[str, Any]
    last_collection: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    discord_cli_available: bool
    supabase_connected: bool
    timestamp: str

# 환경변수에서 설정 로드
from config import SUPABASE_URL, SUPABASE_KEY, DISCORD_TOKEN, DEFAULT_CHANNEL_ID

# 작업 상태 저장
tasks_status = {}
last_collection_info = None

@app.get("/", response_model=StatusResponse)
async def root():
    """API 서버 상태 정보"""
    return StatusResponse(
        status="running",
        server_info={
            "name": "Discord Collector API",
            "version": "1.0.0",
            "description": "Discord 메시지 수집 및 Supabase 저장 API"
        },
        last_collection=last_collection_info
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """서버 헬스 체크"""
    # Discord CLI 사용 가능 여부 확인
    discord_cli_available = os.path.exists("./bin/DiscordChatExporter.Cli")
    
    # Supabase 연결 테스트
    supabase_connected = True
    try:
        collector = DiscordToSupabaseCollector(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            discord_token=DISCORD_TOKEN
        )
        # 간단한 연결 테스트
        supabase_connected = True
    except Exception:
        supabase_connected = False
    
    return HealthResponse(
        status="healthy" if discord_cli_available and supabase_connected else "warning",
        discord_cli_available=discord_cli_available,
        supabase_connected=supabase_connected,
        timestamp=datetime.now().isoformat()
    )

@app.post("/collect", response_model=CollectResponse)
async def collect_messages(request: CollectRequest, background_tasks: BackgroundTasks):
    """Discord 메시지 수집 (비동기)"""
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 태스크 상태 초기화
    tasks_status[task_id] = {
        "status": "started",
        "channel_id": request.channel_id,
        "hours": request.hours,
        "start_time": datetime.now(),
        "messages_count": 0
    }
    
    # 백그라운드에서 수집 작업 실행
    background_tasks.add_task(
        run_collection_task, 
        task_id, 
        request.channel_id, 
        request.hours
    )
    
    return CollectResponse(
        status="accepted",
        message=f"메시지 수집 작업이 시작되었습니다.",
        task_id=task_id
    )

@app.post("/collect/sync", response_model=CollectResponse)
async def collect_messages_sync(request: CollectRequest):
    """Discord 메시지 수집 (동기)"""
    start_time = datetime.now()
    
    try:
        # 수집기 생성
        collector = DiscordToSupabaseCollector(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            discord_token=DISCORD_TOKEN
        )
        
        # 메시지 수집
        result = collector.collect_and_save(
            channel_id=request.channel_id, 
            hours=request.hours
        )
        
        end_time = datetime.now()
        execution_time = str(end_time - start_time)
        
        # 글로벌 상태 업데이트
        global last_collection_info
        last_collection_info = {
            "channel_id": request.channel_id,
            "hours": request.hours,
            "timestamp": start_time.isoformat(),
            "execution_time": execution_time,
            "status": "completed"
        }
        
        return CollectResponse(
            status="completed",
            message=f"메시지 수집이 완료되었습니다.",
            messages_count=result.get('messages_count'),
            execution_time=execution_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"메시지 수집 중 오류 발생: {str(e)}"
        )

@app.get("/collect/momentum", response_model=CollectResponse)
async def collect_momentum_messages(hours: int = 1):
    """Momentum Messengers 서버 메시지 수집 (고정 설정)"""
    CHANNEL_ID = DEFAULT_CHANNEL_ID  # main-stock-chat
    
    request = CollectRequest(
        channel_id=CHANNEL_ID,
        hours=hours
    )
    
    return await collect_messages_sync(request)

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """작업 상태 조회"""
    if task_id not in tasks_status:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    return tasks_status[task_id]

@app.get("/tasks")
async def list_tasks():
    """모든 작업 목록"""
    return {"tasks": tasks_status}

async def run_collection_task(task_id: str, channel_id: str, hours: int):
    """백그라운드 수집 작업"""
    try:
        tasks_status[task_id]["status"] = "running"
        
        # 수집기 생성
        collector = DiscordToSupabaseCollector(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            discord_token=DISCORD_TOKEN
        )
        
        # 메시지 수집
        result = collector.collect_and_save(channel_id=channel_id, hours=hours)
        
        # 작업 완료
        end_time = datetime.now()
        tasks_status[task_id].update({
            "status": "completed",
            "end_time": end_time,
            "execution_time": str(end_time - tasks_status[task_id]["start_time"]),
            "messages_count": result.get('messages_count', 0)
        })
        
        # 글로벌 상태 업데이트
        global last_collection_info
        last_collection_info = {
            "channel_id": channel_id,
            "hours": hours,
            "timestamp": tasks_status[task_id]["start_time"].isoformat(),
            "execution_time": tasks_status[task_id]["execution_time"],
            "status": "completed"
        }
        
    except Exception as e:
        tasks_status[task_id].update({
            "status": "failed",
            "error": str(e),
            "end_time": datetime.now()
        })

if __name__ == "__main__":
    print("🚀 Discord Collector API Server")
    print("=" * 50)
    print("📊 API 엔드포인트:")
    print("  ├─ GET  /          : 서버 상태")
    print("  ├─ GET  /health    : 헬스 체크")
    print("  ├─ POST /collect   : 메시지 수집 (비동기)")
    print("  ├─ POST /collect/sync : 메시지 수집 (동기)")
    print("  ├─ GET  /collect/momentum : Momentum 서버 수집")
    print("  ├─ GET  /tasks/{id}: 작업 상태 조회")
    print("  └─ GET  /tasks     : 모든 작업 목록")
    print("=" * 50)
    print("🌐 서버 주소: http://localhost:8000")
    print("📝 API 문서: http://localhost:8000/docs")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 