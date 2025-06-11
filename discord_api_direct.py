#!/usr/bin/env python3
"""
Discord Direct API Collector (Railway/Free hosting 호환)
Discord API를 직접 사용해서 메시지를 수집하는 모듈
"""

import os
import requests
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class DiscordAPICollector:
    def __init__(self, discord_token: str, supabase_url: str, supabase_key: str):
        """
        Initialize the Discord API collector
        
        Args:
            discord_token: Discord bot token (Bot prefix will be added automatically)
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
        """
        self.discord_token = discord_token
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Discord token 형식 확인 및 설정 (User token 지원)
        if discord_token.startswith('Bot '):
            self.headers = {
                'Authorization': discord_token,
                'Content-Type': 'application/json'
            }
        else:
            # User token인 경우 그대로 사용
            self.headers = {
                'Authorization': discord_token,
                'Content-Type': 'application/json'
            }
        
    def fetch_channel_messages(self, channel_id: str, hours: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Discord REST API를 사용해서 채널 메시지 가져오기
        
        Args:
            channel_id: Discord channel ID
            hours: Number of hours to go back
            limit: Maximum number of messages per request (Discord limit: 100)
            
        Returns:
            List of message dictionaries
        """
        logger.info(f"Fetching messages from channel {channel_id} for last {hours} hours")
        
        # 시간 계산
        after_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        all_messages = []
        last_message_id = None
        
        while True:
            params = {'limit': limit}
            if last_message_id:
                params['before'] = last_message_id
                
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                messages = response.json()
                
                if not messages:
                    break
                    
                # 시간 필터링
                filtered_messages = []
                for msg in messages:
                    msg_time = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                    if msg_time < after_time:
                        # 더 이상 오래된 메시지는 가져오지 않음
                        return all_messages
                    filtered_messages.append(msg)
                
                all_messages.extend(filtered_messages)
                
                # 다음 페이지를 위한 설정
                if len(messages) < limit:
                    break
                last_message_id = messages[-1]['id']
                
                logger.info(f"Fetched {len(filtered_messages)} messages in this batch")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to fetch messages: {e}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response: {e.response.text}")
                raise
        
        logger.info(f"Total fetched: {len(all_messages)} messages")
        return all_messages
    
    def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """
        채널 정보 가져오기
        """
        url = f"https://discord.com/api/v10/channels/{channel_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch channel info: {e}")
            return {}
    
    def get_guild_info(self, guild_id: str) -> Dict[str, Any]:
        """
        서버(길드) 정보 가져오기
        """
        if not guild_id:
            return {}
            
        url = f"https://discord.com/api/v10/guilds/{guild_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch guild info: {e}")
            return {}
    
    def format_messages_for_supabase(self, messages: List[Dict], channel_info: Dict, guild_info: Dict) -> List[Dict[str, Any]]:
        """
        Discord API 응답을 Supabase 형식으로 변환
        """
        formatted_messages = []
        
        for msg in messages:
            author = msg.get('author', {})
            
            formatted_msg = {
                'id': int(msg['id']),
                'channel_id': int(channel_info.get('id', 0)),
                'channel_name': channel_info.get('name', ''),
                'server_id': int(guild_info.get('id', 0)) if guild_info.get('id') else None,
                'server_name': guild_info.get('name', ''),
                'author_id': int(author.get('id', 0)),
                'author_name': author.get('username', ''),
                'author_discriminator': author.get('discriminator', ''),
                'author_avatar': f"https://cdn.discordapp.com/avatars/{author.get('id')}/{author.get('avatar')}.png" if author.get('avatar') else '',
                'content': msg.get('content', ''),
                'timestamp': msg.get('timestamp', ''),
                'message_type': msg.get('type', 0),
                'is_pinned': msg.get('pinned', False),
                'reference_message_id': int(msg['message_reference']['message_id']) if msg.get('message_reference', {}).get('message_id') else None,
                'attachments': json.dumps(msg.get('attachments', [])),
                'embeds': json.dumps(msg.get('embeds', [])),
                'reactions': json.dumps(msg.get('reactions', [])),
                'mentions': json.dumps(msg.get('mentions', []))
            }
            formatted_messages.append(formatted_msg)
        
        return formatted_messages
    
    def save_to_supabase(self, messages: List[Dict[str, Any]]) -> int:
        """
        메시지를 Supabase에 저장
        """
        if not messages:
            logger.warning("No messages to save")
            return 0
        
        logger.info(f"Saving {len(messages)} messages to Supabase")
        
        try:
            # 배치로 나누어 저장
            batch_size = 50
            total_saved = 0
            
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                result = self.supabase.table('discord_messages').upsert(
                    batch,
                    on_conflict='id'
                ).execute()
                total_saved += len(batch)
                logger.info(f"Saved batch {i//batch_size + 1}: {len(batch)} messages")
            
            logger.info(f"Successfully saved {total_saved} messages")
            return total_saved
            
        except Exception as e:
            logger.error(f"Failed to save messages: {e}")
            raise
    
    def collect_and_save(self, channel_id: str, hours: int = 1) -> Dict[str, Any]:
        """
        전체 워크플로우: 메시지 가져오기 -> 변환 -> 저장
        """
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting collection for channel {channel_id}, last {hours} hours")
        
        try:
            # 1. 메시지 가져오기
            messages = self.fetch_channel_messages(channel_id, hours)
            
            # 2. 채널 정보 가져오기
            channel_info = self.get_channel_info(channel_id)
            
            # 3. 서버 정보 가져오기
            guild_id = channel_info.get('guild_id')
            guild_info = self.get_guild_info(guild_id) if guild_id else {}
            
            # 4. Supabase 형식으로 변환
            formatted_messages = self.format_messages_for_supabase(messages, channel_info, guild_info)
            
            # 5. Supabase에 저장
            saved_count = self.save_to_supabase(formatted_messages)
            
            end_time = datetime.now(timezone.utc)
            execution_time = end_time - start_time
            
            result = {
                'status': 'success',
                'channel_id': channel_id,
                'channel_name': channel_info.get('name', ''),
                'server_name': guild_info.get('name', ''),
                'hours': hours,
                'messages_fetched': len(messages),
                'messages_saved': saved_count,
                'execution_time': str(execution_time),
                'timestamp': start_time.isoformat()
            }
            
            logger.info(f"Collection completed successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Collection failed: {e}")
            raise 