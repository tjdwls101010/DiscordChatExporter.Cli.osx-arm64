#!/usr/bin/env python3
"""
Discord Collector API Client
FastAPI 서버와 통신하는 클라이언트
"""

import requests
import time
import sys
from datetime import datetime
from typing import Optional, Dict, Any

class DiscordCollectorClient:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        Discord Collector API 클라이언트 초기화
        
        Args:
            api_base_url: API 서버 주소
        """
        self.api_base_url = api_base_url.rstrip('/')
        
    def check_health(self) -> Dict[str, Any]:
        """서버 헬스 체크"""
        try:
            response = requests.get(f"{self.api_base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def get_server_status(self) -> Dict[str, Any]:
        """서버 상태 조회"""
        try:
            response = requests.get(f"{self.api_base_url}/")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def collect_messages_sync(self, channel_id: str, days: int = 1) -> Dict[str, Any]:
        """
        메시지 동기 수집
        
        Args:
            channel_id: 디스코드 채널 ID
            days: 수집할 일수
        
        Returns:
            수집 결과
        """
        payload = {
            "channel_id": channel_id,
            "days": days
        }
        
        try:
            print(f"📡 메시지 수집 시작 (채널: {channel_id}, 기간: {days}일)")
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_base_url}/collect/sync",
                json=payload
            )
            response.raise_for_status()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            result = response.json()
            result["client_execution_time"] = f"{execution_time:.2f}초"
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def collect_messages_async(self, channel_id: str, days: int = 1) -> Dict[str, Any]:
        """
        메시지 비동기 수집
        
        Args:
            channel_id: 디스코드 채널 ID
            days: 수집할 일수
        
        Returns:
            태스크 정보
        """
        payload = {
            "channel_id": channel_id,
            "days": days
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/collect",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def collect_momentum_messages(self, days: int = 1) -> Dict[str, Any]:
        """
        Momentum Messengers 서버 메시지 수집 (고정 설정)
        
        Args:
            days: 수집할 일수
            
        Returns:
            수집 결과
        """
        try:
            print(f"🎯 Momentum Messengers 메시지 수집 시작 ({days}일)")
            start_time = time.time()
            
            response = requests.get(
                f"{self.api_base_url}/collect/momentum",
                params={"days": days}
            )
            response.raise_for_status()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            result = response.json()
            result["client_execution_time"] = f"{execution_time:.2f}초"
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """작업 상태 조회"""
        try:
            response = requests.get(f"{self.api_base_url}/tasks/{task_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def list_tasks(self) -> Dict[str, Any]:
        """모든 작업 목록 조회"""
        try:
            response = requests.get(f"{self.api_base_url}/tasks")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
    
    def wait_for_task(self, task_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """
        작업 완료까지 대기
        
        Args:
            task_id: 작업 ID
            max_wait_time: 최대 대기 시간 (초)
        
        Returns:
            최종 작업 상태
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.get_task_status(task_id)
            
            if status.get("status") == "error":
                return status
            
            task_status = status.get("status")
            
            if task_status in ["completed", "failed"]:
                return status
            
            print(f"⏳ 작업 진행 중... ({task_status})")
            time.sleep(2)
        
        return {"status": "timeout", "message": "작업 완료 대기 시간 초과"}

def main():
    """메인 실행 함수"""
    print("🤖 Discord Collector API Client")
    print("=" * 60)
    
    # 클라이언트 초기화
    client = DiscordCollectorClient()
    
    # 서버 상태 확인
    print("🔍 서버 상태 확인 중...")
    health = client.check_health()
    
    if health.get("status") == "error":
        print(f"❌ API 서버 연결 실패: {health.get('message')}")
        print("💡 서버가 실행 중인지 확인해주세요:")
        print("   cd Collector && python discord_api_server.py")
        sys.exit(1)
    
    print(f"✅ 서버 상태: {health.get('status', 'unknown')}")
    print(f"  ├─ Discord CLI: {'✅' if health.get('discord_cli_available') else '❌'}")
    print(f"  └─ Supabase: {'✅' if health.get('supabase_connected') else '❌'}")
    
    # 사용자 선택
    print("\n📋 수집 방법을 선택하세요:")
    print("  1. Momentum Messengers 자동 수집 (권장)")
    print("  2. 커스텀 채널 동기 수집")
    print("  3. 커스텀 채널 비동기 수집")
    print("  4. 작업 상태 조회")
    print("  5. 서버 정보 조회")
    
    choice = input("\n선택 (1-5): ").strip()
    
    if choice == "1":
        # Momentum Messengers 자동 수집
        days = input("수집할 일수 (기본값: 1): ").strip()
        days = int(days) if days.isdigit() else 1
        
        print(f"\n🚀 Momentum Messengers 메시지 수집 시작...")
        result = client.collect_momentum_messages(days)
        
        if result.get("status") == "completed":
            print(f"✅ 수집 완료!")
            print(f"  ├─ 실행 시간: {result.get('execution_time', 'N/A')}")
            print(f"  ├─ 클라이언트 시간: {result.get('client_execution_time', 'N/A')}")
            print(f"  └─ 메시지 수: {result.get('messages_count', 'N/A')}")
        else:
            print(f"❌ 수집 실패: {result.get('message', 'Unknown error')}")
    
    elif choice == "2":
        # 커스텀 채널 동기 수집
        channel_id = input("채널 ID: ").strip()
        days = input("수집할 일수 (기본값: 1): ").strip()
        days = int(days) if days.isdigit() else 1
        
        if not channel_id:
            print("❌ 채널 ID가 필요합니다.")
            return
        
        print(f"\n🚀 메시지 수집 시작...")
        result = client.collect_messages_sync(channel_id, days)
        
        if result.get("status") == "completed":
            print(f"✅ 수집 완료!")
            print(f"  ├─ 실행 시간: {result.get('execution_time', 'N/A')}")
            print(f"  ├─ 클라이언트 시간: {result.get('client_execution_time', 'N/A')}")
            print(f"  └─ 메시지 수: {result.get('messages_count', 'N/A')}")
        else:
            print(f"❌ 수집 실패: {result.get('message', 'Unknown error')}")
    
    elif choice == "3":
        # 커스텀 채널 비동기 수집
        channel_id = input("채널 ID: ").strip()
        days = input("수집할 일수 (기본값: 1): ").strip()
        days = int(days) if days.isdigit() else 1
        
        if not channel_id:
            print("❌ 채널 ID가 필요합니다.")
            return
        
        print(f"\n🚀 비동기 메시지 수집 시작...")
        result = client.collect_messages_async(channel_id, days)
        
        if result.get("status") == "accepted":
            task_id = result.get("task_id")
            print(f"✅ 작업 시작됨 (ID: {task_id})")
            
            # 작업 완료 대기
            print("⏳ 작업 완료 대기 중...")
            final_result = client.wait_for_task(task_id)
            
            if final_result.get("status") == "completed":
                print(f"✅ 수집 완료!")
                print(f"  ├─ 실행 시간: {final_result.get('execution_time', 'N/A')}")
                print(f"  └─ 메시지 수: {final_result.get('messages_count', 'N/A')}")
            else:
                print(f"❌ 수집 실패: {final_result}")
        else:
            print(f"❌ 작업 시작 실패: {result.get('message', 'Unknown error')}")
    
    elif choice == "4":
        # 작업 상태 조회
        tasks = client.list_tasks()
        
        if tasks.get("status") == "error":
            print(f"❌ 작업 목록 조회 실패: {tasks.get('message')}")
            return
        
        task_list = tasks.get("tasks", {})
        
        if not task_list:
            print("📋 진행 중인 작업이 없습니다.")
        else:
            print("📋 작업 목록:")
            for task_id, info in task_list.items():
                print(f"  ├─ {task_id}: {info.get('status', 'unknown')}")
                print(f"  │  ├─ 채널: {info.get('channel_id', 'N/A')}")
                print(f"  │  ├─ 기간: {info.get('days', 'N/A')}일")
                print(f"  │  └─ 시작: {info.get('start_time', 'N/A')}")
    
    elif choice == "5":
        # 서버 정보 조회
        status = client.get_server_status()
        
        if status.get("status") == "error":
            print(f"❌ 서버 정보 조회 실패: {status.get('message')}")
            return
        
        print("📊 서버 정보:")
        server_info = status.get("server_info", {})
        print(f"  ├─ 이름: {server_info.get('name', 'N/A')}")
        print(f"  ├─ 버전: {server_info.get('version', 'N/A')}")
        print(f"  └─ 설명: {server_info.get('description', 'N/A')}")
        
        last_collection = status.get("last_collection")
        if last_collection:
            print("📈 마지막 수집:")
            print(f"  ├─ 채널: {last_collection.get('channel_id', 'N/A')}")
            print(f"  ├─ 시간: {last_collection.get('timestamp', 'N/A')}")
            print(f"  └─ 상태: {last_collection.get('status', 'N/A')}")
    
    else:
        print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main() 