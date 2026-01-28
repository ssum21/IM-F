# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# Streamlit 포트 노출
EXPOSE 8501

# Streamlit 실행을 위한 헬스체크
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Streamlit 앱 실행
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
