# AutoML Server Architecture

## Overview

`automl_server` is the main FastAPI service. It owns the platform API surface for datasets, annotations, tasks, deployment, inference, AI pipeline bindings, and home-page statistics.

- Default host: `0.0.0.0`
- Default port: `45678`
- Swagger UI: `/swagger-ui`
- Health check: `/health`

## Structure

```text
automl_server/
├── app/
│   ├── common/      # shared response, exceptions, constants
│   ├── config/      # settings, database, S3, Nacos
│   ├── db/          # SQLAlchemy models and sessions
│   ├── modules/    # feature modules
│   ├── mq/          # RabbitMQ client, handlers, messages
│   ├── scheduler/   # periodic jobs
│   └── utils/       # HTTP, S3, SSE and file helpers
├── run.py
├── requirements.txt
└── Dockerfile
```

## Feature Modules

- `dataset`: dataset CRUD, upload, preview, export, sample management
- `annotation`: annotation project CRUD and record handling
- `task`: training task submission, progress, logs, and SSE stream
- `deploy`: model deployment management and status syncing
- `inference`: inference API for deployed models
- `ai_pipeline`: AI pipeline templates, providers, and bindings
- `home`: platform statistics and recent activity

## Runtime Dependencies

- MySQL for primary persistence
- MinIO for datasets, models, annotations, and artifacts
- RabbitMQ for task and model lifecycle events
- Nacos for runtime configuration
- `model_trainer` for training execution
- `model_deploy` for deployment and runtime management
- `ai_pipeline_runtime` for AI-assisted annotation capabilities

## Request Flow

1. Frontend calls `automl_server`
2. `automl_server` reads config from Nacos or environment variables
3. The service persists metadata to MySQL and artifacts to MinIO
4. Training and deployment requests are published to RabbitMQ
5. Status updates are consumed back from RabbitMQ
6. AI-assisted annotation calls are routed to the AI pipeline runtime

## Configuration

Main configuration lives in:

- `app/config/settings.py`
- `app/config/s3_config.py`
- `app/config/nacos_config_center.py`

Environment examples:

- `automl_server/.env.example`
- root `.env.example`

Nacos config source:

- `nacos/automl-config.yaml`

## Local Run

```bash
cd automl_server
pip install -r requirements.txt
python run.py
```

The service reads `APP_HOST` and `APP_PORT` from the environment and falls back to `0.0.0.0:45678`.
