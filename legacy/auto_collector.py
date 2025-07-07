# source discord_collector_env/bin/activate && python auto_collector.py

#!/usr/bin/env python3
"""
Discord to Supabase Collector - 완전 자동화 스크립트
서버: momentum messangers (1159481575235403857)
채널: main-stock-chat (1159487918512017488)
자동 실행: 5일치 메시지 수집
"""

import os
import sys
from discord_to_supabase import DiscordToSupabaseCollector

def main():
    # 환경변수에서 설정 로드
    from config import SUPABASE_URL, SUPABASE_KEY, DISCORD_TOKEN, DEFAULT_CHANNEL_ID, DEFAULT_SERVER_ID
    SERVER_ID = DEFAULT_SERVER_ID  # momentum messangers
    CHANNEL_ID = DEFAULT_CHANNEL_ID  # main-stock-chat
    DAYS = 1  # 고정: 1일치 수집
    
    print("🤖 Discord to Supabase Auto Collector")
    print("=" * 60)
    print("📊 자동 실행 설정:")
    print(f"  ├─ 서버: momentum messangers ({SERVER_ID})")
    print(f"  ├─ 채널: main-stock-chat ({CHANNEL_ID})")
    print(f"  ├─ 수집 기간: 최근 {DAYS}일")
    print(f"  ├─ 토큰: {DISCORD_TOKEN[:20]}...{DISCORD_TOKEN[-10:]}")
    print(f"  └─ Supabase: tmywnnshruqmoaempwwi")
    print("=" * 60)
    
    try:
        print("\n⚡ 자동 실행 시작...")
        
        # 수집기 생성
        print("📡 Discord 수집기 초기화 중...")
        collector = DiscordToSupabaseCollector(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            discord_token=DISCORD_TOKEN
        )
        
        # 메시지 수집 및 저장 (자동 실행)
        print(f"🔄 메시지 수집 시작 (최근 {DAYS}일)...")
        collector.collect_and_save(channel_id=CHANNEL_ID, days=DAYS)
        
        print("\n✅ 모든 작업이 완료되었습니다!")
        print("🎯 결과:")
        print("  ├─ Discord 메시지 수집 완료")
        print("  ├─ Supabase 데이터베이스 저장 완료")
        print("  └─ 임시 파일 정리 완료")
        print("\n📊 Supabase 대시보드에서 'discord_messages' 테이블을 확인해보세요!")
        print("🌐 https://supabase.com/dashboard/project/tmywnnshruqmoaempwwi")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n🔍 가능한 원인:")
        print("  ├─ Discord 토큰 만료")
        print("  ├─ 채널 접근 권한 없음")
        print("  ├─ 네트워크 연결 문제")
        print("  └─ Supabase 연결 문제")
        sys.exit(1)

if __name__ == "__main__":
    main() 