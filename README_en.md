<div align="center">
  <img src="./readme/icon_with_text.png" width="300" height="300">
</div>

<p align="center">📘 Other Language Versions</p>
<p align="center">
  <a href="README_en.md">English</a> | <a href="README.md">简体中文</a>
</p>

<p align="center">
  <strong>All-in-One Computer Vision AutoML Platform</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-project-structure">Project Structure</a> •
  <a href="#-development-guide">Development Guide</a>
</p>

---

## 📖 Introduction

AutoML is an open-source end-to-end computer vision platform that provides a complete workflow from **data management**, **image annotation**, **model training** to **model deployment**. Built with a modern microservices architecture and visual interface, AutoML makes AI model development simple and efficient.

**Key Advantages:**
- 🎯 **Full Process Coverage**: Dataset Management → Annotation → Training → Deployment, all in one place
- 🏷️ **Professional Annotation Tool**: Supports BBox, OBB (Oriented Bounding Box), Polygon, and more
- 🚀 **Microservices Architecture**: Distributed architecture based on Docker + RabbitMQ + Nacos, easy to scale
- 💾 **Object Storage Integration**: Supports MinIO/S3 storage for efficient management of large-scale datasets and models
- 🌐 **Modern Frontend**: React 19 + TypeScript + Ant Design 6, smooth user experience
- 🔌 **Plugin Design**: Independent training and deployment services, flexible extensibility

---

## ✨ Features

### 📂 Dataset Management
- Support for images, videos, text, and other data types
- ZIP/TAR batch import for rapid dataset creation
- S3/MinIO object storage for large-scale data management
- Complete operations: preview, export, append, and more

### 🏷️ Image Annotation
- **BBox Annotation**: Standard bounding boxes for object detection
- **OBB Annotation**: Rotated bounding boxes for oriented object detection
- **Polygon Annotation**: Polygon annotations for instance segmentation
- Annotation project management with custom classes
- High-performance rendering engine based on Konva
- Efficient annotation experience with undo/redo and keyboard shortcuts

### 🧪 Model Training
- Support for mainstream object detection models like YOLO
- Visual training task management
- Real-time training log viewing
- Base model library management
- Asynchronous task scheduling based on RabbitMQ

### ☁️ Model Deployment
- One-click deployment of trained models
- Dynamic port allocation for concurrent multi-model deployment
- RESTful API inference endpoints
- Model health checks and status monitoring
- Hot load/unload without service restart

### 🏠 Visual Dashboard
- Statistics for datasets, annotations, and models
- Recent activity tracking
- Storage usage overview
- Quick creation shortcuts

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React + TypeScript)           │
│                    http://localhost:5173                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────────┐
│                  AutoML Server (FastAPI)                     │
│                    Port: 45678                               │
│  ┌──────────┬──────────┬──────┬────────┬────────┐           │
│  │ Dataset  │Annotation│ Task │ Deploy │  Home  │           │
│  └──────────┴──────────┴──────┴────────┴────────┘           │
└────┬──────────────┬──────────────┬──────────────────────────┘
     │              │              │
     ▼              ▼              ▼
┌────────┐    ┌──────────┐   ┌──────────┐
│ MySQL  │    │  MinIO   │   │ RabbitMQ │
│  :3306 │    │  :9000   │   │  :5672   │
└────────┘    └──────────┘   └────┬─────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
          ┌─────────▼─────────┐      ┌─────────▼─────────┐
          │  Model Trainer    │      │  Model Deploy     │
          │  Port: 8081       │      │  Port: 8082       │
          │                   │      │  Runtime: 9001+   │
          └───────────────────┘      └───────────────────┘
```

### Tech Stack

**Frontend**
- React 19 + TypeScript
- Vite 8 (Build Tool)
- Ant Design 6 (UI Components)
- React Router 7 (Routing)
- Zustand (State Management)
- Konva + React-Konva (Canvas Rendering)
- i18next (Internationalization)
- Axios (HTTP Client)

**Backend**
- Python 3.10+
- FastAPI (Web Framework)
- SQLAlchemy 2.0 + AsyncIO (Async ORM)
- Uvicorn (ASGI Server)

**Infrastructure**
- MySQL 8.0 (Relational Database)
- MinIO (Object Storage)
- RabbitMQ (Message Queue)
- Nacos (Configuration Center)
- Docker & Docker Compose (Container Orchestration)

**Microservices**
- Model Trainer Service
- Model Deploy Service

---

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Node.js** 18+ (for frontend development)
- **Python** 3.10+ (for backend development)
- **Git** 2.0+

### Option 1: One-Click Docker Start (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/auto_ml.git
cd auto_ml

# 2. Configure environment variables
cp .env.example .env
# Modify the .env file as needed

# 3. Start all services
docker-compose up -d

# 4. Check service status
docker-compose ps

# 5. View logs
docker-compose logs -f
```

After services are started, access:
- **Frontend Dev Server**: `http://localhost:5173` (requires separate start, see Development Mode below)
- **AutoML Server API**: `http://localhost:45678`
- **API Docs (Swagger)**: `http://localhost:45678/swagger-ui`
- **Model Trainer**: `http://localhost:8081`
- **Model Deploy**: `http://localhost:8082`
- **RabbitMQ Management**: `http://localhost:15672` (user: automl / automl123456)
- **MinIO Console**: `http://localhost:9010` (user: minioadmin / minioadmin123)
- **Nacos Console**: `http://localhost:8848`

### Option 2: Development Mode

#### 1. Start Infrastructure

```bash
# Start only database, message queue, object storage, etc.
docker-compose up -d mysql rabbitmq minio nacos
```

#### 2. Start Frontend

```bash
cd frontend_v2

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

The frontend will run at `http://localhost:5173` with proxy configured to forward to the backend.

#### 3. Start Backend

```bash
cd automl_server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
python run.py
```

The backend will run at `http://localhost:45678`.

#### 4. Start Microservices (Optional)

```bash
# Model Trainer Service
cd model_trainer
pip install -r requirements.txt
python server.py

# Model Deploy Service
cd model_deploy
pip install -r requirements.txt
python server.py
```

---

## 📁 Project Structure

```
auto_ml/
├── frontend_v2/              # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── api/             # API clients
│   │   ├── pages/           # Page components
│   │   │   ├── home/        # Dashboard
│   │   │   ├── dataset/     # Dataset management
│   │   │   ├── annotation/  # Annotation tool
│   │   │   ├── task/        # Training tasks
│   │   │   └── deploy/      # Model deployment
│   │   ├── layouts/         # Layout components
│   │   ├── stores/          # State management
│   │   ├── types/           # TypeScript type definitions
│   │   └── i18n/            # Internationalization
│   └── package.json
│
├── automl_server/           # Main Server (FastAPI)
│   ├── app/
│   │   ├── modules/         # Business modules
│   │   │   ├── dataset/     # Dataset module
│   │   │   ├── annotation/  # Annotation module
│   │   │   ├── task/        # Training task module
│   │   │   ├── deploy/      # Deployment module
│   │   │   └── home/        # Dashboard module
│   │   ├── db/              # Database models
│   │   ├── mq/              # RabbitMQ message handling
│   │   ├── config/          # Configuration management
│   │   └── common/          # Common utilities
│   └── requirements.txt
│
├── model_trainer/           # Model Training Microservice
│   ├── core/                # Training core logic
│   ├── utils/               # Utilities
│   └── server.py            # Service entry
│
├── model_deploy/            # Model Deployment Microservice
│   ├── core/                # Deployment core logic
│   ├── runtime/             # Model runtime
│   ├── utils/               # Utilities
│   └── server.py            # Service entry
│
├── auto_augment_pipeline/   # Data Augmentation Pipeline (Optional)
│
├── docker-compose.yml       # Docker Compose configuration
├── mysql/init/              # Database initialization scripts
├── nacos/                   # Nacos configuration
└── readme/                  # Documentation images
```

---

## 🛠️ Development Guide

### Database Management

Database initialization script is located at `mysql/init/01_init_automl.sql`, executed automatically on first container startup.

To reset the database:
```bash
docker-compose down -v
docker-compose up -d mysql
```

### Configuration Management

The project uses Nacos as the configuration center. Configuration files are located at `nacos/automl-config.yaml`.

Main configuration items:
- MySQL connection details
- MinIO/S3 storage configuration
- RabbitMQ message queue configuration
- Microservice URL configuration

### API Documentation

Access Swagger UI after starting the service:
```
http://localhost:45678/swagger-ui
```

### Frontend Development

```bash
cd frontend_v2

# Install dependencies
pnpm install

# Start development server (with hot reload)
pnpm dev

# Build for production
pnpm build

# Lint code
pnpm lint
```

### Backend Development

```bash
cd automl_server

# Install dependencies
pip install -r requirements.txt

# Start development server (with hot reload)
python run.py

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 45678
```

---


## 🔧 Troubleshooting

### 1. Service Start Failure

Check Docker container status and logs:
```bash
docker-compose ps
docker-compose logs <service-name>
```

### 2. Database Connection Error

Ensure MySQL container is running and healthy:
```bash
docker-compose exec mysql mysql -u automl -p auto_ml
```

### 3. MinIO Access Issues

Check MinIO Console at `http://localhost:9010` and confirm buckets are created:
- `auto-ml-datasets`
- `auto-ml-models`
- `auto-ml-annotations`

### 4. Frontend Cannot Connect to Backend

Verify proxy configuration in `.env.development`:
```
VITE_API_BASE_URL=http://localhost:45678
```

---


## 🤝 Contributing

Contributions are welcome! Whether it's code, bug reports, or feature suggestions.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the [AGPL License](LICENSE).

---

## 🙏 Acknowledgments

Thanks to the following open-source projects:
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Ant Design](https://ant.design/)
- [Konva](https://konvajs.org/)
- [YOLO](https://github.com/ultralytics/ultralytics)
- [RabbitMQ](https://www.rabbitmq.com/)
- [MinIO](https://min.io/)

---

<div align="center">
  <strong>AutoML</strong> - Making Computer Vision Development Easier
</div>
