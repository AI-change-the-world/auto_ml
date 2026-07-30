# Model Trainer Service

模型训练服务，作为可选插件式能力面向训练任务。当前主要支持 YOLO 系列的检测和分类，训练任务由 `automl_server` 通过 RabbitMQ 下发，服务按配置并发执行，并通过 RabbitMQ 回传状态、日志和模型注册结果。

## 服务特性

- 独立部署：训练任务通过 RabbitMQ 接收，HTTP 只承担健康检查和取消任务
- 异步执行：训练任务在后台线程中运行，API 立即返回
- 并发控制：由部署配置控制同时执行的训练数
- 状态追踪：实时记录训练日志和进度到数据库
- 模型上传：训练完成后自动上传模型到 S3 / MinIO

## 通信方式

- 任务下发：`automl_server -> RabbitMQ -> model_trainer`
- 状态回传：`model_trainer -> RabbitMQ -> automl_server`
- 回传消息：
  - `task.status.update`
  - `task.log`
  - `model.registered`
- HTTP 接口：
  - `GET /health`
  - `POST /tasks/{task_id}/cancel`

当前没有单独启用 `service.heartbeat` 这类 MQ 心跳消息。主服务展示训练服务状态时，会按需请求 `model_trainer` 的 `/health`；任务总览页的 SSE 也只是每 5 秒重新探测一次 `/health`。

## 当前支持

1. 目标检测 (Detection): YOLOv8 / YOLOv11 检测模型
2. 图像分类 (Classification): YOLOv8 / YOLOv11 分类模型

## 扩展性

- 训练入口和任务结构已预留，后续可接入分割、姿态、OBB 等任务类型
- 模型适配层与数据处理逻辑分离，后续可扩展到其他训练后端
- 任务参数、导出格式和标签规范可按新模型继续扩展

## 部署方式

按需启用时启动该服务：

```bash
docker-compose up -d model-trainer
```

配置项见下表，通常由 `docker-compose.yml`、Nacos 或部署平台统一注入。

## API 接口

### 健康检查

`/health` 会返回服务状态、并发信息和版本号，当前版本为 `1.0.0`。

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

## 配置项

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
