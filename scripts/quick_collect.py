#!/usr/bin/env python3
"""
Momentum Messengers 빠른 수집 스크립트
API 클라이언트를 사용하여 자동으로 메시지 수집
"""

import sys
from discord_api_client import DiscordCollectorClient

def main():
    print("⚡ Momentum Messengers 빠른 수집")
    print("=" * 50)
    
    # 수집할 일수 입력
    try:
        days_input = input("수집할 일수 (기본값: 1, 엔터로 건너뛰기): ").strip()
        days = int(days_input) if days_input.isdigit() else 1
    except KeyboardInterrupt:
        print("\n🛑 사용자가 취소했습니다.")
        return
    
    print(f"🎯 {days}일치 메시지 수집을 시작합니다...")
    print()
    
    # 클라이언트 생성
    client = DiscordCollectorClient()
    
    # 서버 상태 확인
    health = client.check_health()
    if health.get("status") == "error":
        print(f"❌ API 서버 연결 실패!")
        print("💡 서버를 먼저 시작해주세요:")
        print("   python start_server.py")
        print()
        print(f"🔍 에러 내용: {health.get('message')}")
        return
    
    print(f"✅ API 서버 연결됨")
    
    # 메시지 수집
    try:
        result = client.collect_momentum_messages(days)
        
        if result.get("status") == "completed":
            print()
            print("🎉 수집 완료!")
            print("=" * 30)
            print(f"📊 실행 시간: {result.get('execution_time', 'N/A')}")
            print(f"⚡ 네트워크 시간: {result.get('client_execution_time', 'N/A')}")
            print(f"📝 메시지 수: {result.get('messages_count', 'N/A')}")
            print()
            print("🌐 Supabase에서 결과 확인:")
            print("   https://supabase.com/dashboard/project/tmywnnshruqmoaempwwi")
        else:
            print(f"❌ 수집 실패: {result.get('message', 'Unknown error')}")
            
    except KeyboardInterrupt:
        print("\n🛑 사용자가 수집을 취소했습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    main() 