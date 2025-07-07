#!/usr/bin/env python3
"""
Discord Collector API Server 시작 스크립트
"""

import os
import sys

def main():
    print("🚀 Discord Collector API Server 시작")
    print("=" * 50)
    
    # 가상환경 활성화 안내
    if 'discord_collector_env' not in sys.prefix:
        print("⚠️  가상환경이 활성화되지 않았을 수 있습니다.")
        print("💡 가상환경 활성화:")
        print("   source ../discord_collector_env/bin/activate")
        print()
    
    # Discord CLI 확인
    if not os.path.exists("./bin/DiscordChatExporter.Cli"):
        print("❌ DiscordChatExporter.Cli를 찾을 수 없습니다.")
        print("💡 현재 위치가 Collector 폴더인지 확인해주세요.")
        return
    
    print("✅ 환경 확인 완료")
    print("🌐 서버 주소: http://localhost:8000")
    print("📝 API 문서: http://localhost:8000/docs")
    print("🔄 서버를 중지하려면 Ctrl+C를 누르세요")
    print("=" * 50)
    print()
    
    # 서버 시작
    from discord_api_server import app
    import uvicorn
    from config import API_HOST, API_PORT
    
    try:
        uvicorn.run(app, host=API_HOST, port=API_PORT)
    except KeyboardInterrupt:
        print("\n🛑 서버가 중지되었습니다.")
    except Exception as e:
        print(f"\n❌ 서버 시작 실패: {e}")

if __name__ == "__main__":
    main() 