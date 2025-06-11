#!/usr/bin/env python3
"""
Discord Chat to Supabase Collector
최근 5일치 Discord 메시지를 수집해서 Supabase에 저장하는 스크립트
"""

import json
import subprocess
import os
import tempfile
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from supabase import create_client, Client
from pathlib import Path

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
        self.discord_exporter_path = "./bin/DiscordChatExporter.Cli"
        
    def export_messages(self, channel_id: str, days: int = 5) -> str:
        """
        Export messages from Discord channel using DiscordChatExporter
        
        Args:
            channel_id: Discord channel ID
            days: Number of days to go back
            
        Returns:
            Path to the exported JSON file
        """
        start_time = time.time()
        logger.info(f"⏰ [STEP 1] Discord 메시지 내보내기 시작: {channel_id} (최근 {days}일)")
        
        # 날짜 계산 (5일 전)
        after_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 임시 출력 파일
        output_file = f"messages_{channel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # DiscordChatExporter CLI 명령어
        cmd = [
            self.discord_exporter_path,
            "export",
            "--channel", channel_id,
            "--token", self.discord_token,
            "--format", "Json",
            "--after", after_date,
            "--output", output_file,
            "--media", "false"  # 미디어 다운로드 안함 (속도 향상)
        ]
        
        logger.info(f"명령어: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.info(f"✅ [STEP 1] 내보내기 완료: {output_file} (소요시간: {elapsed_time:.2f}초)")
            return output_file
        except subprocess.CalledProcessError as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.error(f"❌ [STEP 1] DiscordChatExporter 실행 실패 (소요시간: {elapsed_time:.2f}초): {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            raise
    
    def parse_discord_json(self, json_file: str) -> List[Dict[str, Any]]:
        """
        Parse Discord JSON export file
        
        Args:
            json_file: Path to JSON file
            
        Returns:
            List of parsed message dictionaries
        """
        start_time = time.time()
        logger.info(f"⏰ [STEP 2] JSON 파일 파싱 시작: {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages = []
            channel_info = data.get('channel', {})
            guild_info = data.get('guild', {})
            
            for msg in data.get('messages', []):
                parsed_msg = {
                    'id': int(msg['id']),
                    'channel_id': int(channel_info.get('id', 0)),
                    'channel_name': channel_info.get('name', ''),
                    'server_id': int(guild_info.get('id', 0)) if guild_info.get('id') else None,
                    'server_name': guild_info.get('name', ''),
                    'author_id': int(msg['author']['id']),
                    'author_name': msg['author']['name'],
                    'author_discriminator': msg['author'].get('discriminator', ''),
                    'author_avatar': msg['author'].get('avatarUrl', ''),
                    'content': msg.get('content', ''),
                    'timestamp': msg['timestamp'],
                    'message_type': msg.get('type', 'Default'),
                    'is_pinned': msg.get('isPinned', False),
                    'reference_message_id': int(msg['reference']['messageId']) if msg.get('reference', {}).get('messageId') else None,
                    'attachments': json.dumps(msg.get('attachments', [])),
                    'embeds': json.dumps(msg.get('embeds', [])),
                    'reactions': json.dumps(msg.get('reactions', [])),
                    'mentions': json.dumps(msg.get('mentions', []))
                }
                messages.append(parsed_msg)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.info(f"✅ [STEP 2] 파싱 완료: {len(messages)}개 메시지 (소요시간: {elapsed_time:.2f}초)")
            return messages
            
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.error(f"❌ [STEP 2] JSON 파싱 실패 (소요시간: {elapsed_time:.2f}초): {e}")
            raise
    
    def save_to_supabase(self, messages: List[Dict[str, Any]]) -> None:
        """
        Save messages to Supabase
        
        Args:
            messages: List of message dictionaries
        """
        if not messages:
            logger.warning("저장할 메시지가 없습니다.")
            return
        
        start_time = time.time()
        logger.info(f"⏰ [STEP 3] Supabase에 {len(messages)}개 메시지 저장 시작")
        
        try:
            # 배치로 나누어 저장 (한 번에 너무 많이 보내지 않기 위해)
            batch_size = 100
            for i in range(0, len(messages), batch_size):
                batch_start_time = time.time()
                batch = messages[i:i + batch_size]
                
                # UPSERT 사용 (중복 메시지 처리)
                result = self.supabase.table('discord_messages').upsert(
                    batch,
                    on_conflict='id'
                ).execute()
                
                batch_end_time = time.time()
                batch_elapsed = batch_end_time - batch_start_time
                logger.info(f"  📦 배치 {i//batch_size + 1} 저장 완료: {len(batch)}개 메시지 (배치 소요시간: {batch_elapsed:.2f}초)")
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.info(f"✅ [STEP 3] 모든 메시지 저장 완료 (총 소요시간: {elapsed_time:.2f}초)")
            
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.error(f"❌ [STEP 3] Supabase 저장 실패 (소요시간: {elapsed_time:.2f}초): {e}")
            raise
    
    def collect_and_save(self, channel_id: str, days: int = 5) -> None:
        """
        Complete workflow: export, parse, and save messages
        
        Args:
            channel_id: Discord channel ID
            days: Number of days to go back
        """
        total_start_time = time.time()
        logger.info(f"🚀 전체 작업 시작: 채널 {channel_id} (최근 {days}일)")
        
        try:
            # 1. Discord에서 메시지 내보내기
            json_file = self.export_messages(channel_id, days)
            
            # 2. JSON 파일 파싱
            messages = self.parse_discord_json(json_file)
            
            # 3. Supabase에 저장
            self.save_to_supabase(messages)
            
            # 4. 임시 파일 정리
            cleanup_start_time = time.time()
            logger.info(f"⏰ [STEP 4] 임시 파일 정리 시작")
            if os.path.exists(json_file):
                os.remove(json_file)
                cleanup_end_time = time.time()
                cleanup_elapsed = cleanup_end_time - cleanup_start_time
                logger.info(f"✅ [STEP 4] 임시 파일 삭제: {json_file} (소요시간: {cleanup_elapsed:.2f}초)")
            
            total_end_time = time.time()
            total_elapsed = total_end_time - total_start_time
            logger.info(f"🎉 전체 작업 완료! (총 소요시간: {total_elapsed:.2f}초)")
            
            # 시간 요약 출력
            logger.info("=" * 50)
            logger.info("📊 작업 시간 요약:")
            logger.info(f"  전체 작업 시간: {total_elapsed:.2f}초 ({total_elapsed/60:.1f}분)")
            logger.info("=" * 50)
            
        except Exception as e:
            total_end_time = time.time()
            total_elapsed = total_end_time - total_start_time
            logger.error(f"❌ 작업 실패 (경과시간: {total_elapsed:.2f}초): {e}")
            raise


def main():
    """
    메인 실행 함수
    환경변수에서 설정을 로드합니다
    """
    
    # 환경변수에서 설정 로드
    from config import SUPABASE_URL, SUPABASE_KEY, DISCORD_TOKEN, DEFAULT_CHANNEL_ID, COLLECTION_DAYS, validate_config
    
    # 설정 검증
    try:
        validate_config()
    except ValueError as e:
        logger.error(str(e))
        return
        
    CHANNEL_ID = DEFAULT_CHANNEL_ID
    
    # 수집기 생성 및 실행
    collector = DiscordToSupabaseCollector(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY,
        discord_token=DISCORD_TOKEN
    )
    
    # 메시지 수집 및 저장 (환경변수에서 설정된 기간)
    collector.collect_and_save(channel_id=CHANNEL_ID, days=COLLECTION_DAYS)


if __name__ == "__main__":
    main() 