#!/usr/bin/env python3
"""
Supabase 연결 테스트 스크립트
"""

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

def test_supabase_connection():
    print(f"URL: {SUPABASE_URL}")
    print(f"Key (first 30 chars): {SUPABASE_KEY[:30]}...")
    
    try:
        # 클라이언트 생성
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase 클라이언트 생성 성공")
        
        # 테이블 목록 확인 (간단한 테스트)
        result = supabase.table('discord_messages').select("count", count="exact").execute()
        print(f"✅ 테이블 접근 성공: {result}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print(f"오류 타입: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_supabase_connection() 