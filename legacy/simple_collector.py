#!/usr/bin/env python3
"""
Simple Discord to Supabase Collector
간단한 스키마: id, timestamp, author_name, content, attachments, embeds만 저장
"""

import json
import subprocess
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from supabase import create_client, Client

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleDiscordCollector:
    def __init__(self, supabase_url: str, supabase_key: str, discord_token: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.discord_token = discord_token
        self.discord_exporter_path = "./bin/DiscordChatExporter.Cli"
        
    def export_messages(self, channel_id: str, days: int = 1) -> str:
        """Discord에서 메시지 내보내기"""
        after_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        output_file = f"simple_messages_{channel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        cmd = [
            self.discord_exporter_path,
            "export",
            "--channel", channel_id,
            "--token", self.discord_token,
            "--format", "Json",
            "--after", after_date,
            "--output", output_file,
            "--media", "false"
        ]
        
        logger.info(f"메시지 내보내기 시작: {channel_id} (최근 {days}일)")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"내보내기 완료: {output_file}")
            return output_file
        except subprocess.CalledProcessError as e:
            logger.error(f"내보내기 실패: {e}")
            raise
    
    def parse_and_simplify(self, json_file: str) -> List[Dict[str, Any]]:
        """JSON 파일을 파싱하고 간단한 형태로 변환 (답장 정보 포함)"""
        logger.info(f"JSON 파일 파싱 시작: {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 먼저 모든 메시지의 ID와 content를 매핑
            message_map = {}
            for msg in data.get('messages', []):
                message_map[msg['id']] = msg.get('content', '')
            
            simple_messages = []
            for msg in data.get('messages', []):
                # 답장 정보 처리
                reference_message_id = None
                reference_message_content = None
                
                if msg.get('reference'):
                    ref_id = msg['reference'].get('messageId')
                    if ref_id:
                        reference_message_id = int(ref_id)
                        # 같은 파일에서 참조 메시지의 content 찾기
                        reference_message_content = message_map.get(ref_id, '')
                
                simple_msg = {
                    'id': int(msg['id']),
                    'timestamp': msg['timestamp'],
                    'author_name': msg['author']['name'],
                    'content': msg.get('content', ''),
                    'attachments': json.dumps(msg.get('attachments', [])),
                    'embeds': json.dumps(msg.get('embeds', [])),
                    'reference_message_id': reference_message_id,
                    'reference_message_content': reference_message_content
                }
                simple_messages.append(simple_msg)
            
            logger.info(f"간단 파싱 완료: {len(simple_messages)}개 메시지")
            return simple_messages
            
        except Exception as e:
            logger.error(f"파싱 실패: {e}")
            raise
    
    def save_to_supabase(self, messages: List[Dict[str, Any]]) -> None:
        """Supabase 간단한 테이블에 저장"""
        if not messages:
            logger.warning("저장할 메시지가 없습니다.")
            return
        
        logger.info(f"Supabase에 {len(messages)}개 메시지 저장 시작")
        
        try:
            batch_size = 100
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                
                result = self.supabase.table('simple_discord_messages').upsert(
                    batch,
                    on_conflict='id'
                ).execute()
                
                logger.info(f"배치 {i//batch_size + 1} 저장 완료: {len(batch)}개 메시지")
            
            logger.info("모든 메시지 저장 완료")
            
        except Exception as e:
            logger.error(f"저장 실패: {e}")
            raise
    
    def collect_and_save(self, channel_id: str, days: int = 1) -> Dict[str, Any]:
        """전체 워크플로우 실행 (시간 측정 포함)"""
        start_time = time.time()
        
        try:
            # 1. 메시지 내보내기
            json_file = self.export_messages(channel_id, days)
            
            # 2. 간단하게 파싱
            messages = self.parse_and_simplify(json_file)
            
            # 3. 간단한 테이블에 저장
            self.save_to_supabase(messages)
            
            # 4. 파일 정리
            if os.path.exists(json_file):
                os.remove(json_file)
                logger.info(f"임시 파일 삭제: {json_file}")
            
            end_time = time.time()
            total_time = end_time - start_time
            
            logger.info("전체 작업 완료!")
            
            return {
                'success': True,
                'message_count': len(messages),
                'total_time_seconds': total_time,
                'total_time_formatted': self.format_time(total_time)
            }
            
        except Exception as e:
            end_time = time.time()
            total_time = end_time - start_time
            logger.error(f"작업 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_time_seconds': total_time,
                'total_time_formatted': self.format_time(total_time)
            }
    
    def format_time(self, seconds: float) -> str:
        """초를 분:초 형태로 포맷팅"""
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}분 {remaining_seconds}초"

def main():
    # 환경변수에서 설정 로드
    from config import SUPABASE_URL, SUPABASE_KEY, DISCORD_TOKEN, DEFAULT_CHANNEL_ID
    CHANNEL_ID = DEFAULT_CHANNEL_ID  # main-stock-chat
    DAYS = 1
    
    print("🤖 Simple Discord to Supabase Collector")
    print("=" * 60)
    print("📊 간단한 스키마:")
    print("  ├─ timestamp: 작성 시간")
    print("  ├─ author_name: 작성자명")
    print("  ├─ reference_message_content: 답장 대상 메시지 내용")
    print("  ├─ content: 메시지 내용")
    print("  ├─ attachments: 첨부파일 (JSON)")
    print("  ├─ embeds: 임베드 (JSON)")
    print("  ├─ id: 메시지 ID")
    print("  ├─ reference_message_id: 답장 대상 메시지 ID")
    print("  └─ created_at: 수집 시간")
    print("=" * 60)
    
    print("\n⚡ 간단한 수집 시작...")
    
    collector = SimpleDiscordCollector(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY,
        discord_token=DISCORD_TOKEN
    )
    
    result = collector.collect_and_save(channel_id=CHANNEL_ID, days=DAYS)
    
    if result['success']:
        print("\n✅ 모든 작업이 완료되었습니다!")
        print(f"📊 처리된 메시지: {result['message_count']}개")
        print(f"⏱️  총 소요시간: {result['total_time_formatted']}")
        print("📊 간단한 테이블: simple_discord_messages")
        print("🌐 https://supabase.com/dashboard/project/tmywnnshruqmoaempwwi")
    else:
        print(f"\n❌ 오류 발생: {result['error']}")
        print(f"⏱️  총 소요시간: {result['total_time_formatted']}")

if __name__ == "__main__":
    main() 