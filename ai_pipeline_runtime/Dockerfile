FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/ai_pipeline_runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY ai_pipeline_runtime/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install -r /tmp/requirements.txt

COPY ai_pipeline_runtime /app/ai_pipeline_runtime

EXPOSE 8010

CMD ["uvicorn", "ai_pipeline_runtime.app:app", "--host", "0.0.0.0", "--port", "8010"]
