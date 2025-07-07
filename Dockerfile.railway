# Railway 최적화 Dockerfile
FROM python:3.11-slim

# 환경변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 시스템 패키지 업데이트 및 필요한 도구 설치
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    libicu-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# .NET 8 런타임 설치 (DiscordChatExporter.Cli용)
RUN wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh \
    && chmod +x dotnet-install.sh \
    && ./dotnet-install.sh --channel 8.0 --runtime aspnetcore --install-dir /usr/share/dotnet \
    && rm dotnet-install.sh

ENV PATH="/usr/share/dotnet:$PATH"

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치 (캐싱 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY ./app .

# Railway는 PORT 환경변수를 자동으로 설정
# 서버 시작 명령어는 railway.json에서 정의됨
CMD ["uvicorn", "discord_api_server:app", "--host", "0.0.0.0", "--port", "8000"] 