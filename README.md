# Discord Message Collector API

Discord 채널의 메시지를 수집하여 Supabase 데이터베이스에 저장하는 REST API입니다.

## 🚀 기능

- Discord REST API를 사용한 메시지 수집
- Supabase 데이터베이스에 자동 저장
- 시간 기반 필터링 (설정 가능한 수집 기간)
- RESTful API 엔드포인트 제공
- Railway 클라우드 배포 지원

## 📚 API 엔드포인트

### 1. 서버 상태 확인
```
GET /
```
API 서버의 상태와 마지막 수집 정보를 반환합니다.

### 2. 헬스 체크
```
GET /health
```
서버와 Supabase 연결 상태를 확인합니다.

### 3. 메시지 수집 (동기)
```
POST /collect/sync
```
**Body:**
```json
{
  "channel_id": "your_channel_id",
  "hours": 24
}
```

### 4. 기본 채널 메시지 수집
```
GET /collect/momentum?hours=24
```
환경변수에 설정된 기본 채널에서 메시지를 수집합니다.

### 5. 작업 상태 조회
```
GET /tasks/{task_id}
GET /tasks
```

## 🛠 Railway 배포 가이드

### 1. Repository 준비
이 프로젝트를 자신의 GitHub 계정에 Fork하거나 Clone합니다.

### 2. Railway 프로젝트 생성
1. [Railway](https://railway.app)에 로그인
2. "New Project" 클릭
3. "Deploy from GitHub repo" 선택
4. 이 Repository 선택

### 3. 환경변수 설정
Railway 대시보드에서 다음 환경변수들을 설정하세요:

```
DISCORD_TOKEN=your_discord_bot_or_user_token
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
DEFAULT_CHANNEL_ID=your_discord_channel_id
DEFAULT_SERVER_ID=your_discord_server_id
COLLECTION_HOURS=24
```

### 4. Supabase 테이블 설정
Supabase에서 다음 테이블을 생성하세요:

```sql
CREATE TABLE discord_messages (
    id BIGINT PRIMARY KEY,
    channel_id BIGINT,
    channel_name TEXT,
    server_id BIGINT,
    server_name TEXT,
    author_id BIGINT,
    author_name TEXT,
    author_discriminator TEXT,
    author_avatar TEXT,
    content TEXT,
    timestamp TIMESTAMPTZ,
    message_type INTEGER,
    is_pinned BOOLEAN,
    reference_message_id BIGINT,
    attachments JSONB,
    embeds JSONB,
    reactions JSONB,
    mentions JSONB
);
```

### 5. 배포 완료
Railway가 자동으로 애플리케이션을 빌드하고 배포합니다. 배포가 완료되면 제공되는 URL을 통해 API에 접근할 수 있습니다.

## 🔑 Discord 토큰 발급

### Bot Token (권장)
1. [Discord Developer Portal](https://discord.com/developers/applications) 방문
2. "New Application" → 애플리케이션 이름 입력
3. "Bot" 탭 → "Add Bot"
4. "Token" 복사
5. 봇을 서버에 초대 (필요한 권한: Read Message History, View Channel)

### User Token (주의: 이용약관 위반 가능성)
User Token 사용은 Discord 이용약관에 위반될 수 있으므로 권장하지 않습니다.

## 📝 사용 예시

배포된 API 사용 예시:

```bash
# 헬스 체크
curl https://your-railway-app.railway.app/health

# 메시지 수집
curl -X POST https://your-railway-app.railway.app/collect/sync \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "123456789", "hours": 24}'

# 기본 채널 수집
curl https://your-railway-app.railway.app/collect/momentum?hours=48
```

## ⚠️ 주의사항

1. **Discord API 제한**: Discord API는 속도 제한이 있으므로 과도한 요청을 피하세요.
2. **개인정보 보호**: 수집된 메시지에는 개인정보가 포함될 수 있으므로 적절히 보호하세요.
3. **권한**: 봇이나 사용자가 해당 채널에 접근 권한이 있어야 합니다.
4. **비용**: Railway 무료 플랜에는 제한이 있으므로 사용량을 모니터링하세요.

## 🐛 문제 해결

### 일반적인 오류들

**403 Forbidden**: Discord 토큰이나 채널 접근 권한을 확인하세요.
**500 Internal Server Error**: Supabase 연결 설정을 확인하세요.
**Connection Timeout**: Railway 환경변수 설정을 확인하세요.

### 로그 확인
Railway 대시보드에서 "Deployments" → "View Logs"를 통해 실시간 로그를 확인할 수 있습니다.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 