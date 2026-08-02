FROM python:3.12-slim

WORKDIR /app

ARG RUNTIME_UID=10002
ARG RUNTIME_GID=10002

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid "${RUNTIME_GID}" runtime \
    && useradd --uid "${RUNTIME_UID}" --gid "${RUNTIME_GID}" --create-home --shell /usr/sbin/nologin runtime

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

COPY . .

USER runtime

EXPOSE 8012

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8012"]
