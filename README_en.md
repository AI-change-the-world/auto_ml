# AutoML Studio

A platform for multi-modal dataset management, annotation, training, deployment, and AI-assisted labeling. It covers image, text, multimodal conversation, and preference labeling scenarios.

<div align="center">
  <img src="./readme/icon_v2.png" width="220" alt="AutoML Studio" />
</div>

## Platform Scope

- Dataset management for image, text, and multimodal conversation data
- Annotation workbenches for detection, classification, segmentation, pose, LLM/MLLM conversation, and DPO preference labeling
- Training services, currently focused on YOLO detection and classification
- Deployment services, currently focused on ONNX model serving and inference
- AI-assisted annotation capabilities for scene understanding, draft labeling, and white-overlay extraction

## Pluggable Services

`model_trainer`, `model_deploy`, and `ai_pipeline_runtime` are optional extension services. They do not have to run alongside the core platform, and can be enabled on demand as new training backends, inference backends, or AI capabilities are added.

## Components

- `frontend_v2`: React + TypeScript frontend, Vite dev server, default port `3000`
- `automl_server`: main API service that orchestrates datasets, annotations, tasks, deployments, and AI pipelines, default port `45678`
- `model_trainer`: optional training service, default port `8081`
- `model_deploy`: optional deployment service, default port `8082`
- `ai_pipeline_runtime`: optional AI capability runtime, default port `8010`
- Infrastructure: MySQL, MinIO, RabbitMQ, Nacos

## Architecture

```mermaid
flowchart TB
    B[Browser] --> F[frontend_v2\n:3000]
    F -->|/api| S[automl_server\n:45678]

    S --> DB[(MySQL)]
    S --> M[(MinIO)]
    S --> Q[(RabbitMQ)]
    S --> N[(Nacos)]
    S --> T[model_trainer\n:8081]
    S --> D[model_deploy\n:8082]
    S --> A[ai_pipeline_runtime\n:8010]

    T --> Q
    D --> Q
    A --> Q
    T --> N
    D --> N
    A --> N
```

## Repository Layout

```text
auto_ml/
├── frontend_v2/
├── automl_server/
├── model_trainer/
├── model_deploy/
├── ai_pipeline_runtime/
├── mysql/
├── nacos/
├── docker-compose.yml
├── docker-compose.dev.yml
└── .env.example
```

## Requirements

- Docker 20.10+
- Docker Compose v2
- Node.js `^20.19.0 || >=22.12.0`
- Python 3.10+
- pnpm `>=10`

## Quick Start

### 1. Start the core platform

```bash
cp .env.example .env
docker compose up -d
```

Endpoints:

- Frontend: `http://localhost:3000`
- Main API: `http://localhost:45678`
- Swagger UI: `http://localhost:45678/swagger-ui`
- Trainer: `http://localhost:8081`
- Deploy: `http://localhost:8082`
- AI runtime: `http://localhost:8010`
- RabbitMQ: `http://localhost:15672`
- MinIO: `http://localhost:9010`
- Nacos: `http://localhost:8848`

Optional service endpoints are available only when those services are enabled.

### 2. Local development

```bash
docker compose -f docker-compose.dev.yml up -d mysql rabbitmq minio nacos nacos-init
```

Frontend:

```bash
cd frontend_v2
pnpm install
pnpm dev
```

Main service:

```bash
cd automl_server
pip install -r requirements.txt
python run.py
```

Other services:

- `model_trainer/server.py`
- `model_deploy/server.py`
- `ai_pipeline_runtime/app.py`

## Configuration

- Root [.env.example](./.env.example) is used by `docker-compose.yml`
- `automl_server/.env.example` is for standalone backend runs
- `frontend_v2/.env.example` is for frontend development/builds
- `nacos/automl-config.yaml` is the Nacos config source

## Docs

- [Main service architecture](./automl_server/ARCHITECTURE.md)
- [Trainer service](./model_trainer/readme.md)
- [Deploy service](./model_deploy/readme.md)
- [AI runtime](./ai_pipeline_runtime/readme.md)

## Database

- Initial schema: `mysql/init/01_init_automl.sql`
- Migrations: `mysql/migrations/*.sql`

## Run Notes

- `docker-compose.yml` starts the core platform; optional services can be enabled on demand
- `/api` is proxied from the frontend container to the main service
- Runtime configuration is primarily provided by Nacos; `.env.example` files are for local development and container startup
- Each service `/health` now returns version information; optional services currently use `1.0.0`

## Acknowledgments

This project is built on top of the following open-source projects:

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Vite](https://vite.dev/)
- [Ant Design](https://ant.design/)
- [Konva](https://konvajs.org/)
- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
- [RabbitMQ](https://www.rabbitmq.com/)
- [MinIO](https://min.io/)
- [Nacos](https://nacos.io/)
- [Docker](https://www.docker.com/)
