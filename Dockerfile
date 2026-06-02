# 1. Base 이미지 설정 (conda가 포함된 miniconda3 이미지 사용)
FROM continuumio/miniconda3:latest

# 2. 작업 디렉토리 생성 및 설정
WORKDIR /app

# 3. Python 관련 환경 변수 설정
# - PYTHONDONTWRITEBYTECODE: .pyc 파일 생성을 방지하여 컨테이너 경량화 유지
# - PYTHONUNBUFFERED: 버퍼링 없이 즉시 로그를 출력하도록 설정하여 docker logs 확인 용이
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드, 메인 스크립트 및 데이터베이스 파일 복사
COPY main.py .
COPY scr/ ./scr/
COPY data_base/ ./data_base/

# 6. 볼륨 마운트를 위한 빈 디렉토리 생성
RUN mkdir -p input output

# 7. 애플리케이션 실행 명령어
CMD ["python", "main.py"]
