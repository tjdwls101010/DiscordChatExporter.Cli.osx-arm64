#!/usr/bin/env python3
"""
Discord Direct API Collector
Discord API를 직접 사용해서 메시지를 수집하는 모듈 (Vercel serverless functions용)
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class DiscordDirectCollector:
    def __init__(self, discord_token: str, supabase_url: str, supabase_key: str):
        """
        Initialize the direct API collector
        
        Args:
            discord_token: Discord bot or user token
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
        """
        self.discord_token = discord_token
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.headers = {
            'Authorization': discord_token,
            'Content-Type': 'application/json'
        }
        
    def get_channel_messages(self, channel_id: str, hours: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Discord API를 사용해서 채널 메시지 직접 가져오기
        
        Args:
            channel_id: Discord channel ID
            hours: Number of hours to go back
            limit: Maximum number of messages to fetch
            
        Returns:
            List of message dictionaries
        """
        # 시간 계산
        after_time = datetime.utcnow() - timedelta(hours=hours)
        after_snowflake = int((after_time.timestamp() - 1420070400) * 1000) << 22
        
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        params = {
            'after': str(after_snowflake),
            'limit': limit
        }
        
        logger.info(f"Fetching messages from channel {channel_id} after {after_time}")
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            messages = response.json()
            
            logger.info(f"Fetched {len(messages)} messages")
            return messages
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch messages: {e}")
            raise
    
    def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """
        채널 정보 가져오기
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            Channel information dictionary
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
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            Guild information dictionary
        """
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
        
        Args:
            messages: Discord API messages
            channel_info: Channel information
            guild_info: Guild information
            
        Returns:
            Formatted messages for Supabase
        """
        formatted_messages = []
        
        for msg in messages:
            # 메시지 작성자 정보
            author = msg.get('author', {})
            
            # 첨부파일, 임베드, 반응, 멘션 정보
            attachments = msg.get('attachments', [])
            embeds = msg.get('embeds', [])
            reactions = msg.get('reactions', [])
            mentions = msg.get('mentions', [])
            
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
                'attachments': json.dumps(attachments),
                'embeds': json.dumps(embeds),
                'reactions': json.dumps(reactions),
                'mentions': json.dumps(mentions)
            }
            formatted_messages.append(formatted_msg)
        
        return formatted_messages
    
    def save_to_supabase(self, messages: List[Dict[str, Any]]) -> int:
        """
        메시지를 Supabase에 저장
        
        Args:
            messages: Formatted message list
            
        Returns:
            Number of saved messages
        """
        if not messages:
            logger.warning("No messages to save")
            return 0
        
        logger.info(f"Saving {len(messages)} messages to Supabase")
        
        try:
            # UPSERT 사용 (중복 메시지 처리)
            result = self.supabase.table('discord_messages').upsert(
                messages,
                on_conflict='id'
            ).execute()
            
            logger.info(f"Successfully saved {len(messages)} messages")
            return len(messages)
            
        except Exception as e:
            logger.error(f"Failed to save messages: {e}")
            raise
    
    def collect_and_save(self, channel_id: str, hours: int = 1) -> Dict[str, Any]:
        """
        전체 워크플로우: 메시지 가져오기 -> 변환 -> 저장
        
        Args:
            channel_id: Discord channel ID
            hours: Number of hours to go back
            
        Returns:
            Collection result summary
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting collection for channel {channel_id}, {hours} hours")
        
        try:
            # 1. 메시지 가져오기
            messages = self.get_channel_messages(channel_id, hours)
            
            # 2. 채널 정보 가져오기
            channel_info = self.get_channel_info(channel_id)
            
            # 3. 서버 정보 가져오기 (채널 정보에서 guild_id 추출)
            guild_id = channel_info.get('guild_id')
            guild_info = self.get_guild_info(guild_id) if guild_id else {}
            
            # 4. Supabase 형식으로 변환
            formatted_messages = self.format_messages_for_supabase(messages, channel_info, guild_info)
            
            # 5. Supabase에 저장
            saved_count = self.save_to_supabase(formatted_messages)
            
            end_time = datetime.utcnow()
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
            
            logger.info(f"Collection completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Collection failed: {e}")
            raise 