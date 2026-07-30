# Model Deploy Service

模型部署服务，作为可选插件式能力负责 ONNX 模型的部署、运行时管理和推理转发，当前主要面向 YOLO 系列模型。当前这条链路是“HTTP 控制 + MQ 状态同步”：主服务直接调用部署接口，部署结果再通过 RabbitMQ 回写主库。

## 服务特性

- 控制面 / 数据面分离：Deploy Service 负责控制，Model Runtime 负责执行
- 模型即部署单元：管理的是部署实例，而不是单个进程
- ONNX 统一格式：训练 -> 导出 ONNX -> 部署
- 轻量运行：不依赖 K8s 或 Triton，Docker Compose 即可运行

## 通信方式

- 部署控制：`automl_server -> HTTP -> model_deploy`
- 推理调用：`automl_server -> HTTP -> model_deploy`
- 状态同步：`model_deploy -> RabbitMQ -> automl_server`
- 回传消息：
  - `model.deployed`
  - `model.undeployed`
- HTTP 接口：
  - `GET /health`
  - `POST /deploy`
  - `POST /undeploy/{model_id}`
  - `GET /deployments`
  - `GET /deploy/{model_id}/health`
  - `POST /predict/{model_id}` 及其 `base64` / `url` 变体

当前没有单独启用 `service.heartbeat` 这类 MQ 心跳消息。主服务获取部署概览或单模型运行状态时，会直接调用 `model_deploy` 的 `/deployments` 与 `/deploy/{model_id}/health`。

## 当前支持

1. ONNX 模型部署与推理
2. YOLO 检测模型运行时
3. YOLO 分类模型运行时
4. 多实例端口管理与健康检查

## 整体架构

```text
automl_server
  ├─ HTTP /deploy /undeploy /deployments /deploy/{id}/health /predict
  ▼
model-deploy
  ├─ Runtime Manager
  ▼
model runtime processes (port 9001+)

model-deploy
  ├─ MQ: model.deployed / model.undeployed
  ▼
RabbitMQ
  ▼
automl_server
```

## 核心组件

### 1. Runtime Manager

- 启动 / 停止模型实例进程
- 端口分配管理 (9001-9100)
- 健康检查
- 自动重启

### 2. Model Runtime

- 每个模型一个独立的 FastAPI 服务
- ONNX Runtime 推理
- 支持目标检测和分类

### 3. Deploy Service

- 部署 / 卸载模型
- 推理请求路由
- 部署状态管理

## 扩展性

- 运行时与部署控制分离，后续可接入更多 ONNX 可导出的模型类型
- 目前以 YOLO 检测和分类为主，后续可继续补充分割、姿态或其他视觉模型
- 推理转发和实例管理是通用层，便于后续增加 GPU 调度、版本管理和灰度发布

## 部署方式

按需启用时启动该服务：

```bash
docker-compose up -d model-deploy
```

配置项见下表，通常由 `docker-compose.yml`、Nacos 或部署平台统一注入。

## API 接口

### 健康检查

`/health` 会返回服务状态、运行时依赖和版本号，当前版本为 `1.0.0`。

```bash
GET /health
```

### 部署模型

```bash
POST /deploy
Content-Type: application/json

{
  "model_id": 1,
  "device": "cpu",
  "version": "v1"
}
```

响应：

```json
{
  "success": true,
  "deployment_id": 1,
  "port": 9001
}
```

### 卸载模型

```bash
POST /undeploy/{model_id}
```

### 获取部署列表

```bash
GET /deployments
```

### 执行推理

```bash
POST /predict/{model_id}
Content-Type: multipart/form-data

file: <image_file>
```

### Base64 推理

```bash
POST /predict/{model_id}/base64
Content-Type: application/json

{
  "image": "base64_encoded_image_string"
}
```

### URL 推理

```bash
POST /predict/{model_id}/url
Content-Type: application/json

{
  "image_url": "https://example.com/presigned-image-url"
}
```

迁移期同时保留 `base64` 和 `url` 两种方式，便于上游逐步切换到 presigned URL。

### 检查部署健康

```bash
GET /deploy/{model_id}/health
```

### 重启运行时

```bash
POST /runtime/{model_id}/restart
```

### 转换 YOLO 到 ONNX

```bash
POST /convert/yolo-to-onnx
Content-Type: application/json

{
  "pt_path": "/path/to/model.pt",
  "output_path": "/path/to/model.onnx"
}
```

## 工作流程

### 1. 部署流程

```
1. 接收部署请求 (API)
2. 从 S3 拉取 ONNX 模型
3. 校验模型文件
4. 启动 Runtime 实例 (独立进程)
5. 注册实例 (端口 / PID)
6. 通过 MQ 回传 `model.deployed`，由主服务更新数据库
```

### 2. 推理流程

```
1. 接收推理请求
2. 查找对应的 Runtime 实例
3. 转发请求到实例
4. 返回推理结果
```

### 3. 卸载流程

```
1. 接收卸载请求
2. 停止 Runtime 进程
3. 释放端口
4. 通过 MQ 回传 `model.undeployed`，由主服务清理部署状态
```

## 目录结构

```
model_deploy/
├── core/
│   ├── runtime_manager.py   # 运行时管理
│   └── deploy_service.py    # 部署服务逻辑
├── runtime/
│   └── runtime_server.py    # 模型运行时服务
├── db/
│   ├── base.py              # 数据库基础
│   ├── models.py            # 数据模型
│   └── crud.py              # 数据库操作
├── utils/
│   ├── config.py            # 配置管理
│   └── logger.py            # 日志配置
├── server.py                # FastAPI 主服务
├── requirements.txt
└── Dockerfile
```

## 配置项

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| S3_ACCESS_KEY | S3 Access Key | - |
| S3_SECRET_KEY | S3 Secret Key | - |
| S3_ENDPOINT | S3 服务端点 | - |
| S3_MODELS_BUCKET | 模型存储 Bucket | - |
| RABBITMQ_HOST | RabbitMQ 主机 | localhost |
| RABBITMQ_PORT | RabbitMQ 端口 | 5672 |
| RABBITMQ_USER | RabbitMQ 用户名 | automl |
| RABBITMQ_PASSWORD | RabbitMQ 密码 | automl123456 |
| RABBITMQ_VHOST | RabbitMQ 虚拟主机 | / |
| RABBITMQ_EXCHANGE | RabbitMQ Exchange | auto_ml_exchange |
| RABBITMQ_EXCHANGE_TYPE | RabbitMQ Exchange 类型 | topic |
| RUNTIME_BASE_PORT | 运行时起始端口 | 9001 |
| RUNTIME_MAX_PORT | 运行时最大端口 | 9100 |
| MODEL_CACHE_DIR | 模型缓存目录 | ./models |
| HOST | 服务监听地址 | 0.0.0.0 |
| PORT | 服务端口 | 8082 |
| USE_NACOS | 是否启用 Nacos | true |
| NACOS_SERVER_ADDR | Nacos 地址 | 127.0.0.1:8848 |
| NACOS_NAMESPACE | Nacos Namespace | public |
| NACOS_DATA_ID | Nacos Data ID | AUTO_ML_CONFIG |
| NACOS_GROUP | Nacos Group | AUTO_ML |

## 模型格式

### ONNX 模型要求

- 输入: `(1, 3, 640, 640)` - BCHW 格式
- 输出: YOLO 标准输出格式
- 预处理: 归一化到 0-1

### 从 YOLO 导出 ONNX

```python
from ultralytics import YOLO

model = YOLO("yolo11n.pt")
model.export(format="onnx", imgsz=640)
```

## 能力范围

- 多模型部署
- 多实例扩展
- 推理路由
- 健康检查
- 与训练服务打通
