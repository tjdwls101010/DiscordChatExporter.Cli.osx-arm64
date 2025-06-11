# 🚀 Discord Collector API 배포 가이드

## 🎯 배포 옵션

### 1️⃣ Docker를 이용한 로컬 배포

```bash
# 1. 환경변수 설정
cp env.example .env
# .env 파일을 편집해서 실제 토큰/키 입력

# 2. Docker 빌드 & 실행
docker-compose up -d

# 3. 접속 확인
curl http://localhost:8000/health
```

### 2️⃣ Railway 배포 (무료)

```bash
# 1. Railway CLI 설치
npm install -g @railway/cli

# 2. 로그인 & 프로젝트 생성
railway login
railway init

# 3. 환경변수 설정
railway variables set DISCORD_TOKEN=your_token_here
railway variables set SUPABASE_KEY=your_key_here

# 4. 배포
railway up
```

### 3️⃣ Render 배포 (무료)

1. GitHub에 코드 푸시
2. [render.com](https://render.com) 가입
3. "New Web Service" 선택
4. GitHub 저장소 연결
5. 환경변수 설정:
   - `DISCORD_TOKEN`
   - `SUPABASE_KEY`
6. 배포 완료!

### 4️⃣ VPS 직접 배포

```bash
# 서버에서 실행
git clone your-repo
cd Collector
pip install -r requirements.txt

# 환경변수 설정
export DISCORD_TOKEN=your_token
export SUPABASE_KEY=your_key

# 서버 실행 (백그라운드)
nohup uvicorn discord_api_server:app --host 0.0.0.0 --port 8000 &
```

## 🔐 보안 고려사항

### ⚠️ 반드시 해야 할 것들:

1. **토큰 숨기기**: 절대 코드에 하드코딩하지 말고 환경변수 사용
2. **HTTPS 사용**: 프로덕션에서는 SSL 인증서 필수
3. **API 키 제한**: Supabase에서 IP/도메인 제한 설정
4. **Rate Limiting**: API 호출 횟수 제한 (Discord API 제한 준수)
5. **인증 추가**: 공개 API라면 API 키나 JWT 토큰 인증 필요

### 🛡️ 추가 보안 강화:

```python
# API 키 인증 예시
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

def verify_api_key(token: str = Depends(security)):
    if token.credentials != os.getenv("API_SECRET_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token
```

## 🌐 도메인 연결

배포 후 커스텀 도메인을 연결하려면:

1. **Railway**: `railway domain add your-domain.com`
2. **Render**: 대시보드에서 Custom Domain 설정
3. **VPS**: Nginx/Cloudflare 설정

## 📊 모니터링

프로덕션에서는 다음 도구들 추천:
- **로그**: Sentry, LogRocket
- **메트릭**: Prometheus + Grafana
- **업타임**: UptimeRobot, Pingdom

---

성진아, 이제 전 세계 어디서든 API를 사용할 수 있어! 🎉 