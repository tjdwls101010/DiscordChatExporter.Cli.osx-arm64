#!/usr/bin/env python3
"""
Vercel Serverless Function: Discord Message Collector
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from discord_collector_direct import DiscordDirectCollector

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(request, context):
    """
    Vercel serverless function handler
    """
    try:
        # 환경변수 로드
        discord_token = os.getenv('DISCORD_TOKEN')
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        default_channel_id = os.getenv('DEFAULT_CHANNEL_ID')
        
        # 필수 환경변수 체크
        if not all([discord_token, supabase_url, supabase_key]):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Missing required environment variables',
                    'required': ['DISCORD_TOKEN', 'SUPABASE_URL', 'SUPABASE_KEY']
                })
            }
        
        # HTTP 메서드 확인
        method = request.method
        
        if method == 'GET':
            # GET 요청 처리 (간단한 수집)
            query_params = getattr(request, 'args', {})
            channel_id = query_params.get('channel_id', default_channel_id)
            hours = int(query_params.get('hours', 1))
            
        elif method == 'POST':
            # POST 요청 처리 (JSON 바디)
            try:
                body = json.loads(request.get_data().decode('utf-8'))
                channel_id = body.get('channel_id', default_channel_id)
                hours = body.get('hours', 1)
            except (json.JSONDecodeError, AttributeError):
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Invalid JSON body'})
                }
        
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        # 유효성 검사
        if not channel_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'channel_id is required'})
            }
        
        if hours < 1 or hours > 24:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'hours must be between 1 and 24'})
            }
        
        # Discord 수집기 생성
        collector = DiscordDirectCollector(
            discord_token=discord_token,
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        
        # 메시지 수집 실행
        result = collector.collect_and_save(channel_id=channel_id, hours=hours)
        
        # 성공 응답
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'success',
                'message': f'Successfully collected messages from channel {channel_id}',
                'data': result
            })
        }
        
    except Exception as e:
        logger.error(f"Function execution failed: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            })
        } 