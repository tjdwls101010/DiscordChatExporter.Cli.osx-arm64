#!/usr/bin/env python3
"""
Discord Chat to Supabase Collector
Discord API를 직접 사용해서 메시지를 수집하고 Supabase에 저장하는 스크립트
"""

import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from supabase import create_client, Client
from pathlib import Path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from discord_api_direct import DiscordAPICollector

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DiscordToSupabaseCollector:
    def __init__(self, supabase_url: str, supabase_key: str, discord_token: str):
        """
        Initialize the collector
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key  
            discord_token: Discord user or bot token
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.discord_token = discord_token
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
    
    def collect_and_save(self, channel_id: str, hours: int = 1) -> Dict[str, Any]:
        """
        Complete workflow: collect messages using Discord API and save to Supabase
        
        Args:
            channel_id: Discord channel ID
            hours: Number of hours to go back
            
        Returns:
            Dictionary with collection results
        """
        total_start_time = time.time()
        logger.info(f"🚀 전체 작업 시작: 채널 {channel_id} (최근 {hours}시간)")
        
        try:
            # Discord API를 직접 사용하여 메시지 수집
            api_collector = DiscordAPICollector(
                discord_token=self.discord_token,
                supabase_url=self.supabase_url,
                supabase_key=self.supabase_key
            )
            
            result = api_collector.collect_and_save(channel_id, hours)
            
            total_end_time = time.time()
            total_elapsed = total_end_time - total_start_time
            
            logger.info(f"✅ 전체 작업 완료 (총 소요시간: {total_elapsed:.2f}초)")
            logger.info(f"📊 수집 결과: {result.get('messages_saved', 0)}개 메시지")
            
            return {
                'status': 'success',
                'messages_count': result.get('messages_saved', 0),
                'execution_time': f"{total_elapsed:.2f}초",
                'channel_id': channel_id,
                'hours': hours,
                'channel_name': result.get('channel_name', ''),
                'server_name': result.get('server_name', '')
            }
            
        except Exception as e:
            total_end_time = time.time()
            total_elapsed = total_end_time - total_start_time
            logger.error(f"❌ 전체 작업 실패 (소요시간: {total_elapsed:.2f}초): {e}")
            raise


def main():
    """
    메인 실행 함수
    환경변수에서 설정을 로드합니다
    """
    
    # 환경변수에서 설정 로드
    from config import SUPABASE_URL, SUPABASE_KEY, DISCORD_TOKEN, DEFAULT_CHANNEL_ID, COLLECTION_DAYS, COLLECTION_HOURS, validate_config
    
    # 설정 검증
    if not validate_config():
        logger.error("환경변수 설정을 확인해주세요.")
        return
        
    CHANNEL_ID = DEFAULT_CHANNEL_ID
    
    # 수집기 생성 및 실행
    collector = DiscordToSupabaseCollector(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY,
        discord_token=DISCORD_TOKEN
    )
    
    # 메시지 수집 및 저장 (환경변수에서 설정된 기간)
    result = collector.collect_and_save(channel_id=CHANNEL_ID, hours=COLLECTION_HOURS)
    print(f"Collection completed: {result}")


if __name__ == "__main__":
    main() 