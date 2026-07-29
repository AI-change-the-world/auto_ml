FROM python:3.12-slim

WORKDIR /app

ARG SANDBOX_UID=10001
ARG SANDBOX_GID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid "${SANDBOX_GID}" sandbox \
    && useradd --uid "${SANDBOX_UID}" --gid "${SANDBOX_GID}" --create-home --shell /usr/sbin/nologin sandbox

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

COPY . .
RUN mkdir -p /app/runtime-data/venvs /app/runtime-data/pip-cache /app/scripts \
    && chown -R "${SANDBOX_UID}:${SANDBOX_GID}" /app/runtime-data

USER sandbox

EXPOSE 8011

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8011"]
