FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# DiscordChatExporter.Cli 실행 권한 설정
RUN chmod +x ./bin/DiscordChatExporter.Cli

# 포트 노출
EXPOSE 8000

# 환경변수 설정
ENV PYTHONPATH=/app

# 서버 실행
CMD ["uvicorn", "discord_api_server:app", "--host", "0.0.0.0", "--port", "8000"] 