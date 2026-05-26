# Model Trainer Service

轻量级模型训练服务，专门用于 YOLO 模型的训练。
训练任务统一通过 RabbitMQ 下发，服务内部按并发限制消费执行。

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

# 关闭 Nacos，直接走本地环境变量
export USE_NACOS=false
export S3_ACCESS_KEY="minioadmin"
export S3_SECRET_KEY="minioadmin"
export S3_ENDPOINT="http://localhost:9000"
export S3_MODELS_BUCKET="auto-ml-models"
export S3_DATASETS_BUCKET="auto-ml-datasets"
export S3_ANNOTATIONS_BUCKET="auto-ml-annotations"
export RABBITMQ_HOST="localhost"
export RABBITMQ_PORT=5672
export RABBITMQ_USER="automl"
export RABBITMQ_PASSWORD="automl123456"
export RABBITMQ_VHOST="/"
export RABBITMQ_EXCHANGE="auto_ml_exchange"
export RABBITMQ_EXCHANGE_TYPE="topic"
export TRAINER_TASK_QUEUE="trainer.task.queue"
export TRAINER_TASK_ROUTING_KEY="trainer.task.submit"
export TRAINER_MAX_CONCURRENT=1

# 启动服务
export PORT=8081
python server.py
```

### Docker 运行

```bash
# 构建镜像
docker build -t model-trainer ./model_trainer

# 运行容器
docker run -d \
  -p 8081:8081 \
  -e USE_NACOS=false \
  -e S3_ACCESS_KEY="minioadmin" \
  -e S3_SECRET_KEY="minioadmin" \
  -e S3_ENDPOINT="http://minio:9000" \
  -e S3_DATASETS_BUCKET="auto-ml-datasets" \
  -e S3_MODELS_BUCKET="auto-ml-models" \
  -e S3_ANNOTATIONS_BUCKET="auto-ml-annotations" \
  -e RABBITMQ_HOST="rabbitmq" \
  -e RABBITMQ_PORT=5672 \
  -e RABBITMQ_USER="automl" \
  -e RABBITMQ_PASSWORD="automl123456" \
  -e RABBITMQ_VHOST="/" \
  -e RABBITMQ_EXCHANGE="auto_ml_exchange" \
  -e RABBITMQ_EXCHANGE_TYPE="topic" \
  -e TRAINER_TASK_QUEUE="trainer.task.queue" \
  -e TRAINER_TASK_ROUTING_KEY="trainer.task.submit" \
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

### MQ 训练任务
```bash
{
  "task_id": 1,
  "task_type": "detection",
  "sources": [
    {
      "dataset_id": 1,
      "annotation_id": 1,
      "source_order": 0,
      "source_name": "dataset / annotation",
      "samples": [
        {
          "sample_item_id": 101,
          "item_key": "image-001.jpg",
          "item_type": "image",
          "asset": {
            "file_name": "image-001.jpg",
            "save_path": "datasets/.../image-001.jpg",
            "asset_type": "image"
          },
          "annotation": {
            "annotation_type": 0,
            "content": {
              "format": "yolo",
              "label_text": "0 0.500000 0.500000 0.250000 0.250000"
            }
          }
        }
      ]
    }
  ],
  "classes": ["person", "car", "dog"],
  "task_config": {
    "name": "yolo11n.pt",
    "epoch": 10,
    "size": 640,
    "batch": 8,
    "device": "cpu",
    "label_format": "auto",
    "dataset_id": 1,
    "annotation_id": 1
  }
}
```

`task_config.label_format` 支持：

- `auto`: 默认。模型名包含 `obb` 时导出为 OBB，否则导出为普通 YOLO BBox
- `bbox`: 统一导出为 `class x_center y_center width height`
- `obb`: 统一导出为 `class x1 y1 x2 y2 x3 y3 x4 y4`

Detection 训练允许标注目录里混放 BBox 和 OBB；训练前会自动归一化：

- 训练 `bbox` 时：`OBB -> 外接 BBox`
- 训练 `obb` 时：`BBox -> 四点 OBB`

分类任务将 `task_type` 改为 `classification`，并省略 `classes`。

## 消息队列模式

启动服务后会自动监听训练队列。

```bash
python server.py
```

并发训练数通过环境变量控制：

```bash
export TRAINER_MAX_CONCURRENT=1
```

服务会把超出并发上限的任务保存在本地等待队列中，并持续通过 RabbitMQ 回传状态和日志。

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
| S3_ACCESS_KEY | S3 Access Key | - |
| S3_SECRET_KEY | S3 Secret Key | - |
| S3_ENDPOINT | S3 服务端点 | - |
| S3_DATASETS_BUCKET | 数据集 Bucket | - |
| S3_MODELS_BUCKET | 模型存储 Bucket | - |
| S3_ANNOTATIONS_BUCKET | 标注 Bucket | - |
| RABBITMQ_HOST | RabbitMQ 主机 | localhost |
| RABBITMQ_PORT | RabbitMQ 端口 | 5672 |
| RABBITMQ_USER | RabbitMQ 用户名 | automl |
| RABBITMQ_PASSWORD | RabbitMQ 密码 | automl123456 |
| RABBITMQ_VHOST | RabbitMQ 虚拟主机 | / |
| RABBITMQ_EXCHANGE | RabbitMQ Exchange | auto_ml_exchange |
| RABBITMQ_EXCHANGE_TYPE | RabbitMQ Exchange 类型 | topic |
| TRAINER_MAX_CONCURRENT | 最大并发训练数 | 1 |
| TRAINER_TASK_QUEUE | 训练任务队列名 | trainer.task.queue |
| TRAINER_TASK_ROUTING_KEY | 训练任务路由键 | trainer.task.submit |
| USE_NACOS | 是否启用 Nacos | true |
| NACOS_SERVER_ADDR | Nacos 地址 | 127.0.0.1:8848 |
| NACOS_NAMESPACE | Nacos Namespace | public |
| NACOS_DATA_ID | Nacos Data ID | AUTO_ML_CONFIG |
| NACOS_GROUP | Nacos Group | AUTO_ML |
| HOST | 服务监听地址 | 0.0.0.0 |
| PORT | 服务端口 | 8081 |
