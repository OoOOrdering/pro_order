# 베이스 이미지 (본인 프로젝트에 맞는 버전 기입)
FROM python:3.13.1

# 환경변수 설정
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# 종속성 파일 복사
#COPY ./poetry.lock ./pyproject.toml /WiStarBack/
COPY ./poetry.lock /WiStarBack/
COPY ./pyproject.toml /WiStarBack/

# 작업 디렉토리 설정
WORKDIR /WiStarBack

# 종속성 설치
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root
RUN poetry add gunicorn

# 애플리케이션 코드 복사
#COPY ./apps /WiStarBack/apps
#WORKDIR /WiStarBack/apps
COPY . /WiStarBack/


# 소켓 파일 생성 디렉토리 권한 설정
RUN mkdir -p /WiStarBack && chmod -R 755 /WiStarBack

# 기존 코드: 직접 gunicorn 사용해서 실행
# Gunicorn을 사용하여 애플리케이션 실행
#CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]

# 변경된 코드: 스크립트를 사용하여 애플리케이션 실행
COPY ./resources/scripts /resources/scripts
#RUN chmod +x /WiStarBack/resources/scripts/run.sh
RUN chmod +x /resources/scripts/run.sh
CMD ["/resources/scripts/run.sh"]


# readme = "README.md"