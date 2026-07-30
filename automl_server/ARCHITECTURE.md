# AutoML Server Architecture

## Overview

`automl_server` is the main FastAPI service. It owns the platform API surface for datasets, annotations, tasks, deployment, inference, AI pipeline bindings, and home-page statistics across image, text, multimodal conversation, and preference labeling workflows.

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
- `annotation`: annotation project CRUD and record handling for detection, classification, segmentation, pose, LLM/MLLM, and DPO workflows
- `task`: training task submission, progress, logs, and SSE stream
- `deploy`: model deployment management and status syncing
- `inference`: inference API for deployed models
- `ai_pipeline`: AI pipeline templates, providers, and bindings
- `home`: platform statistics and recent activity

## Runtime Dependencies

- MySQL for primary persistence
- MinIO for datasets, models, annotations, and artifacts
- RabbitMQ for training jobs, AI Pipeline RPC, batch annotation execution, and deployment status callbacks
- Nacos for runtime configuration
- `model_trainer` as an optional training plug-in
- `model_deploy` as an optional deployment plug-in
- `ai_pipeline_runtime` as an optional AI-assisted annotation plug-in
- `ai_pipeline_sandbox` as the batch annotation execution plug-in

## Communication Paths

- Training:
  - `automl_server -> RabbitMQ -> model_trainer` for training job delivery
  - `model_trainer -> RabbitMQ -> automl_server` for task status, task logs, and model registration
  - `automl_server -> model_trainer` over HTTP for `/health` and `/tasks/{task_id}/cancel`
- Deployment:
  - `automl_server -> model_deploy` over HTTP for deploy, undeploy, deployment listing, deployment health, and inference
  - `model_deploy -> RabbitMQ -> automl_server` for `model.deployed` and `model.undeployed`
- AI runtime:
  - `automl_server <-> ai_pipeline_runtime` via RabbitMQ RPC for assist annotation and pipeline execution
- Batch annotation:
  - `automl_server -> RabbitMQ -> ai_pipeline_sandbox` for `pipeline.batch.execute`
  - `ai_pipeline_sandbox -> RabbitMQ -> automl_server` for progress and result callbacks

`service.heartbeat` still exists in the shared message definitions, but trainer and deploy do not currently use a standalone MQ heartbeat channel. Service status in the UI is derived from on-demand `/health` probes initiated by `automl_server`.

## Request Flow

1. Frontend calls `automl_server`
2. `automl_server` reads config from Nacos or environment variables
3. The service persists metadata to MySQL and artifacts to MinIO
4. Training jobs are published to RabbitMQ when `model_trainer` is enabled
5. Deployment control and inference requests are sent to `model_deploy` over HTTP
6. Deployment status, training status, logs, model registration, and batch callbacks are consumed back from RabbitMQ
7. AI-assisted annotation calls are routed to `ai_pipeline_runtime` via RabbitMQ RPC when enabled

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
