# 1. 가벼운 파이썬 이미지를 베이스로 사용
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 필수 패키지 설치를 위해 파일 복사
COPY requirements.txt .

# 4. 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 5. 프로젝트 전체 파일 복사 (scripts, templates 포함)
COPY . .

# 6. Fly.io 환경에 맞춰 포트 설정 (8080 권장) 및 실행
# uvicorn 실행 시 host를 0.0.0.0으로 해야 외부 접속이 가능합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]