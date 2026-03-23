# Model Trainer Service

轻量级模型训练服务，专门用于 YOLO 模型的训练。

## 架构特点

- **独立服务**: 可单独部署，通过 HTTP API 或消息队列接收训练任务
- **串行训练**: 单 GPU/CPU 场景下串行执行训练任务
- **异步处理**: 训练任务在后台线程中执行，API 立即返回
- **状态追踪**: 实时记录训练日志和进度到数据库
- **模型上传**: 训练完成后自动上传模型到 S3

## 支持的模型类型

1. **目标检测 (Detection)**: YOLOv8/v11 检测模型
2. **图像分类 (Classification)**: YOLOv8/v11 分类模型

## 快速开始

### 本地运行

```bash
cd model_trainer
pip install -r requirements.txt

# 设置环境变量
export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/auto_ml"
export S3_ACCESS_KEY="minioadmin"
export S3_SECRET_KEY="minioadmin"
export S3_ENDPOINT="http://localhost:9000"
export S3_MODELS_BUCKET="auto-ml-models"
export S3_DATASETS_BUCKET="auto-ml-datasets"

# 启动服务
python server.py
```

### Docker 运行

```bash
# 构建镜像
docker build -t model-trainer ./model_trainer

# 运行容器
docker run -d \
  -p 8081:8080 \
  -e DATABASE_URL="mysql+pymysql://user:password@host:3306/auto_ml" \
  -e S3_ACCESS_KEY="minioadmin" \
  -e S3_SECRET_KEY="minioadmin" \
  -e S3_ENDPOINT="http://minio:9000" \
  model-trainer
```

### Docker Compose

```bash
# 复制环境变量模板
cp .env.example .env
# 编辑 .env 文件配置你的环境变量

# 启动所有服务
docker-compose up -d model-trainer
```

## API 接口

### 健康检查
```bash
GET /health
```

### 启动检测模型训练
```bash
POST /train/detection
Content-Type: application/json

{
  "task_id": 1,
  "dataset_path": "datasets/dataset_1",
  "annotation_path": "annotations/anno_1",
  "classes": ["person", "car", "dog"],
  "task_config": {
    "name": "yolo11n.pt",
    "epoch": 10,
    "size": 640,
    "batch": 8,
    "device": "cpu",
    "dataset_id": 1,
    "annotation_id": 1
  }
}
```

### 启动分类模型训练
```bash
POST /train/classification
Content-Type: application/json

{
  "task_id": 2,
  "dataset_path": "datasets/dataset_2",
  "annotation_path": "annotations/anno_2",
  "task_config": {
    "name": "yolo11n-cls.pt",
    "epoch": 10,
    "size": 640,
    "batch": 8,
    "device": "cpu",
    "dataset_id": 2,
    "annotation_id": 2
  }
}
```

### 查询训练状态
```bash
GET /train/{task_id}/status
```

## 消息队列模式

启动 MQ 消费者模式（用于异步处理训练任务）：

```bash
export MQ_CONSUMER=true
python server.py
```

向 Redis 队列推送任务：
```python
import redis
import json

r = redis.from_url("redis://localhost:6379/0")
task = {
    "task_type": "detection",
    "task_id": 1,
    "dataset_path": "datasets/dataset_1",
    "annotation_path": "annotations/anno_1",
    "classes": ["person", "car"],
    "task_config": {...}
}
r.lpush("model_trainer_queue", json.dumps(task))
```

## 目录结构

```
model_trainer/
├── core/
│   ├── dataset.py      # 数据集处理
│   └── trainer.py      # 训练核心逻辑
├── db/
│   ├── base.py         # 数据库基础
│   ├── models.py       # 数据模型
│   └── crud.py         # 数据库操作
├── utils/
│   ├── config.py       # 配置管理
│   └── logger.py       # 日志配置
├── server.py           # FastAPI 服务
├── requirements.txt
└── Dockerfile
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | 数据库连接 URL | - |
| S3_ACCESS_KEY | S3 Access Key | - |
| S3_SECRET_KEY | S3 Secret Key | - |
| S3_ENDPOINT | S3 服务端点 | - |
| S3_MODELS_BUCKET | 模型存储 Bucket | - |
| S3_DATASETS_BUCKET | 数据集 Bucket | - |
| MQ_TYPE | 消息队列类型 (redis) | redis |
| MQ_URL | 消息队列连接 URL | redis://localhost:6379/0 |
| HOST | 服务监听地址 | 0.0.0.0 |
| PORT | 服务端口 | 8080 |